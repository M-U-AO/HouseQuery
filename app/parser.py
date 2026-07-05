from __future__ import annotations

import re
from html import unescape
from urllib.parse import parse_qs, urljoin, urlparse

from bs4 import BeautifulSoup, Tag

from app.config import BASE_URL, STATUS_BY_COLOR
from app.grouping import group_for_project
from app.models import Building, HouseState, OfficialProject, ParsedProjectDetail


class ParseError(ValueError):
    pass


def clean_text(value: str | None) -> str:
    if value is None:
        return ""
    value = unescape(value)
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def abs_url(href: str) -> str:
    return urljoin(BASE_URL, href)


def query_value(url: str, key: str) -> str:
    return parse_qs(urlparse(url).query).get(key, [""])[0]


def parse_project_list(html: str) -> list[OfficialProject]:
    soup = BeautifulSoup(html, "lxml")
    rows = soup.select("table tr")
    projects: list[OfficialProject] = []

    for row in rows:
        links = row.select('a[href*="pageId=53618754"][href*="projectID="]')
        if len(links) < 2:
            continue
        name = clean_text(links[0].get_text())
        permit_no = clean_text(links[1].get_text())
        href = links[0].get("href", "")
        project_id = query_value(href, "projectID")
        if not project_id or not name:
            continue
        group_id, in_scope = group_for_project(project_id, name)
        issue_date = ""
        cells = row.find_all("td")
        if cells:
            issue_date = clean_text(cells[-1].get_text())
        projects.append(
            OfficialProject(
                project_id=project_id,
                group_id=group_id,
                name=name,
                permit_no=permit_no,
                issue_date=issue_date,
                detail_url=abs_url(href),
                is_in_scope=in_scope,
            )
        )

    deduped: dict[str, OfficialProject] = {}
    for project in projects:
        deduped[project.project_id] = project
    return list(deduped.values())


def parse_project_detail(html: str, fallback_project_id: str = "") -> ParsedProjectDetail:
    soup = BeautifulSoup(html, "lxml")
    field = _field_getter(soup)

    project_id = fallback_project_id
    building_links = soup.select('a[href*="pageId=53618755"][href*="buildingId="]')
    if building_links:
        project_id = project_id or query_value(building_links[0].get("href", ""), "salePermitId")
    if not project_id:
        raise ParseError("project_id missing from project detail")

    name = field("项目名称")
    permit_no = field("预售许可证编号")
    group_id, in_scope = group_for_project(project_id, name)
    project = OfficialProject(
        project_id=project_id,
        group_id=group_id,
        name=name,
        permit_no=permit_no,
        issue_date=field("发证日期"),
        land_location=field("坐落位置"),
        developer=field("开发企业"),
        planning_permit_no=field("建设工程规划许可证编号"),
        approved_scope=field("批准预售部位"),
        is_in_scope=in_scope,
    )

    buildings: list[Building] = []
    for link in building_links:
        href = link.get("href", "")
        row = _ancestor_row(link)
        cells = [clean_text(cell.get_text()) for cell in row.find_all("td")] if row else []
        building_id = query_value(href, "buildingId")
        sale_permit_id = query_value(href, "salePermitId")
        if not building_id:
            continue
        buildings.append(
            Building(
                building_id=building_id,
                project_id=sale_permit_id or project_id,
                name=cells[0] if len(cells) > 0 else "",
                approved_units=cells[1] if len(cells) > 1 else "",
                approved_area=cells[2] if len(cells) > 2 else "",
                sale_status=cells[3] if len(cells) > 3 else "",
                price=cells[4] if len(cells) > 4 else "",
                detail_url=abs_url(href),
            )
        )

    return ParsedProjectDetail(project=project, buildings=buildings)


def parse_building_page(
    html: str,
    project_id: str,
    building_id: str,
    source_url: str = "",
) -> list[HouseState]:
    soup = BeautifulSoup(html, "lxml")
    houses: list[HouseState] = []
    for div in soup.select('div[style*="background:"]'):
        style = div.get("style", "")
        color = _extract_color(style)
        if not color or color not in STATUS_BY_COLOR:
            continue
        link = div.find("a")
        if not link:
            continue
        house_no = clean_text(link.get_text())
        if not house_no or not re.search(r"\d", house_no):
            continue
        status_code, status_label = STATUS_BY_COLOR[color]
        href = link.get("href", "")
        house_id = query_value(href, "houseId") if href and href != "#" else ""
        unit_no, floor_no = _parse_house_no(house_no)
        house_key = f"{project_id}:{building_id}:{house_no}"
        houses.append(
            HouseState(
                building_id=building_id,
                project_id=project_id,
                house_key=house_key,
                house_no=house_no,
                unit_no=unit_no,
                floor_no=floor_no,
                display_floor=str(floor_no) if floor_no is not None else "",
                status_code=status_code,
                status_label=status_label,
                status_color=color,
                house_id=house_id,
                source_url=source_url,
            )
        )
    if not houses:
        raise ParseError("no houses parsed from building page")
    return houses


def _field_getter(soup: BeautifulSoup):
    def get(label: str) -> str:
        cell = soup.find(id=label)
        return clean_text(cell.get_text()) if cell else ""

    return get


def _ancestor_row(tag: Tag) -> Tag | None:
    parent = tag
    while parent:
        if isinstance(parent, Tag) and parent.name == "tr":
            return parent
        parent = parent.parent
    return None


def _extract_color(style: str) -> str:
    match = re.search(r"background\s*:\s*(#[0-9a-fA-F]{6})", style)
    if not match:
        return ""
    color = match.group(1)
    for configured in STATUS_BY_COLOR:
        if configured.lower() == color.lower():
            return configured
    return color


def _parse_house_no(house_no: str) -> tuple[str, int | None]:
    unit = house_no.split("-", 1)[0] if "-" in house_no else "房号"
    match = re.search(r"-(\d+)", house_no)
    if not match:
        match = re.fullmatch(r"(\d+)", house_no)
    if not match:
        return unit, None
    digits = match.group(1)
    if len(digits) <= 2:
        return unit, None
    return unit, int(digits[:-2])
