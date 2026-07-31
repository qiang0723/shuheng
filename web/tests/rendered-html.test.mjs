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
  assert.match(html, /五命中、五未命中/);
  assert.match(html, /主窗累计异常收益/);
  assert.match(html, /不把“不显著”改写成“无效”/);
  assert.match(html, /生命周期/);
  assert.match(html, /统计判决/);
  assert.match(html, /证据效力/);
  assert.doesNotMatch(html, /Building your site|Starter Project|codex-preview/i);
});

test("实验台账区分生命周期、统计判决和证据效力", async () => {
  const html = await htmlFor("/experiments");

  assert.match(html, /实验台账/);
  assert.match(html, /26行台账/);
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
  assert.match(html, /2026-07-31 10:57:18（UTC\+8）/);
  assert.match(html, /ledger_snapshot\.csv/);
  assert.match(html, /calibration_results\.csv/);
  assert.match(html, /财务退市风险警示/);
});
