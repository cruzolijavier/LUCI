# Publishes a new version of LUCI.
#   .\publish.ps1 -Version 0.3.1 -Notes "- Fix in CURATE`n- New program X"
# Updates the version number, commits all changes, creates the tag v0.3.1 and pushes it to GitHub.
# GitHub then builds the .exe and publishes it under "Releases"; open LUCI windows will show the
# "Update LUCI" button with a red "!".
param(
    [Parameter(Mandatory = $true)][string]$Version,
    [Parameter(Mandatory = $true)][string]$Notes
)
$ErrorActionPreference = 'Stop'

if ($Version -notmatch '^\d+\.\d+\.\d+$') { throw "The version must look like 0.3.1 (three numbers separated by dots)." }
$tag = "v$Version"
if (git tag --list $tag) { throw "Version $tag already exists. Use a new number." }

$utf8 = New-Object System.Text.UTF8Encoding($false)
foreach ($item in @(@('src/luci/__init__.py', '(?m)^__version__ = ".*"', "__version__ = `"$Version`""),
                    @('pyproject.toml', '(?m)^version = ".*"', "version = `"$Version`""))) {
    $path = Join-Path $PWD $item[0]
    $text = [IO.File]::ReadAllText($path)
    [IO.File]::WriteAllText($path, [regex]::Replace($text, $item[1], $item[2]), $utf8)
}

git add -A
git commit --allow-empty -m "$tag" -m "$Notes"
git tag $tag
git push
git push origin $tag
Write-Host "Done: GitHub is building $tag. It will appear under 'Releases' of the repository in a few minutes."
