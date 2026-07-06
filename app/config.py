import os
from pathlib import Path

BASE_URL = "http://bjjs.zjw.beijing.gov.cn"
ENTRY_URL = f"{BASE_URL}/eportal/ui?pageId=53618753&isTrue=1"
PROJECT_URL = f"{BASE_URL}/eportal/ui?pageId=53618754&projectID={{project_id}}&systemID=2&srcId=1"
BUILDING_URL = (
    f"{BASE_URL}/eportal/ui?pageId=53618755&systemId=2&categoryId=1"
    "&salePermitId={sale_permit_id}&buildingId={building_id}"
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
DB_PATH = DATA_DIR / "app.db"
RAW_DIR = DATA_DIR / "raw"

SHIJINGSHAN_DISTRICT_ID = "9"
EXPECTED_IN_SCOPE_PROJECTS = 17
RAW_SNAPSHOT_KEEP = 7

STATUS_BY_COLOR = {
    "#CCCCCC": ("disabled", "不可售"),
    "#33CC00": ("available", "可售"),
    "#FFCC99": ("reserved", "已预订"),
    "#FF0000": ("signed", "已签约"),
    "#ffff00": ("mortgage", "已办理预售项目抵押"),
    "#d2691e": ("recorded", "网上联机备案"),
    "#00FFFF": ("checking", "资格核验中"),
}

DEAL_STATUS_CODES = {"signed", "recorded"}


def get_refresh_token() -> str:
    return os.environ.get("REFRESH_TOKEN", "")


def get_auto_refresh_enabled() -> bool:
    return os.environ.get("AUTO_REFRESH_ENABLED", "1").strip().lower() not in {
        "0",
        "false",
        "no",
        "off",
    }


def get_auto_refresh_time() -> str:
    return os.environ.get("AUTO_REFRESH_TIME", "09:00")


def get_auto_refresh_timezone() -> str:
    return os.environ.get("AUTO_REFRESH_TIMEZONE", "Asia/Shanghai")
