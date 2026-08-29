[CmdletBinding()]
param(
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"
$repositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$profileName = "Last Asylum Doctor"
$workspaceFiles = @(
    (Join-Path $repositoryRoot ".vscode\atlas.code-workspace"),
    (Join-Path $repositoryRoot ".vscode\scout.code-workspace"),
    (Join-Path $repositoryRoot ".vscode\probe.code-workspace")
)

foreach ($workspaceFile in $workspaceFiles) {
    if (-not (Test-Path -LiteralPath $workspaceFile -PathType Leaf)) {
        throw "Workspace file not found: $workspaceFile"
    }
}

$codeCommand = Get-Command code -ErrorAction Stop
foreach ($workspaceFile in $workspaceFiles) {
    $arguments = @(
        "--new-window",
        "--profile",
        "`"$profileName`"",
        "`"$workspaceFile`""
    )
    if ($DryRun) {
        Write-Output ("DRY RUN: code " + ($arguments -join " "))
        continue
    }
    Start-Process -FilePath $codeCommand.Source -ArgumentList $arguments
}