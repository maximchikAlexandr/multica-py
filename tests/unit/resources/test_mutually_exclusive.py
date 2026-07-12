from __future__ import annotations

import pytest

from multica_py._internal.transport import CliTransport
from multica_py.config import ClientConfig
from multica_py.models.issues import (
    FileDescription,
    InlineDescription,
    IssueAssignmentRequest,
    IssueCreateRequest,
    IssueReorderRequest,
    NoDescription,
    StdinDescription,
)
from multica_py.resources.issues import IssueResource


def test_description_input_is_tagged_union():
    req = IssueCreateRequest(title="Test")
    assert isinstance(req.description_input, NoDescription)


def test_inline_description_is_exclusive():
    req = IssueCreateRequest(title="Test", description_input=InlineDescription(text="hello"))
    assert isinstance(req.description_input, InlineDescription)
    assert not isinstance(req.description_input, (FileDescription, StdinDescription, NoDescription))


def test_file_description_is_exclusive():
    req = IssueCreateRequest(title="Test", description_input=FileDescription(path="/tmp/desc"))
    assert isinstance(req.description_input, FileDescription)
    assert not isinstance(
        req.description_input, (InlineDescription, StdinDescription, NoDescription)
    )


def test_stdin_description_is_exclusive():
    req = IssueCreateRequest(title="Test", description_input=StdinDescription())
    assert isinstance(req.description_input, StdinDescription)
    assert not isinstance(
        req.description_input, (InlineDescription, FileDescription, NoDescription)
    )


def test_unknown_description_type_rejected():
    req = IssueCreateRequest(title="Test", description_input=InlineDescription(text="a"))
    desc = req.description_input
    assert not isinstance(desc, (FileDescription, StdinDescription))
    args = ["issue", "create", "--title", "Test"]
    if isinstance(desc, InlineDescription):
        args.extend(["--description", desc.text])
    elif isinstance(desc, FileDescription):
        args.extend(["--description-file", desc.path])
    elif isinstance(desc, StdinDescription):
        args.append("--description-stdin")
    assert "--description" in args
    assert "--description-file" not in args
    assert "--description-stdin" not in args


def test_invalid_value_rejected():
    with pytest.raises(TypeError):
        IssueCreateRequest(title="Test", description_input="some random string")  # type: ignore[arg-type]


def test_description_dispatch():
    req = IssueCreateRequest(title="Test", description_input=InlineDescription(text="a"))
    transport = CliTransport(ClientConfig())
    IssueResource(transport, ClientConfig())
    args = ["issue", "create", "--title", "Test"]
    desc = req.description_input
    if isinstance(desc, InlineDescription):
        args.extend(["--description", desc.text])
    elif isinstance(desc, FileDescription):
        args.extend(["--description-file", desc.path])
    elif isinstance(desc, StdinDescription):
        args.append("--description-stdin")
    assert "--description" in args
    assert "--description-file" not in args


def test_issue_assignment_request_rejects_multiple_targets():
    with pytest.raises(ValueError, match="Exactly one assignment target must be set"):
        IssueAssignmentRequest(issue_id="iss_001", member_id="usr_001", unassign=True)


def test_issue_reorder_request_rejects_multiple_targets():
    with pytest.raises(ValueError, match="Exactly one reorder target must be set"):
        IssueReorderRequest(issue_id="iss_001", before_id="iss_002", bottom=True)
