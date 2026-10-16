@echo off
cd /d "C:\Users\PC\Desktop\Programs\MediViHall"
"C:\Python313\python.exe" stage1_extract_claims.py >> medvihall_outputs\stage1_run.log 2>&1
