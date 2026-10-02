const assert=require("assert");
const fs=require("fs");
const path=require("path");
const root=path.resolve(__dirname,"..");
const read=rel=>fs.readFileSync(path.join(root,rel),"utf8");
const required=[
  "backend/railway.toml","backend/railway-worker.toml","backend/railway-beat.toml","frontend/railway.toml",
  "backend/.env.railway.example","frontend/.env.railway.example",
  "backend/apps/accounts/management/commands/bootstrap_business_owner.py",
  "backend/apps/core/management/commands/railway_preflight.py",
  "backend/apps/core/tests_railway_health.py","backend/apps/core/tests_railway_preflight.py",
  "scripts/test-railway-deployment.ps1",
  "docs/RAILWAY_DEPLOYMENT.md","docs/RAILWAY_RELEASE_CHECKLIST.md"
];
for(const rel of required)assert.ok(fs.existsSync(path.join(root,rel)),`Missing ${rel}`);
const api=read("backend/railway.toml");
for(const token of ["preDeployCommand","manage.py railway_preflight","manage.py migrate --noinput","/api/v1/health/","ON_FAILURE"])assert.ok(api.includes(token),`Backend Railway contract missing ${token}`);
assert.ok(api.indexOf("manage.py railway_preflight")<api.indexOf("manage.py migrate --noinput"),"Railway preflight must run before migrations");
const worker=read("backend/railway-worker.toml");assert.ok(worker.includes("celery -A config worker"));
const beat=read("backend/railway-beat.toml");assert.ok(beat.includes("celery -A config beat"));
const front=read("frontend/railway.toml");assert.ok(front.includes('healthcheckPath = "/login"'));
const docker=read("backend/Dockerfile");assert.ok(docker.includes("${PORT:-8000}"),"Backend Dockerfile must bind Railway PORT");
const frontendDocker=read("frontend/Dockerfile");
for(const token of ["ARG NEXT_PUBLIC_API_URL","ARG NEXT_PUBLIC_API_ROOT","ENV NEXT_PUBLIC_API_URL","ENV NEXT_PUBLIC_API_ROOT"])assert.ok(frontendDocker.includes(token),`Frontend Railway build contract missing ${token}`);
const nextConfig=read("frontend/next.config.ts");assert.ok(nextConfig.includes('output:"standalone"'),"Next standalone output is required for Docker/Railway");
const settings=read("backend/config/settings.py");
for(const token of ["RAILWAY_PUBLIC_DOMAIN","RAILWAY_PRIVATE_DOMAIN","CAF_INO_FRONTEND_ORIGIN","REDIS_URL","ImproperlyConfigured","healthcheck.railway.app","SECURE_REDIRECT_EXEMPT"])assert.ok(settings.includes(token),`Django Railway hardening missing ${token}`);
const preflight=read("backend/apps/core/management/commands/railway_preflight.py");
for(const token of ["postgresql","CELERY_BROKER_URL","SECURE_SSL_REDIRECT","healthcheck.railway.app","wildcard"]){
  const lookup=token==="wildcard"?"must not contain wildcard":token;
  assert.ok(preflight.includes(lookup),`Railway preflight missing ${lookup}`);
}
const bootstrap=read("backend/apps/accounts/management/commands/bootstrap_business_owner.py");
for(const token of ["CAF_INO_BOOTSTRAP_OWNER_PASSWORD","bootstrap_business_owner"])assert.ok(bootstrap.includes(token),`Bootstrap command missing ${token}`);
const bootstrapService=read("backend/apps/accounts/bootstrap.py");
assert.ok(bootstrapService.includes("User.Role.OWNER"),"Bootstrap service must create an OWNER account");
const backendEnv=read("backend/.env.railway.example");
for(const token of ["CAF_INO_ENV=saas","DJANGO_DEBUG=0","${{Postgres.DATABASE_URL}}","${{Redis.REDIS_URL}}","CAF_INO_FRONTEND_ORIGIN=https://"])assert.ok(backendEnv.includes(token),`Backend Railway env template missing ${token}`);
const frontendEnv=read("frontend/.env.railway.example");
for(const token of ["NEXT_PUBLIC_API_ROOT=https://","NEXT_PUBLIC_API_URL=https://"])assert.ok(frontendEnv.includes(token),`Frontend Railway env template missing ${token}`);
const smoke=read("scripts/test-railway-deployment.ps1");
for(const token of ["https://","/api/v1/health/","/login","Access-Control-Allow-Origin","/api/v1/local/bootstrap/","CAF_INO_SMOKE_USERNAME","/api/token/","/api/v1/me/"])assert.ok(smoke.includes(token),`Railway post-deploy smoke missing ${token}`);
const docs=read("docs/RAILWAY_DEPLOYMENT.md");assert.ok(docs.includes("bootstrap_business_owner"),"Railway runbook must document the production owner bootstrap.");
const checklist=read("docs/RAILWAY_RELEASE_CHECKLIST.md");
for(const token of ["/backend/railway.toml","/frontend/railway.toml","railway_preflight","NEXT_PUBLIC_API_ROOT"] )assert.ok(checklist.includes(token),`Railway release checklist missing ${token}`);
console.log("Cafino Railway deployment contract passed");
