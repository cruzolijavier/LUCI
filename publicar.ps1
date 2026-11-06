# Publica una versión nueva de LUCI.
#   .\publicar.ps1 -Version 0.3.1 -Notas "- Arreglo en CURATE`n- Nuevo programa X"
# Actualiza el número de versión, hace commit de todos los cambios, crea la etiqueta v0.3.1 y lo sube a
# GitHub. A partir de ahí GitHub compila el .exe y lo publica en "Releases"; los LUCI abiertos avisarán
# con el botón «Update LUCI».
param(
    [Parameter(Mandatory = $true)][string]$Version,
    [Parameter(Mandatory = $true)][string]$Notas
)
$ErrorActionPreference = 'Stop'

if ($Version -notmatch '^\d+\.\d+\.\d+$') { throw "La versión debe ser del tipo 0.3.1 (tres números separados por puntos)." }
$tag = "v$Version"
if (git tag --list $tag) { throw "La versión $tag ya existe. Usa un número nuevo." }

$utf8 = New-Object System.Text.UTF8Encoding($false)
foreach ($item in @(@('src/luci/__init__.py', '(?m)^__version__ = ".*"', "__version__ = `"$Version`""),
                    @('pyproject.toml', '(?m)^version = ".*"', "version = `"$Version`""))) {
    $path = Join-Path $PWD $item[0]
    $text = [IO.File]::ReadAllText($path)
    [IO.File]::WriteAllText($path, [regex]::Replace($text, $item[1], $item[2]), $utf8)
}

git add -A
git commit --allow-empty -m "$tag" -m "$Notas"
git tag $tag
git push
git push origin $tag
Write-Host "Listo: GitHub está compilando $tag. En unos minutos aparecerá en 'Releases' del repositorio."
