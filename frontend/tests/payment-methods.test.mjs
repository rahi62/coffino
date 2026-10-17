import test from "node:test";
import assert from "node:assert/strict";
import {PAYMENT_METHODS,PAYMENT_METHOD_LABELS} from "../src/lib/payment-methods.mjs";

test("card-reader display label never becomes an API method",()=>{
  assert.equal(PAYMENT_METHODS.POS,"POS");
  assert.equal(PAYMENT_METHOD_LABELS.POS,"کارت‌خوان");
  assert.notEqual(PAYMENT_METHOD_LABELS.POS,PAYMENT_METHODS.POS);
});
test("all payment method codes match payment API choices",()=>{
  assert.deepEqual(Object.values(PAYMENT_METHODS).sort(),["POS","CASH","CREDIT","WALLET","GIFT_CARD"].sort());
  assert.deepEqual(Object.keys(PAYMENT_METHOD_LABELS).sort(),Object.values(PAYMENT_METHODS).sort());
});
