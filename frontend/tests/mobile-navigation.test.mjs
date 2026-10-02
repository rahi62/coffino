import test from "node:test";
import assert from "node:assert/strict";

import { reduceMobileNavigation } from "../src/components/mobile-navigation-state.mjs";

test("mobile navigation closes after selecting a route", () => {
  const opened = reduceMobileNavigation(false, "open");
  assert.equal(opened, true);

  const afterNavigation = reduceMobileNavigation(opened, "navigate");
  assert.equal(afterNavigation, false);
});

test("mobile navigation can be dismissed by the backdrop or close button", () => {
  assert.equal(reduceMobileNavigation(true, "close"), false);
  assert.equal(reduceMobileNavigation(true, "toggle"), false);
});
