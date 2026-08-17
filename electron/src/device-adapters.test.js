const assert=require("assert");
const {registryPayload,callPager,sendPosAmount}=require("./device-adapters");

const registry=registryPayload({});
assert.equal(registry.ok,true);
assert.equal(registry.groups.PRINTER.selected,"SYSTEM");
assert.equal(registry.groups.PAGER.selected,"NONE");
assert.equal(registry.groups.POS.selected,"MANUAL");
assert.equal(registry.groups.PRINTER.adapters.find(x=>x.selected).status,"ready");

const fallback=registryPayload({CAF_INO_POS_ADAPTER:"UNKNOWN",CAF_INO_PAGER_ADAPTER:"UNKNOWN"});
assert.equal(fallback.groups.POS.selected,"MANUAL");
assert.equal(fallback.groups.PAGER.selected,"NONE");

const manual=sendPosAmount(125000,{});
assert.equal(manual.ok,false);
assert.equal(manual.requiresManual,true);
assert.equal(manual.adapter,"MANUAL");
assert.equal(sendPosAmount(0,{}).ok,false);

const pager=callPager({number:"12"},{});
assert.equal(pager.ok,false);
assert.equal(pager.status,"unconfigured");
assert.equal(pager.adapter,"NONE");

console.log("device adapter registry contract: ok");
