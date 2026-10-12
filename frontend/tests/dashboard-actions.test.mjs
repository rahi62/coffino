import test from "node:test";
import assert from "node:assert/strict";
import {dashboardActions,mobileActions,permittedActions,routeIsActive} from "../src/lib/dashboard-actions.mjs";

test("no privileged quick action renders before permissions load or after request failure",()=>{
  assert.deepEqual(permittedActions(dashboardActions,null),[]);
  assert.deepEqual(permittedActions(dashboardActions,{}),[]);
  assert.deepEqual(permittedActions(dashboardActions,{"orders.create":false}),[]);
});
test("POS is reachable only with the effective backend create permission",()=>{
  assert.deepEqual(permittedActions(dashboardActions,{"orders.create":true}).map(x=>x.href),["/pos"]);
  assert.deepEqual(permittedActions(dashboardActions,{"orders.view":true}).map(x=>x.href),["/orders"]);
});
test("all eight quick actions have unique real routes and explicit permissions",()=>{
  assert.equal(dashboardActions.length,8);
  assert.equal(new Set(dashboardActions.map(x=>x.href)).size,8);
  assert.ok(dashboardActions.every(x=>x.href.startsWith("/")&&x.permission));
});
test("mobile destinations preserve dashboard while disallowing unauthorized sales",()=>{
  assert.deepEqual(permittedActions(mobileActions,{}).map(x=>x.href),["/"]);
  assert.deepEqual(permittedActions(mobileActions,{"orders.create":true,"orders.view":true,"tables.use":false}).map(x=>x.href),["/","/pos","/orders"]);
});
test("active route does not highlight dashboard for every page",()=>{
  assert.equal(routeIsActive("/","/"),true);
  assert.equal(routeIsActive("/pos","/"),false);
  assert.equal(routeIsActive("/orders/123","/orders"),true);
  assert.equal(routeIsActive("/orders-archived","/orders"),false);
});
