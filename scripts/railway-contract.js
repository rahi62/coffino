const assert=require("assert");
const fs=require("fs");
const path=require("path");
const root=path.resolve(__dirname,"..");
const read=rel=>fs.readFileSync(path.join(root,rel),"utf8");
for(const rel of ["backend/railway.toml","backend/railway-worker.toml","backend/railway-beat.toml","frontend/railway.toml","docs/RAILWAY_DEPLOYMENT.md"]){assert.ok(fs.existsSync(path.join(root,rel)),`Missing ${rel}`)}
const api=read("backend/railway.toml");
for(const token of ["preDeployCommand","manage.py migrate --noinput","/api/v1/health/","ON_FAILURE"])assert.ok(api.includes(token),`Backend Railway contract missing ${token}`);
const worker=read("backend/railway-worker.toml");assert.ok(worker.includes("celery -A config worker"));
const beat=read("backend/railway-beat.toml");assert.ok(beat.includes("celery -A config beat"));
const front=read("frontend/railway.toml");assert.ok(front.includes('healthcheckPath = "/login"'));
const docker=read("backend/Dockerfile");assert.ok(docker.includes("${PORT:-8000}"),"Backend Dockerfile must bind Railway PORT");
const settings=read("backend/config/settings.py");
for(const token of ["RAILWAY_PUBLIC_DOMAIN","CAF_INO_FRONTEND_ORIGIN","REDIS_URL","ImproperlyConfigured"])assert.ok(settings.includes(token),`Django Railway hardening missing ${token}`);
console.log("Cafino Railway deployment contract passed");
