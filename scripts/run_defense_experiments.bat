@echo off
setlocal enabledelayedexpansion

cd /d C:\Users\wwyl5\Project\malware
call conda activate malware

if not exist results\logs mkdir results\logs

echo =====================================================
echo Running defense experiments sequentially
echo =====================================================

set CONFIGS=blue_clipping blue_median blue_trimmed_mean blue_multi_krum full_clipping full_median full_trimmed_mean full_multi_krum

for %%C in (%CONFIGS%) do (
    echo.
    echo =====================================================
    echo Running %%C
    echo Config: configs\defense\%%C.yaml
    echo Log: results\logs\defense_%%C.log
    echo =====================================================

    python scripts\train_fl_backdoor_defense.py --config configs\defense\%%C.yaml > results\logs\defense_%%C.log 2>&1

    if errorlevel 1 (
        echo [FAILED] %%C
        echo Check results\logs\defense_%%C.log
        type results\logs\defense_%%C.log
        exit /b 1
    ) else (
        echo [DONE] %%C
    )
)

echo.
echo =====================================================
echo Collecting defense metrics
echo =====================================================
python scripts\collect_defense_results.py

echo.
echo Finished defense experiments.
echo Summary: results\defense_summary.csv
pause
