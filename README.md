# 石景山期房余量查询

本地 Web 应用，用于采集北京住建委石景山区期房房源状态，保存 SQLite 快照，并展示小区、楼栋、房源状态变化。

## 启动

```bash
.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
```

打开：

```text
http://127.0.0.1:8000/
```

局域网访问时可绑定到所有网卡：

```bash
.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
```

公网部署建议通过 Caddy/Nginx 反向代理到 `127.0.0.1:8000`，并设置
`REFRESH_TOKEN` 保护刷新接口。完整步骤见
[国内公网部署步骤](docs/DEPLOYMENT_CN.md)。

## 测试

```bash
.venv/bin/python -m pytest -q
.venv/bin/ruff check .
node --check web/app.js
```

## 一期范围

- 只处理住建委“新建商品房房屋检索”中石景山区当前 17 条预售项目。
- 额外车库/非住宅预售证暂不纳入深度分析。
- 如果新增第 18 条，后续可展示为新增项目，但一期不自动深挖。
- 刷新全量成功才写入成功快照；失败不覆盖上一次成功数据。
- HTML 原文保留最近 7 次刷新，用于排查官网结构变化。

## 模块边界

- `app/crawler.py`：下载住建委 HTML，并编排刷新。
- `app/parser.py`：纯 HTML 解析，不访问网络和数据库。
- `app/repository.py`：SQLite schema、快照、查询和变化对比。
- `app/main.py`：FastAPI 接口和静态页面服务。
- `web/`：前端页面、样式和交互，只通过 `/api/*` 读取数据。
- `tests/fixtures/`：固定 HTML 样本，保障解析器回归。

## 设计与验证

- [架构说明](docs/ARCHITECTURE.md)
- [测试与验收策略](docs/TESTING.md)
- [一期需求边界](docs/PHASE1_SCOPE.md)
