"""Human-facing multica-py command line."""

from __future__ import annotations

from typing import Annotated

import typer

from multica_py.bug_report import (
    BugReportError,
    ReportKind,
    as_json,
    init_report,
    preview_report,
    submit_report,
)

app = typer.Typer(
    no_args_is_help=True,
    pretty_exceptions_enable=False,
    help="Utilities shipped with multica-py.",
)
bug_report_app = typer.Typer(
    no_args_is_help=True,
    help="Create and publish reproducible bug reports.",
)
app.add_typer(bug_report_app, name="bug-report")


def _fail(error: BugReportError) -> None:
    typer.echo(f"error: {error}", err=True)
    raise typer.Exit(1)


@bug_report_app.command("init")  # type: ignore[misc]
def bug_report_init(
    title: Annotated[str, typer.Option(help="One-line GitHub issue title.")],
    kind: Annotated[
        ReportKind,
        typer.Option(help="Report kind recorded in the local draft."),
    ] = "bug",
    json_output: Annotated[
        bool,
        typer.Option("--json", help="Print one JSON document."),
    ] = False,
) -> None:
    """Create a private local draft under ~/.multica-py/bug-reports."""

    try:
        draft = init_report(title, kind)
    except BugReportError as error:
        _fail(error)
    if json_output:
        typer.echo(as_json(draft))
    else:
        typer.echo(f"Created {draft.report_id}: {draft.directory}/report.md")


@bug_report_app.command("submit")  # type: ignore[misc]
def bug_report_submit(
    report_id: Annotated[str, typer.Argument(help="Complete draft UUID.")],
    dry_run: Annotated[
        bool,
        typer.Option("--dry-run", help="Validate and print review data without publishing."),
    ] = False,
    json_output: Annotated[
        bool,
        typer.Option("--json", help="Print one JSON document."),
    ] = False,
) -> None:
    """Validate a draft and publish it after independent approval."""

    try:
        preview = preview_report(report_id)
        if dry_run:
            typer.echo(as_json(preview) if json_output else _preview_text(preview))
            if preview.blockers:
                raise typer.Exit(1)
            return
        issue_url = submit_report(report_id)
    except BugReportError as error:
        _fail(error)
    typer.echo(issue_url)


def _preview_text(preview: object) -> str:
    from multica_py.bug_report import Preview

    if not isinstance(preview, Preview):
        raise TypeError("preview must be a Preview")
    lines = [
        f"Payload SHA-256: {preview.payload_sha256}",
        f"Approved: {'yes' if preview.approved else 'no'}",
    ]
    if preview.next_review_path:
        lines.append(f"Next review: {preview.next_review_path}")
    lines.extend(f"Blocker: {blocker}" for blocker in preview.blockers)
    return "\n".join(lines)


if __name__ == "__main__":
    app()
