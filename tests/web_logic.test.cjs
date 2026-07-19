const test = require("node:test");
const assert = require("node:assert/strict");

const {
  buildStatusTimeline,
  createRequestGate,
  escapeHtml,
  safeColor,
  safeUrl,
  salesWindowLabel,
} = require("../web/app_logic.js");

test("escapeHtml neutralizes markup and attributes", () => {
  assert.equal(
    escapeHtml('<img src=x onerror="alert(1)">'),
    "&lt;img src=x onerror=&quot;alert(1)&quot;&gt;",
  );
});

test("safeUrl only permits HTTP links", () => {
  assert.equal(safeUrl("javascript:alert(1)"), "");
  assert.equal(safeUrl("https://example.test/a").startsWith("https://example.test/a"), true);
});

test("safeColor rejects CSS injection", () => {
  assert.equal(safeColor("red;position:fixed"), "#cccccc");
  assert.equal(safeColor("#d2691e"), "#d2691e");
});

test("sales labels and request gates are deterministic", () => {
  assert.equal(salesWindowLabel("7d"), "近7天");
  const gate = createRequestGate();
  const first = gate.next();
  const second = gate.next();
  assert.equal(gate.isCurrent(first), false);
  assert.equal(gate.isCurrent(second), true);
  gate.invalidate();
  assert.equal(gate.isCurrent(second), false);
});

test("status timeline merges consecutive changes for one house", () => {
  const timeline = buildStatusTimeline([
    { from: "signed", to: "recorded", completedAt: "2026-07-17T01:03:00Z" },
    { from: "reserved", to: "signed", completedAt: "2026-07-11T01:01:00Z" },
  ]);
  assert.deepEqual(timeline.statuses, ["reserved", "signed", "recorded"]);
  assert.deepEqual(timeline.events.map(event => event.to), ["signed", "recorded"]);
});
