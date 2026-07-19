from __future__ import annotations

import asyncio
import secrets
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from datetime import time as datetime_time
from pathlib import Path
from typing import Annotated
from zoneinfo import ZoneInfo

from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.config import (
    ENTRY_URL,
    get_auto_refresh_enabled,
    get_auto_refresh_time,
    get_auto_refresh_timezone,
    get_refresh_token,
)
from app.crawler import RefreshService
from app.repository import Repository


class RefreshRuntime:
    """Per-application refresh state.

    Keeping this off module-level globals makes the API testable with an isolated
    temporary database while production still uses the same `app.main:app` entry.
    """

    def __init__(self, repository: Repository):
        self.repository = repository
        self.lock = asyncio.Lock()
        self.state: dict[str, object] = {"status": "idle", "message": ""}


WEB_ROOT = Path(__file__).resolve().parents[1] / "web"
CHANGE_WINDOWS = {"24h": 24, "3d": 72, "7d": 168, "30d": 720}


def create_app(repository: Repository | None = None) -> FastAPI:
    repo = repository or Repository()
    runtime = RefreshRuntime(repo)

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        repo.init_schema()
        repo.mark_abandoned_running_snapshots()
        auto_refresh_task: asyncio.Task[None] | None = None
        if get_auto_refresh_enabled():
            auto_refresh_task = asyncio.create_task(_run_daily_refresh(runtime))
        try:
            yield
        finally:
            if auto_refresh_task:
                auto_refresh_task.cancel()
                try:
                    await auto_refresh_task
                except asyncio.CancelledError:
                    pass

    app = FastAPI(title="石景山期房余量查询", lifespan=lifespan)
    app.state.repository = repo
    app.state.refresh_runtime = runtime

    @app.get("/api/dashboard")
    def dashboard() -> dict:
        repo.init_schema()
        payload = repo.dashboard()
        payload["source_links"] = {
            "official_entry": ENTRY_URL,
            "official_entry_label": "住建委新建商品房检索",
        }
        return payload

    @app.get("/api/groups/{group_id}")
    def group_detail(group_id: str, change_window: str = "24h") -> dict:
        if change_window not in CHANGE_WINDOWS:
            raise HTTPException(status_code=400, detail="invalid change window")
        detail = repo.group_detail(group_id, CHANGE_WINDOWS[change_window])
        if not detail or not detail.get("group"):
            raise HTTPException(status_code=404, detail="group data not found")
        return detail

    @app.get("/api/buildings/{building_id}")
    def building_detail(building_id: str) -> dict:
        detail = repo.building_detail(building_id)
        if not detail or not detail.get("building"):
            raise HTTPException(status_code=404, detail="building data not found")
        return detail

    @app.get("/api/buildings/{building_id}/houses/{house_key}/history")
    def house_history(building_id: str, house_key: str) -> dict:
        detail = repo.house_history(building_id, house_key)
        if not detail:
            raise HTTPException(status_code=404, detail="house history not found")
        return detail

    @app.post("/api/refresh")
    async def refresh(
        x_refresh_token: Annotated[str | None, Header(alias="X-Refresh-Token")] = None,
    ) -> dict:
        expected_token = get_refresh_token()
        if expected_token and not secrets.compare_digest(x_refresh_token or "", expected_token):
            raise HTTPException(status_code=401, detail="refresh token required")
        if runtime.lock.locked():
            return {"success": False, "status": "running", "message": "刷新正在进行中"}
        asyncio.create_task(_run_refresh(runtime))
        return {"success": True, "status": "running", "message": "刷新已开始"}

    @app.get("/api/refresh/status")
    def refresh_status() -> dict:
        return dict(runtime.state)

    app.mount("/static", StaticFiles(directory=WEB_ROOT), name="static")

    @app.get("/")
    def index() -> FileResponse:
        return FileResponse(WEB_ROOT / "index.html", headers={"Cache-Control": "no-cache"})

    return app


async def _run_refresh(runtime: RefreshRuntime) -> None:
    async with runtime.lock:
        runtime.state.update({"status": "running", "message": "正在刷新中"})
        try:
            snapshot_id = await asyncio.to_thread(RefreshService(runtime.repository).refresh)
        except Exception as exc:
            runtime.state.update({"status": "failed", "message": str(exc)})
            return
        runtime.state.update(
            {"status": "success", "message": "刷新完成", "snapshot_id": snapshot_id}
        )


async def _run_daily_refresh(runtime: RefreshRuntime) -> None:
    timezone = ZoneInfo(get_auto_refresh_timezone())
    refresh_time = _parse_daily_time(get_auto_refresh_time())
    while True:
        now = datetime.now(timezone)
        await asyncio.sleep(_seconds_until_next_daily_run(now, refresh_time))
        if not runtime.lock.locked():
            await _run_refresh(runtime)


def _parse_daily_time(value: str) -> datetime_time:
    try:
        hour_text, minute_text = value.split(":", 1)
        hour = int(hour_text)
        minute = int(minute_text)
        return datetime_time(hour=hour, minute=minute)
    except ValueError as exc:
        raise ValueError(f"invalid AUTO_REFRESH_TIME {value!r}, expected HH:MM") from exc


def _seconds_until_next_daily_run(now: datetime, refresh_time: datetime_time) -> float:
    scheduled = now.replace(
        hour=refresh_time.hour,
        minute=refresh_time.minute,
        second=0,
        microsecond=0,
    )
    if scheduled <= now:
        scheduled += timedelta(days=1)
    return (scheduled - now).total_seconds()


app = create_app()
