const REGISTRY={
  PRINTER:{
    SYSTEM:{id:"SYSTEM",label:"System Printer",status:"ready",transport:"electron",description:"چاپ از طریق Printerهای نصب‌شده سیستم عامل."},
  },
  PAGER:{
    NONE:{id:"NONE",label:"بدون Pager",status:"unconfigured",transport:"none",description:"Pager سخت‌افزاری برای این نصب انتخاب نشده است."},
    GENERIC_SERIAL:{id:"GENERIC_SERIAL",label:"Generic Serial Pager",status:"planned",transport:"serial",description:"Adapter رزروشده برای پروتکل Serial؛ نیازمند مشخصات برند/مدل است."},
  },
  POS:{
    MANUAL:{id:"MANUAL",label:"POS دستی",status:"manual",transport:"operator",description:"مبلغ روی ترمینال بانکی توسط اپراتور ثبت می‌شود؛ Cafino ارسال مستقیم مبلغ انجام نمی‌دهد."},
    VENDOR_SDK:{id:"VENDOR_SDK",label:"Vendor POS SDK",status:"planned",transport:"sdk",description:"Adapter رزروشده برای SDK/API شرکت ارائه‌دهنده POS."},
  },
};

function normalize(type,value,fallback){
  const key=String(value||fallback||"").trim().toUpperCase();
  return REGISTRY[type]&&REGISTRY[type][key]?key:fallback;
}

function selections(env=process.env){
  return {
    PRINTER:normalize("PRINTER",env.CAFINO_PRINTER_ADAPTER,"SYSTEM"),
    PAGER:normalize("PAGER",env.CAFINO_PAGER_ADAPTER,"NONE"),
    POS:normalize("POS",env.CAFINO_POS_ADAPTER,"MANUAL"),
  };
}

function registryPayload(env=process.env){
  const selected=selections(env);
  const groups={};
  for(const [type,entries] of Object.entries(REGISTRY)){
    groups[type]={
      selected:selected[type],
      adapters:Object.values(entries).map(item=>({...item,selected:item.id===selected[type]})),
    };
  }
  return {ok:true,groups};
}

function callPager(pager,env=process.env){
  const adapter=selections(env).PAGER;
  if(adapter==="NONE")return{ok:false,adapter,status:"unconfigured",message:"Pager سخت‌افزاری برای این نصب پیکربندی نشده است.",pager};
  return{ok:false,adapter,status:"planned",message:"Adapter انتخاب‌شده هنوز به پروتکل سخت‌افزار متصل نشده است.",pager};
}

function sendPosAmount(amount,env=process.env){
  const adapter=selections(env).POS;
  const numeric=Number(amount||0);
  if(!Number.isFinite(numeric)||numeric<=0)return{ok:false,adapter,error:"مبلغ POS نامعتبر است."};
  if(adapter==="MANUAL")return{ok:false,adapter,status:"manual",requiresManual:true,message:"POS در حالت دستی است؛ مبلغ را روی ترمینال بانکی وارد کنید.",amount:numeric};
  return{ok:false,adapter,status:"planned",message:"Adapter بانکی انتخاب‌شده هنوز به SDK/API فروشنده متصل نشده است.",amount:numeric};
}

module.exports={REGISTRY,registryPayload,callPager,sendPosAmount};
