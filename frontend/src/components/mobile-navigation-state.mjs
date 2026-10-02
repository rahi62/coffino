/** @typedef {"open" | "close" | "toggle" | "navigate"} MobileNavigationAction */

/**
 * Keeps the mobile drawer transitions explicit and independently testable.
 * @param {boolean} isOpen
 * @param {MobileNavigationAction} action
 */
export function reduceMobileNavigation(isOpen, action) {
  if (action === "open") return true;
  if (action === "toggle") return !isOpen;
  return false;
}
