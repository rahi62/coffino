param(
  [Parameter(Mandatory=$true)][string]$BackendUrl,
  [Parameter(Mandatory=$true)][string]$FrontendUrl
)

$ErrorActionPreference="Stop"

function Normalize-Https([string]$Value,[string]$Name){
  $value=$Value.Trim().TrimEnd('/')
  if($value -notmatch '^https://'){throw "$Name must use https://"}
  return $value
}

function Invoke-ExpectStatus([string]$Method,[string]$Url,[int[]]$Allowed,$Headers=$null,$Body=$null){
  $params=@{Method=$Method;Uri=$Url;TimeoutSec=15;MaximumRedirection=0;ErrorAction="Stop";UseBasicParsing=$true}
  if($Headers){$params.Headers=$Headers}
  if($null -ne $Body){$params.ContentType="application/json";$params.Body=($Body|ConvertTo-Json -Depth 8 -Compress)}
  try{
    $response=Invoke-WebRequest @params
    if([int]$response.StatusCode -notin $Allowed){throw "Unexpected HTTP $($response.StatusCode) from $Url"}
    return $response
  }catch{
    if($_.Exception.Response){
      $status=[int]$_.Exception.Response.StatusCode
      if($status -in $Allowed){return $_.Exception.Response}
    }
    throw
  }
}

$backend=Normalize-Https $BackendUrl "BackendUrl"
$frontend=Normalize-Https $FrontendUrl "FrontendUrl"

Write-Host "1/6 Backend health..." -ForegroundColor Cyan
$health=Invoke-ExpectStatus "GET" "$backend/api/v1/health/" @(200)
$healthJson=$health.Content|ConvertFrom-Json
if($healthJson.status -ne "ok" -or $healthJson.service -ne "cafino-backend"){
  throw "Backend health payload is not the Cafino contract."
}

Write-Host "2/6 Frontend login page..." -ForegroundColor Cyan
$loginPage=Invoke-ExpectStatus "GET" "$frontend/login" @(200)
if(-not $loginPage.Content){throw "Frontend /login returned an empty body."}

Write-Host "3/6 Browser CORS preflight..." -ForegroundColor Cyan
$cors=Invoke-ExpectStatus "OPTIONS" "$backend/api/token/" @(200) @{
  Origin=$frontend
  "Access-Control-Request-Method"="POST"
  "Access-Control-Request-Headers"="content-type"
}
$allowOrigin=String($cors.Headers["Access-Control-Allow-Origin"])
if($allowOrigin.TrimEnd('/') -ne $frontend.TrimEnd('/')){
  throw "CORS does not allow the configured Frontend origin. Returned: $allowOrigin"
}

Write-Host "4/6 Local first-run must be closed on SaaS..." -ForegroundColor Cyan
[void](Invoke-ExpectStatus "GET" "$backend/api/v1/local/bootstrap/" @(404))

Write-Host "5/6 Optional Owner JWT login..." -ForegroundColor Cyan
$username=String($env:CAF_INO_SMOKE_USERNAME).Trim()
$password=String($env:CAF_INO_SMOKE_PASSWORD)
if($username -and $password){
  $tokenResponse=Invoke-ExpectStatus "POST" "$backend/api/token/" @(200) $null @{username=$username;password=$password}
  $tokenJson=$tokenResponse.Content|ConvertFrom-Json
  if(-not $tokenJson.access){throw "JWT login returned no access token."}
  $me=Invoke-ExpectStatus "GET" "$backend/api/v1/me/" @(200) @{Authorization="Bearer $($tokenJson.access)"}
  $meJson=$me.Content|ConvertFrom-Json
  if($meJson.username -ne $username){throw "Authenticated /me user does not match the smoke username."}
  if($meJson.role -ne "OWNER" -and -not $meJson.is_platform_admin){throw "Smoke account is not OWNER/platform admin."}
  Write-Host "JWT + /me passed for $username." -ForegroundColor Green
}else{
  Write-Host "CAF_INO_SMOKE_USERNAME/PASSWORD not set; authenticated smoke skipped." -ForegroundColor Yellow
}

Write-Host "6/6 Railway SaaS public-boundary smoke passed." -ForegroundColor Green
Write-Host "Backend:  $backend"
Write-Host "Frontend: $frontend"
Write-Host "Next: run Owner onboarding, one real checkout, Worker/Beat log verification and Settings -> Go-Live."
