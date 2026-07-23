from __future__ import annotations

import pytest

from tests.live._live_helpers import label_name
from tests.live.session import LiveCase, LiveSession

pytestmark = [pytest.mark.live, pytest.mark.live_extended, pytest.mark.serial]


def test_project_description_absent_empty_and_null_semantics(
    live_session: LiveSession,
    live_case: LiveCase,
) -> None:
    """Verify raw project description absent, empty, and null shapes without SDK normalization."""
    omitted = live_session.oracle.create_project(f"{live_case.unique_name}-omit")
    omitted_id = str(omitted["id"])
    live_case.defer_cleanup(
        live_session.oracle.delete_callback(f"/api/projects/{omitted_id}", "project"),
    )
    omitted_body = live_session.oracle.get_project(omitted_id)
    if "description" not in omitted_body:
        with pytest.raises(KeyError):
            live_session.oracle.project_description(omitted_body)
    else:
        assert omitted_body["description"] in (None, "")

    empty = live_session.oracle.create_project(f"{live_case.unique_name}-empty", description="")
    empty_id = str(empty["id"])
    live_case.defer_cleanup(
        live_session.oracle.delete_callback(f"/api/projects/{empty_id}", "project"),
    )
    assert live_session.oracle.project_description(live_session.oracle.get_project(empty_id)) == ""

    live_session.oracle.update_project(omitted_id, {"description": None})
    assert (
        live_session.oracle.project_description(live_session.oracle.get_project(omitted_id)) is None
    )


def test_label_optional_color_and_issue_raw_fields_without_sdk_normalization(
    live_session: LiveSession,
    live_case: LiveCase,
) -> None:
    """Verify oracle label color and raw issue fields remain visible without SDK decode."""
    label = live_session.oracle.create_label(
        label_name(live_case.unique_name, "opt"), color="#abcdef"
    )
    label_id = str(label["id"])
    live_case.defer_cleanup(live_session.oracle.delete_callback(f"/api/labels/{label_id}", "label"))
    raw_label = live_session.oracle.get_label(label_id)
    assert raw_label.get("color") == "#abcdef"

    issue = live_session.oracle.create_issue(
        f"{live_case.unique_name}-optional-fields", description=""
    )
    issue_id = str(issue["id"])
    live_case.defer_cleanup(live_session.oracle.delete_callback(f"/api/issues/{issue_id}", "issue"))
    raw_issue = live_session.oracle.get_issue(issue_id)
    assert raw_issue.get("description") == ""
    assert isinstance(raw_issue.get("id"), str)
    sdk_issue = live_session.client.issues.get(issue_id)
    assert sdk_issue.description == ""
    assert sdk_issue.id == issue_id
    assert set(raw_issue.keys()) >= {"id", "title", "status"}
