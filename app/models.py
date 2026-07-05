from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class ProjectGroup:
    id: str
    name: str
    description: str
    developer_hint: str
    sort_order: int


@dataclass(frozen=True)
class OfficialProject:
    project_id: str
    group_id: str
    name: str
    permit_no: str
    issue_date: str = ""
    detail_url: str = ""
    land_location: str = ""
    developer: str = ""
    planning_permit_no: str = ""
    approved_scope: str = ""
    is_in_scope: bool = True


@dataclass(frozen=True)
class Building:
    building_id: str
    project_id: str
    name: str
    detail_url: str
    approved_units: str = ""
    approved_area: str = ""
    sale_status: str = ""
    price: str = ""


@dataclass(frozen=True)
class HouseState:
    building_id: str
    project_id: str
    house_key: str
    house_no: str
    unit_no: str
    floor_no: int | None
    display_floor: str
    status_code: str
    status_label: str
    status_color: str
    house_id: str = ""
    source_url: str = ""


@dataclass(frozen=True)
class ParsedProjectDetail:
    project: OfficialProject
    buildings: list[Building] = field(default_factory=list)


@dataclass(frozen=True)
class SnapshotResult:
    snapshot_id: int
    status: str
    completed_at: datetime | None
    error_message: str = ""
