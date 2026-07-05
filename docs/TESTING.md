# 测试与验收策略

## 本地自动化

```bash
.venv/bin/python -m pytest -q
.venv/bin/ruff check .
node --check web/app.js
```

## 测试分层

- Parser 测试：读取 `tests/fixtures/` 的住建委 HTML 样本，验证列表页、项目详情页、楼栋楼盘表解析结果。
- Repository 测试：用临时 SQLite 数据库写入两次快照，验证状态变化、新增房源、失败快照不覆盖成功快照。
- API 测试：通过 `create_app(Repository(tmp_db))` 注入临时数据库，避免碰真实 `data/app.db`。
- Crawler 测试：使用 `FixtureClient` 离线模拟住建委，不真实访问官网，覆盖成功刷新和失败回退。
- 浏览器验收：启动本地服务后，用浏览器检查首页总览、小区详情、楼栋楼盘表、返回和刷新状态。

## 官网访问约束

自动测试禁止访问住建委官网。真实刷新只应由用户点击刷新或人工执行，且失败时不覆盖上一次成功数据。

## 回归重点

- 石景山项目数仍是一期定义的 17 条。
- 刷新失败后 `/api/dashboard` 仍返回上一次成功快照。
- `/static` 只能访问 `web/` 里的前端资源。
- 楼盘表展示不能因为同一单元同一楼层多户而漏格。
