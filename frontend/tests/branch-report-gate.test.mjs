import test from "node:test";
import assert from "node:assert/strict";
import {createBranchReportGate} from "../src/lib/branch-report-gate.mjs";
test("slow older branch response cannot replace selected branch result",()=>{
  const gate=createBranchReportGate();
  const first=gate.start();
  const second=gate.start();
  assert.equal(gate.isCurrent(first),false);
  assert.equal(gate.isCurrent(second),true);
});
test("unmount invalidates outstanding report request",()=>{
  const gate=createBranchReportGate();
  const id=gate.start();gate.invalidate();
  assert.equal(gate.isCurrent(id),false);
});
