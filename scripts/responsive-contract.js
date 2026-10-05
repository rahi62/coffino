const fs = require("node:fs");
const path = require("node:path");

const root = path.resolve(__dirname, "..");
const read = (relativePath) => fs.readFileSync(path.join(root, relativePath), "utf8");
const requireToken = (source, token, message) => { if (!source.includes(token)) throw new Error(message); };

const layout = read("frontend/src/app/layout.tsx");
const sidebar = read("frontend/src/components/sidebar.tsx");
const globals = read("frontend/src/app/globals.css");
const pos = read("frontend/src/app/pos/page.tsx");

requireToken(layout, 'className="flex min-h-screen w-full min-w-0"', "App shell must be width-safe.");
requireToken(layout, "pt-[4.5rem] md:p-5 xl:p-6", "Main content must follow mobile/tablet/desktop spacing.");
requireToken(sidebar, "md:hidden", "Mobile top bar breakpoint is missing.");
requireToken(sidebar, "md:flex xl:hidden", "Tablet icon rail is missing.");
requireToken(sidebar, "hidden h-screen w-64", "Desktop full sidebar is missing.");
requireToken(sidebar, "fixed inset-0 z-50 xl:hidden", "Mobile/tablet drawer is missing.");
requireToken(sidebar, '"/operations"', "Production Operations navigation must not regress.");
requireToken(sidebar, "document.body.style.overflow", "Open drawer must lock background scrolling.");
requireToken(pos, "md:grid-cols-[minmax(0,1fr)_minmax(320px,360px)]", "Tablet POS layout is missing.");
requireToken(pos, "xl:grid-cols-[140px_minmax(0,1fr)_minmax(340px,420px)]", "Desktop POS three-pane layout is missing.");
requireToken(pos, "setCartOpen(false)", "Mobile cart must close after checkout.");
requireToken(pos, "safe-area-inset-bottom", "Mobile checkout controls must respect safe areas.");
requireToken(globals, "touch-action:manipulation", "Touch manipulation guard is missing.");
requireToken(globals, "@media (pointer:coarse)", "Touch target sizing guard is missing.");
requireToken(globals, "@media (max-width:767px)", "Phone input zoom guard is missing.");

console.log("Responsive contract: PASS");
