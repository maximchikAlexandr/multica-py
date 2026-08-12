from multica_py import Page
from multica_py.entities.issues import Issue
from multica_py.models.autopilots import AutopilotListPage, AutopilotRunListPage
from multica_py.models.issues import IssueChildrenResult, IssueListPage

issue_page: IssueListPage = IssueListPage(issues=())
children_page: IssueChildrenResult = IssueChildrenResult(children=())
autopilot_page: AutopilotListPage[str] = AutopilotListPage(autopilots=())
run_page: AutopilotRunListPage[int] = AutopilotRunListPage(runs=())

issue_items: tuple[Issue, ...] = children_page.items
issue_alias: tuple[Issue, ...] = children_page.children
page_of_issue: Page[Issue] = children_page
assert issue_items is issue_alias

issue_items_from_list: tuple[Issue, ...] = issue_page.items
autopilot_items: tuple[str, ...] = autopilot_page.items
run_items: tuple[int, ...] = run_page.items
