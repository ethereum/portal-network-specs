@echo off

if "%1"=="" goto help
if "%1"=="help" goto help
if "%1"=="install-deps" goto install-deps
if "%1"=="format-json" goto format-json
if "%1"=="check-format-json" goto check-format-json

:help
echo Available commands:
echo format.bat install-deps     - Install Node.js dependencies
echo format.bat format-json      - Format JSON files
echo format.bat check-format-json - Check JSON formatting
goto :eof

:install-deps
cd jsonrpc
call npm ci
cd ..
goto :eof

:format-json
call :install-deps
cd jsonrpc
call npm run format
cd ..
goto :eof

:check-format-json
call :install-deps
cd jsonrpc
call npm run check-format
cd ..
goto :eof 