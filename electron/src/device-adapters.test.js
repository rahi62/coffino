const assert=require("assert");
const http=require("http");
const {registryPayload,callPager,sendPosAmount,allowedBridgeHost,normalizeResponse,saleInput}=require("./device-adapters");

(async()=>{
  const registry=registryPayload({});
  assert.equal(registry.ok,true);
  assert.equal(registry.groups.PRINTER.selected,"SYSTEM");
  assert.equal(registry.groups.PAGER.selected,"NONE");
  assert.equal(registry.groups.POS.selected,"MANUAL");
  assert.equal(registry.groups.PRINTER.adapters.find(x=>x.selected).status,"ready");

  const fallback=registryPayload({CAF_INO_POS_ADAPTER:"UNKNOWN",CAF_INO_PAGER_ADAPTER:"UNKNOWN"});
  assert.equal(fallback.groups.POS.selected,"MANUAL");
  assert.equal(fallback.groups.PAGER.selected,"NONE");
  assert.equal(allowedBridgeHost("127.0.0.1",{}),true);
  assert.equal(allowedBridgeHost("192.168.1.25",{}),true);
  assert.equal(allowedBridgeHost("8.8.8.8",{}),false);

  const manual=await sendPosAmount(125000,{});
  assert.equal(manual.ok,false);
  assert.equal(manual.requiresManual,true);
  assert.equal(manual.adapter,"MANUAL");
  assert.equal((await sendPosAmount(0,{})).ok,false);
  assert.equal(saleInput({amount:120000},{CAF_INO_POS_AMOUNT_UNIT:"TOMAN"}).terminalAmount,12000);
  assert.equal(saleInput({amount:120001},{CAF_INO_POS_AMOUNT_UNIT:"TOMAN"}),null);

  const normalized=normalizeResponse({status:"approved",rrn:"123456789",pan:"6037991234567890"},"HTTP_BRIDGE",{amount:1000,terminalAmount:1000,currency:"IRR"});
  assert.equal(normalized.ok,true);assert.equal(normalized.referenceNumber,"123456789");assert.equal(normalized.maskedPan,"****7890");
  const transportOnly=normalizeResponse({ok:true,status:"transport_ok"},"HTTP_BRIDGE",{amount:1000,terminalAmount:1000,currency:"IRR"});
  assert.equal(transportOnly.ok,false,"Transport success must never be treated as bank approval");
  const responseCode00=normalizeResponse({status:"00",rrn:"RRN-00"},"HTTP_BRIDGE",{amount:1000,terminalAmount:1000,currency:"IRR"});
  assert.equal(responseCode00.ok,true);assert.equal(responseCode00.referenceNumber,"RRN-00");

  const server=http.createServer((req,res)=>{let body="";req.on("data",c=>body+=c);req.on("end",()=>{const payload=JSON.parse(body);assert.equal(payload.amount,125000);assert.equal(payload.reference,"checkout-1:pos:0");res.writeHead(200,{"content-type":"application/json"});res.end(JSON.stringify({status:"approved",rrn:"RRN-1",trace:"42",terminal_id:"T-1",pan:"6037991111112222"}))})});
  await new Promise(resolve=>server.listen(0,"127.0.0.1",resolve));
  try{
    const address=server.address();
    const result=await sendPosAmount({amount:125000,reference:"checkout-1:pos:0"},{CAF_INO_POS_ADAPTER:"HTTP_BRIDGE",CAF_INO_POS_BRIDGE_URL:`http://127.0.0.1:${address.port}/sale`});
    assert.equal(result.ok,true);assert.equal(result.referenceNumber,"RRN-1");assert.equal(result.maskedPan,"****2222");
  }finally{await new Promise(resolve=>server.close(resolve))}

  const publicBridge=await sendPosAmount({amount:1000,reference:"x"},{CAF_INO_POS_ADAPTER:"HTTP_BRIDGE",CAF_INO_POS_BRIDGE_URL:"https://8.8.8.8/sale",CAF_INO_POS_TIMEOUT_MS:"1000"});
  assert.equal(publicBridge.ok,false);
  assert.match(publicBridge.message,/local\/private/i);

  const pager=callPager({number:"12"},{});
  assert.equal(pager.ok,false);assert.equal(pager.status,"unconfigured");assert.equal(pager.adapter,"NONE");
  console.log("device adapter registry contract: ok");
})().catch(error=>{console.error(error);process.exit(1)});
