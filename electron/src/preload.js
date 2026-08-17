const {contextBridge,ipcRenderer}=require("electron");

contextBridge.exposeInMainWorld("cafino",{
  health:()=>ipcRenderer.invoke("system:health"),
  preflight:()=>ipcRenderer.invoke("system:preflight"),
  deviceAdapters:()=>ipcRenderer.invoke("device:adapters"),
  createBackup:()=>ipcRenderer.invoke("backup:create"),
  verifyBackup:()=>ipcRenderer.invoke("backup:verify"),
  restoreBackup:()=>ipcRenderer.invoke("backup:restore"),
  openExternal:(url)=>ipcRenderer.invoke("system:openExternal",url),
  listPrinters:()=>ipcRenderer.invoke("printer:list"),
  printHtml:(html,deviceName)=>ipcRenderer.invoke("printer:printHtml",{html,deviceName}),
  printReceipt:(payload,deviceName)=>ipcRenderer.invoke("printer:printReceipt",{payload,deviceName}),
  printKitchen:(payload,deviceName)=>ipcRenderer.invoke("printer:printKitchen",{payload,deviceName}),
  callPager:(pager)=>ipcRenderer.invoke("pager:call",pager),
  sendPosAmount:(amount)=>ipcRenderer.invoke("pos:sendAmount",amount),
});
