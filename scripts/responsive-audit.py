#!/usr/bin/env python3
"""Responsive browser audit for Cafino. Requires Playwright Chromium."""
import argparse, json, sys
from playwright.sync_api import sync_playwright

BASE="http://127.0.0.1:3000"
SIZES={"mobile":(390,844),"tablet-p":(820,1180),"tablet-l":(1180,820),"desktop":(1440,900)}
ROUTES=["/","/pos","/orders","/split-bill","/order-transfer","/tables","/reservations","/kitchen","/takeaway","/cashier","/purchasing","/suppliers","/expenses","/products","/recipes","/inventory","/inventory-lots","/inventory-control","/lot-count","/stock-transfers","/production","/waste","/reports","/kpi","/sales-analytics","/branches-dashboard","/daily-close","/customers-loyalty","/gift-cards","/delivery","/discounts","/workforce","/approvals","/audit","/settings","/operations","/local-tools"]
PROBE="""() => {
 const vw=document.documentElement.clientWidth,bad=[];
 for(const el of document.querySelectorAll('body *')){
  const r=el.getBoundingClientRect(); if(!r.width||!r.height) continue;
  if(r.right>vw+1||r.left<-1){
   let p=el.parentElement,contained=false;
   while(p&&p!==document.body){
    const o=getComputedStyle(p).overflowX;
    if(['auto','scroll','hidden','clip'].includes(o)){const pr=p.getBoundingClientRect();if(pr.right<=vw+1&&pr.left>=-1){contained=true;break}}
    p=p.parentElement;
   }
   if(!contained) bad.push(el.tagName.toLowerCase()+'.'+String(el.className||'').split(' ')[0].slice(0,30));
  }
 }
 const main=document.querySelector('main'),mw=main?main.getBoundingClientRect().width:vw;
 return {vw,clipped:bad.length,sample:bad.slice(0,5),mainRatio:+(mw/vw).toFixed(2)};
}"""

def main():
 ap=argparse.ArgumentParser();ap.add_argument("--user",default="admin");ap.add_argument("--password",default="admin1234");ap.add_argument("--sizes",default=",".join(SIZES));ap.add_argument("--routes",default="");ap.add_argument("--json",default="");a=ap.parse_args()
 routes=a.routes.split(",") if a.routes else ROUTES;report={};failures=0
 with sync_playwright() as p:
  browser=p.chromium.launch();ctx=browser.new_context(viewport={"width":1440,"height":900},locale="fa-IR");page=ctx.new_page();page.goto(BASE+"/login");page.wait_for_timeout(1000);inputs=page.query_selector_all("input");inputs[0].fill(a.user);inputs[1].fill(a.password);page.keyboard.press("Enter");page.wait_for_timeout(2500);state=ctx.storage_state();ctx.close()
  for name in a.sizes.split(","):
   w,h=SIZES[name];ctx=browser.new_context(viewport={"width":w,"height":h},locale="fa-IR",storage_state=state,has_touch=name!="desktop");page=ctx.new_page();rows=[]
   for route in routes:
    try: page.goto(BASE+route,wait_until="domcontentloaded");page.wait_for_timeout(800);m=page.evaluate(PROBE)
    except Exception as exc: m={"error":str(exc)[:100],"clipped":0,"mainRatio":1}
    m["route"]=route;m["fail"]=bool(m.get("clipped")) or m.get("mainRatio",1)<0.6;rows.append(m)
   report[name]=rows;ctx.close()
  browser.close()
 for name,rows in report.items():
  bad=[r for r in rows if r["fail"]];failures+=len(bad);print("\n==",name,SIZES[name],f"{len(bad)}/{len(rows)} failing")
  for row in bad[:25]: print("  ",row["route"],"clipped=",row.get("clipped"),"main=",row.get("mainRatio"),row.get("sample",""))
 if a.json:
  with open(a.json,"w",encoding="utf-8") as handle: json.dump(report,handle,ensure_ascii=False,indent=2)
 sys.exit(1 if failures else 0)

if __name__=="__main__": main()
