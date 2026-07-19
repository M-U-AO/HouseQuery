(function exposeHouseQueryLogic(global) {
  function escapeHtml(value) {
    return String(value ?? "").replace(/[&<>'"]/g, character => ({
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      "'": "&#39;",
      "\"": "&quot;",
    })[character]);
  }

  function safeUrl(value) {
    if (!value) {
      return "";
    }
    try {
      const url = new URL(String(value), global.location?.origin || "http://localhost");
      return url.protocol === "http:" || url.protocol === "https:" ? url.href : "";
    } catch {
      return "";
    }
  }

  function safeColor(value, fallback = "#cccccc") {
    return /^#[0-9a-f]{3,8}$/i.test(String(value || "")) ? String(value) : fallback;
  }

  function salesWindowLabel(windowKey) {
    return {
      "24h": "近24小时",
      "3d": "近3天",
      "7d": "近7天",
      "30d": "近30天",
    }[windowKey] || "近24小时";
  }

  function createRequestGate() {
    let generation = 0;
    return {
      next() {
        generation += 1;
        return generation;
      },
      isCurrent(token) {
        return token === generation;
      },
      invalidate() {
        generation += 1;
      },
    };
  }

  function buildStatusTimeline(events) {
    const sortedEvents = [...events].sort((a, b) => (
      String(a.completedAt || "").localeCompare(String(b.completedAt || ""))
    ));
    const statuses = [];
    sortedEvents.forEach(event => {
      if (!statuses.length || statuses[statuses.length - 1] !== event.from) {
        statuses.push(event.from);
      }
      if (statuses[statuses.length - 1] !== event.to) {
        statuses.push(event.to);
      }
    });
    return { events: sortedEvents, statuses };
  }

  const logic = {
    buildStatusTimeline,
    createRequestGate,
    escapeHtml,
    safeColor,
    safeUrl,
    salesWindowLabel,
  };
  global.HouseQueryLogic = logic;
  if (typeof module !== "undefined" && module.exports) {
    module.exports = logic;
  }
})(globalThis);
