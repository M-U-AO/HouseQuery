from dataclasses import replace

from app.models import Building, HouseState, OfficialProject
from app.repository import Repository


def project(project_id: str = "p1") -> OfficialProject:
    return OfficialProject(
        project_id=project_id,
        group_id="ruiwenli",
        name="瑞宸苑",
        permit_no="京房售证字(2026)3号",
        is_in_scope=True,
    )


def building(building_id: str = "b1") -> Building:
    return Building(building_id=building_id, project_id="p1", name="1#住宅楼", detail_url="")


def house(no: str, status: str, building_id: str = "b1") -> HouseState:
    labels = {"available": "可售", "signed": "已签约", "recorded": "网上联机备案"}
    colors = {"available": "#33CC00", "signed": "#FF0000", "recorded": "#d2691e"}
    return HouseState(
        building_id=building_id,
        project_id="p1",
        house_key=f"p1:{building_id}:{no}",
        house_no=no,
        unit_no=no.split("-", 1)[0],
        floor_no=1,
        display_floor="1",
        status_code=status,
        status_label=labels[status],
        status_color=colors[status],
    )


def test_snapshot_diff_and_dashboard(tmp_path) -> None:
    repo = Repository(tmp_path / "app.db")
    repo.init_schema()

    first = repo.create_snapshot()
    repo.save_successful_snapshot(
        first,
        [project()],
        [building()],
        [house("1单元-101", "available"), house("1单元-102", "available")],
    )

    second = repo.create_snapshot()
    repo.save_successful_snapshot(
        second,
        [project()],
        [building()],
        [
            house("1单元-101", "signed"),
            house("1单元-102", "available"),
            house("1单元-103", "recorded"),
        ],
    )

    dashboard = repo.dashboard()
    assert dashboard["metrics"]["projects"] == 1
    assert dashboard["metrics"]["available"] == 1
    assert dashboard["metrics"]["changes"] == 2
    assert len(dashboard["changes"]) == dashboard["metrics"]["changes"]
    assert dashboard["groups"][0]["deal_count"] == 2
    assert dashboard["changes"][0]["project_name"] == "瑞宸苑"

    detail = repo.group_detail("ruiwenli")
    assert len(detail["changes"]) == 2
    assert detail["changes"][0]["project_name"] == "瑞宸苑"


def test_failed_snapshot_does_not_replace_latest(tmp_path) -> None:
    repo = Repository(tmp_path / "app.db")
    repo.init_schema()
    first = repo.create_snapshot()
    repo.save_successful_snapshot(
        first,
        [project()],
        [building()],
        [house("1单元-101", "available")],
    )

    failed = repo.create_snapshot()
    repo.mark_snapshot_failed(failed, "network failed")

    assert repo.latest_successful_snapshot_id() == first


def test_blank_project_land_does_not_overwrite_existing_land(tmp_path) -> None:
    repo = Repository(tmp_path / "app.db")
    repo.init_schema()

    first = repo.create_snapshot()
    first_project = replace(
        project(),
        land_location="石景山区西黄村棚户区改造土地开发项目1606-650地块",
    )
    repo.save_successful_snapshot(
        first,
        [first_project],
        [building()],
        [house("1单元-101", "available")],
    )

    second = repo.create_snapshot()
    second_project = replace(project(), land_location="")
    repo.save_successful_snapshot(
        second,
        [second_project],
        [building()],
        [house("1单元-101", "signed")],
    )

    detail = repo.group_detail("ruiwenli")
    assert detail["projects"][0]["land_location"] == first_project.land_location
