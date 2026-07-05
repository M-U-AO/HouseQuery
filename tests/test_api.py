from fastapi.testclient import TestClient

from app.main import create_app
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


def test_refresh_requires_token_when_configured(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("REFRESH_TOKEN", "secret-token")
    app = create_app(Repository(tmp_path / "app.db"))

    with TestClient(app) as client:
        response = client.post("/api/refresh")
        bad_response = client.post("/api/refresh", headers={"X-Refresh-Token": "wrong"})

    assert response.status_code == 401
    assert bad_response.status_code == 401
