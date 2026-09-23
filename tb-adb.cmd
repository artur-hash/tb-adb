@echo off
rem Permite rodar "tb-adb on IP" no Windows: coloque esta pasta no PATH.
where py >nul 2>nul
if %errorlevel%==0 (py -3 "%~dp0tb-adb" %*) else (python "%~dp0tb-adb" %*)
