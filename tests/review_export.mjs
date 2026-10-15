import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import vm from "node:vm";

const html = readFileSync(0, "utf8");
assert.ok(!html.includes("PRIVATE_SENTINEL_93"));
const payload = html.match(/<script type="application\/json" id="report">([\s\S]*?)<\/script>/)[1];
const report = JSON.parse(payload);
assert.equal(report.report_mode, "value-redacted");
const script = html.match(/<script>([\s\S]*?)<\/script>/)[1];
const select = { value: "", dataset: { index: "0" } };
const elements = { report: { textContent: payload }, download: {}, status: {} };
let blob;
let downloaded = false;
const context = {
  document: {
    getElementById: (id) => elements[id],
    querySelectorAll: () => [select],
    createElement: () => ({ click() { downloaded = true; } }),
  },
  Blob,
  URL: { createObjectURL(value) { blob = value; return "blob:local"; }, revokeObjectURL() {} },
  setTimeout(fn) { fn(); },
};
vm.runInNewContext(script, context);
select.value = "remote";
elements.download.onclick();
assert.ok(downloaded);
const text = await blob.text();
assert.ok(!text.includes("PRIVATE_SENTINEL_93"));
const plan = JSON.parse(text);
assert.deepEqual(Object.keys(plan).sort(), ["choices", "input_sha256", "keyed_arrays", "version"]);
assert.deepEqual(plan.input_sha256, report.input_sha256);
assert.deepEqual(plan.keyed_arrays, report.keyed_arrays);
assert.deepEqual(plan.choices, { [report.conflicts[0].path]: "remote" });
console.log("Downloaded redacted replay plan is value-free and hash-bound.");
