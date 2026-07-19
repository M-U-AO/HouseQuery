from datetime import datetime
from zoneinfo import ZoneInfo

import pytest
from fastapi.testclient import TestClient

from app.main import CHANGE_WINDOWS, _parse_daily_time, _seconds_until_next_daily_run, create_app
from app.models import Building, HouseState, OfficialProject
from app.repository import Repository


def test_dashboard_empty_database(tmp_path) -> None:
    app = create_app(Repository(tmp_path / "app.db"))

    with TestClient(app) as client:
        response = client.get("/api/dashboard")

    assert response.status_code == 200
    payload = response.json()
    assert payload["metrics"] == {
        "projects": 0,
        "buildings": 0,
        "available": 0,
        "changes": 0,
        "new_projects": 0,
    }


def test_api_reads_seeded_snapshot_from_isolated_database(tmp_path) -> None:
    repo = Repository(tmp_path / "app.db")
    repo.init_schema()
    snapshot = repo.create_snapshot()
    repo.save_successful_snapshot(
        snapshot,
        [
            OfficialProject(
                project_id="8156386",
                group_id="ruiwenli",
                name="瑞宸苑",
                permit_no="京房售证字(2026)3号",
                detail_url="https://example.test/project/8156386",
                is_in_scope=True,
            )
        ],
        [Building(building_id="571199", project_id="8156386", name="5#住宅楼", detail_url="")],
        [
            HouseState(
                building_id="571199",
                project_id="8156386",
                house_key="8156386:571199:1单元-101",
                house_no="1单元-101",
                unit_no="1单元",
                floor_no=1,
                display_floor="1",
                status_code="available",
                status_label="可售",
                status_color="#33CC00",
            )
        ],
    )
    app = create_app(repo)

    with TestClient(app) as client:
        dashboard = client.get("/api/dashboard").json()
        group = client.get("/api/groups/ruiwenli").json()
        building = client.get("/api/buildings/571199").json()

    assert dashboard["metrics"]["projects"] == 1
    assert dashboard["metrics"]["available"] == 1
    assert dashboard["source_links"]["official_entry"].startswith("http://bjjs.zjw.beijing.gov.cn")
    assert group["projects"][0]["project_id"] == "8156386"
    assert group["buildings"][0]["project_name"] == "瑞宸苑"
    assert group["buildings"][0]["permit_no"] == "京房售证字(2026)3号"
    assert group["buildings"][0]["project_url"] == "https://example.test/project/8156386"
    assert "land_location" in group["buildings"][0]
    assert building["building"]["name"] == "5#住宅楼"
    assert building["building"]["project_name"] == "瑞宸苑"
    assert building["building"]["project_url"] == "https://example.test/project/8156386"
    assert building["houses"][0]["house_no"] == "1单元-101"


def test_static_mount_does_not_expose_project_root(tmp_path) -> None:
    app = create_app(Repository(tmp_path / "app.db"))

    with TestClient(app) as client:
        assert client.get("/static/app.js").status_code == 200
        assert client.get("/static/README.md").status_code == 404


def test_index_revalidates_cached_html(tmp_path) -> None:
    app = create_app(Repository(tmp_path / "app.db"))

    with TestClient(app) as client:
        response = client.get("/")

    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "no-cache"
    assert "/static/app_logic.js?v=24" in response.text
    assert "/static/app.js?v=24" in response.text


def test_refresh_requires_token_when_configured(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("REFRESH_TOKEN", "secret-token")
    app = create_app(Repository(tmp_path / "app.db"))

    with TestClient(app) as client:
        response = client.post("/api/refresh")
        bad_response = client.post("/api/refresh", headers={"X-Refresh-Token": "wrong"})

    assert response.status_code == 401
    assert bad_response.status_code == 401


def test_seconds_until_next_daily_run_same_day() -> None:
    now = datetime(2026, 7, 6, 8, 30, tzinfo=ZoneInfo("Asia/Shanghai"))
    refresh_time = _parse_daily_time("09:00")

    assert _seconds_until_next_daily_run(now, refresh_time) == 30 * 60


def test_seconds_until_next_daily_run_next_day() -> None:
    now = datetime(2026, 7, 6, 9, 1, tzinfo=ZoneInfo("Asia/Shanghai"))
    refresh_time = _parse_daily_time("09:00")

    assert _seconds_until_next_daily_run(now, refresh_time) == (23 * 60 + 59) * 60


def test_parse_daily_time_rejects_invalid_value() -> None:
    with pytest.raises(ValueError, match="AUTO_REFRESH_TIME"):
        _parse_daily_time("9am")


@pytest.mark.parametrize("window_key,hours", CHANGE_WINDOWS.items())
def test_group_change_window_api_mapping(tmp_path, monkeypatch, window_key, hours) -> None:
    repo = Repository(tmp_path / "app.db")
    observed: list[int] = []

    def group_detail(group_id: str, change_window_hours: int = 24) -> dict:
        observed.append(change_window_hours)
        return {"group": {"id": group_id}, "change_window_hours": change_window_hours}

    monkeypatch.setattr(repo, "group_detail", group_detail)
    app = create_app(repo)

    with TestClient(app) as client:
        response = client.get(f"/api/groups/ruiwenli?change_window={window_key}")

    assert response.status_code == 200
    assert response.json()["change_window_hours"] == hours
    assert observed == [hours]


def test_group_change_window_api_rejects_unknown_value(tmp_path) -> None:
    app = create_app(Repository(tmp_path / "app.db"))

    with TestClient(app) as client:
        response = client.get("/api/groups/ruiwenli?change_window=2d")

    assert response.status_code == 400
