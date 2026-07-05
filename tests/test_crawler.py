from __future__ import annotations

from pathlib import Path

import pytest

from app.crawler import RefreshService
from app.repository import Repository

FIXTURES = Path(__file__).parent / "fixtures"


class FixtureClient:
    """Offline stand-in for the Beijing housing site.

    The crawler only needs two operations: POST list pages and GET detail pages.
    Keeping this fake small lets refresh tests cover orchestration without
    touching the official site.
    """

    def __init__(self, *, fail_building: bool = False):
        self.fail_building = fail_building
        self.get_calls: list[str] = []

    def post_project_list(self, page: int) -> str:
        return (FIXTURES / f"project_list_sjs_p{page}.html").read_text(encoding="utf-8")

    def get(self, url: str) -> str:
        self.get_calls.append(url)
        if "projectID=8156386" in url:
            return (FIXTURES / "project_8156386_ruichen.html").read_text(encoding="utf-8")
        if "projectID=8102776" in url:
            return (FIXTURES / "project_8102776_ruiyu.html").read_text(encoding="utf-8")
        if "pageId=53618755" in url:
            if self.fail_building:
                raise RuntimeError("simulated building network failure")
            return (FIXTURES / "building_571199_ruichen_5.html").read_text(encoding="utf-8")
        return _minimal_project_detail()


def test_refresh_success_uses_fixtures_without_network(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr("app.crawler.RAW_DIR", tmp_path / "raw")
    repo = Repository(tmp_path / "app.db")

    snapshot_id = RefreshService(repo, client=FixtureClient()).refresh()
    dashboard = repo.dashboard()

    assert snapshot_id == repo.latest_successful_snapshot_id()
    assert dashboard["metrics"]["projects"] == 17
    assert dashboard["metrics"]["buildings"] == 5
    assert dashboard["metrics"]["available"] > 0
    assert (tmp_path / "raw" / str(snapshot_id) / "project_list_p1.html").exists()


def test_refresh_failure_preserves_previous_successful_snapshot(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr("app.crawler.RAW_DIR", tmp_path / "raw")
    repo = Repository(tmp_path / "app.db")
    first_snapshot = RefreshService(repo, client=FixtureClient()).refresh()

    with pytest.raises(RuntimeError, match="simulated building network failure"):
        RefreshService(repo, client=FixtureClient(fail_building=True)).refresh()

    assert repo.latest_successful_snapshot_id() == first_snapshot
    assert repo.dashboard()["snapshot"]["id"] == first_snapshot


def _minimal_project_detail() -> str:
    return """
    <html>
      <body>
        <span id="项目名称"></span>
        <span id="预售许可证编号"></span>
        <span id="发证日期"></span>
        <span id="坐落位置"></span>
        <span id="开发企业"></span>
        <span id="建设工程规划许可证编号"></span>
        <span id="批准预售部位"></span>
      </body>
    </html>
    """
