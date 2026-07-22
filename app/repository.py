from __future__ import annotations

import sqlite3
from collections import defaultdict
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from pathlib import Path

from app.config import DB_PATH
from app.grouping import GROUPS
from app.models import Building, HouseState, OfficialProject


def utc_now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


class Repository:
    """SQLite persistence boundary for snapshots and read models.

    The rest of the application should not know table details. Crawler code
    writes full successful snapshots here, while API code reads dashboard-ready
    dictionaries from here.
    """

    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def init_schema(self) -> None:
        with self.connect() as conn:
            conn.executescript(SCHEMA)
            for group in GROUPS:
                conn.execute(
                    """
                    INSERT INTO project_groups (id, name, description, developer_hint, sort_order)
                    VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(id) DO UPDATE SET
                      name=excluded.name,
                      description=excluded.description,
                      developer_hint=excluded.developer_hint,
                      sort_order=excluded.sort_order
                    """,
                    (
                        group.id,
                        group.name,
                        group.description,
                        group.developer_hint,
                        group.sort_order,
                    ),
                )

    def create_snapshot(self) -> int:
        with self.connect() as conn:
            cur = conn.execute(
                "INSERT INTO snapshots (started_at, status) VALUES (?, 'running')",
                (utc_now(),),
            )
            return int(cur.lastrowid)

    def mark_snapshot_failed(self, snapshot_id: int, error: str) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                UPDATE snapshots
                SET completed_at=?, status='failed', error_message=?
                WHERE id=?
                """,
                (utc_now(), error[:2000], snapshot_id),
            )

    def mark_abandoned_running_snapshots(self) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                UPDATE snapshots
                SET completed_at=?, status='failed', error_message=?
                WHERE status='running'
                """,
                (utc_now(), "service restarted before refresh completed"),
            )

    def save_successful_snapshot(
        self,
        snapshot_id: int,
        projects: list[OfficialProject],
        buildings: list[Building],
        houses: list[HouseState],
    ) -> None:
        previous_id = self.latest_successful_snapshot_id()
        with self.connect() as conn:
            for project in projects:
                conn.execute(
                    """
                    INSERT INTO official_projects (
                      project_id, group_id, name, permit_no, issue_date, detail_url,
                      land_location, developer, planning_permit_no, approved_scope, is_in_scope
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(project_id) DO UPDATE SET
                      group_id=excluded.group_id,
                      name=excluded.name,
                      permit_no=excluded.permit_no,
                      issue_date=excluded.issue_date,
                      detail_url=excluded.detail_url,
                      land_location=COALESCE(
                        NULLIF(excluded.land_location, ''),
                        official_projects.land_location
                      ),
                      developer=excluded.developer,
                      planning_permit_no=excluded.planning_permit_no,
                      approved_scope=excluded.approved_scope,
                      is_in_scope=excluded.is_in_scope
                    """,
                    (
                        project.project_id,
                        project.group_id,
                        project.name,
                        project.permit_no,
                        project.issue_date,
                        project.detail_url,
                        project.land_location,
                        project.developer,
                        project.planning_permit_no,
                        project.approved_scope,
                        int(project.is_in_scope),
                    ),
                )
            for building in buildings:
                conn.execute(
                    """
                    INSERT INTO buildings (
                      building_id, project_id, name, detail_url, approved_units,
                      approved_area, sale_status, price
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(building_id) DO UPDATE SET
                      project_id=excluded.project_id,
                      name=excluded.name,
                      detail_url=excluded.detail_url,
                      approved_units=excluded.approved_units,
                      approved_area=excluded.approved_area,
                      sale_status=excluded.sale_status,
                      price=excluded.price
                    """,
                    (
                        building.building_id,
                        building.project_id,
                        building.name,
                        building.detail_url,
                        building.approved_units,
                        building.approved_area,
                        building.sale_status,
                        building.price,
                    ),
                )
            conn.executemany(
                """
                INSERT INTO house_states (
                  snapshot_id, building_id, project_id, house_key, house_no, unit_no,
                  floor_no, display_floor, status_code, status_label, status_color,
                  house_id, source_url
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        snapshot_id,
                        house.building_id,
                        house.project_id,
                        house.house_key,
                        house.house_no,
                        house.unit_no,
                        house.floor_no,
                        house.display_floor,
                        house.status_code,
                        house.status_label,
                        house.status_color,
                        house.house_id,
                        house.source_url,
                    )
                    for house in houses
                ],
            )
            self._write_changes(conn, snapshot_id, previous_id)
            conn.execute(
                "UPDATE snapshots SET completed_at=?, status='success' WHERE id=?",
                (utc_now(), snapshot_id),
            )

    def latest_successful_snapshot_id(self) -> int | None:
        with self.connect() as conn:
            row = conn.execute(
                "SELECT id FROM snapshots WHERE status='success' ORDER BY id DESC LIMIT 1"
            ).fetchone()
            return int(row["id"]) if row else None

    def in_scope_projects(self) -> list[OfficialProject]:
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM official_projects
                WHERE is_in_scope=1
                ORDER BY project_id
                """
            )
            return [
                OfficialProject(
                    project_id=row["project_id"],
                    group_id=row["group_id"],
                    name=row["name"],
                    permit_no=row["permit_no"],
                    issue_date=row["issue_date"],
                    detail_url=row["detail_url"],
                    land_location=row["land_location"],
                    developer=row["developer"],
                    planning_permit_no=row["planning_permit_no"],
                    approved_scope=row["approved_scope"],
                    is_in_scope=bool(row["is_in_scope"]),
                )
                for row in rows
            ]

    def houses_for_building_from_latest_successful(self, building_id: str) -> list[HouseState]:
        snapshot_id = self.latest_successful_snapshot_id()
        if snapshot_id is None:
            return []
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM house_states
                WHERE snapshot_id=? AND building_id=?
                ORDER BY COALESCE(floor_no, -999) DESC, house_no
                """,
                (snapshot_id, building_id),
            )
            return [
                HouseState(
                    building_id=row["building_id"],
                    project_id=row["project_id"],
                    house_key=row["house_key"],
                    house_no=row["house_no"],
                    unit_no=row["unit_no"],
                    floor_no=row["floor_no"],
                    display_floor=row["display_floor"],
                    status_code=row["status_code"],
                    status_label=row["status_label"],
                    status_color=row["status_color"],
                    house_id=row["house_id"],
                    source_url=row["source_url"],
                )
                for row in rows
            ]

    def buildings_for_project(self, project_id: str) -> list[Building]:
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM buildings
                WHERE project_id=?
                ORDER BY name, building_id
                """,
                (project_id,),
            )
            return [
                Building(
                    building_id=row["building_id"],
                    project_id=row["project_id"],
                    name=row["name"],
                    detail_url=row["detail_url"],
                    approved_units=row["approved_units"],
                    approved_area=row["approved_area"],
                    sale_status=row["sale_status"],
                    price=row["price"],
                )
                for row in rows
            ]

    def dashboard(self) -> dict:
        snapshot_id = self.latest_successful_snapshot_id()
        if snapshot_id is None:
            with self.connect() as conn:
                groups = [
                    dict(row)
                    for row in conn.execute("SELECT * FROM project_groups ORDER BY sort_order")
                ]
            return {
                "snapshot": None,
                "metrics": {
                    "projects": 0,
                    "buildings": 0,
                    "available": 0,
                    "changes": 0,
                    "new_projects": 0,
                },
                "groups": [
                    {
                        **group,
                        "project_count": 0,
                        "house_count": 0,
                        "available": 0,
                        "deal_count": 0,
                        "change_count": 0,
                    }
                    for group in groups
                ],
                "trend": [],
                "changes": [],
            }
        with self.connect() as conn:
            snapshot = conn.execute("SELECT * FROM snapshots WHERE id=?", (snapshot_id,)).fetchone()
            previous_snapshot = conn.execute(
                """
                SELECT * FROM snapshots
                WHERE status='success' AND id < ?
                ORDER BY id DESC
                LIMIT 1
                """,
                (snapshot_id,),
            ).fetchone()
            groups = [
                dict(row)
                for row in conn.execute("SELECT * FROM project_groups ORDER BY sort_order")
            ]
            project_counts = {
                row["group_id"]: row["count"]
                for row in conn.execute(
                    """
                    SELECT group_id, COUNT(*) AS count
                    FROM official_projects
                    WHERE is_in_scope=1
                    GROUP BY group_id
                    """
                )
            }
            house_counts = self._group_house_counts(conn, snapshot_id)
            change_counts = {
                row["group_id"]: row["count"]
                for row in conn.execute(
                    """
                    SELECT group_id, COUNT(*) AS count
                    FROM state_changes
                    WHERE snapshot_id=?
                    GROUP BY group_id
                    """,
                    (snapshot_id,),
                )
            }
            deal_counts = {
                row["group_id"]: row["count"]
                for row in conn.execute(
                    """
                    SELECT group_id, COUNT(*) AS count
                    FROM state_changes
                    WHERE snapshot_id=? AND to_status IN ('signed', 'recorded')
                    GROUP BY group_id
                    """,
                    (snapshot_id,),
                )
            }
            changes = self._changes(conn, snapshot_id, limit=None)
            trend = [
                {
                    "snapshot_id": row["id"],
                    "value": row["change_count"],
                    "label": row["completed_at"] or "",
                }
                for row in conn.execute(
                    """
                    SELECT s.id, s.completed_at, COUNT(c.id) AS change_count
                    FROM snapshots s
                    LEFT JOIN state_changes c ON c.snapshot_id=s.id
                    WHERE s.status='success'
                    GROUP BY s.id
                    ORDER BY s.id DESC
                    LIMIT 7
                    """
                )
            ][::-1]
            total_available = sum(counts.get("available", 0) for counts in house_counts.values())
            total_changes = sum(change_counts.values())
            total_buildings = conn.execute("SELECT COUNT(*) AS count FROM buildings").fetchone()[
                "count"
            ]
            total_projects = conn.execute(
                "SELECT COUNT(*) AS count FROM official_projects WHERE is_in_scope=1"
            ).fetchone()["count"]
            return {
                "snapshot": dict(snapshot),
                "previous_snapshot": dict(previous_snapshot) if previous_snapshot else None,
                "metrics": {
                    "projects": total_projects,
                    "buildings": total_buildings,
                    "available": total_available,
                    "changes": total_changes,
                    "new_projects": 0,
                },
                "groups": [
                    {
                        **group,
                        "project_count": project_counts.get(group["id"], 0),
                        "house_count": sum(house_counts.get(group["id"], {}).values()),
                        "available": house_counts.get(group["id"], {}).get("available", 0),
                        "deal_count": deal_counts.get(group["id"], 0),
                        "change_count": change_counts.get(group["id"], 0),
                    }
                    for group in groups
                ],
                "trend": trend,
                "changes": changes,
            }

    def group_detail(
        self,
        group_id: str,
        change_window_hours: int = 24,
        as_of: datetime | None = None,
    ) -> dict:
        snapshot_id = self.latest_successful_snapshot_id()
        with self.connect() as conn:
            group = conn.execute("SELECT * FROM project_groups WHERE id=?", (group_id,)).fetchone()
            if snapshot_id is None:
                return {
                    "group": dict(group) if group else None,
                    "counts": {},
                    "projects": [],
                    "buildings": [],
                    "changes": [],
                }
            counts = self._group_house_counts(conn, snapshot_id).get(group_id, {})
            change_cutoff = (as_of or datetime.now(UTC)) - timedelta(hours=change_window_hours)
            changes_since = change_cutoff.isoformat(timespec="seconds")
            projects = [
                dict(row)
                for row in conn.execute(
                    """
                    SELECT * FROM official_projects
                    WHERE group_id=? AND is_in_scope=1
                    ORDER BY issue_date, permit_no
                    """,
                    (group_id,),
                )
            ]
            buildings = [
                dict(row)
                for row in conn.execute(
                    """
                    SELECT b.*, p.group_id, p.name AS project_name, p.permit_no,
                      p.detail_url AS project_url, p.land_location,
                      SUM(CASE WHEN h.status_code='available' THEN 1 ELSE 0 END) AS available,
                      COUNT(h.id) AS house_count
                    FROM buildings b
                    JOIN official_projects p ON p.project_id=b.project_id
                    LEFT JOIN house_states h ON h.building_id=b.building_id AND h.snapshot_id=?
                    WHERE p.group_id=?
                    GROUP BY b.building_id
                    ORDER BY b.name
                    """,
                    (snapshot_id, group_id),
                )
            ]
            status_changes_by_building = [
                dict(row)
                for row in conn.execute(
                    """
                    SELECT
                      b.building_id,
                      b.name AS building_name,
                      p.name AS project_name,
                      COUNT(*) AS change_count
                    FROM state_changes c
                    JOIN snapshots s ON s.id=c.snapshot_id
                    JOIN buildings b ON b.building_id=c.building_id
                    JOIN official_projects p ON p.project_id=b.project_id
                    WHERE c.group_id=? AND s.completed_at>=?
                      AND c.change_type='status' AND s.status='success'
                    GROUP BY b.building_id
                    ORDER BY p.name, b.name
                    """,
                    (group_id, changes_since),
                )
            ]
            return {
                "group": dict(group) if group else None,
                "counts": counts,
                "projects": projects,
                "buildings": buildings,
                "status_changes_by_building": status_changes_by_building,
                "status_changes": self._status_changes(conn, group_id, changes_since),
                "change_window_hours": change_window_hours,
                "change_time_basis": "snapshot_observed_at",
                "changes": self._changes(conn, snapshot_id, group_id=group_id, limit=30),
            }

    def building_detail(self, building_id: str) -> dict:
        snapshot_id = self.latest_successful_snapshot_id()
        if snapshot_id is None:
            return {}
        with self.connect() as conn:
            building = conn.execute(
                """
                SELECT b.*, p.name AS project_name, p.permit_no, p.detail_url AS project_url
                FROM buildings b
                JOIN official_projects p ON p.project_id=b.project_id
                WHERE b.building_id=?
                """,
                (building_id,),
            ).fetchone()
            houses = [
                dict(row)
                for row in conn.execute(
                    """
                    SELECT * FROM house_states
                    WHERE snapshot_id=? AND building_id=?
                    ORDER BY COALESCE(floor_no, -999) DESC, house_no
                    """,
                    (snapshot_id, building_id),
                )
            ]
            return {"building": dict(building) if building else None, "houses": houses}

    def house_history(self, building_id: str, house_key: str) -> dict:
        """Return recorded status transitions for one house across successful snapshots."""
        with self.connect() as conn:
            baseline = conn.execute(
                """
                SELECT h.status_code, h.status_label, h.status_color, s.completed_at
                FROM house_states h
                JOIN snapshots s ON s.id=h.snapshot_id
                WHERE h.building_id=? AND h.house_key=? AND s.status='success'
                ORDER BY s.id ASC
                LIMIT 1
                """,
                (building_id, house_key),
            ).fetchone()
            if baseline is None:
                return {}
            events = [
                dict(row)
                for row in conn.execute(
                    """
                    WITH successful_snapshots AS (
                      SELECT id, completed_at,
                        LAG(completed_at) OVER (ORDER BY id) AS previous_completed_at
                      FROM snapshots
                      WHERE status='success'
                    )
                    SELECT c.from_status, c.to_status, s.completed_at,
                      s.previous_completed_at
                    FROM state_changes c
                    JOIN successful_snapshots s ON s.id=c.snapshot_id
                    WHERE c.building_id=? AND c.house_key=?
                      AND c.change_type='status'
                    ORDER BY c.snapshot_id DESC, c.id DESC
                    """,
                    (building_id, house_key),
                )
            ]
            return {"baseline": dict(baseline), "events": events}

    def _write_changes(
        self,
        conn: sqlite3.Connection,
        snapshot_id: int,
        previous_id: int | None,
    ) -> None:
        if previous_id is None:
            return
        previous = {
            row["house_key"]: row
            for row in conn.execute(
                "SELECT * FROM house_states WHERE snapshot_id=?",
                (previous_id,),
            )
        }
        current = {
            row["house_key"]: row
            for row in conn.execute(
                "SELECT * FROM house_states WHERE snapshot_id=?",
                (snapshot_id,),
            )
        }
        project_groups = {
            row["project_id"]: row["group_id"]
            for row in conn.execute("SELECT project_id, group_id FROM official_projects")
        }
        rows = []
        for key, row in current.items():
            prev = previous.get(key)
            if prev is None:
                change_type = "new"
                from_status = ""
            elif prev["status_code"] != row["status_code"]:
                change_type = "status"
                from_status = prev["status_code"]
            else:
                continue
            rows.append(
                (
                    snapshot_id,
                    project_groups[row["project_id"]],
                    row["building_id"],
                    row["house_key"],
                    row["house_no"],
                    change_type,
                    from_status,
                    row["status_code"],
                )
            )
        for key, row in previous.items():
            if key in current:
                continue
            rows.append(
                (
                    snapshot_id,
                    project_groups[row["project_id"]],
                    row["building_id"],
                    row["house_key"],
                    row["house_no"],
                    "missing",
                    row["status_code"],
                    "",
                )
            )
        conn.executemany(
            """
            INSERT INTO state_changes (
              snapshot_id, group_id, building_id, house_key, house_no,
              change_type, from_status, to_status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            rows,
        )

    def _group_house_counts(
        self,
        conn: sqlite3.Connection,
        snapshot_id: int,
    ) -> dict[str, dict[str, int]]:
        counts: dict[str, dict[str, int]] = defaultdict(dict)
        rows = conn.execute(
            """
            SELECT p.group_id, h.status_code, COUNT(*) AS count
            FROM house_states h
            JOIN official_projects p ON p.project_id=h.project_id
            WHERE h.snapshot_id=?
            GROUP BY p.group_id, h.status_code
            """,
            (snapshot_id,),
        )
        for row in rows:
            counts[row["group_id"]][row["status_code"]] = row["count"]
        return counts

    def _changes(
        self,
        conn: sqlite3.Connection,
        snapshot_id: int,
        group_id: str | None = None,
        limit: int | None = 20,
    ) -> list[dict]:
        params: list[object] = [snapshot_id]
        where = "c.snapshot_id=?"
        if group_id:
            where += " AND c.group_id=?"
            params.append(group_id)
        limit_clause = ""
        if limit is not None:
            limit_clause = "LIMIT ?"
            params.append(limit)
        return [
            dict(row)
            for row in conn.execute(
                f"""
                SELECT c.*, g.name AS group_name, b.name AS building_name, p.name AS project_name
                FROM state_changes c
                JOIN project_groups g ON g.id=c.group_id
                LEFT JOIN buildings b ON b.building_id=c.building_id
                LEFT JOIN official_projects p ON p.project_id=b.project_id
                WHERE {where}
                ORDER BY c.id DESC
                {limit_clause}
                """,
                params,
            )
        ]

    def _status_changes(
        self,
        conn: sqlite3.Connection,
        group_id: str,
        changes_since: str,
    ) -> list[dict]:
        return [
            dict(row)
            for row in conn.execute(
                """
                WITH successful_snapshots AS (
                  SELECT id, completed_at,
                    LAG(completed_at) OVER (ORDER BY id) AS previous_completed_at
                  FROM snapshots
                  WHERE status='success'
                )
                SELECT c.*, s.completed_at, s.previous_completed_at,
                  b.name AS building_name, p.name AS project_name
                FROM state_changes c
                JOIN successful_snapshots s ON s.id=c.snapshot_id
                JOIN buildings b ON b.building_id=c.building_id
                JOIN official_projects p ON p.project_id=b.project_id
                WHERE c.group_id=? AND s.completed_at>=?
                  AND c.change_type='status'
                ORDER BY s.completed_at, c.id
                """,
                (group_id, changes_since),
            )
        ]

SCHEMA = """
CREATE TABLE IF NOT EXISTS project_groups (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  description TEXT NOT NULL,
  developer_hint TEXT NOT NULL,
  sort_order INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS official_projects (
  project_id TEXT PRIMARY KEY,
  group_id TEXT NOT NULL REFERENCES project_groups(id),
  name TEXT NOT NULL,
  permit_no TEXT NOT NULL,
  issue_date TEXT NOT NULL DEFAULT '',
  detail_url TEXT NOT NULL DEFAULT '',
  land_location TEXT NOT NULL DEFAULT '',
  developer TEXT NOT NULL DEFAULT '',
  planning_permit_no TEXT NOT NULL DEFAULT '',
  approved_scope TEXT NOT NULL DEFAULT '',
  is_in_scope INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS buildings (
  building_id TEXT PRIMARY KEY,
  project_id TEXT NOT NULL REFERENCES official_projects(project_id),
  name TEXT NOT NULL,
  detail_url TEXT NOT NULL,
  approved_units TEXT NOT NULL DEFAULT '',
  approved_area TEXT NOT NULL DEFAULT '',
  sale_status TEXT NOT NULL DEFAULT '',
  price TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS snapshots (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  started_at TEXT NOT NULL,
  completed_at TEXT,
  status TEXT NOT NULL,
  source_scope TEXT NOT NULL DEFAULT 'shijingshan_17',
  error_message TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS house_states (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  snapshot_id INTEGER NOT NULL REFERENCES snapshots(id),
  building_id TEXT NOT NULL REFERENCES buildings(building_id),
  project_id TEXT NOT NULL REFERENCES official_projects(project_id),
  house_key TEXT NOT NULL,
  house_no TEXT NOT NULL,
  unit_no TEXT NOT NULL DEFAULT '',
  floor_no INTEGER,
  display_floor TEXT NOT NULL DEFAULT '',
  status_code TEXT NOT NULL,
  status_label TEXT NOT NULL,
  status_color TEXT NOT NULL,
  house_id TEXT NOT NULL DEFAULT '',
  source_url TEXT NOT NULL DEFAULT '',
  UNIQUE(snapshot_id, house_key)
);

CREATE TABLE IF NOT EXISTS state_changes (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  snapshot_id INTEGER NOT NULL REFERENCES snapshots(id),
  group_id TEXT NOT NULL REFERENCES project_groups(id),
  building_id TEXT NOT NULL,
  house_key TEXT NOT NULL,
  house_no TEXT NOT NULL,
  change_type TEXT NOT NULL,
  from_status TEXT NOT NULL DEFAULT '',
  to_status TEXT NOT NULL DEFAULT ''
);

CREATE INDEX IF NOT EXISTS idx_house_states_snapshot_building
ON house_states(snapshot_id, building_id);

CREATE INDEX IF NOT EXISTS idx_house_states_snapshot_project
ON house_states(snapshot_id, project_id);

CREATE INDEX IF NOT EXISTS idx_state_changes_snapshot_group
ON state_changes(snapshot_id, group_id);

CREATE INDEX IF NOT EXISTS idx_state_changes_group_snapshot_status
ON state_changes(group_id, snapshot_id, to_status);

CREATE INDEX IF NOT EXISTS idx_state_changes_building_house_snapshot
ON state_changes(building_id, house_key, snapshot_id);

CREATE INDEX IF NOT EXISTS idx_house_states_building_house_snapshot
ON house_states(building_id, house_key, snapshot_id);
"""
