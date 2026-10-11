import test from "node:test";
import assert from "node:assert/strict";
import {
  asciiDigits,
  canContinueRegistration,
  isStrongPassword,
  normalizeMobileInput,
} from "../src/lib/registration-state.mjs";

test("Persian and Arabic digits normalize for OTP/mobile fields",()=>{
  assert.equal(asciiDigits("۰۹۱۲٣٤٥٦٧٨٩"),"09123456789");
  assert.equal(normalizeMobileInput("+98 (912) 345-6789"),"+989123456789");
});

test("registration cannot pass verification step without a grant",()=>{
  assert.equal(canContinueRegistration("verify",{verificationGrant:""}),false);
  assert.equal(canContinueRegistration("verify",{verificationGrant:"signed"}),true);
});

test("owner password contract matches backend baseline",()=>{
  assert.equal(isStrongPassword("short1"),false);
  assert.equal(isStrongPassword("NoDigitsHere!"),false);
  assert.equal(isStrongPassword("Cafino-Strong-2026!"),true);
});

test("branch details require a real primary branch name",()=>{
  assert.equal(canContinueRegistration("branch",{branchName:"   "}),false);
  assert.equal(canContinueRegistration("branch",{branchName:"شعبه اصلی"}),true);
});
