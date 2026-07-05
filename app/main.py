from __future__ import annotations

import asyncio
import secrets
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.config import ENTRY_URL, get_refresh_token
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


def create_app(repository: Repository | None = None) -> FastAPI:
    repo = repository or Repository()
    runtime = RefreshRuntime(repo)

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        repo.init_schema()
        repo.mark_abandoned_running_snapshots()
        yield

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
    def group_detail(group_id: str) -> dict:
        detail = repo.group_detail(group_id)
        if not detail or not detail.get("group"):
            raise HTTPException(status_code=404, detail="group data not found")
        return detail

    @app.get("/api/buildings/{building_id}")
    def building_detail(building_id: str) -> dict:
        detail = repo.building_detail(building_id)
        if not detail or not detail.get("building"):
            raise HTTPException(status_code=404, detail="building data not found")
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
        return FileResponse(WEB_ROOT / "index.html")

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


app = create_app()
