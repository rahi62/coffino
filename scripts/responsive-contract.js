const fs = require("node:fs");
const path = require("node:path");

const root = path.resolve(__dirname, "..");
const read = (relativePath) => fs.readFileSync(path.join(root, relativePath), "utf8");
const requireToken = (source, token, message) => {
  if (!source.includes(token)) throw new Error(message);
};

const layout = read("frontend/src/app/layout.tsx");
const sidebar = read("frontend/src/components/sidebar.tsx");
const globals = read("frontend/src/app/globals.css");

requireToken(layout, 'className="flex min-h-screen w-full"', "App shell must explicitly span the mobile viewport.");
requireToken(layout, 'className="min-w-0 w-full flex-1', "Main content must be width-safe inside the responsive shell.");

requireToken(sidebar, 'data-testid="mobile-nav-trigger"', "Mobile navigation trigger is missing.");
requireToken(sidebar, "lg:hidden", "Mobile navigation controls must be hidden on desktop.");
requireToken(sidebar, "fixed inset-y-0 right-0", "Sidebar must become a fixed drawer on small screens.");
requireToken(sidebar, "translate-x-full", "Closed mobile drawer state is missing.");
requireToken(sidebar, "lg:sticky", "Desktop sidebar must remain sticky.");
requireToken(sidebar, 'aria-label="بستن منوی اصلی"', "Mobile drawer needs an accessible close control.");
requireToken(sidebar, "setMobileOpen(false)", "Mobile drawer must close after route changes.");
requireToken(sidebar, "document.body.style.overflow", "Open mobile drawer must prevent background scrolling.");

requireToken(globals, "touch-action:manipulation", "Touch controls must avoid delayed/accidental double-tap behavior.");
requireToken(globals, "img,video,canvas{max-width:100%;height:auto}", "Media must stay inside the mobile viewport.");

console.log("Responsive contract: PASS");
