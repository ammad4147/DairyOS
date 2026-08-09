$Output = "application_dump.txt"

if (Test-Path $Output) {
    Remove-Item $Output
}

Get-ChildItem ".\dairyos\application" -Recurse -Filter *.py |
Sort-Object FullName |
ForEach-Object {

    Add-Content $Output ""
    Add-Content $Output "======================================================================="
    Add-Content $Output $_.FullName
    Add-Content $Output "======================================================================="
    Get-Content $_.FullName | Add-Content $Output
}

Write-Host ""
Write-Host "Created $Output"
