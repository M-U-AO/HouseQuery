from __future__ import annotations

import logging
import shutil
import time
from collections.abc import Callable
from pathlib import Path

import httpx

from app.config import (
    BUILDING_URL,
    ENTRY_URL,
    EXPECTED_IN_SCOPE_PROJECTS,
    PROJECT_URL,
    RAW_DIR,
    RAW_SNAPSHOT_KEEP,
    SHIJINGSHAN_DISTRICT_ID,
)
from app.models import Building, HouseState, OfficialProject
from app.parser import parse_building_page, parse_project_detail, parse_project_list
from app.repository import Repository

logger = logging.getLogger(__name__)


class RefreshError(RuntimeError):
    pass


class ZjwClient:
    def __init__(
        self,
        timeout: float = 20.0,
        retries: int = 3,
        retry_delay: float = 1.0,
        transport: httpx.BaseTransport | None = None,
    ):
        self.timeout = timeout
        self.retries = retries
        self.retry_delay = retry_delay
        self.transport = transport

    def get(self, url: str) -> str:
        return self._request_with_retry(lambda client: client.get(url))

    def post_project_list(self, page: int) -> str:
        data = {
            "isTrue": "1",
            "ddlQX": SHIJINGSHAN_DISTRICT_ID,
            "rblFWType1": "q",
            "ddlYT": "-1",
            "ddlFW": "-1",
            "ddlQW": "-1",
            "ddlHX": "-1",
            "currentPage": str(page),
            "pageSize": "15",
        }
        return self._request_with_retry(lambda client: client.post(ENTRY_URL, data=data))

    def _request_with_retry(self, request: Callable[[httpx.Client], httpx.Response]) -> str:
        last_error: Exception | None = None
        attempts = self.retries + 1
        for attempt in range(1, attempts + 1):
            try:
                with httpx.Client(
                    timeout=self.timeout,
                    follow_redirects=True,
                    transport=self.transport,
                ) as client:
                    response = request(client)
                    response.raise_for_status()
                    return response.text
            except httpx.HTTPStatusError as exc:
                last_error = exc
                if exc.response.status_code < 500 and exc.response.status_code != 429:
                    raise
            except httpx.RequestError as exc:
                last_error = exc
            if attempt < attempts:
                time.sleep(self.retry_delay)
        if last_error is None:
            raise RefreshError("request failed without an exception")
        raise last_error


class RefreshService:
    def __init__(self, repository: Repository, client: ZjwClient | None = None):
        self.repository = repository
        self.client = client or ZjwClient()

    def refresh(self) -> int:
        self.repository.init_schema()
        snapshot_id = self.repository.create_snapshot()
        raw_dir = RAW_DIR / str(snapshot_id)
        raw_dir.mkdir(parents=True, exist_ok=True)
        try:
            projects, buildings, houses = self._collect(snapshot_id, raw_dir)
            self.repository.save_successful_snapshot(snapshot_id, projects, buildings, houses)
            self._trim_raw_dirs()
            return snapshot_id
        except Exception as exc:
            self.repository.mark_snapshot_failed(snapshot_id, str(exc))
            raise

    def _collect(
        self, snapshot_id: int, raw_dir: Path
    ) -> tuple[list[OfficialProject], list[Building], list[HouseState]]:
        list_html = []
        for page in (1, 2):
            html = self.client.post_project_list(page)
            (raw_dir / f"project_list_p{page}.html").write_text(html, encoding="utf-8")
            list_html.append(html)
        listed_projects = _dedupe_projects(
            [project for html in list_html for project in parse_project_list(html)]
        )
        in_scope_projects = [project for project in listed_projects if project.is_in_scope]
        if len(in_scope_projects) != EXPECTED_IN_SCOPE_PROJECTS:
            raise RefreshError(
                "expected "
                f"{EXPECTED_IN_SCOPE_PROJECTS} in-scope projects, "
                f"got {len(in_scope_projects)}"
            )

        project_details: list[OfficialProject] = []
        buildings: list[Building] = []
        houses: list[HouseState] = []

        for listed_project in sorted(in_scope_projects, key=lambda item: item.project_id):
            project_html = self.client.get(PROJECT_URL.format(project_id=listed_project.project_id))
            (raw_dir / f"project_{listed_project.project_id}.html").write_text(
                project_html, encoding="utf-8"
            )
            detail = parse_project_detail(
                project_html,
                fallback_project_id=listed_project.project_id,
            )
            merged_project = _merge_project(listed_project, detail.project)
            project_details.append(merged_project)
            buildings.extend(detail.buildings)
            for building in detail.buildings:
                building_url = BUILDING_URL.format(
                    sale_permit_id=building.project_id,
                    building_id=building.building_id,
                )
                try:
                    building_html = self.client.get(building_url)
                    (raw_dir / f"building_{building.building_id}.html").write_text(
                        building_html, encoding="utf-8"
                    )
                    parsed_houses = parse_building_page(
                        building_html,
                        project_id=building.project_id,
                        building_id=building.building_id,
                        source_url=building.detail_url,
                    )
                except Exception as exc:
                    previous_houses = self.repository.houses_for_building_from_latest_successful(
                        building.building_id
                    )
                    if not previous_houses:
                        raise RefreshError(
                            "failed parsing building "
                            f"{building.building_id} of project {building.project_id} "
                            f"({building.name}): {exc}"
                        ) from exc
                    logger.warning(
                        "failed parsing building "
                        "%s of project %s (%s); reused %s houses from previous snapshot: %s",
                        building.building_id,
                        building.project_id,
                        building.name,
                        len(previous_houses),
                        exc,
                    )
                    parsed_houses = previous_houses
                houses.extend(parsed_houses)
        if not buildings:
            raise RefreshError("no buildings collected")
        if not houses:
            raise RefreshError("no houses collected")
        return project_details, buildings, houses

    def _trim_raw_dirs(self) -> None:
        RAW_DIR.mkdir(parents=True, exist_ok=True)
        dirs = sorted(
            [path for path in RAW_DIR.iterdir() if path.is_dir()],
            key=lambda path: path.name,
        )
        for old in dirs[:-RAW_SNAPSHOT_KEEP]:
            shutil.rmtree(old, ignore_errors=True)


def _dedupe_projects(projects: list[OfficialProject]) -> list[OfficialProject]:
    result: dict[str, OfficialProject] = {}
    for project in projects:
        result[project.project_id] = project
    return list(result.values())


def _merge_project(listed: OfficialProject, detail: OfficialProject) -> OfficialProject:
    return OfficialProject(
        project_id=listed.project_id,
        group_id=listed.group_id,
        name=detail.name or listed.name,
        permit_no=detail.permit_no or listed.permit_no,
        issue_date=detail.issue_date or listed.issue_date,
        detail_url=listed.detail_url,
        land_location=detail.land_location,
        developer=detail.developer,
        planning_permit_no=detail.planning_permit_no,
        approved_scope=detail.approved_scope,
        is_in_scope=listed.is_in_scope,
    )
