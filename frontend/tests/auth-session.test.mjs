import test from "node:test";
import assert from "node:assert/strict";
import {
  ACCESS_TOKEN_KEY,
  REFRESH_TOKEN_KEY,
  clearSessionStorage,
  createRefreshCoordinator,
  readSession,
  requestWithOneRefresh,
  writeSession,
} from "../src/lib/auth-session.mjs";

function storage(){
  const values=new Map();
  return {
    getItem:key=>values.has(key)?values.get(key):null,
    setItem:(key,value)=>values.set(key,String(value)),
    removeItem:key=>values.delete(key),
  };
}

test("session storage writes, reads and clears both tokens",()=>{
  const s=storage();
  writeSession(s,{access:"a1",refresh:"r1"});
  assert.deepEqual(readSession(s),{access:"a1",refresh:"r1"});
  clearSessionStorage(s);
  assert.deepEqual(readSession(s),{access:null,refresh:null});
});

test("refresh preserves refresh token when backend rotates access only",async()=>{
  const s=storage();
  writeSession(s,{access:"old",refresh:"r1"});
  const refresh=createRefreshCoordinator({
    storage:s,
    refreshUrl:"/api/token/refresh/",
    fetchImpl:async()=>({ok:true,json:async()=>({access:"new"})}),
  });
  assert.equal(await refresh(),"new");
  assert.deepEqual(readSession(s),{access:"new",refresh:"r1"});
});

test("concurrent refresh callers share one network request",async()=>{
  const s=storage();writeSession(s,{access:"old",refresh:"r1"});
  let calls=0;let release;
  const gate=new Promise(resolve=>{release=resolve});
  const refresh=createRefreshCoordinator({
    storage:s,refreshUrl:"/refresh",
    fetchImpl:async()=>{calls++;await gate;return{ok:true,json:async()=>({access:"new"})}},
  });
  const a=refresh();const b=refresh();
  assert.equal(calls,1);
  release();
  assert.deepEqual(await Promise.all([a,b]),["new","new"]);
  assert.equal(calls,1);
});

test("failed refresh clears stale session",async()=>{
  const s=storage();writeSession(s,{access:"old",refresh:"bad"});
  const refresh=createRefreshCoordinator({
    storage:s,refreshUrl:"/refresh",fetchImpl:async()=>({ok:false,json:async()=>({})}),
  });
  await assert.rejects(refresh,/refresh_failed/);
  assert.deepEqual(readSession(s),{access:null,refresh:null});
});

test("one-refresh request retries exactly once",async()=>{
  let access="old";let requests=0;let refreshes=0;
  const response=await requestWithOneRefresh({
    getAccessToken:()=>access,
    request:async token=>{requests++;return{status:token==="old"?401:200}},
    refresh:async()=>{refreshes++;access="new"},
  });
  assert.equal(response.status,200);
  assert.equal(requests,2);
  assert.equal(refreshes,1);
});

test("second 401 is returned without an infinite refresh loop",async()=>{
  let requests=0;let refreshes=0;
  const response=await requestWithOneRefresh({
    getAccessToken:()=>"token",
    request:async()=>{requests++;return{status:401}},
    refresh:async()=>{refreshes++},
  });
  assert.equal(response.status,401);
  assert.equal(requests,2);
  assert.equal(refreshes,1);
});
