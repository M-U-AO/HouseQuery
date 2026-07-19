from app.models import ProjectGroup

GROUPS: list[ProjectGroup] = [
    ProjectGroup("ruiwenli", "中海瑞文里", "西黄村棚改 1606-648/650 地块", "北京鑫安兴业", 1),
    ProjectGroup("yuzhang", "玉章苑", "西黄村棚改 1606-640 地块", "北京鑫安兴业", 2),
    ProjectGroup("yuansong", "源颂苑", "首钢东南区 1612-831 地块", "北京海鑫兴业", 3),
    ProjectGroup("yuanxi", "首钢元玺片区", "新首钢国际人才社区核心区", "北京首怡科新", 4),
    ProjectGroup("changanshougang", "首钢长安系", "首钢片区璟悦/璟瑞长安", "北京首景", 5),
    ProjectGroup("yujing", "玉景阳光里", "玉泉西一路 X-18160 地块", "北京中实", 6),
]

GROUP_BY_PROJECT_ID = {
    "8102776": "ruiwenli",
    "8156388": "ruiwenli",
    "8104626": "ruiwenli",
    "8104625": "ruiwenli",
    "8116266": "ruiwenli",
    "8138322": "ruiwenli",
    "8156386": "ruiwenli",
    "8115251": "yuzhang",
    "8130368": "yuzhang",
    "8156387": "yuzhang",
    "8092297": "yuansong",
    "8129234": "yuansong",
    "7769635": "yuanxi",
    "7769633": "yuanxi",
    "8067898": "changanshougang",
    "8195341": "changanshougang",
    "6219204": "yujing",
}

PROJECT_LAND_BY_ID = {
    "8102776": "石景山区西黄村棚户区改造土地开发项目1606-648地块",
    "8156388": "石景山区西黄村棚户区改造土地开发项目1606-648地块",
    "8104626": "石景山区西黄村棚户区改造土地开发项目1606-650地块",
    "8104625": "石景山区西黄村棚户区改造土地开发项目1606-650地块",
    "8116266": "石景山区西黄村棚户区改造土地开发项目1606-650地块",
    "8138322": "石景山区西黄村棚户区改造土地开发项目1606-650地块",
    "8156386": "石景山区西黄村棚户区改造土地开发项目1606-650地块",
    "8115251": "石景山区西黄村棚户区改造土地开发项目1606-640地块",
    "8130368": "石景山区西黄村棚户区改造土地开发项目1606-640地块",
    "8156387": "石景山区西黄村棚户区改造土地开发项目1606-640地块",
}


def group_for_project(project_id: str, name: str = "") -> tuple[str, bool]:
    if project_id in GROUP_BY_PROJECT_ID:
        return GROUP_BY_PROJECT_ID[project_id], True
    if name == "瑞宸苑" or name == "瑞玉苑":
        return "ruiwenli", False
    if name == "玉章苑":
        return "yuzhang", False
    if name == "源颂苑":
        return "yuansong", False
    if name in {"元禧景园", "元禧雅园"}:
        return "yuanxi", False
    if name in {"璟悦家园", "璟瑞家园"}:
        return "changanshougang", False
    if name == "玉景阳光里":
        return "yujing", False
    return "unknown", False


def known_land_for_project(project_id: str) -> str:
    return PROJECT_LAND_BY_ID.get(project_id, "")
