const exactPublicRoutes=new Set([
  "/login",
  "/register",
  "/forgot-password",
  "/reset-password",
]);

export function isPublicRoute(pathname=""){
  const path=String(pathname||"").split("?")[0].split("#")[0]||"/";
  return exactPublicRoutes.has(path)||path.startsWith("/menu/");
}
