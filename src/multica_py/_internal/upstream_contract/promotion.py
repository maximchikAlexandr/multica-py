from __future__ import annotations

import contextlib
import hashlib
import os
import pathlib
import shutil
import tempfile
import time

import msgspec

from .coverage import collect_contract_review_items
from .models import (
    CandidateBaseline,
    PromotionDecision,
    SemanticCLIContract,
    SupportedBaseline,
    UpstreamState,
)
from .normalize import canonical_bytes, semantic_hash
from .paths import SUPPORTED_CONTRACT_REL
from .provenance import is_full_commit
from .schema import decode_contract
from .state import replace_supported

PROMOTION_SCHEMA_VERSION = 1
JOURNAL_SCHEMA_VERSION = 1

ALLOWED_TRUST_LEVELS: tuple[str, ...] = ("verified", "approved-contract-bound")

_LOCK_REL = pathlib.Path(".devlocal") / "upstream-promotion.lock"
_JOURNAL_REL = pathlib.Path(".devlocal") / "upstream-promotion-journal.json"
_BACKUP_SUFFIX = ".promote-backup"

PROMOTION_DESTINATIONS: tuple[str, ...] = (
    "src/multica_py/_generated/upstream_supported_contract.json",
    "src/multica_py/_generated/upstream_state.json",
    "src/multica_py/_generated/upstream_coverage.json",
    "src/multica_py/_generated/cli_manifest.json",
    "contracts/multica-live-target.toml",
)


class PromotionError(ValueError):
    """Promotion refused with an explicit failure category."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


class PromotionTransactionError(ValueError):
    """Transaction-level failure (lock, journal, rollback)."""


class JournalEntry(msgspec.Struct, frozen=True, kw_only=True):
    ordinal: int
    destination: str
    original_sha256: str
    staged_sha256: str


class PromotionJournal(msgspec.Struct, frozen=True, kw_only=True):
    schema_version: int
    transaction_id: str
    ordinal: int
    state: str
    destinations: tuple[str, ...]
    entries: tuple[JournalEntry, ...]


def validate_promotion(decision: PromotionDecision) -> PromotionDecision:
    if not is_full_commit(decision.candidate_commit):
        raise ValueError(f"candidate_commit must be 40-char hex, got {decision.candidate_commit!r}")
    if not is_full_commit(decision.previous_supported_commit):
        raise ValueError(
            f"previous_supported_commit must be 40-char hex, got {decision.previous_supported_commit!r}"
        )
    if not decision.candidate_semantic_hash.startswith("sha256:"):
        raise ValueError("candidate_semantic_hash must be sha256: prefix")
    if not decision.clean_gate_ref:
        raise ValueError("clean_gate_ref is required")
    if not decision.reviewer:
        raise ValueError("reviewer is required")
    return decision


def apply_promotion(
    state: UpstreamState,
    decision: PromotionDecision,
    candidate: CandidateBaseline,
    *,
    candidate_contract: SemanticCLIContract,
) -> UpstreamState:
    validate_promotion(decision)
    contract_trust = candidate_contract.artifact.trust_level
    if contract_trust not in ALLOWED_TRUST_LEVELS:
        raise PromotionError(
            "trust",
            f"candidate contract trust_level {contract_trust!r} not in {ALLOWED_TRUST_LEVELS}; "
            "refusing to promote",
        )
    if candidate.trust_level not in ALLOWED_TRUST_LEVELS:
        raise PromotionError(
            "trust",
            f"candidate trust_level {candidate.trust_level!r} not in {ALLOWED_TRUST_LEVELS}; "
            "refusing to promote",
        )
    if contract_trust != candidate.trust_level:
        raise PromotionError(
            "trust",
            f"candidate contract trust_level {contract_trust!r} does not match "
            f"state candidate trust_level {candidate.trust_level!r}",
        )
    if candidate.unresolved_items:
        raise PromotionError(
            "unresolved",
            f"candidate has unresolved_items: {', '.join(candidate.unresolved_items)}",
        )
    if state.observed is not None and candidate.version != state.observed.version:
        raise PromotionError(
            "version_mismatch",
            f"candidate.version {candidate.version!r} does not match "
            f"observed.version {state.observed.version!r}",
        )
    _verify_candidate_contract_hash(candidate, decision, candidate_contract)
    review_items = collect_contract_review_items(candidate_contract)
    if review_items:
        raise PromotionError(
            "unresolved",
            f"candidate contract has review_items: {', '.join(review_items)}",
        )
    if candidate.commit != decision.candidate_commit:
        raise ValueError("candidate.commit does not match decision.candidate_commit")
    if candidate.semantic_hash != decision.candidate_semantic_hash:
        raise ValueError("candidate.semantic_hash does not match decision.candidate_semantic_hash")
    if state.supported and state.supported.commit != decision.previous_supported_commit:
        raise ValueError("decision.previous_supported_commit does not match current supported")
    new_supported = SupportedBaseline(
        version=decision.candidate_version,
        tag=decision.candidate_tag,
        commit=decision.candidate_commit,
        semantic_hash=decision.candidate_semantic_hash,
        contract_ref=SUPPORTED_CONTRACT_REL,
    )
    return replace_supported(state, new_supported)


def _verify_candidate_contract_hash(
    candidate: CandidateBaseline,
    decision: PromotionDecision,
    candidate_contract: SemanticCLIContract,
) -> None:
    on_disk_hash = candidate_contract.artifact.semantic_hash
    recomputed_hash = semantic_hash(candidate_contract)
    if on_disk_hash and on_disk_hash != recomputed_hash:
        raise PromotionError(
            "hash_mismatch",
            "on-disk candidate artifact.semantic_hash does not match recomputed digest",
        )
    effective_hash = on_disk_hash if on_disk_hash.startswith("sha256:") else recomputed_hash
    if effective_hash != decision.candidate_semantic_hash:
        raise PromotionError(
            "hash_mismatch",
            "candidate contract semantic_hash does not match promotion decision",
        )
    if effective_hash != candidate.semantic_hash:
        raise PromotionError(
            "hash_mismatch",
            "candidate contract semantic_hash does not match state.candidate.semantic_hash",
        )


def write_promoted_artifacts(
    *,
    repo_root: pathlib.Path,
    new_state: UpstreamState,
    candidate_contract: SemanticCLIContract,
    state_path: pathlib.Path,
) -> None:
    if new_state.supported is None:
        raise ValueError("promoted state must include supported baseline")
    contract_path = repo_root / SUPPORTED_CONTRACT_REL
    contract_payload: dict[str, object] = msgspec.to_builtins(candidate_contract)
    contract_bytes = canonical_bytes(contract_payload) + b"\n"
    state_payload: dict[str, object] = msgspec.to_builtins(new_state)
    state_bytes = canonical_bytes(state_payload) + b"\n"
    parent = contract_path.parent
    parent.mkdir(parents=True, exist_ok=True)
    staging = pathlib.Path(tempfile.mkdtemp(prefix="promote.", dir=str(parent)))
    try:
        staging_contract = staging / contract_path.name
        staging_state = staging / state_path.name
        staging_contract.write_bytes(contract_bytes)
        staging_state.write_bytes(state_bytes)
        os.replace(staging_contract, contract_path)
        os.replace(staging_state, state_path)
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    finally:
        if staging.exists():
            shutil.rmtree(staging, ignore_errors=True)


def load_candidate_contract(
    repo_root: pathlib.Path,
    candidate: CandidateBaseline,
) -> SemanticCLIContract:
    return decode_contract(repo_root / candidate.contract_ref)


def apply_rejection(
    state: UpstreamState,
    decision: PromotionDecision,
) -> UpstreamState:
    if not decision.reviewer:
        raise ValueError("rejection requires a reviewer")
    if state.candidate is None:
        return state
    return msgspec.structs.replace(state, candidate=None)


def _fsync_parent(path: pathlib.Path) -> None:
    fd = os.open(str(path.parent), os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _backup_path(dest: pathlib.Path) -> pathlib.Path:
    return dest.parent / (dest.name + _BACKUP_SUFFIX)


class PromotionTransaction:
    """Rollback-capable 5-destination promotion writer.

    Usage:

        txn = PromotionTransaction(repo_root)
        txn.run(contract_bytes, state_bytes, coverage_bytes,
                manifest_bytes, live_target_bytes)

    On success the journal and backup files are cleaned up.  On any failure
    completed destinations are restored from backup and the journal is marked
    ``rolled_back``.

    Call ``PromotionTransaction.recover_prepared(repo_root)`` at startup to
    recover any interrupted transaction.
    """

    def __init__(self, repo_root: pathlib.Path, *, _failure_before: int | None = None):
        self._repo_root = repo_root.resolve()
        self._lock_path = self._repo_root / _LOCK_REL
        self._journal_path = self._repo_root / _JOURNAL_REL
        self._failure_before = _failure_before
        self._lock_fd: int | None = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(self, *contents: bytes) -> None:
        if len(contents) != 5:
            raise ValueError(f"PromotionTransaction needs 5 byte strings, got {len(contents)}")
        self._acquire_lock()
        txn_id: str = f"{time.time_ns():x}{os.urandom(4).hex()}"
        entries: list[JournalEntry] = []
        journal: PromotionJournal
        try:
            for i, (dest_rel, content) in enumerate(zip(PROMOTION_DESTINATIONS, contents), start=1):
                dest = self._repo_root / dest_rel
                orig_bytes: bytes | None = dest.read_bytes() if dest.is_file() else None
                orig_sha = _sha256_bytes(orig_bytes) if orig_bytes is not None else ""
                staged_sha = _sha256_bytes(content)
                entries.append(
                    JournalEntry(
                        ordinal=i,
                        destination=dest_rel,
                        original_sha256=orig_sha,
                        staged_sha256=staged_sha,
                    )
                )
            journal = PromotionJournal(
                schema_version=JOURNAL_SCHEMA_VERSION,
                transaction_id=txn_id,
                ordinal=0,
                state="prepared",
                destinations=PROMOTION_DESTINATIONS,
                entries=tuple(entries),
            )
            self._write_journal_raw(journal)
            journal = self._replace_all(PROMOTION_DESTINATIONS, contents, journal)
            committed = msgspec.structs.replace(journal, ordinal=5, state="committed")
            self._write_journal_raw(committed)
            self._cleanup()
        except BaseException:
            current = self._read_journal()
            self._rollback(journal if current is None else current)
            raise
        finally:
            self._release_lock()

    @classmethod
    def recover_prepared(cls, repo_root: pathlib.Path) -> None:
        journal_path = repo_root / _JOURNAL_REL
        if not journal_path.is_file():
            return
        raw = journal_path.read_bytes()
        if not raw.strip():
            journal_path.unlink(missing_ok=True)
            return
        journal: PromotionJournal = msgspec.json.decode(raw, type=PromotionJournal)
        if journal.state != "prepared":
            journal_path.unlink(missing_ok=True)
            return
        txn = cls(repo_root)
        txn._acquire_lock()
        try:
            txn._restore_range(journal.ordinal, journal.destinations)
            rolled_back = msgspec.structs.replace(journal, state="rolled_back")
            txn._write_journal_raw(rolled_back)
            txn._cleanup_backups(journal.destinations)
        finally:
            txn._release_lock()

    # ------------------------------------------------------------------
    # Lock
    # ------------------------------------------------------------------

    def _acquire_lock(self) -> None:
        self._lock_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            self._lock_fd = os.open(str(self._lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(self._lock_fd, str(os.getpid()).encode())
        except FileExistsError:
            raise PromotionTransactionError("promotion lock already held")

    def _release_lock(self) -> None:
        if self._lock_fd is not None:
            os.close(self._lock_fd)
            self._lock_fd = None
            self._lock_path.unlink(missing_ok=True)

    # ------------------------------------------------------------------
    # Journal
    # ------------------------------------------------------------------

    def _write_journal_raw(self, journal: PromotionJournal) -> None:
        self._journal_path.parent.mkdir(parents=True, exist_ok=True)
        data = msgspec.json.encode(journal)
        tmp = self._journal_path.with_suffix(".journal.tmp")
        tmp.write_bytes(data)
        _fsync_parent(tmp)
        os.replace(tmp, self._journal_path)

    def _read_journal(self) -> PromotionJournal | None:
        if not self._journal_path.is_file():
            return None
        return msgspec.json.decode(self._journal_path.read_bytes(), type=PromotionJournal)

    # ------------------------------------------------------------------
    # Replace
    # ------------------------------------------------------------------

    def _replace_all(
        self,
        destinations: tuple[str, ...],
        contents: tuple[bytes, ...],
        journal: PromotionJournal,
    ) -> PromotionJournal:
        current = journal
        for i, (dest_rel, content) in enumerate(zip(destinations, contents), start=1):
            if self._failure_before is not None and i == self._failure_before:
                raise PromotionTransactionError(f"injected failure before ordinal {i}")
            current = self._replace_one(dest_rel, content, i, current)
        return current

    def _replace_one(
        self,
        dest_rel: str,
        content: bytes,
        ordinal: int,
        journal: PromotionJournal,
    ) -> PromotionJournal:
        dest = self._repo_root / dest_rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        # Stage
        with tempfile.NamedTemporaryFile(
            prefix=f".promote.{dest.name}.", dir=str(dest.parent), delete=False
        ) as tmp:
            tmp.write(content)
            tmp.flush()
            os.fsync(tmp.fileno())
            stage = pathlib.Path(tmp.name)
        # Backup
        if dest.is_file():
            shutil.copy2(dest, _backup_path(dest))
        # Replace
        os.replace(stage, dest)
        _fsync_parent(dest)
        # Journal progress
        updated = msgspec.structs.replace(journal, ordinal=ordinal)
        self._write_journal_raw(updated)
        return updated

    # ------------------------------------------------------------------
    # Rollback
    # ------------------------------------------------------------------

    def _rollback(self, journal: PromotionJournal) -> None:
        self._restore_range(journal.ordinal, PROMOTION_DESTINATIONS)
        rolled_back = msgspec.structs.replace(journal, state="rolled_back")
        with contextlib.suppress(BaseException):
            self._write_journal_raw(rolled_back)
        self._cleanup_backups(PROMOTION_DESTINATIONS)

    def _restore_range(self, up_to_ordinal: int, destinations: tuple[str, ...]) -> None:
        for i in range(up_to_ordinal, 0, -1):
            dest_rel = destinations[i - 1]
            dest = self._repo_root / dest_rel
            backup = _backup_path(dest)
            if backup.is_file():
                os.replace(backup, dest)
                _fsync_parent(dest)
            elif dest.is_file():
                dest.unlink()
                _fsync_parent(dest)

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------

    def _cleanup(self) -> None:
        self._cleanup_backups(PROMOTION_DESTINATIONS)
        self._journal_path.unlink(missing_ok=True)

    def _cleanup_backups(self, destinations: tuple[str, ...]) -> None:
        for dest_rel in destinations:
            backup = _backup_path(self._repo_root / dest_rel)
            backup.unlink(missing_ok=True)
