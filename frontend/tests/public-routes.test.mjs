import test from "node:test";
import assert from "node:assert/strict";
import {isPublicRoute} from "../src/lib/public-routes.mjs";

test("auth pages are public",()=>{
  for(const path of ["/login","/register","/forgot-password","/reset-password"]){
    assert.equal(isPublicRoute(path),true,path);
  }
});

test("public menu routes are public but app routes remain protected",()=>{
  assert.equal(isPublicRoute("/menu/demo"),true);
  assert.equal(isPublicRoute("/"),false);
  assert.equal(isPublicRoute("/settings/onboarding"),false);
  assert.equal(isPublicRoute("/pos"),false);
});

test("query strings do not change public route classification",()=>{
  assert.equal(isPublicRoute("/login?reset=1"),true);
});
