from __future__ import annotations

import pytest

from multica_py.client import MulticaClient
from tests.live.oracle import DirectApiOracle
from tests.live.settings import label_name

pytestmark = [pytest.mark.live, pytest.mark.live_extended]


def test_project_description_absent_empty_and_null_semantics(
    api_oracle: DirectApiOracle,
    register_resource,
    resource_name: str,
) -> None:
    """Verify raw project description absent, empty, and null shapes without SDK normalization."""
    omitted = api_oracle.create_project(f"{resource_name}-omit")
    omitted_id = str(omitted["id"])
    register_resource(
        key=f"project-{omitted_id}",
        cleanup=api_oracle.delete_callback(f"/api/projects/{omitted_id}", "project"),
    )
    omitted_body = api_oracle.get_project(omitted_id)
    with pytest.raises(KeyError):
        api_oracle.project_description(omitted_body)

    empty = api_oracle.create_project(f"{resource_name}-empty", description="")
    empty_id = str(empty["id"])
    register_resource(
        key=f"project-{empty_id}",
        cleanup=api_oracle.delete_callback(f"/api/projects/{empty_id}", "project"),
    )
    assert api_oracle.project_description(api_oracle.get_project(empty_id)) == ""

    api_oracle.update_project(omitted_id, {"description": None})
    assert api_oracle.project_description(api_oracle.get_project(omitted_id)) is None


def test_label_optional_color_and_issue_raw_fields_without_sdk_normalization(
    live_client: MulticaClient,
    api_oracle: DirectApiOracle,
    register_resource,
    resource_name: str,
) -> None:
    """Verify oracle label color and raw issue fields remain visible without SDK decode."""
    label = api_oracle.create_label(label_name(resource_name, "opt"), color="#abcdef")
    label_id = str(label["id"])
    register_resource(
        key=f"label-{label_id}",
        cleanup=api_oracle.delete_callback(f"/api/labels/{label_id}", "label"),
    )
    raw_label = api_oracle.get_label(label_id)
    assert raw_label.get("color") == "#abcdef"

    issue = api_oracle.create_issue(f"{resource_name}-optional-fields", description="")
    issue_id = str(issue["id"])
    register_resource(
        key=f"issue-{issue_id}",
        cleanup=api_oracle.delete_callback(f"/api/issues/{issue_id}", "issue"),
    )
    raw_issue = api_oracle.get_issue(issue_id)
    assert raw_issue.get("description") == ""
    assert isinstance(raw_issue.get("id"), str)
    sdk_issue = live_client.issues.get(issue_id)
    assert sdk_issue.description == ""
    assert sdk_issue.id == issue_id
    assert set(raw_issue.keys()) >= {"id", "title", "status"}
