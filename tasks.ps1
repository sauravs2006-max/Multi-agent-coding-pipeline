# Same targets as the Makefile, for PowerShell without make:
#   .\tasks.ps1 up
#   .\tasks.ps1 eval -Runs 3
#   .\tasks.ps1 eval -Tasks e01_fizzbuzz,h03_sudoku
#   .\tasks.ps1 load-test -Label fake -Users 1,5,10,20 -Duration 4m
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("build", "up", "down", "logs", "test", "eval", "load-test", "clean")]
    [string]$Target,
    [int]$Runs = 1,
    [string]$Tasks = "",
    [int[]]$Users = @(1, 5, 10, 20),
    [string]$Label = "real",
    [string]$Duration = "4m",
    [string]$Python = "python"
)

$ErrorActionPreference = "Stop"

switch ($Target) {
    "build" { docker compose build }
    "up" { docker compose up -d --wait }
    "down" { docker compose down }
    "logs" { docker compose logs -f --tail=100 }
    "test" { & $Python -m pytest tests -q }
    "eval" {
        $taskArgs = if ($Tasks) { @("--tasks", $Tasks) } else { @() }
        docker compose --profile tools run --rm --no-deps eval python eval/run_eval.py --runs $Runs @taskArgs
    }
    "load-test" {
        # the level runner is a bash script. plain "bash" can resolve to the WSL
        # launcher, so use the bash that ships with Git for Windows
        $gitBash = Join-Path (Split-Path (Split-Path (Get-Command git).Source)) "bin\bash.exe"
        $env:DURATION = $Duration
        & $gitBash loadtest/run_levels.sh $Label @Users
        if ($LASTEXITCODE -ne 0) { throw "load test failed" }
        & $Python loadtest/summarize.py
    }
    "clean" {
        docker compose --profile tools down -v --remove-orphans
        docker ps -aq --filter label=app=pipeline-sandbox | ForEach-Object { docker rm -f $_ }
        docker volume ls -q --filter label=app=pipeline-sandbox | ForEach-Object { docker volume rm $_ }
    }
}
