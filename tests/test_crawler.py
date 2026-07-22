from __future__ import annotations

from pathlib import Path

import httpx
import pytest

from app.crawler import RefreshService, ZjwClient, _merge_project
from app.models import OfficialProject
from app.repository import Repository

FIXTURES = Path(__file__).parent / "fixtures"


class FixtureClient:
    """Offline stand-in for the Beijing housing site.

    The crawler only needs two operations: POST list pages and GET detail pages.
    Keeping this fake small lets refresh tests cover orchestration without
    touching the official site.
    """

    def __init__(
        self,
        *,
        fail_building: bool = False,
        omit_ruichen_buildings: bool = False,
        incomplete_list_once: bool = False,
        always_incomplete_list: bool = False,
    ):
        self.fail_building = fail_building
        self.omit_ruichen_buildings = omit_ruichen_buildings
        self.incomplete_list_once = incomplete_list_once
        self.always_incomplete_list = always_incomplete_list
        self.get_calls: list[str] = []
        self.list_calls = 0
        self.retries = 3

    def post_project_list(self, page: int) -> str:
        self.list_calls += 1
        if self.always_incomplete_list or (
            self.incomplete_list_once and self.list_calls <= 2
        ):
            return _minimal_project_detail()
        return (FIXTURES / f"project_list_sjs_p{page}.html").read_text(encoding="utf-8")

    def get(self, url: str) -> str:
        self.get_calls.append(url)
        if "projectID=8156386" in url:
            if self.omit_ruichen_buildings:
                return _minimal_project_detail()
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


def test_refresh_reuses_previous_building_houses_on_building_failure(
    tmp_path, monkeypatch
) -> None:
    monkeypatch.setattr("app.crawler.RAW_DIR", tmp_path / "raw")
    repo = Repository(tmp_path / "app.db")
    first_snapshot = RefreshService(repo, client=FixtureClient()).refresh()

    second_snapshot = RefreshService(repo, client=FixtureClient(fail_building=True)).refresh()

    assert second_snapshot != first_snapshot
    assert repo.latest_successful_snapshot_id() == second_snapshot
    assert repo.dashboard()["snapshot"]["id"] == second_snapshot
    assert repo.dashboard()["metrics"]["available"] > 0


def test_refresh_building_failure_without_previous_snapshot_fails(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr("app.crawler.RAW_DIR", tmp_path / "raw")
    repo = Repository(tmp_path / "app.db")

    with pytest.raises(RuntimeError, match="simulated building network failure"):
        RefreshService(repo, client=FixtureClient(fail_building=True)).refresh()

    assert repo.latest_successful_snapshot_id() is None


def test_refresh_reuses_previous_buildings_when_project_detail_omits_them(
    tmp_path, monkeypatch
) -> None:
    monkeypatch.setattr("app.crawler.RAW_DIR", tmp_path / "raw")
    repo = Repository(tmp_path / "app.db")
    first_snapshot = RefreshService(repo, client=FixtureClient()).refresh()

    second_snapshot = RefreshService(
        repo,
        client=FixtureClient(omit_ruichen_buildings=True),
    ).refresh()

    assert second_snapshot != first_snapshot
    assert repo.latest_successful_snapshot_id() == second_snapshot
    houses = repo.building_detail("571199")["houses"]
    assert houses
    assert all(house["snapshot_id"] == second_snapshot for house in houses)


def test_refresh_retries_incomplete_project_list(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr("app.crawler.RAW_DIR", tmp_path / "raw")
    monkeypatch.setattr("app.crawler.time.sleep", lambda _: None)
    repo = Repository(tmp_path / "app.db")
    client = FixtureClient(incomplete_list_once=True)

    snapshot_id = RefreshService(repo, client=client).refresh()

    assert snapshot_id == repo.latest_successful_snapshot_id()
    assert client.list_calls == 4


def test_refresh_reuses_cached_projects_when_list_remains_incomplete(
    tmp_path, monkeypatch
) -> None:
    monkeypatch.setattr("app.crawler.RAW_DIR", tmp_path / "raw")
    monkeypatch.setattr("app.crawler.time.sleep", lambda _: None)
    repo = Repository(tmp_path / "app.db")
    first_snapshot = RefreshService(repo, client=FixtureClient()).refresh()
    client = FixtureClient(always_incomplete_list=True)

    second_snapshot = RefreshService(repo, client=client).refresh()

    assert second_snapshot != first_snapshot
    assert repo.latest_successful_snapshot_id() == second_snapshot
    assert repo.dashboard()["metrics"]["projects"] == 17
    assert client.list_calls == 8


def test_refresh_incomplete_list_without_cached_projects_fails(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr("app.crawler.RAW_DIR", tmp_path / "raw")
    monkeypatch.setattr("app.crawler.time.sleep", lambda _: None)
    repo = Repository(tmp_path / "app.db")

    with pytest.raises(RuntimeError, match="expected 17 in-scope projects, got 0"):
        RefreshService(repo, client=FixtureClient(always_incomplete_list=True)).refresh()

    assert repo.latest_successful_snapshot_id() is None


def test_merge_project_fills_known_land_when_detail_is_blank() -> None:
    listed = OfficialProject(
        project_id="8156388",
        group_id="ruiwenli",
        name="瑞玉苑",
        permit_no="京房售证字(2026)4号",
        detail_url="https://example.test/project/8156388",
        is_in_scope=True,
    )
    detail = OfficialProject(
        project_id="8156388",
        group_id="ruiwenli",
        name="瑞玉苑",
        permit_no="",
    )

    merged = _merge_project(listed, detail)

    assert merged.land_location == "石景山区西黄村棚户区改造土地开发项目1606-648地块"


def test_zjw_client_retries_transient_disconnect() -> None:
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if calls == 1:
            raise httpx.RemoteProtocolError("Server disconnected without sending a response.")
        return httpx.Response(200, text="ok")

    client = ZjwClient(retries=1, retry_delay=0, transport=httpx.MockTransport(handler))

    assert client.get("https://example.test/detail") == "ok"
    assert calls == 2


def test_zjw_client_retries_retryable_status() -> None:
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if calls == 1:
            return httpx.Response(503, text="temporary unavailable")
        return httpx.Response(200, text="ok")

    client = ZjwClient(retries=1, retry_delay=0, transport=httpx.MockTransport(handler))

    assert client.post_project_list(1) == "ok"
    assert calls == 2


def test_zjw_client_uses_exponential_backoff(monkeypatch) -> None:
    calls = 0
    sleeps: list[float] = []

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        raise httpx.RemoteProtocolError("temporary disconnect")

    monkeypatch.setattr("app.crawler.time.sleep", sleeps.append)
    client = ZjwClient(retries=3, retry_delay=2, transport=httpx.MockTransport(handler))

    with pytest.raises(httpx.RemoteProtocolError):
        client.get("https://example.test/detail")

    assert calls == 4
    assert sleeps == [2, 4, 8]


def test_zjw_client_does_not_retry_non_retryable_status() -> None:
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(404, text="not found")

    client = ZjwClient(retries=3, retry_delay=0, transport=httpx.MockTransport(handler))

    with pytest.raises(httpx.HTTPStatusError):
        client.get("https://example.test/missing")
    assert calls == 1


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
