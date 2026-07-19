@echo off
cd /d C:\Users\wwyl5\Project\malware
call conda activate malware
python scripts\collect_backbone_seed42_results.py
pause
