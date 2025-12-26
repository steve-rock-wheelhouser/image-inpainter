# PowerShell script to create or update the 'windows-mac' branch

# Navigate to the repository root (assuming the script is run from the repository)
Set-Location -Path $PSScriptRoot\..

# Try to checkout the branch; if it doesn't exist, create it
git checkout windows-mac 2>$null
if ($LASTEXITCODE -ne 0) {
    # Branch doesn't exist, create it
    git checkout -b windows-mac
    git push -u origin windows-mac
    Write-Host "Created and pushed new branch 'windows-mac'."
} else {
    # Branch exists, check for changes
    $changes = git status --porcelain
    if ($changes) {
        git add .
        git commit -m "Update windows-mac branch"
        git push
        Write-Host "Successfully updated and pushed the 'windows-mac' branch."
    } else {
        Write-Host "No changes to commit on the 'windows-mac' branch."
    }
}