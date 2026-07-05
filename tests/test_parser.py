from pathlib import Path

from app.parser import parse_building_page, parse_project_detail, parse_project_list

FIXTURES = Path(__file__).parent / "fixtures"


def read_fixture(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def test_parse_shijingshan_project_list_pages() -> None:
    page1 = parse_project_list(read_fixture("project_list_sjs_p1.html"))
    page2 = parse_project_list(read_fixture("project_list_sjs_p2.html"))
    projects = {project.project_id: project for project in page1 + page2}

    assert len(projects) == 17
    assert projects["8156386"].name == "瑞宸苑"
    assert projects["8156386"].permit_no == "京房售证字(2026)3号"
    assert projects["8156386"].group_id == "ruiwenli"
    assert projects["6219204"].group_id == "yujing"


def test_parse_project_detail_extracts_buildings() -> None:
    detail = parse_project_detail(read_fixture("project_8156386_ruichen.html"), "8156386")

    assert detail.project.name == "瑞宸苑"
    assert detail.project.land_location == "石景山区西黄村棚户区改造土地开发项目1606-650地块"
    assert detail.project.planning_permit_no == "2025规自(石)建字0015号"
    assert len(detail.buildings) == 1
    assert detail.buildings[0].building_id == "571199"
    assert detail.buildings[0].name == "5#住宅楼"


def test_parse_multi_building_project_detail() -> None:
    detail = parse_project_detail(read_fixture("project_8102776_ruiyu.html"), "8102776")

    assert detail.project.name == "瑞玉苑"
    assert len(detail.buildings) == 4
    assert {building.name for building in detail.buildings} == {
        "1#住宅楼",
        "3#住宅楼",
        "4#住宅楼",
        "5#住宅楼",
    }


def test_parse_building_page_house_statuses() -> None:
    houses = parse_building_page(
        read_fixture("building_571199_ruichen_5.html"),
        project_id="8156386",
        building_id="571199",
    )

    assert len(houses) == 60
    by_no = {house.house_no: house for house in houses}
    assert by_no["1单元-1502"].status_code == "available"
    assert by_no["1单元-1502"].house_id == "17544065"
    assert by_no["2单元-901"].status_code == "signed"
    assert by_no["1单元-1501"].status_code == "recorded"
    assert by_no["1单元-901"].floor_no == 9


def test_parse_building_page_without_unit_prefix() -> None:
    houses = parse_building_page(
        (FIXTURES / "building_550661_yuanxi_6.html").read_text(encoding="utf-8"),
        project_id="7769633",
        building_id="550661",
    )

    by_no = {house.house_no: house for house in houses}
    assert by_no["1802"].status_code == "available"
    assert by_no["1802"].unit_no == "房号"
    assert by_no["1802"].floor_no == 18
