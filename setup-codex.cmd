@echo off
setlocal
rem Run from the extracted or cloned folder, including paths containing spaces.
pushd "%~dp0"
if errorlevel 1 exit /b 1
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0setup.ps1" %*
set "setupResult=%ERRORLEVEL%"
popd
echo.
echo Read README.md and the Korean usage guide in this folder.
echo Open this folder in Codex after setup. Sign in with your own account.
if "%~1"=="" pause
exit /b %setupResult%
