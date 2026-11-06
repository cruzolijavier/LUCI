@echo off
rem Build the Windows executable of LUCI: double-click this file.
rem Result: dist\LUCI\ (LUCI.exe + luci-cli.exe + _internal\) and dist\LUCI_windows.zip to share.
rem It builds in a clean, separate Python (made with uv), so Anaconda, PyQt5 or other
rem installed packages never get into the executable.
setlocal
cd /d "%~dp0.."
set "PYTHONPATH="
set "PYTHONHOME="

rem Any Python works to fetch uv (set LUCI_PYTHON to choose it yourself).
set "PY=%LUCI_PYTHON%"
if defined PY goto :found
py -3 -c "import sys" >nul 2>&1
if not errorlevel 1 set "PY=py -3"
if defined PY goto :found
python -c "import sys" >nul 2>&1
if not errorlevel 1 set "PY=python"
if defined PY goto :found
echo No Python was found. Install Python from https://www.python.org/downloads/ and try again.
goto :error

:found
echo [1/5] Getting uv...
%PY% -m pip install --upgrade --quiet uv || goto :error
set "UV="
for /f "delims=" %%u in ('%PY% -c "import uv; print(uv.find_uv_bin())"') do set "UV=%%u"
if not defined UV goto :error

echo [2/5] Making a clean Python 3.12 for the build (build\exe-venv)...
set "VENV=%CD%\build\exe-venv"
"%UV%" venv "%VENV%" --python 3.12 --managed-python --allow-existing || goto :error
set "VPY=%VENV%\Scripts\python.exe"
"%UV%" pip install --python "%VPY%" --upgrade -e ".[gui]" pyinstaller || goto :error

rem From here on, nothing else installed on this computer is visible to the build.
set "PATH=%VENV%\Scripts;%SystemRoot%\System32;%SystemRoot%;%SystemRoot%\System32\Wbem;%SystemRoot%\System32\WindowsPowerShell\v1.0"

echo [3/5] Packing the OpenAI key of the assistant...
"%VPY%" packaging\bundle_key.py || goto :error

echo [4/5] Building (a few minutes)...
if exist "dist\LUCI" rmdir /s /q "dist\LUCI"
if exist "dist\LUCI" (
    echo dist\LUCI is in use: close LUCI.exe ^(and any window or console opened in that folder^) and try again.
    goto :error
)
"%VPY%" -m PyInstaller --noconfirm --clean packaging\luci.spec
set BUILD=%ERRORLEVEL%
del /q "src\luci\assistant\bundled_key.txt" 2>nul
if not "%BUILD%"=="0" goto :error

echo [5/5] Making dist\LUCI_windows.zip...
powershell -NoProfile -Command "Compress-Archive -Path 'dist\LUCI' -DestinationPath 'dist\LUCI_windows.zip' -Force" || goto :error

echo.
echo Done. Share dist\LUCI_windows.zip: unzip it anywhere and open LUCI.exe.
pause
exit /b 0

:error
del /q "src\luci\assistant\bundled_key.txt" 2>nul
echo.
echo The build failed: look at the messages above.
pause
exit /b 1
