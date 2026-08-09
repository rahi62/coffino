self.addEventListener('install',()=>self.skipWaiting());
self.addEventListener('activate',e=>e.waitUntil(self.clients.claim()));
self.addEventListener('push',event=>{
  let data={};try{data=event.data.json()}catch{data={body:event.data?.text()||''}}
  event.waitUntil(self.registration.showNotification(data.title||'Cafino',{body:data.body||'',data:{order_id:data.order_id},tag:data.event||'cafino'}));
});
self.addEventListener('notificationclick',event=>{
  event.notification.close();
  event.waitUntil(self.clients.matchAll({type:'window',includeUncontrolled:true}).then(cs=>cs[0]?cs[0].focus():self.clients.openWindow('/')));
});
