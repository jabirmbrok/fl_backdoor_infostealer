@echo off
setlocal enabledelayedexpansion

cd /d C:\Users\wwyl5\Project\malware
call conda activate malware

if not exist results\logs mkdir results\logs

echo =====================================================
echo Backbone Selection Study - Seed 42 only
echo Output: results\backbone_summary_seed42.csv
echo =====================================================

python scripts\create_manifest.py --dataset-root dataset\processed\dataset_rgb_stack_combined --output results\manifest_rgb_stack.csv > results\logs\backbone_manifest_rgb_stack.log 2>&1
if errorlevel 1 (
    echo [FAILED] RGB-stack manifest
    type results\logs\backbone_manifest_rgb_stack.log
    exit /b 1
)

python scripts\create_manifest.py --dataset-root dataset\processed\dataset_opacity_blend --output results\manifest_opacity_blend.csv > results\logs\backbone_manifest_opacity_blend.log 2>&1
if errorlevel 1 (
    echo [FAILED] opacity blend manifest
    type results\logs\backbone_manifest_opacity_blend.log
    exit /b 1
)

python scripts\create_splits.py --manifest results\manifest_rgb_stack.csv --seed 42 --output dataset\splits\split_rgb_stack_seed42.csv > results\logs\backbone_split_rgb_stack_seed42.log 2>&1
if errorlevel 1 (
    echo [FAILED] RGB-stack split seed42
    type results\logs\backbone_split_rgb_stack_seed42.log
    exit /b 1
)

python scripts\create_splits.py --manifest results\manifest_opacity_blend.csv --seed 42 --output dataset\splits\split_opacity_blend_seed42.csv > results\logs\backbone_split_opacity_blend_seed42.log 2>&1
if errorlevel 1 (
    echo [FAILED] opacity blend split seed42
    type results\logs\backbone_split_opacity_blend_seed42.log
    exit /b 1
)

set CONFIGS=rgb_stack_small_cnn_seed42 rgb_stack_mobilenet_v2_seed42 rgb_stack_resnet18_seed42 opacity_blend_small_cnn_seed42 opacity_blend_mobilenet_v2_seed42 opacity_blend_resnet18_seed42

for %%C in (%CONFIGS%) do (
    echo.
    echo =====================================================
    echo Running %%C
    echo =====================================================
    python scripts\train_centralized.py --config configs\backbone\%%C.yaml > results\logs\backbone_%%C.log 2>&1
    if errorlevel 1 (
        echo [FAILED] %%C
        type results\logs\backbone_%%C.log
        exit /b 1
    )
    echo [DONE] %%C
)

python scripts\collect_backbone_seed42_results.py

echo.
echo Finished Backbone Selection Study.
echo Output:
echo - results\backbone_summary_seed42.csv
pause
