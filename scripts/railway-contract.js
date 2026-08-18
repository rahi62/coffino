const assert=require("assert");
const fs=require("fs");
const path=require("path");
const root=path.resolve(__dirname,"..");
const read=rel=>fs.readFileSync(path.join(root,rel),"utf8");
const required=[
  "backend/railway.toml","backend/railway-worker.toml","backend/railway-beat.toml","frontend/railway.toml",
  "backend/apps/accounts/management/commands/bootstrap_business_owner.py","docs/RAILWAY_DEPLOYMENT.md",
  "backend/apps/core/tests_railway_health.py"
];
for(const rel of required)assert.ok(fs.existsSync(path.join(root,rel)),`Missing ${rel}`);
const api=read("backend/railway.toml");
for(const token of ["preDeployCommand","manage.py migrate --noinput","/api/v1/health/","ON_FAILURE"])assert.ok(api.includes(token),`Backend Railway contract missing ${token}`);
const worker=read("backend/railway-worker.toml");assert.ok(worker.includes("celery -A config worker"));
const beat=read("backend/railway-beat.toml");assert.ok(beat.includes("celery -A config beat"));
const front=read("frontend/railway.toml");assert.ok(front.includes('healthcheckPath = "/login"'));
const docker=read("backend/Dockerfile");assert.ok(docker.includes("${PORT:-8000}"),"Backend Dockerfile must bind Railway PORT");
const settings=read("backend/config/settings.py");
for(const token of ["RAILWAY_PUBLIC_DOMAIN","RAILWAY_PRIVATE_DOMAIN","CAF_INO_FRONTEND_ORIGIN","REDIS_URL","ImproperlyConfigured","healthcheck.railway.app","SECURE_REDIRECT_EXEMPT"])assert.ok(settings.includes(token),`Django Railway hardening missing ${token}`);
const bootstrap=read("backend/apps/accounts/management/commands/bootstrap_business_owner.py");
for(const token of ["CAF_INO_BOOTSTRAP_OWNER_PASSWORD","validate_password","transaction.atomic","User.Role.OWNER"])assert.ok(bootstrap.includes(token),`Bootstrap command missing ${token}`);
const docs=read("docs/RAILWAY_DEPLOYMENT.md");assert.ok(docs.includes("bootstrap_business_owner"),"Railway runbook must document the production owner bootstrap.");
console.log("Cafino Railway deployment contract passed");
