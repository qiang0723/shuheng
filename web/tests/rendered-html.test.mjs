import assert from "node:assert/strict";
import test from "node:test";

async function render(pathname = "/") {
  const workerUrl = new URL("../dist/server/index.js", import.meta.url);
  workerUrl.searchParams.set("test", `${process.pid}-${Date.now()}-${pathname}`);
  const { default: worker } = await import(workerUrl.href);

  return worker.fetch(
    new Request(`http://localhost${pathname}`, {
      headers: { accept: "text/html" },
    }),
    {
      ASSETS: {
        fetch: async () => new Response("Not found", { status: 404 }),
      },
    },
    {
      waitUntil() {},
      passThroughOnException() {},
    },
  );
}

async function htmlFor(pathname) {
  const response = await render(pathname);
  assert.equal(response.status, 200);
  assert.match(response.headers.get("content-type") ?? "", /^text\/html\b/i);
  return response.text();
}

test("首页给出当前结论、证据边界与中文字段说明", async () => {
  const html = await htmlFor("/");

  assert.match(html, /研究判断平台/);
  assert.match(html, /工程流水线已成熟/);
  assert.match(html, /正式真实研究/);
  assert.match(html, /唯一正式真实统计显著结果/);
  assert.match(html, /五命中、七未命中/);
  assert.match(html, /主窗累计异常收益/);
  assert.match(html, /不把“不显著”改写成“无效”/);
  assert.match(html, /生命周期/);
  assert.match(html, /统计判决/);
  assert.match(html, /证据效力/);
  assert.match(html, /现在能给出股票吗/);
  assert.match(html, /当前不输出个股候选/);
  assert.match(html, /历史事件研究，不是实时选股系统/);
  assert.match(html, /跨期暂停/);
  assert.match(html, /两类时点独立/);
  for (const id of [18, 21, 22, 23]) assert.match(html, new RegExp(`href="/experiments/${id}"`));
  assert.doesNotMatch(html, /Building your site|Starter Project|codex-preview/i);
});

test("实验台账区分生命周期、统计判决和证据效力", async () => {
  const html = await htmlFor("/experiments");

  assert.match(html, /实验台账/);
  assert.match(html, /26行台账/);
  assert.match(html, /十二条校准/);
  assert.match(html, /生命周期/);
  assert.match(html, /统计判决/);
  assert.match(html, /证据效力/);
  assert.match(html, /实施ST风险警示/);
  assert.match(html, /合成冒烟·不计正式研究/);
  assert.match(html, /预筛选/);
});

test("实验详情保留正式结果和不可交易边界", async () => {
  const html = await htmlFor("/experiments/568");

  assert.match(html, /实施ST风险警示/);
  assert.match(html, /聚集校正后达到统计显著/);
  assert.match(html, /只具预筛选效力/);
  assert.match(html, /基什有效样本量/);
  assert.match(html, /一字跌停锁死价格观察/);
  assert.match(html, /不得读作可成交收益或可执行策略/);
  assert.match(html, /来源与快照/);
  assert.match(html, /2026-08-09 22:14:05\.537694（UTC\+8）/);
  assert.match(html, /ledger_snapshot\.csv/);
  assert.match(html, /calibration_results\.csv/);
  assert.match(html, /财务退市风险警示/);
});

test("新增闭卷实验展示当前状态、指标与边界", async () => {
  const dividend = await htmlFor("/experiments/19");
  assert.match(dividend, /分红超预期/);
  assert.match(dividend, /已闭卷/);
  assert.match(dividend, /密封方向未中/);
  assert.match(dividend, /2024年剔除集中于稳健窗与数据右界/);

  const exDiv = await htmlFor("/experiments/14");
  assert.match(exDiv, /除权缺口/);
  assert.match(exDiv, /已闭卷/);
  assert.match(exDiv, /复权总回报/);
});

test("证据硬门实验详情区分研发停点与研究结果快照", async () => {
  const html = await htmlFor("/experiments/22");

  assert.match(html, /财务退市风险警示/);
  assert.match(html, /当前研究停点/);
  assert.match(html, /跨期暂停/);
  assert.match(html, /官方公告分页集合发生漂移/);
  assert.match(html, /STATE 一百五十一笔，2026-08-11（UTC\+8）/);
  assert.match(html, /2026-08-09 22:14:05\.537694（UTC\+8）/);
  assert.match(html, /本段只解释研发停点，不构成统计结果、代理证据或恢复授权/);
});
