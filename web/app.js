const STATUS = {
  disabled: { label: "不可售", color: "#CCCCCC" },
  available: { label: "可售", color: "#33CC00" },
  reserved: { label: "已预订", color: "#FFCC99" },
  signed: { label: "已签约", color: "#FF0000" },
  mortgage: { label: "已办理预售项目抵押", color: "#ffff00" },
  recorded: { label: "网上联机备案", color: "#d2691e" },
  checking: { label: "资格核验中", color: "#00FFFF" },
};

const {
  buildStatusTimeline,
  createRequestGate,
  escapeHtml,
  safeColor,
  safeUrl,
  salesWindowLabel,
} = window.HouseQueryLogic;

let groups = [
  {
    id: "ruiwenli",
    name: "中海瑞文里",
    developer: "北京鑫安兴业房地产开发有限公司",
    description: "西黄村棚改 1606-648/650 地块",
    projects: [
      p("8102776", "瑞玉苑", "京房售证字(2025)103号", "1606-648", "1#、3#、4#、5#住宅楼"),
      p("8156388", "瑞玉苑", "京房售证字(2026)4号", "1606-648", "2#住宅楼"),
      p("8104626", "瑞宸苑", "京房售证字(2025)105号", "1606-650", "1#、3#住宅楼"),
      p("8104625", "瑞宸苑", "京房售证字(2025)106号", "1606-650", "7#、8#、9#住宅楼"),
      p("8116266", "瑞宸苑", "京房售证字(2025)119号", "1606-650", "2#、10#、11#住宅楼"),
      p("8138322", "瑞宸苑", "京房售证字(2025)144号", "1606-650", "4#、6#住宅楼"),
      p("8156386", "瑞宸苑", "京房售证字(2026)3号", "1606-650", "5#住宅楼"),
    ],
    counts: c(6, 184, 14, 31, 0, 28, 2),
    changes: [
      change("瑞宸苑 5#住宅楼", "1单元-901", "reserved", "signed"),
      change("瑞宸苑 5#住宅楼", "2单元-1501", "available", "recorded"),
      change("瑞玉苑 2#住宅楼", "1单元-702", "available", "reserved"),
      change("瑞宸苑 11#住宅楼", "2单元-1202", "available", "signed"),
      change("瑞玉苑 3#住宅楼", "新增楼栋", "disabled", "available", "新增房源"),
    ],
  },
  {
    id: "yuzhang",
    name: "玉章苑",
    developer: "北京鑫安兴业房地产开发有限公司",
    description: "西黄村棚改 1606-640 地块",
    projects: [
      p("8115251", "玉章苑", "京房售证字(2025)117号", "1606-640", "1#、2#、3#住宅楼"),
      p("8130368", "玉章苑", "京房售证字(2025)132号", "1606-640", "5#住宅楼"),
      p("8156387", "玉章苑", "京房售证字(2026)2号", "1606-640", "4#住宅楼"),
    ],
    counts: c(2, 96, 8, 17, 0, 10, 1),
    changes: [
      change("玉章苑 5#住宅楼", "1单元-902", "available", "reserved"),
      change("玉章苑 4#住宅楼", "2单元-701", "reserved", "signed"),
    ],
  },
  {
    id: "yuansong",
    name: "源颂苑",
    developer: "北京海鑫兴业房地产开发有限公司",
    description: "首钢东南区 1612-831 地块",
    projects: [
      p("8092297", "源颂苑", "京房售证字(2025)89号", "1612-831", "1#、6#、7#住宅楼"),
      p("8129234", "源颂苑", "京房售证字(2025)133号", "1612-831", "2#、3#、4#、5#住宅楼"),
    ],
    counts: c(4, 121, 5, 22, 0, 9, 0),
    changes: [
      change("源颂苑 6#住宅楼", "1单元-1101", "available", "signed"),
    ],
  },
  {
    id: "yuanxi",
    name: "首钢元玺片区",
    developer: "北京首怡科新置业有限公司",
    description: "新首钢国际人才社区核心区",
    projects: [
      p("7769635", "元禧景园", "京房售证字(2023)142号", "1609-014", "2#、3#、6#、7#、8#住宅楼"),
      p("7769633", "元禧雅园", "京房售证字(2023)143号", "1609-019", "2#、4#、5#、6#、7#、8#、9#、10#住宅楼"),
    ],
    counts: c(11, 42, 0, 188, 0, 4, 0),
    changes: [
      change("元禧景园 7#住宅楼", "2单元-302", "recorded", "signed"),
      change("元禧雅园 4#住宅楼", "1单元-801", "available", "recorded"),
    ],
  },
  {
    id: "changanshougang",
    name: "首钢长安系",
    developer: "北京首景房地产开发有限公司",
    description: "首钢片区璟悦/璟瑞长安",
    projects: [
      p("8067898", "璟悦家园", "京房售证字(2025)73号", "SS00-1617-0003", "1#-16#部分住宅楼"),
      p("8195341", "璟瑞家园", "京房售证字(2026)35号", "SS00-1609-0012", "1#-7#住宅楼"),
    ],
    counts: c(9, 213, 7, 58, 1, 11, 3),
    changes: [
      change("璟瑞家园 1#住宅楼", "1单元-501", "available", "reserved"),
      change("璟悦家园 10#住宅楼", "2单元-1602", "available", "checking"),
    ],
  },
  {
    id: "yujing",
    name: "玉景阳光里",
    developer: "北京中实置业有限公司",
    description: "玉泉西一路 X-18160 地块",
    projects: [
      p("6219204", "玉景阳光里", "京房售证字(2018)181号", "X-18160", "1#-14#楼"),
    ],
    counts: c(18, 34, 0, 96, 0, 6, 0),
    changes: [
      change("玉景阳光里 3#住宅楼", "2单元-302", "available", "signed"),
    ],
  },
];

const buildingSets = {
  ruiwenli: [
    b("rc-5", "瑞宸苑 5#住宅楼", 60, c(1, 49, 5, 3, 0, 7, 0)),
    b("rc-11", "瑞宸苑 11#住宅楼", 60, c(0, 42, 3, 8, 0, 6, 1)),
    b("ry-2", "瑞玉苑 2#住宅楼", 56, c(2, 39, 4, 5, 0, 5, 1)),
    b("ry-3", "瑞玉苑 3#住宅楼", 89, c(3, 54, 2, 15, 0, 13, 2)),
  ],
  yuzhang: [
    b("yz-1", "玉章苑 1#住宅楼", 44, c(1, 31, 3, 6, 0, 3, 0)),
    b("yz-4", "玉章苑 4#住宅楼", 40, c(0, 28, 2, 7, 0, 2, 1)),
    b("yz-5", "玉章苑 5#住宅楼", 38, c(1, 23, 3, 4, 0, 7, 0)),
  ],
  yuansong: [
    b("ys-1", "源颂苑 1#住宅楼", 72, c(2, 38, 2, 18, 0, 12, 0)),
    b("ys-6", "源颂苑 6#住宅楼", 80, c(1, 47, 3, 14, 0, 15, 0)),
  ],
  yuanxi: [
    b("yxj-7", "元禧景园 7#住宅楼", 72, c(3, 18, 0, 47, 0, 4, 0)),
    b("yxy-4", "元禧雅园 4#住宅楼", 86, c(4, 24, 0, 55, 0, 3, 0)),
  ],
  changanshougang: [
    b("jr-1", "璟瑞家园 1#住宅楼", 72, c(3, 55, 2, 7, 0, 3, 2)),
    b("jy-10", "璟悦家园 10#住宅楼", 90, c(2, 63, 3, 17, 1, 2, 2)),
    b("jy-16", "璟悦家园 16#住宅楼", 80, c(4, 52, 2, 17, 0, 5, 0)),
  ],
  yujing: [
    b("yj-3", "玉景阳光里 3#住宅楼", 48, c(7, 12, 0, 27, 0, 2, 0)),
    b("yj-9", "玉景阳光里 9#住宅楼", 54, c(5, 14, 0, 32, 0, 3, 0)),
  ],
};

let activeGroup = groups[0];
let activeBuilding = null;
let selectedHouse = null;
let salesWindow = "24h";
let salesLoading = false;
const houseHistoryCache = new Map();
const houseHistoryRequests = new Map();
const groupRequestGate = createRequestGate();
const buildingRequestGate = createRequestGate();
const houseRequestGate = createRequestGate();
let currentView = "home";
let dashboardMetrics = null;
let homeChanges = null;
let trendData = null;
let snapshotInfo = null;
let previousRefreshInfo = null;
let sourceLinks = {};
let apiBacked = false;

function p(id, name, permit, land, buildings) {
  return { id, name, permit, land, buildings, status: "正在预售" };
}

function c(disabled, available, reserved, signed, mortgage, recorded, checking) {
  return { disabled, available, reserved, signed, mortgage, recorded, checking };
}

function b(id, label, total, counts) {
  return { id, label, total, counts };
}

function change(building, house, from, to, note = "状态变化") {
  return { building, house, from, to, note };
}

function render() {
  renderGroups();
  renderMetrics();
  renderDaily();
  renderHomeChanges();
  renderTrend();
  syncView();
  renderOverview();
  renderBuildingSales();
  renderBuildingCards();
  renderProjects();
  renderChanges();
  renderBuildingBoard();
}

async function loadDashboard() {
  try {
    const response = await fetch("/api/dashboard");
    if (!response.ok) {
      throw new Error(`dashboard ${response.status}`);
    }
    const payload = await response.json();
    apiBacked = true;
    snapshotInfo = payload.snapshot || null;
    previousRefreshInfo = payload.previous_snapshot || null;
    sourceLinks = payload.source_links || {};
    dashboardMetrics = payload.metrics;
    trendData = payload.trend || [];
    homeChanges = payload.changes || [];
    groups = (payload.groups || []).map(group => ({
      id: group.id,
      name: group.name,
      developer: group.developer_hint || "",
      description: group.description || "",
      projects: [],
      counts: {
        disabled: 0,
        available: group.available || 0,
        reserved: 0,
        signed: 0,
        mortgage: 0,
        recorded: 0,
        checking: 0,
      },
      project_count: group.project_count || 0,
      house_count: group.house_count || 0,
      deal_count: group.deal_count || 0,
      change_count: group.change_count || 0,
      changes: [],
    }));
    activeGroup = groups.find(group => group.id === activeGroup?.id) || groups[0] || activeGroup;
    render();
  } catch {
    apiBacked = false;
    render();
  }
}

async function openGroup(groupId) {
  buildingRequestGate.invalidate();
  dismissHousePopover();
  activeGroup = groups.find(group => group.id === groupId) || activeGroup;
  activeBuilding = null;
  currentView = "detail";
  salesWindow = "24h";
  salesLoading = false;
  if (apiBacked) {
    await loadGroupDetail(groupId, salesWindow);
  }
  render();
}

async function loadGroupDetail(groupId, requestedWindow = salesWindow) {
  const requestToken = groupRequestGate.next();
  let response;
  try {
    response = await fetch(`/api/groups/${encodeURIComponent(groupId)}?change_window=${encodeURIComponent(requestedWindow)}`);
  } catch {
    return false;
  }
  if (!response.ok) {
    return false;
  }
  const detail = await response.json();
  if (
    !groupRequestGate.isCurrent(requestToken) ||
    activeGroup.id !== groupId ||
    salesWindow !== requestedWindow
  ) {
    return false;
  }
  activeGroup = {
    ...activeGroup,
    ...(detail.group || {}),
    counts: normalizeCounts(detail.counts || {}),
    projects: (detail.projects || []).map(project => ({
      id: project.project_id,
      name: project.name,
      permit: project.permit_no,
      land: project.land_location,
      buildings: project.approved_scope,
      url: project.detail_url,
      status: "正在预售",
    })),
    buildings: detail.buildings || [],
    buildingStatusChanges: detail.status_changes_by_building || [],
    windowStatusChanges: normalizeChanges(detail.status_changes || []),
    changes: normalizeChanges(detail.changes || []),
  };
  return true;
}

async function openBuilding(buildingId) {
  const requestToken = buildingRequestGate.next();
  const groupId = activeGroup.id;
  const source = activeGroup.buildings || buildingSets[activeGroup.id] || [];
  activeBuilding = source.find(building => String(building.building_id || building.id) === buildingId);
  selectedHouse = null;
  hideHousePopover();
  if (apiBacked) {
    const response = await fetch(`/api/buildings/${encodeURIComponent(buildingId)}`);
    if (response.ok) {
      const detail = await response.json();
      if (!buildingRequestGate.isCurrent(requestToken) || activeGroup.id !== groupId) {
        return;
      }
      activeBuilding = {
        ...activeBuilding,
        ...(detail.building || {}),
        id: buildingId,
        label: detail.building?.name || activeBuilding?.name || activeBuilding?.label,
        houses: detail.houses || [],
      };
    }
  }
  if (!buildingRequestGate.isCurrent(requestToken) || activeGroup.id !== groupId) {
    return;
  }
  renderBuildingCards();
  renderBuildingBoard();
  window.requestAnimationFrame(() => {
    document.getElementById("buildingPanel")?.scrollIntoView({ block: "start", behavior: "smooth" });
  });
}

function renderGroups() {
  const list = document.getElementById("groupList");
  list.innerHTML = groups.map(group => `
    <button class="group-button ${group.id === activeGroup.id ? "active" : ""}" data-group="${escapeHtml(group.id)}" type="button">
      <strong>${escapeHtml(group.name)}</strong>
      <span>${projectCount(group)} 条预售项目 · 房源 ${houseCount(group)} 套</span>
      <span>查看项目组详情</span>
    </button>
  `).join("");

  list.querySelectorAll("button").forEach(button => {
    button.addEventListener("click", () => {
      openGroup(button.dataset.group);
    });
  });
}

function renderMetrics() {
  if (dashboardMetrics) {
    renderOfficialEntryLink();
    document.getElementById("metricProjects").textContent = dashboardMetrics.projects;
    document.getElementById("metricBuildings").textContent = dashboardMetrics.buildings;
    document.getElementById("metricAvailable").textContent = dashboardMetrics.available;
    document.getElementById("metricChanges").textContent = dashboardMetrics.changes;
    document.getElementById("metricNew").textContent = dashboardMetrics.new_projects;
    document.getElementById("groupCount").textContent = `${groups.length} 个项目组`;
    document.getElementById("refreshState").textContent = formatSnapshotTime(snapshotInfo);
    document.getElementById("homeChangeCompareText").textContent = compareRefreshText();
    document.getElementById("snapshotText").textContent = hasComparableSnapshot()
      ? "本次刷新数据已加载"
      : "首次刷新数据已加载，暂无历史对比";
    return;
  }
  const allCounts = groups.reduce((acc, group) => {
    Object.keys(STATUS).forEach(key => acc[key] += group.counts[key]);
    return acc;
  }, c(0, 0, 0, 0, 0, 0, 0));
  document.getElementById("metricProjects").textContent = groups.reduce((n, g) => n + g.projects.length, 0);
  document.getElementById("metricBuildings").textContent = "68";
  document.getElementById("metricAvailable").textContent = allCounts.available;
  document.getElementById("metricChanges").textContent = groups.reduce((n, g) => n + g.changes.length, 0);
  document.getElementById("metricNew").textContent = "0";
  document.getElementById("groupCount").textContent = `${groups.length} 个项目组`;
}

function syncView() {
  document.getElementById("homeView").classList.toggle("is-hidden", currentView !== "home");
  document.getElementById("detailView").classList.toggle("is-hidden", currentView !== "detail");
}

function renderTrend() {
  const values = trendData?.length ? trendData.map(item => Number(item.value) || 0) : [6, 9, 5, 11, 8, 13, 10];
  const max = Math.max(...values, 1);
  document.getElementById("trendChart").innerHTML = values.map((value, index) => `
    <div class="trend-bar">
      <strong>${value}</strong>
      <div class="trend-bar-fill" style="height:${Math.round((value / max) * 150)}px"></div>
      <span>${index === values.length - 1 ? "本次" : `${values.length - index}日前`}</span>
    </div>
  `).join("");
}

function renderDaily() {
  document.getElementById("dailyGrid").innerHTML = groups.map(group => {
    const changed = changeCount(group);
    return `
      <button class="daily-card" data-group="${escapeHtml(group.id)}" type="button">
        <strong>${escapeHtml(group.name)}</strong>
        <div class="daily-stats">
          <div class="daily-stat sale">
            <span>本次状态变化</span>
            <b>${changed}</b>
          </div>
          <div class="daily-stat">
            <span>当前可售</span>
            <b>${Number(group.counts?.available || 0)}</b>
          </div>
        </div>
      </button>
    `;
  }).join("");

  document.querySelectorAll(".daily-card").forEach(button => {
    button.addEventListener("click", () => {
      openGroup(button.dataset.group);
    });
  });
}

function renderHomeChanges() {
  const items = homeChanges?.length
    ? normalizeChanges(homeChanges)
    : groups.flatMap(group => group.changes.map(item => ({ ...item, group: group.name }))).slice(0, 8);
  if (!items.length) {
    document.getElementById("homeChangeList").innerHTML = emptyChangeMessage();
    return;
  }
  document.getElementById("homeChangeList").innerHTML = items.map(item => `
    <div class="change-item">
      <strong>${escapeHtml(changeTitle(item, true))}</strong>
      <div class="change-flow">
        <span class="state-chip" style="--state-color:${STATUS[item.from]?.color || "#ccc"}">${escapeHtml(STATUS[item.from]?.label || item.from)}</span>
        <span>到</span>
        <span class="state-chip" style="--state-color:${STATUS[item.to]?.color || "#ccc"}">${escapeHtml(STATUS[item.to]?.label || item.to)}</span>
      </div>
      <span>${escapeHtml(item.note)}</span>
    </div>
  `).join("");
}

function renderOverview() {
  document.getElementById("activeGroupName").textContent = activeGroup.name;
  document.getElementById("activeGroupMeta").textContent = `${activeGroup.projects.length} 条预售项目 · ${activeGroup.developer}`;
  document.getElementById("statusGrid").innerHTML = Object.entries(STATUS).map(([key, status]) => `
    <div class="status-tile" style="--status-color:${status.color}">
      <span>${status.label}</span>
      <strong>${activeGroup.counts[key]}</strong>
    </div>
  `).join("");
}

function renderBuildingSales() {
  const container = document.getElementById("buildingSalesChart");
  const windowLabel = salesWindowLabel(salesWindow);
  const rows = activeGroup.buildingStatusChanges || [];
  const statusChanges = activeGroup.windowStatusChanges || [];
  const totalChanges = rows.reduce((total, row) => total + Number(row.change_count || 0), 0);
  const activeBuildings = rows.filter(row => Number(row.change_count || 0) > 0).length;
  document.getElementById("salesSummary").textContent = totalChanges
    ? `${totalChanges} 条变化 · ${activeBuildings} 栋`
    : `${windowLabel}暂无状态变化`;
  document.querySelector(".sales-title-row h2").textContent = `${windowLabel}状态变化`;
  document.querySelectorAll("#salesWindowTabs button").forEach(button => {
    const isActive = button.dataset.window === salesWindow;
    button.classList.toggle("active", isActive);
    button.setAttribute("aria-pressed", String(isActive));
    button.onclick = () => selectSalesWindow(button.dataset.window);
  });

  if (salesLoading) {
    document.getElementById("salesSummary").textContent = "正在读取状态变化";
    container.innerHTML = '<div class="empty-state">正在加载所选时间范围</div>';
    return;
  }

  if (!rows.length) {
    container.innerHTML = `<div class="empty-state">${apiBacked ? `${escapeHtml(windowLabel)}未监测到房源状态变化` : "连接数据后显示状态变化"}</div>`;
    return;
  }

  const max = Math.max(...rows.map(row => Number(row.change_count || 0)), 1);
  const byProject = new Map();
  rows.forEach(row => {
    const project = row.project_name || "未识别项目";
    if (!byProject.has(project)) {
      byProject.set(project, []);
    }
    byProject.get(project).push(row);
  });
  container.innerHTML = Array.from(byProject.entries()).map(([project, buildings]) => `
    <section class="sales-project-group">
      <header><strong>${escapeHtml(project)}</strong><span>${buildings.reduce((total, item) => total + Number(item.change_count || 0), 0)} 条变化</span></header>
      <div class="sales-bars">
        ${buildings.sort((a, b) => Number(b.change_count || 0) - Number(a.change_count || 0)).map(row => {
          const total = Number(row.change_count || 0);
          const width = total ? Math.max((total / max) * 100, 7) : 0;
          return `
            <button class="sales-bar-row" data-building="${escapeHtml(row.building_id)}" type="button">
              <span class="sales-building-name">${escapeHtml(row.building_name)}</span>
              <span class="sales-bar-track" aria-label="${total} 条状态变化">
                <i class="sales-bar-fill" style="width:${width}%"></i>
              </span>
              <span class="sales-value">${total}<small>条</small></span>
            </button>
          `;
        }).join("")}
      </div>
      ${renderProjectStatusTimelines(project, buildings, statusChanges, windowLabel)}
    </section>
  `).join("");
  container.querySelectorAll(".sales-bar-row, .status-house-row").forEach(button => {
    button.addEventListener("click", () => openBuilding(button.dataset.building));
  });
}

function renderProjectStatusTimelines(project, buildings, statusChanges, windowLabel) {
  const buildingGroups = buildings.map(building => {
    const changes = statusChanges.filter(item => (
      item.project === project && item.building === building.building_name
    ));
    const byHouse = new Map();
    changes.forEach(changeItem => {
      if (!byHouse.has(changeItem.house)) {
        byHouse.set(changeItem.house, []);
      }
      byHouse.get(changeItem.house).push(changeItem);
    });
    return {
      building,
      timelines: Array.from(byHouse.entries()).map(([house, events]) => ({
        house,
        ...buildStatusTimeline(events),
      })),
    };
  }).filter(group => group.timelines.length);
  if (!buildingGroups.length) {
    return "";
  }
  return `
    <div class="status-timeline-list">
      <span class="status-timeline-title">${escapeHtml(windowLabel)}房源状态变化</span>
      ${buildingGroups.map(({ building, timelines }) => `
        <section class="status-building-group">
          <strong>${escapeHtml(building.building_name)}</strong>
          <div>
            ${timelines.map(timeline => `
              <button class="status-house-row" data-building="${escapeHtml(building.building_id)}" type="button">
                <b>${escapeHtml(timeline.house)}</b>
                <span class="status-chain">
                  ${timeline.statuses.map((status, index) => `
                    ${index ? '<i aria-hidden="true">→</i>' : ""}
                    <em class="state-chip" style="--state-color:${STATUS[status]?.color || "#ccc"}">${escapeHtml(STATUS[status]?.label || status)}</em>
                  `).join("")}
                </span>
                <span class="status-intervals">
                  ${timeline.events.map((event, index) => `
                    <time><small>${index + 1}</small>${escapeHtml(formatCompactInterval(event.previousCompletedAt, event.completedAt))}</time>
                  `).join("")}
                </span>
              </button>
            `).join("")}
          </div>
        </section>
      `).join("")}
    </div>
  `;
}

async function selectSalesWindow(windowKey) {
  if (!windowKey || windowKey === salesWindow) {
    return;
  }
  salesWindow = windowKey;
  salesLoading = true;
  renderBuildingSales();
  if (apiBacked) {
    await loadGroupDetail(activeGroup.id, windowKey);
  }
  if (salesWindow !== windowKey) {
    return;
  }
  salesLoading = false;
  renderBuildingSales();
}

function renderBuildingCards() {
  const buildings = activeGroup.buildings?.length ? activeGroup.buildings : buildingSets[activeGroup.id] || [];
  document.getElementById("buildingCards").innerHTML = groupedBuildings(buildings).map(group => `
    <section class="building-land-group">
      <header class="building-land-header">
        <div>
          <strong>${escapeHtml(group.title)}</strong>
          <span>${escapeHtml(group.meta)}</span>
        </div>
        ${sourceLink(group.projectUrl, "项目详情页")}
      </header>
      <div class="building-card-grid-inner">
        ${group.buildings.map(building => buildingCardTemplate(building)).join("")}
      </div>
    </section>
  `).join("");

  document.querySelectorAll(".building-card").forEach(card => {
    card.addEventListener("click", event => {
      if (event.target.closest("a")) {
        return;
      }
      openBuilding(card.dataset.building);
    });
    card.addEventListener("keydown", event => {
      if (event.key !== "Enter" && event.key !== " ") {
        return;
      }
      event.preventDefault();
      openBuilding(card.dataset.building);
    });
  });
}

function buildingCardTemplate(building) {
  return `
    <article class="building-card ${isActiveBuilding(building) ? "active" : ""}" data-building="${escapeHtml(buildingKey(building))}" tabindex="0" role="button">
      <strong>${escapeHtml(buildingLabel(building))}</strong>
      <span>${escapeHtml(buildingPermit(building))}房源 ${buildingTotal(building)} 套 · 可售 ${building.available || building.counts?.available || 0}</span>
      <div class="building-source-links">
        ${sourceLink(building.project_url, "项目页")}
        ${sourceLink(building.detail_url, "楼栋页")}
      </div>
      <div class="mini-status" aria-hidden="true">
        <i style="--mini-color:${STATUS.available.color}"></i>
        <i style="--mini-color:${STATUS.reserved.color}"></i>
        <i style="--mini-color:${STATUS.signed.color}"></i>
        <i style="--mini-color:${STATUS.recorded.color}"></i>
      </div>
    </article>
  `;
}

function groupedBuildings(buildings) {
  const sorted = [...buildings].sort(compareBuildings);
  const groupsByKey = new Map();
  sorted.forEach(building => {
    const land = landCode(building.land_location || building.land || "");
    const key = `${building.project_name || "楼栋"}|${land}`;
    if (!groupsByKey.has(key)) {
      groupsByKey.set(key, {
        title: `${building.project_name || "楼栋"}${land ? ` · ${land} 地块` : ""}`,
        landLocation: building.land_location || "地块信息待补充",
        permits: new Set(),
        buildings: [],
      });
    }
    const group = groupsByKey.get(key);
    if (building.permit_no) {
      group.permits.add(building.permit_no);
    }
    group.buildings.push(building);
  });
  return Array.from(groupsByKey.values()).map(group => ({
    ...group,
    meta: `${group.landLocation} · ${group.permits.size || 0} 条预售证 · ${group.buildings.length} 栋`,
  }));
}

function groupedProjects(projects) {
  const sorted = [...projects].sort((a, b) => (
    landCode(a.land || "").localeCompare(landCode(b.land || ""), "zh-CN", { numeric: true }) ||
    String(a.name || "").localeCompare(String(b.name || ""), "zh-CN", { numeric: true }) ||
    String(a.permit || "").localeCompare(String(b.permit || ""), "zh-CN", { numeric: true })
  ));
  const groupsByKey = new Map();
  sorted.forEach(project => {
    const land = landCode(project.land || "");
    const key = `${project.name || "预售项目"}|${land}`;
    if (!groupsByKey.has(key)) {
      groupsByKey.set(key, {
        title: `${project.name || "预售项目"}${land ? ` · ${land} 地块` : ""}`,
        meta: `${project.land || "地块信息待补充"}`,
        projects: [],
      });
    }
    groupsByKey.get(key).projects.push(project);
  });
  return Array.from(groupsByKey.values()).map(group => ({
    ...group,
    meta: `${group.meta} · ${group.projects.length} 条预售证`,
  }));
}

function compareBuildings(a, b) {
  return (
    landCode(a.land_location || a.land || "").localeCompare(
      landCode(b.land_location || b.land || ""),
      "zh-CN",
      { numeric: true }
    ) ||
    String(a.project_name || "").localeCompare(String(b.project_name || ""), "zh-CN", { numeric: true }) ||
    buildingNumber(a).localeCompare(buildingNumber(b), "zh-CN", { numeric: true })
  );
}

function buildingNumber(building) {
  return String(building.name || building.label || "");
}

function landCode(text) {
  return String(text).match(/\d{4}-\d{3}/)?.[0] || "";
}

function renderProjects() {
  document.getElementById("projectScope").textContent = `当前 ${activeGroup.projects.length} 条`;
  document.getElementById("projectRows").innerHTML = groupedProjects(activeGroup.projects).map(group => `
    <section class="project-land-group">
      <header class="project-land-header">
        <div>
          <strong>${escapeHtml(group.title)}</strong>
          <span>${escapeHtml(group.meta)}</span>
        </div>
      </header>
      <div class="project-table-wrap">
        <table class="project-table">
          <thead>
            <tr>
              <th>项目</th>
              <th>预售证</th>
              <th>楼栋</th>
              <th>状态</th>
            </tr>
          </thead>
          <tbody>
            ${group.projects.map(project => `
              <tr>
                <td>${escapeHtml(project.name)}${sourceLink(project.url, "项目页")}</td>
                <td>${escapeHtml(project.permit)}</td>
                <td>${escapeHtml(project.buildings)}</td>
                <td><span class="pill">${escapeHtml(project.status)}</span></td>
              </tr>
            `).join("")}
          </tbody>
        </table>
      </div>
    </section>
  `).join("");
}

function renderChanges() {
  document.getElementById("changeCompareText").textContent = compareRefreshText();
  const items = activeGroup.changes.length ? activeGroup.changes : [];
  if (!items.length) {
    document.getElementById("changeList").innerHTML = emptyChangeMessage();
    return;
  }
  document.getElementById("changeList").innerHTML = groupedChanges(items).map(group => `
    <section class="change-tree-group">
      <header>
        <strong>${escapeHtml(group.title)}</strong>
        <span>${group.items.length} 条变化</span>
      </header>
      <div>
        ${group.items.map(item => `
          <div class="change-item">
            <strong>${escapeHtml(detailChangeTitle(item))}</strong>
            <div class="change-flow">
              <span class="state-chip" style="--state-color:${STATUS[item.from]?.color || "#ccc"}">${escapeHtml(STATUS[item.from]?.label || item.from)}</span>
              <span>到</span>
              <span class="state-chip" style="--state-color:${STATUS[item.to]?.color || "#ccc"}">${escapeHtml(STATUS[item.to]?.label || item.to)}</span>
            </div>
            <span>${escapeHtml(item.note)}</span>
          </div>
        `).join("")}
      </div>
    </section>
  `).join("");
}

function renderBuildingBoard() {
  const panel = document.getElementById("buildingPanel");
  const board = document.getElementById("buildingBoard");
  const placeholder = document.getElementById("buildingPlaceholder");
  const orientationNote = document.getElementById("orientationNote");
  if (!activeBuilding) {
    panel.classList.add("is-hidden");
    document.getElementById("buildingTitle").textContent = "选择楼栋查看楼盘表";
    document.getElementById("buildingHint").textContent = "先从上方楼栋概览中选择一个楼栋";
    renderBuildingOfficialLink(null);
    renderBuildingSourceTrail(null);
    placeholder.classList.add("is-hidden");
    orientationNote.classList.add("is-hidden");
    orientationNote.textContent = "";
    board.classList.add("is-hidden");
    board.innerHTML = "";
    hideHousePopover();
    return;
  }

  panel.classList.remove("is-hidden");
  document.getElementById("buildingTitle").textContent = buildingLabel(activeBuilding);
  document.getElementById("buildingHint").textContent =
    `${buildingPermit(activeBuilding)}房源 ${buildingTotal(activeBuilding)} 套 · 可售 ${
      activeBuilding.available || activeBuilding.counts?.available || 0
    } 套`;
  renderBuildingOfficialLink(activeBuilding.detail_url);
  renderBuildingSourceTrail(activeBuilding);
  placeholder.classList.add("is-hidden");
  board.classList.remove("is-hidden");
  if (activeBuilding.houses?.length) {
    renderHousesFromApi(board, activeBuilding.houses);
    return;
  }
  const heads = ["自然楼层", "1单元-01", "1单元-02", "2单元-01", "2单元-02"];
  const rows = [];
  for (let floor = 15; floor >= 1; floor -= 1) {
    rows.push({ floor, houses: makeFloor(floor) });
  }
  board.innerHTML = heads.map(head => `<div class="board-head">${escapeHtml(head)}</div>`).join("") +
    rows.map(row => `
      <div class="floor-label">${row.floor}</div>
      ${row.houses.map(house => `
        <div class="house-cell" style="--house-color:${STATUS[house.status].color}" title="${escapeHtml(house.no)} · ${escapeHtml(STATUS[house.status].label)}">
          ${escapeHtml(house.no)}
        </div>
      `).join("")}
    `).join("");
  hideHousePopover();
}

function renderHousesFromApi(board, houses) {
  const floors = [...new Set(houses.map(house => house.floor_no).filter(Boolean))].sort((a, b) => b - a);
  const columns = [...new Map(houses
    .map(house => [houseColumnKey(house), houseColumnLabel(house)])
    .sort(([a], [b]) => a.localeCompare(b, "zh-CN", { numeric: true }))).values()];
  renderOrientationNote(columns);
  board.style.gridTemplateColumns = `74px repeat(${Math.max(columns.length, 1)}, 150px)`;
  board.innerHTML = ["自然楼层", ...columns].map(head => `<div class="board-head">${escapeHtml(head)}</div>`).join("") +
    floors.map(floor => {
      const cells = columns.map(column => {
        const house = houses.find(item => item.floor_no === floor && houseColumnLabel(item) === column);
        if (!house) {
          return `<div class="house-cell" style="--house-color:#f3f3f3"></div>`;
        }
        return `
          <button class="house-cell" data-house-key="${escapeHtml(house.house_key)}" style="--house-color:${safeColor(house.status_color)}" title="${escapeHtml(house.house_no)} · ${escapeHtml(house.status_label)}" type="button">
            ${escapeHtml(house.house_no)}
          </button>
        `;
      }).join("");
      return `<div class="floor-label">${floor}</div>${cells}`;
    }).join("");
  board.querySelectorAll(".house-cell[data-house-key]").forEach(cell => {
    cell.addEventListener("mouseenter", () => openHousePopover(cell.dataset.houseKey, cell));
    cell.addEventListener("mouseleave", () => {
      if (!selectedHouse?.pinned) {
        dismissHousePopover();
      }
    });
    cell.addEventListener("focus", () => openHousePopover(cell.dataset.houseKey, cell));
    cell.addEventListener("blur", () => {
      if (!selectedHouse?.pinned) {
        dismissHousePopover();
      }
    });
    cell.addEventListener("click", () => {
      const isPinned = selectedHouse?.key === cell.dataset.houseKey && selectedHouse.pinned;
      if (isPinned) {
        dismissHousePopover();
        return;
      }
      openHousePopover(cell.dataset.houseKey, cell, true);
    });
  });
}

async function openHousePopover(houseKey, anchor, pinned = false) {
  const house = activeBuilding?.houses?.find(item => item.house_key === houseKey);
  if (!house || !activeBuilding) {
    return;
  }
  const buildingId = buildingKey(activeBuilding);
  const key = `${buildingId}:${houseKey}`;
  const cachedHistory = houseHistoryCache.get(key);
  const requestToken = houseRequestGate.next();
  selectedHouse = {
    key: houseKey,
    house,
    anchor,
    pinned,
    requestToken,
    loading: !cachedHistory,
    history: cachedHistory || null,
  };
  renderHousePopover();
  if (cachedHistory) {
    return;
  }
  try {
    let request = houseHistoryRequests.get(key);
    if (!request) {
      request = fetch(`/api/buildings/${encodeURIComponent(buildingId)}/houses/${encodeURIComponent(houseKey)}/history`)
        .then(response => {
          if (!response.ok) {
            throw new Error(`house history ${response.status}`);
          }
          return response.json();
        });
      houseHistoryRequests.set(key, request);
    }
    const history = await request;
    houseHistoryCache.set(key, history);
    if (
      !houseRequestGate.isCurrent(requestToken) ||
      selectedHouse?.requestToken !== requestToken ||
      buildingKey(activeBuilding) !== buildingId
    ) {
      return;
    }
    selectedHouse = { ...selectedHouse, loading: false, history };
  } catch {
    if (!houseRequestGate.isCurrent(requestToken) || selectedHouse?.requestToken !== requestToken) {
      return;
    }
    selectedHouse = { ...selectedHouse, loading: false, history: null, error: true };
  } finally {
    houseHistoryRequests.delete(key);
  }
  renderHousePopover();
}

function renderHousePopover() {
  const panel = document.getElementById("houseHistoryPopover");
  if (!selectedHouse) {
    panel.classList.add("is-hidden");
    panel.innerHTML = "";
    return;
  }
  panel.classList.remove("is-hidden");
  if (selectedHouse.loading) {
    panel.innerHTML = `<strong>${escapeHtml(selectedHouse.house.house_no)}</strong><span>正在读取状态变化</span>`;
    positionHousePopover();
    return;
  }
  if (selectedHouse.error || !selectedHouse.history?.baseline) {
    panel.innerHTML = `<strong>${escapeHtml(selectedHouse.house.house_no)}</strong><span>未找到状态变化记录</span>`;
    positionHousePopover();
    return;
  }
  const history = selectedHouse.history;
  const baselineTime = formatTimelineTime(history.baseline.completed_at);
  panel.innerHTML = `
    <header><strong>${escapeHtml(selectedHouse.house.house_no)}</strong><span>${history.events.length ? `${history.events.length} 次状态变化` : "未发现状态变化"}</span></header>
    ${history.events.length ? `<ol>${history.events.map(event => `
      <li>
        <time>${escapeHtml(formatChangeInterval(event.previous_completed_at, event.completed_at))}</time>
        <span class="state-chip" style="--state-color:${STATUS[event.from_status]?.color || "#ccc"}">${escapeHtml(STATUS[event.from_status]?.label || event.from_status)}</span>
        <i>变为</i>
        <span class="state-chip" style="--state-color:${STATUS[event.to_status]?.color || "#ccc"}">${escapeHtml(STATUS[event.to_status]?.label || event.to_status)}</span>
      </li>
    `).join("")}</ol>` : ""}
    <p>最早记录 ${escapeHtml(baselineTime)} · 当时为${escapeHtml(STATUS[history.baseline.status_code]?.label || history.baseline.status_label)}；此前未找到状态变化。</p>
  `;
  positionHousePopover();
}

function positionHousePopover() {
  const panel = document.getElementById("houseHistoryPopover");
  const anchor = selectedHouse?.anchor;
  if (!anchor || panel.classList.contains("is-hidden")) {
    return;
  }
  const rect = anchor.getBoundingClientRect();
  const width = Math.min(320, window.innerWidth - 24);
  let left = rect.left + (rect.width / 2) - (width / 2);
  left = Math.max(12, Math.min(left, window.innerWidth - width - 12));
  panel.style.width = `${width}px`;
  panel.style.left = `${left}px`;
  panel.style.top = `${rect.bottom + 8}px`;
  const panelHeight = panel.offsetHeight;
  if (rect.bottom + panelHeight + 12 > window.innerHeight && rect.top > panelHeight + 12) {
    panel.style.top = `${rect.top - panelHeight - 8}px`;
  }
}

function hideHousePopover() {
  const panel = document.getElementById("houseHistoryPopover");
  panel?.classList.add("is-hidden");
}

function dismissHousePopover() {
  selectedHouse = null;
  houseRequestGate.invalidate();
  renderHousePopover();
}

window.addEventListener("scroll", () => {
  if (selectedHouse?.pinned) {
    positionHousePopover();
    return;
  }
  dismissHousePopover();
}, true);

window.addEventListener("resize", () => {
  if (selectedHouse) {
    positionHousePopover();
  }
});

function formatTimelineTime(value) {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? "未知时间" : formatDateTime(date);
}

function formatChangeInterval(previousValue, currentValue) {
  const current = formatTimelineTime(currentValue);
  if (!previousValue) {
    return `截至 ${current} 监测到`;
  }
  return `监测区间 ${formatTimelineTime(previousValue)}–${current}`;
}

function formatCompactInterval(previousValue, currentValue) {
  const previous = new Date(previousValue);
  const current = new Date(currentValue);
  if (Number.isNaN(current.getTime())) {
    return "监测时间未知";
  }
  if (Number.isNaN(previous.getTime())) {
    return `截至 ${formatDateTime(current)}`;
  }
  const previousText = formatDateTime(previous);
  const currentText = formatDateTime(current);
  const sameDay = previous.toLocaleDateString("zh-CN") === current.toLocaleDateString("zh-CN");
  return sameDay
    ? `${previousText}–${currentText.slice(-5)}`
    : `${previousText}–${currentText}`;
}

function houseColumnKey(house) {
  return houseColumnLabel(house);
}

function houseColumnLabel(house) {
  const unit = house.unit_no || "房号";
  const suffix = String(house.house_no || "").match(/(\d{2})$/)?.[1] || "";
  if (unit === "房号" && suffix === "01") {
    return "东侧-01";
  }
  if (unit === "房号" && suffix === "02") {
    return "西侧-02";
  }
  return suffix ? `${unit}-${suffix}` : unit;
}

function renderOrientationNote(columns) {
  const note = document.getElementById("orientationNote");
  if (!columns.length) {
    note.textContent = "";
    note.classList.add("is-hidden");
    return;
  }
  note.textContent = "列方向提示：单元排列从东到西，左侧朝东，右侧朝西。";
  note.classList.remove("is-hidden");
}

function normalizeCounts(counts) {
  return {
    disabled: counts.disabled || 0,
    available: counts.available || 0,
    reserved: counts.reserved || 0,
    signed: counts.signed || 0,
    mortgage: counts.mortgage || 0,
    recorded: counts.recorded || 0,
    checking: counts.checking || 0,
  };
}

function normalizeChanges(changes) {
  return changes.map(item => ({
    group: item.group_name || item.group || activeGroup.name,
    project: item.project_name || item.project || "",
    building: item.building_name || item.building || item.building_id || "",
    house: item.house_no || item.house || "",
    from: item.from_status || item.from || "disabled",
    to: item.to_status || item.to || "disabled",
    completedAt: item.completed_at || item.completedAt || "",
    previousCompletedAt: item.previous_completed_at || item.previousCompletedAt || "",
    note: item.change_type === "new" ? "新增房源" : item.change_type === "missing" ? "房源消失" : "状态变化",
  }));
}

function changeTitle(item, includeGroup) {
  return [
    includeGroup ? item.group : "",
    item.project,
    item.building,
    item.house,
  ].filter(Boolean).join(" · ");
}

function detailChangeTitle(item) {
  return item.house || [item.project, item.building].filter(Boolean).join(" · ") || "未识别房源";
}

function groupedChanges(changes) {
  const groupsByBuilding = new Map();
  changes.forEach(item => {
    const key = [item.project, item.building].filter(Boolean).join(" · ") || "未识别楼栋";
    if (!groupsByBuilding.has(key)) {
      groupsByBuilding.set(key, { title: key, items: [] });
    }
    groupsByBuilding.get(key).items.push(item);
  });
  return Array.from(groupsByBuilding.values());
}

function hasComparableSnapshot() {
  return (trendData || []).length > 1;
}

function emptyChangeMessage() {
  return `
    <div class="empty-state">
      ${hasComparableSnapshot() ? "本次刷新没有房源状态变化" : "当前只有首次刷新数据，暂无上次数据可对比"}
    </div>
  `;
}

function formatSnapshotTime(snapshot) {
  if (!snapshot?.completed_at) {
    return "暂无成功刷新";
  }
  const date = new Date(snapshot.completed_at);
  if (Number.isNaN(date.getTime())) {
    return "刷新数据已加载";
  }
  return `本次刷新 ${formatDateTime(date)}`;
}

function compareRefreshText() {
  if (!previousRefreshInfo?.completed_at) {
    return "暂无上次刷新记录";
  }
  const date = new Date(previousRefreshInfo.completed_at);
  if (Number.isNaN(date.getTime())) {
    return "对比上次刷新";
  }
  return `对比上次刷新 ${formatDateTime(date)}`;
}

function formatDateTime(date) {
  return date.toLocaleString("zh-CN", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  });
}

function renderOfficialEntryLink() {
  const link = document.getElementById("officialEntryLink");
  const url = safeUrl(sourceLinks.official_entry);
  if (!url) {
    link.classList.add("is-hidden");
    return;
  }
  link.href = url;
  link.textContent = sourceLinks.official_entry_label || "住建委入口";
  link.classList.remove("is-hidden");
}

function renderBuildingOfficialLink(url) {
  const link = document.getElementById("buildingOfficialLink");
  const safeLink = safeUrl(url);
  if (!safeLink) {
    link.classList.add("is-hidden");
    return;
  }
  link.href = safeLink;
  link.classList.remove("is-hidden");
}

function renderBuildingSourceTrail(building) {
  const trail = document.getElementById("buildingSourceTrail");
  if (!building) {
    trail.classList.add("is-hidden");
    trail.innerHTML = "";
    return;
  }
  const links = [
    sourceTrailLink(sourceLinks.official_entry, "入口检索页"),
    sourceTrailLink(building.project_url, `${building.project_name || "项目"}详情页`),
    sourceTrailLink(building.detail_url, "楼盘表页面"),
  ].filter(Boolean);
  if (!links.length) {
    trail.classList.add("is-hidden");
    trail.innerHTML = "";
    return;
  }
  trail.innerHTML = `
    <span>住建委链路</span>
    ${links.join("<i>/</i>")}
  `;
  trail.classList.remove("is-hidden");
}

function sourceTrailLink(url, label) {
  const safeLink = safeUrl(url);
  if (!safeLink) {
    return "";
  }
  return `<a href="${escapeHtml(safeLink)}" target="_blank" rel="noopener noreferrer">${escapeHtml(label)}</a>`;
}

function sourceLink(url, label) {
  const safeLink = safeUrl(url);
  if (!safeLink) {
    return "";
  }
  return `<a class="official-link inline-source-link" href="${escapeHtml(safeLink)}" target="_blank" rel="noopener noreferrer">${escapeHtml(label)}</a>`;
}

function projectCount(group) {
  return group.project_count ?? group.projects?.length ?? 0;
}

function houseCount(group) {
  return group.house_count ?? sumCounts(group.counts || {});
}

function changeCount(group) {
  return group.change_count ?? group.changes?.length ?? 0;
}

function buildingKey(building) {
  return String(building.building_id || building.id);
}

function buildingLabel(building) {
  if (building.project_name && building.name) {
    return `${building.project_name} ${building.name}`;
  }
  return building.label || building.name || "";
}

function buildingPermit(building) {
  return building.permit_no ? `${building.permit_no} · ` : "";
}

function buildingTotal(building) {
  return building.house_count || building.total || sumCounts(building.counts || {});
}

function isActiveBuilding(building) {
  return activeBuilding && buildingKey(activeBuilding) === buildingKey(building);
}

function makeFloor(floor) {
  const suffixes = ["01", "02", "01", "02"];
  const units = ["1单元", "1单元", "2单元", "2单元"];
  return suffixes.map((suffix, index) => {
    const no = `${units[index]}-${floor}${suffix}`;
    return { no, status: statusFor(floor, index) };
  });
}

function statusFor(floor, index) {
  const map = {
    "15-0": "recorded",
    "15-2": "recorded",
    "15-3": "recorded",
    "14-0": "reserved",
    "12-0": "recorded",
    "12-1": "reserved",
    "11-0": "signed",
    "10-0": "recorded",
    "9-0": "reserved",
    "9-2": "signed",
    "7-0": "reserved",
    "5-0": "recorded",
  };
  return map[`${floor}-${index}`] || "available";
}

function sumCounts(counts) {
  return Object.values(counts).reduce((a, b) => a + b, 0);
}

function showToast(text) {
  const toast = document.getElementById("toast");
  toast.textContent = text;
  toast.classList.add("show");
  window.setTimeout(() => toast.classList.remove("show"), 2800);
}

async function requestRefresh() {
  const headers = {};
  const savedToken = window.sessionStorage.getItem("refreshToken");
  if (savedToken) {
    headers["X-Refresh-Token"] = savedToken;
  }
  let response = await fetch("/api/refresh", { method: "POST", headers });
  if (response.status !== 401) {
    return response;
  }

  const token = window.prompt("请输入刷新口令");
  if (!token) {
    return response;
  }
  window.sessionStorage.setItem("refreshToken", token);
  response = await fetch("/api/refresh", {
    method: "POST",
    headers: { "X-Refresh-Token": token },
  });
  if (response.status === 401) {
    window.sessionStorage.removeItem("refreshToken");
  }
  return response;
}

document.getElementById("refreshButton").addEventListener("click", () => {
  const button = document.getElementById("refreshButton");
  const state = document.getElementById("refreshState");
  button.disabled = true;
  button.classList.add("is-refreshing");
  state.textContent = "正在刷新中";
  document.getElementById("snapshotText").textContent = "正在获取住建委数据";
  if (apiBacked) {
    requestRefresh()
      .then(async response => {
        if (response.status === 401) {
          throw new Error("刷新口令不正确");
        }
        return response.json();
      })
      .then(payload => {
        if (!payload.success) {
          throw new Error(payload.message || "刷新失败");
        }
        return pollRefreshStatus();
      })
      .then(() => {
        state.textContent = "刚刚刷新";
        document.getElementById("snapshotText").textContent = "本次刷新数据已加载";
        showToast("刷新完成，当前为本次刷新数据");
      })
      .catch(error => {
        state.textContent = "刷新失败";
        document.getElementById("snapshotText").textContent = "仍展示上次成功刷新数据";
        showToast(error.message || "刷新失败，仍展示上次成功数据");
      })
      .finally(() => {
        button.disabled = false;
        button.classList.remove("is-refreshing");
      });
    return;
  }
  window.setTimeout(() => {
    button.disabled = false;
    button.classList.remove("is-refreshing");
    state.textContent = "刚刚刷新";
    document.getElementById("snapshotText").textContent = "本次刷新数据已加载";
    showToast("刷新完成，当前为本次刷新数据");
  }, 1500);
});

document.getElementById("backButton").addEventListener("click", () => {
  currentView = "home";
  render();
});

async function pollRefreshStatus() {
  for (let attempt = 0; attempt < 240; attempt += 1) {
    await new Promise(resolve => window.setTimeout(resolve, 1500));
    const response = await fetch("/api/refresh/status");
    const payload = await response.json();
    if (payload.status === "success") {
      await loadDashboard();
      return;
    }
    if (payload.status === "failed") {
      throw new Error(payload.message || "刷新失败");
    }
  }
  throw new Error("刷新超时，仍展示上次成功数据");
}

loadDashboard();
