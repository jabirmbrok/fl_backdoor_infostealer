@echo off
cd /d C:\Users\wwyl5\Project\malware
call conda activate malware

if not exist results\logs mkdir results\logs

echo Running attack-free trigger controls...

python scripts\evaluate_trigger_control.py --config configs\trigger_control\blue_clean_control.yaml > results\logs\control_blue_clean.log 2>&1
if errorlevel 1 (
    echo [FAILED] blue clean control
    type results\logs\control_blue_clean.log
    exit /b 1
)
echo [DONE] blue clean control

python scripts\evaluate_trigger_control.py --config configs\trigger_control\full_clean_control.yaml > results\logs\control_full_clean.log 2>&1
if errorlevel 1 (
    echo [FAILED] full clean control
    type results\logs\control_full_clean.log
    exit /b 1
)
echo [DONE] full clean control

python scripts\evaluate_trigger_control.py --config configs\trigger_control\red_clean_control.yaml > results\logs\control_red_clean.log 2>&1
if errorlevel 1 (
    echo [FAILED] red clean control
    type results\logs\control_red_clean.log
    exit /b 1
)
echo [DONE] red clean control

python scripts\evaluate_trigger_control.py --config configs\trigger_control\green_clean_control.yaml > results\logs\control_green_clean.log 2>&1
if errorlevel 1 (
    echo [FAILED] green clean control
    type results\logs\control_green_clean.log
    exit /b 1
)
echo [DONE] green clean control

python scripts\collect_trigger_control_results.py

echo.
echo Finished trigger controls.
pause
