# PowerShell script to create or update the 'windows-mac' branch

# Define git path
$gitPath = "C:\Program Files\Git\bin\git.exe"

# Navigate to the repository root (assuming the script is run from the repository)
Set-Location -Path $PSScriptRoot\..

# Try to checkout the branch; if it doesn't exist, create it
& $gitPath checkout windows-mac 2>$null
if ($LASTEXITCODE -ne 0) {
    # Branch doesn't exist, create it
    & $gitPath checkout -b windows-mac
    & $gitPath push -u origin windows-mac
    Write-Host "Created and pushed new branch 'windows-mac'."
} else {
    # Branch exists, check for changes
    $changes = & $gitPath status --porcelain
    if ($changes) {
        & $gitPath add .
        & $gitPath commit -m "Update windows-mac branch"
        & $gitPath push
        Write-Host "Successfully updated and pushed the 'windows-mac' branch."
    } else {
        Write-Host "No changes to commit on the 'windows-mac' branch."
    }
}