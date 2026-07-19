@echo off
setlocal enabledelayedexpansion

cd /d C:\Users\wwyl5\Project\malware
call conda activate malware

if not exist results\logs mkdir results\logs

echo =====================================================
echo Running core multi-seed experiments
echo Seeds: 123, 2026
echo =====================================================

for %%S in (123 2026) do (
    echo.
    echo =====================================================
    echo Creating split for seed %%S
    echo =====================================================
    python scripts\create_splits.py --seed %%S --output dataset\splits\split_rgb_seed%%S.csv > results\logs\split_seed%%S.log 2>&1
    if errorlevel 1 (
        echo [FAILED] split seed %%S
        type results\logs\split_seed%%S.log
        exit /b 1
    )

    echo.
    echo =====================================================
    echo FL clean seed %%S
    echo =====================================================
    python scripts\train_fl_clean.py --config configs\multiseed\fl_clean_seed%%S.yaml > results\logs\fl_clean_seed%%S.log 2>&1
    if errorlevel 1 (
        echo [FAILED] fl clean seed %%S
        type results\logs\fl_clean_seed%%S.log
        exit /b 1
    )

    for %%C in (blue full) do (
        echo.
        echo =====================================================
        echo Backdoor %%C seed %%S
        echo =====================================================
        python scripts\train_fl_backdoor.py --config configs\multiseed\backdoor_%%C_seed%%S.yaml > results\logs\backdoor_%%C_seed%%S.log 2>&1
        if errorlevel 1 (
            echo [FAILED] backdoor %%C seed %%S
            type results\logs\backdoor_%%C_seed%%S.log
            exit /b 1
        )

        echo.
        echo =====================================================
        echo Trigger control %%C seed %%S
        echo =====================================================
        python scripts\evaluate_trigger_control.py --config configs\multiseed\control_%%C_seed%%S.yaml > results\logs\control_%%C_seed%%S.log 2>&1
        if errorlevel 1 (
            echo [FAILED] control %%C seed %%S
            type results\logs\control_%%C_seed%%S.log
            exit /b 1
        )

        echo.
        echo =====================================================
        echo Multi-Krum defense %%C seed %%S
        echo =====================================================
        python scripts\train_fl_backdoor_defense.py --config configs\multiseed\defense_%%C_multi_krum_seed%%S.yaml > results\logs\defense_%%C_multi_krum_seed%%S.log 2>&1
        if errorlevel 1 (
            echo [FAILED] defense %%C seed %%S
            type results\logs\defense_%%C_multi_krum_seed%%S.log
            exit /b 1
        )
    )
)

echo.
echo =====================================================
echo Collecting multi-seed summary
echo =====================================================
python scripts\collect_multiseed_core_results.py

echo.
echo Finished multi-seed core experiments.
echo Output:
echo - results\multiseed_core_raw.csv
echo - results\multiseed_core_mean_std.csv
pause
