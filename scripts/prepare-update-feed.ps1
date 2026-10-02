param(
  [Parameter(Mandatory=$true)][string]$ReleaseDir,
  [ValidateSet("stable","beta")][string]$Channel="stable"
)

$ErrorActionPreference="Stop"
function Write-Utf8NoBom([string]$Path,[string]$Text) {
  $encoding=New-Object System.Text.UTF8Encoding($false)
  [System.IO.File]::WriteAllText($Path,$Text,$encoding)
}

$releaseDir=(Resolve-Path $ReleaseDir).Path
$manifestPath=Join-Path $releaseDir "release-manifest.json"
if (!(Test-Path $manifestPath)) { throw "release-manifest.json is missing." }
$manifest=Get-Content $manifestPath -Raw | ConvertFrom-Json
if ($manifest.channel -ne $Channel) { throw "Release manifest channel mismatch." }
if (-not $manifest.version) { throw "Release manifest version is missing." }

$latest=Get-ChildItem $releaseDir -Filter "latest*.yml" -File | Select-Object -First 1
if (-not $latest) { throw "electron-builder update metadata (latest*.yml) is missing." }
$installer=Get-ChildItem $releaseDir -Filter "Cafino-Setup-*.exe" -File | Select-Object -First 1
if (-not $installer) { throw "Cafino installer is missing." }
$blockmap=Get-ChildItem $releaseDir -Filter "Cafino-Setup-*.exe.blockmap" -File | Select-Object -First 1
if (-not $blockmap) { throw "Cafino installer blockmap is missing." }

$publishRoot=Join-Path $releaseDir "publish"
$channelDir=Join-Path $publishRoot $Channel
Remove-Item $channelDir -Recurse -Force -ErrorAction SilentlyContinue
New-Item $channelDir -ItemType Directory -Force | Out-Null

foreach($file in @($installer,$blockmap,$latest)) { Copy-Item $file.FullName (Join-Path $channelDir $file.Name) -Force }
Copy-Item $manifestPath (Join-Path $channelDir "release-manifest.json") -Force

$files=@()
Get-ChildItem $channelDir -File | Sort-Object Name | ForEach-Object {
  $files+=@{
    name=$_.Name
    size=$_.Length
    sha256=(Get-FileHash $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
  }
}
$channelManifest=[ordered]@{
  schema=1
  channel=$Channel
  version=$manifest.version
  generated_at=(Get-Date).ToUniversalTime().ToString("o")
  files=$files
}
Write-Utf8NoBom (Join-Path $channelDir "channel-manifest.json") ($channelManifest|ConvertTo-Json -Depth 6)
Write-Host "Prepared $Channel update feed: $channelDir" -ForegroundColor Green
