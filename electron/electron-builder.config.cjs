const production=process.env.CAFINO_PRODUCTION_BUILD==="1";
const allowUnsigned=process.env.CAFINO_ALLOW_UNSIGNED==="1";
const updateUrl=String(process.env.CAFINO_UPDATE_URL||"").trim();

if(production&&!updateUrl)throw new Error("CAFINO_UPDATE_URL is required for production build");
if(production&&!/^https:\/\//i.test(updateUrl))throw new Error("CAFINO_UPDATE_URL must use HTTPS");

module.exports={
  appId:"com.digitalafarin.cafino",
  productName:"Cafino",
  forceCodeSigning:production&&!allowUnsigned,
  directories:{output:"release"},
  files:["src/**/*","package.json"],
  extraResources:[
    {from:"release-resources/backend",to:"backend"},
    {from:"release-resources/frontend",to:"frontend"},
    {from:"release-resources/config",to:"config",filter:["**/*"]},
  ],
  artifactName:"Cafino-Setup-${version}.${ext}",
  publish:updateUrl?[{provider:"generic",url:updateUrl}]:undefined,
  win:{target:["nsis"]},
  nsis:{
    oneClick:false,
    perMachine:false,
    allowElevation:true,
    allowToChangeInstallationDirectory:true,
    createDesktopShortcut:true,
    createStartMenuShortcut:true,
    deleteAppDataOnUninstall:false,
    differentialPackage:true,
  },
};
