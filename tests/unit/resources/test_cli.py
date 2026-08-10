from __future__ import annotations

import datetime
import inspect
import sys
from collections.abc import Callable
from dataclasses import dataclass
from unittest.mock import MagicMock

import msgspec
import pytest

from multica_py._internal.specs import RawCommandResult
from multica_py._internal.transport import CliTransport
from multica_py.client import MulticaClient
from multica_py.config import ClientConfig, OperationOptions
from multica_py.exceptions import CommandExecutionError, CommandTimeoutError, ValidationError
from multica_py.resources.cli import CliResource


@dataclass(frozen=True)
class RawCliSecretCase:
    name: str
    argv: tuple[str, ...]
    secret: str
    decoded_secret: str | None = None


@dataclass(frozen=True)
class EnvironmentCliSecretCase:
    name: str
    env_key: str


RAW_CLI_SECRET_CASES = (
    RawCliSecretCase(
        "split password", ("--password", "split-password-secret"), "split-password-secret"
    ),
    RawCliSecretCase(
        "equals api key", ("--api-key=equals-api-key-secret",), "equals-api-key-secret"
    ),
    RawCliSecretCase(
        "split client secret", ("--client-secret", "split-client-secret"), "split-client-secret"
    ),
    RawCliSecretCase(
        "url client secret",
        ("https://example.test/callback?client_secret=url-client-secret",),
        "url-client-secret",
    ),
    RawCliSecretCase(
        "url private key",
        ("https://example.test/callback?private_key=url-private-key",),
        "url-private-key",
    ),
    RawCliSecretCase(
        "url credential",
        ("https://example.test/callback?credential=url-credential",),
        "url-credential",
    ),
    RawCliSecretCase(
        "url percent encoded key and value",
        ("https://example.test/callback?to%6ben=opaque%2Durl%2Dsecret%2D7Qz",),
        "opaque%2Durl%2Dsecret%2D7Qz",
        "opaque-url-secret-7Qz",
    ),
    RawCliSecretCase(
        "url plus encoded fragment value",
        ("https://example.test/callback#client%5Fsecret=opaque+plus+secret+7Qz",),
        "opaque+plus+secret+7Qz",
        "opaque plus secret 7Qz",
    ),
    RawCliSecretCase(
        "url raw auth token",
        ("https://example.test/callback?auth_token=raw-auth-token",),
        "raw-auth-token",
    ),
    RawCliSecretCase(
        "url raw access key",
        ("https://example.test/callback?access_key=raw-access-key",),
        "raw-access-key",
    ),
    RawCliSecretCase(
        "url raw passwd",
        ("https://example.test/callback?passwd=raw-passwd",),
        "raw-passwd",
    ),
    RawCliSecretCase(
        "url percent auth token",
        ("https://example.test/callback?auth%5Ftoken=opaque%2Dauth%2Dtoken%2D7Qz",),
        "opaque%2Dauth%2Dtoken%2D7Qz",
        "opaque-auth-token-7Qz",
    ),
    RawCliSecretCase(
        "url percent access key",
        ("https://example.test/callback?access%5Fkey=opaque%2Daccess%2Dkey%2D7Qz",),
        "opaque%2Daccess%2Dkey%2D7Qz",
        "opaque-access-key-7Qz",
    ),
    RawCliSecretCase(
        "url percent passwd",
        ("https://example.test/callback?pass%77d=opaque%2Dpasswd%2D7Qz",),
        "opaque%2Dpasswd%2D7Qz",
        "opaque-passwd-7Qz",
    ),
    RawCliSecretCase(
        "url plus auth token",
        ("https://example.test/callback#auth%5Ftoken=opaque+auth+token+7Qz",),
        "opaque+auth+token+7Qz",
        "opaque auth token 7Qz",
    ),
    RawCliSecretCase(
        "url plus access key",
        ("https://example.test/callback#access%5Fkey=opaque+access+key+7Qz",),
        "opaque+access+key+7Qz",
        "opaque access key 7Qz",
    ),
    RawCliSecretCase(
        "url plus passwd",
        ("https://example.test/callback#passwd=opaque+passwd+7Qz",),
        "opaque+passwd+7Qz",
        "opaque passwd 7Qz",
    ),
    RawCliSecretCase(
        "url plus whitespace api key",
        ("https://example.test/callback?api+key=opaque+api+key+7Qz",),
        "opaque+api+key+7Qz",
        "opaque api key 7Qz",
    ),
    RawCliSecretCase(
        "url percent whitespace access key",
        ("https://example.test/callback?access%20key=opaque%2Daccess%2Dkey%2D7Qz",),
        "opaque%2Daccess%2Dkey%2D7Qz",
        "opaque-access-key-7Qz",
    ),
    RawCliSecretCase(
        "url camelCase auth token",
        ("https://example.test/callback?authToken=opaque-auth-token-7Qz",),
        "opaque-auth-token-7Qz",
    ),
    RawCliSecretCase(
        "url camelCase client secret",
        ("https://example.test/callback#route?clientSecret=opaque-client-secret-7Qz",),
        "opaque-client-secret-7Qz",
    ),
    RawCliSecretCase(
        "url prefixed raw auth token",
        ("https://example.test/callback?service_auth_token=prefixed-auth-token-7Qz",),
        "prefixed-auth-token-7Qz",
    ),
    RawCliSecretCase(
        "url suffixed raw access key",
        ("https://example.test/callback?access_key_suffix=suffixed-access-key-7Qz",),
        "suffixed-access-key-7Qz",
    ),
    RawCliSecretCase(
        "url prefixed percent access key",
        ("https://example.test/callback?service%5Faccess%5Fkey=opaque%2Dprefixed%2D7Qz",),
        "opaque%2Dprefixed%2D7Qz",
        "opaque-prefixed-7Qz",
    ),
    RawCliSecretCase(
        "url suffixed plus fragment passwd",
        ("https://example.test/callback#/route?passwd_suffix=opaque+suffix+7Qz",),
        "opaque+suffix+7Qz",
        "opaque suffix 7Qz",
    ),
    RawCliSecretCase(
        "url raw userinfo password",
        ("https://alice:opaque-userinfo-7Qz@example.test/path",),
        "opaque-userinfo-7Qz",
    ),
    RawCliSecretCase(
        "url percent userinfo password",
        ("https://alice:opaque%2Duserinfo%2D7Qz@example.test/path",),
        "opaque%2Duserinfo%2D7Qz",
        "opaque-userinfo-7Qz",
    ),
    RawCliSecretCase(
        "url plus userinfo password",
        ("https://alice:opaque+userinfo+7Qz@example.test/path",),
        "opaque+userinfo+7Qz",
    ),
    RawCliSecretCase(
        "url compact apikey raw",
        ("https://example.test/callback?apikey=compact-apikey-7Qz",),
        "compact-apikey-7Qz",
    ),
    RawCliSecretCase(
        "url compact accesskey percent",
        ("https://example.test/callback?access%6bey=compact%2Daccess%2Dkey%2D7Qz",),
        "compact%2Daccess%2Dkey%2D7Qz",
        "compact-access-key-7Qz",
    ),
    RawCliSecretCase(
        "url compact accesstoken plus",
        ("https://example.test/callback#accesstoken=compact+access+token+7Qz",),
        "compact+access+token+7Qz",
        "compact access token 7Qz",
    ),
    RawCliSecretCase(
        "url compact authtoken raw",
        ("https://example.test/callback?authtoken=compact-authtoken-7Qz",),
        "compact-authtoken-7Qz",
    ),
    RawCliSecretCase(
        "url compact clientsecret percent",
        ("https://example.test/callback#route?client%73ecret=compact%2Dclient%2Dsecret%2D7Qz",),
        "compact%2Dclient%2Dsecret%2D7Qz",
        "compact-client-secret-7Qz",
    ),
    RawCliSecretCase(
        "url compact privatekey plus",
        ("https://example.test/callback?privatekey=compact+private+key+7Qz",),
        "compact+private+key+7Qz",
        "compact private key 7Qz",
    ),
)


ENVIRONMENT_CLI_SECRET_CASES = (
    EnvironmentCliSecretCase("apikey", "APIKEY"),
    EnvironmentCliSecretCase("accesskey", "ACCESSKEY"),
    EnvironmentCliSecretCase("accesstoken", "ACCESSTOKEN"),
    EnvironmentCliSecretCase("authtoken", "AUTHTOKEN"),
    EnvironmentCliSecretCase("clientsecret", "CLIENTSECRET"),
    EnvironmentCliSecretCase("privatekey", "PRIVATEKEY"),
)


def test_cli_command_signature_and_preview_are_shell_safe_and_passive(
    cli_resource_factory: Callable[..., tuple[CliResource, MagicMock]],
) -> None:
    resource, transport = cli_resource_factory()

    signature = inspect.signature(resource.command)
    assert tuple(signature.parameters) == ("argv", "options")
    command = resource.command(
        "issue",
        "new-command",
        "value with spaces",
        "$(touch should-not-run)",
        "",
    )

    assert command.commands == (
        "multica issue new-command 'value with spaces' '$(touch should-not-run)' ''",
    )
    transport.run_bytes.assert_not_called()


def test_cli_command_executes_original_argv_and_returns_safe_immutable_result(
    cli_resource_factory: Callable[..., tuple[CliResource, MagicMock]],
    raw_result: Callable[..., RawCommandResult],
) -> None:
    resource, transport = cli_resource_factory()
    transport.run_bytes.return_value = raw_result(
        ("multica", "issue", "get", "i1"),
        stdout=b"secret stdout",
        stderr=b"secret stderr",
        secret_values=("secret",),
        duration=datetime.timedelta(milliseconds=12),
    )

    result = resource.command("issue", "get", "i1").run()

    assert result.stdout == b"*** stdout"
    assert result.stderr == b"*** stderr"
    assert result.duration == datetime.timedelta(milliseconds=12)
    assert not hasattr(result, "argv")
    assert not hasattr(result, "secret_values")
    with pytest.raises((AttributeError, TypeError, msgspec.ValidationError)):
        result.stdout = b"changed"  # type: ignore[misc]
    transport.run_bytes.assert_called_once_with(("issue", "get", "i1"), stdin=None, timeout=None)


@pytest.mark.parametrize("case", RAW_CLI_SECRET_CASES, ids=lambda case: case.name)
def test_cli_command_redacts_secret_options_in_preview(case: RawCliSecretCase) -> None:
    client = MulticaClient(ClientConfig(executable=sys.executable))
    command = client.cli.command(*case.argv)

    rendered = " ".join((command.commands[0], repr(command)))
    assert case.secret not in rendered
    if case.decoded_secret is not None:
        assert case.decoded_secret not in rendered
    assert "***" in rendered


@pytest.mark.parametrize("case", RAW_CLI_SECRET_CASES, ids=lambda case: case.name)
def test_cli_command_redacts_secret_options_in_success_result(case: RawCliSecretCase) -> None:
    client = MulticaClient(ClientConfig(executable=sys.executable))
    code = (
        "from urllib.parse import parse_qs, urlsplit; import sys; "
        "url=sys.argv[-1]; parts=urlsplit(url); "
        "fragment=parts.fragment.split('?', 1)[-1]; "
        "values=parse_qs(parts.query or fragment).values(); "
        "value=parts.password or next(iter(values))[0]; "
        "sys.stdout.write(value); sys.stderr.write('stderr ' + value)"
        if case.decoded_secret is not None
        else "import sys; sys.stdout.write(' '.join(sys.argv[1:])); "
        "sys.stderr.write('stderr ' + sys.argv[-1])"
    )

    result = client.cli.command("-c", code, *case.argv).run()

    assert case.secret not in result.stdout.decode()
    assert case.secret not in result.stderr.decode()
    if case.decoded_secret is not None:
        assert case.decoded_secret not in result.stdout.decode()
        assert case.decoded_secret not in result.stderr.decode()
    assert b"***" in result.stdout or b"***" in result.stderr


@pytest.mark.parametrize("case", RAW_CLI_SECRET_CASES, ids=lambda case: case.name)
def test_cli_command_redacts_secret_options_in_error_diagnostics(case: RawCliSecretCase) -> None:
    client = MulticaClient(ClientConfig(executable=sys.executable))
    code = (
        "from urllib.parse import parse_qs, urlsplit; import sys; "
        "url=sys.argv[-1]; parts=urlsplit(url); "
        "fragment=parts.fragment.split('?', 1)[-1]; "
        "values=parse_qs(parts.query or fragment).values(); "
        "value=parts.password or next(iter(values))[0]; "
        "sys.stdout.write('stdout ' + value); sys.stderr.write('stderr ' + value); sys.exit(1)"
        if case.decoded_secret is not None
        else "import sys; sys.stdout.write('stdout ' + sys.argv[-1]); "
        "sys.stderr.write('stderr ' + sys.argv[-1]); sys.exit(1)"
    )

    with pytest.raises(CommandExecutionError) as exc_info:
        client.cli.command("-c", code, *case.argv).run()

    exc = exc_info.value
    assert case.secret not in str(exc)
    assert case.secret not in exc.stdout
    assert case.secret not in exc.stderr
    assert case.secret not in exc.argv
    if case.decoded_secret is not None:
        assert case.decoded_secret not in str(exc)
        assert case.decoded_secret not in exc.stdout
        assert case.decoded_secret not in exc.stderr
        assert case.decoded_secret not in exc.argv
    assert "***" in exc.stdout or "***" in exc.stderr


@pytest.mark.parametrize("case", ENVIRONMENT_CLI_SECRET_CASES, ids=lambda case: case.name)
def test_cli_command_redacts_compact_environment_secrets_across_surfaces(
    case: EnvironmentCliSecretCase,
) -> None:
    secret = f"{case.name}-environment-secret-7Qz"
    config = ClientConfig(
        executable=sys.executable,
        environment=((case.env_key, secret),),
    )
    client = MulticaClient(config)
    success_code = (
        "import os, sys; value=os.environ[sys.argv[1]] + '|' + sys.argv[-1]; "
        "sys.stdout.write(value); sys.stderr.write(value)"
    )
    error_code = (
        "import os, sys; value=os.environ[sys.argv[1]] + '|' + sys.argv[-1]; "
        "sys.stdout.write(value); sys.stderr.write(value); sys.exit(1)"
    )

    preview = client.cli.command("-c", success_code, case.env_key, secret)
    rendered = " ".join((preview.commands[0], repr(preview)))
    assert secret not in rendered
    assert "***" in rendered

    result = client.cli.command("-c", success_code, case.env_key, secret).run()
    assert secret not in result.stdout.decode()
    assert secret not in result.stderr.decode()
    assert b"***" in result.stdout or b"***" in result.stderr

    with pytest.raises(CommandExecutionError) as exc_info:
        client.cli.command("-c", error_code, case.env_key, secret).run()
    exc = exc_info.value
    for diagnostic in (str(exc), exc.stdout, exc.stderr, exc.argv, repr(exc)):
        assert secret not in diagnostic
    assert "***" in exc.stdout or "***" in exc.stderr


def test_cli_command_honors_operation_options_without_argv_pollution(
    cli_resource_factory: Callable[..., tuple[CliResource, MagicMock]],
    raw_result: Callable[..., RawCommandResult],
) -> None:
    resource, transport = cli_resource_factory(ClientConfig(profile="base", workspace_id="base-ws"))
    transport.run_bytes.return_value = raw_result(("multica", "--profile", "operation", "x"))

    command = resource.command(
        "x",
        options=OperationOptions(
            profile="operation",
            workspace_id="operation-ws",
            timeout=5,
        ),
    )

    assert command.commands == ("multica x",)
    command.run()
    transport.run_bytes.assert_called_once_with(("x",), stdin=None, timeout=None)
    assert command._plan.config_snapshot.profile == "operation"
    assert command._plan.config_snapshot.workspace_id == "operation-ws"
    assert command._plan.config_snapshot.timeout == datetime.timedelta(seconds=5)


@pytest.mark.parametrize(
    ("argv", "error"),
    (
        ((), ValueError),
        (("",), ValueError),
        (("   ",), ValueError),
        (("multica", "version"), ValueError),
        (("issue", 1), TypeError),
        (("issue\x00get",), ValueError),
        (("issue", "get\x00"), ValueError),
    ),
)
def test_cli_command_rejects_invalid_argv_before_transport(
    argv: tuple[object, ...],
    error: type[Exception],
    cli_resource_factory: Callable[..., tuple[CliResource, MagicMock]],
) -> None:
    resource, transport = cli_resource_factory()

    with pytest.raises(error):
        resource.command(*argv)  # type: ignore[arg-type]

    transport.build_full_argv.assert_not_called()
    transport.run_bytes.assert_not_called()


def test_cli_command_allows_later_empty_argv_values(
    cli_resource_factory: Callable[..., tuple[CliResource, MagicMock]],
    raw_result: Callable[..., RawCommandResult],
) -> None:
    resource, transport = cli_resource_factory()
    transport.run_bytes.return_value = raw_result(("multica", "issue", "update", ""))

    command = resource.command("issue", "update", "")

    assert command.commands == ("multica issue update ''",)
    command.run()
    transport.run_bytes.assert_called_once_with(("issue", "update", ""), stdin=None, timeout=None)


def test_cli_command_preserves_timeout_failure_classification(
    cli_resource_factory: Callable[..., tuple[CliResource, MagicMock]],
) -> None:
    resource, transport = cli_resource_factory()
    transport.run_bytes.side_effect = CommandTimeoutError("timed out")

    with pytest.raises(CommandTimeoutError, match="timed out"):
        resource.command("issue", "slow").run()


def test_cli_transport_raw_nonzero_failure_remains_typed_and_redacted(
    raw_result: Callable[..., RawCommandResult],
) -> None:
    config = ClientConfig()
    transport = CliTransport(config)
    resource = CliResource(transport, config)

    def fail(_args: tuple[str, ...], **_kwargs: object) -> RawCommandResult:
        return raw_result(
            ("multica", "issue", "validate", "--token", "***"),
            stdout=b"Invalid request: secret",
            stderr=b"",
            exit_code=5,
            secret_values=("secret",),
        )

    transport._execute = fail  # type: ignore[assignment]
    with pytest.raises(ValidationError) as raised:
        resource.command("issue", "validate", "--token", "secret").run()

    assert "secret" not in str(raised.value)
    assert raised.value.argv == ("multica", "issue", "validate", "--token", "***")
