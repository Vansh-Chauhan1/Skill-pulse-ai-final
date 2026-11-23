param(
    [string]$BaseUrl = "http://127.0.0.1:8000"
)

$ErrorActionPreference = "Stop"
$results = [System.Collections.Generic.List[object]]::new()

function Test-ApiEndpoint {
    param(
        [string]$Name,
        [string]$Path,
        [scriptblock]$Validate,
        [switch]$Optional
    )

    try {
        $response = Invoke-RestMethod -Uri "$BaseUrl$Path" -Method Get -TimeoutSec 30
        if ($Validate) {
            & $Validate $response
        }
        $results.Add([pscustomobject]@{
            Endpoint = $Name
            Status = "PASS"
            Details = "HTTP 200"
        })
        Write-Host "[PASS] $Name" -ForegroundColor Green
    }
    catch {
        $message = $_.Exception.Message
        if ($Optional) {
            $results.Add([pscustomobject]@{
                Endpoint = $Name
                Status = "OPTIONAL / NOT READY"
                Details = $message
            })
            Write-Host "[OPTIONAL] $Name - $message" -ForegroundColor Yellow
        }
        else {
            $results.Add([pscustomobject]@{
                Endpoint = $Name
                Status = "FAIL"
                Details = $message
            })
            Write-Host "[FAIL] $Name - $message" -ForegroundColor Red
        }
    }
}

Write-Host "SkillPulse AI API smoke test: $BaseUrl" -ForegroundColor Cyan
Write-Host "Make sure uvicorn is running in another terminal." -ForegroundColor DarkGray
Write-Host ""

Test-ApiEndpoint -Name "Backend health" -Path "/api/health" -Validate {
    param($r)
    if ($r.status -ne "healthy") { throw "Health response did not report healthy." }
}

Test-ApiEndpoint -Name "PLFS state WPR" -Path "/api/official/plfs/state-wpr" -Validate {
    param($r)
    if (@($r).Count -lt 2) { throw "Expected multiple state/UT rows." }
}

Test-ApiEndpoint -Name "PLFS industry distribution" -Path "/api/official/plfs/industry-distribution" -Validate {
    param($r)
    if (@($r).Count -lt 1) { throw "No industry rows returned." }
}

Test-ApiEndpoint -Name "PLFS monthly CWS WPR" -Path "/api/official/plfs/monthly-cws-wpr" -Validate {
    param($r)
    if (@($r).Count -lt 2) { throw "Expected monthly observations." }
}

Test-ApiEndpoint -Name "NCS sector vacancies" -Path "/api/official/ncs/sector-vacancies" -Validate {
    param($r)
    if (@($r).Count -lt 1) { throw "No NCS sector rows returned." }
}

Test-ApiEndpoint -Name "NCS qualification vacancies" -Path "/api/official/ncs/qualification-vacancies" -Validate {
    param($r)
    if (@($r).Count -lt 1) { throw "No NCS qualification rows returned." }
}

Test-ApiEndpoint -Name "NCS summary" -Path "/api/official/ncs/summary" -Validate {
    param($r)
    if (@($r).Count -lt 1) { throw "No NCS summary rows returned." }
}

Test-ApiEndpoint -Name "Compact market indicators" -Path "/api/analytics/market-indicators" -Validate {
    param($r)
    if (@($r).Count -lt 1) { throw "No compact market indicators returned. Run the compact data pipeline." }
}

Test-ApiEndpoint -Name "Compact market data report" -Path "/api/analytics/market-indicators/summary" -Validate {
    param($r)
    if ($null -eq $r) { throw "Empty quality report returned." }
}

Test-ApiEndpoint -Name "Sector demand trends" -Path "/api/analytics/sector-demand-trends" -Validate {
    param($r)
    if (@($r).Count -lt 1) { throw "No sector trend rows returned." }
}

Test-ApiEndpoint -Name "Sector demand summary" -Path "/api/analytics/sector-demand-trends/summary" -Validate {
    param($r)
    if ($null -eq $r) { throw "Empty sector summary returned." }
}

Test-ApiEndpoint -Name "Integrated intelligence overview" -Path "/api/intelligence/overview?horizon=1" -Validate {
    param($r)
    if ($r.project -ne "SkillPulse AI") { throw "Unexpected intelligence overview response." }
    if ($null -eq $r.employment_indicators -or $null -eq $r.ncs_demand_indicators) {
        throw "The integrated overview is missing expected sections."
    }
}

Test-ApiEndpoint -Name "PLFS WPR forecast" -Path "/api/official/plfs/wpr-forecast?horizon=1" -Validate {
    param($r)
    if (@($r.forecast).Count -lt 1) { throw "Forecast array is empty." }
} -Optional

Write-Host ""
$results | Format-Table -AutoSize

$failed = @($results | Where-Object { $_.Status -eq "FAIL" }).Count
$optional = @($results | Where-Object { $_.Status -eq "OPTIONAL / NOT READY" }).Count
$passed = @($results | Where-Object { $_.Status -eq "PASS" }).Count

Write-Host "Passed: $passed | Failed: $failed | Optional not ready: $optional" -ForegroundColor Cyan

if ($failed -gt 0) {
    Write-Host "Fix the failed endpoints before moving on." -ForegroundColor Red
    exit 1
}

Write-Host "Required API smoke tests passed." -ForegroundColor Green
exit 0
