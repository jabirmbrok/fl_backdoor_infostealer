@echo off
setlocal enabledelayedexpansion

cd /d C:\Users\wwyl5\Project\malware
call conda activate malware

if not exist results\logs mkdir results\logs

echo =====================================================
echo Running all backdoor sweep experiments sequentially
echo Project: C:\Users\wwyl5\Project\malware
echo =====================================================

set CONFIGS=red_p20_s10_r50 green_p20_s10_r50 blue_p20_s10_r50 full_p20_s10_r50 full_p30_s12_r50 red_p30_s12_r50

for %%C in (%CONFIGS%) do (
    echo.
    echo =====================================================
    echo Running %%C
    echo Config: configs\backdoor_sweep\%%C.yaml
    echo Log: results\logs\%%C.log
    echo =====================================================

    python scripts\train_fl_backdoor.py --config configs\backdoor_sweep\%%C.yaml > results\logs\%%C.log 2>&1

    if errorlevel 1 (
        echo [FAILED] %%C
        echo Check results\logs\%%C.log
        exit /b 1
    ) else (
        echo [DONE] %%C
    )
)

echo.
echo =====================================================
echo Collecting final metrics
echo =====================================================
python scripts\collect_backdoor_results.py

echo.
echo All experiments finished.
echo Summary: results\backdoor_sweep_summary.csv
echo =====================================================
pause
