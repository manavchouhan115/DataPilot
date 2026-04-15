Start-Process powershell -ArgumentList "-NoExit -Command .\`.venv\Scripts\Activate.ps1; python -m api.main" -WindowStyle Normal
Start-Process powershell -ArgumentList "-NoExit -Command .\`.venv\Scripts\Activate.ps1; python -m services.extractor" -WindowStyle Normal
Start-Process powershell -ArgumentList "-NoExit -Command .\`.venv\Scripts\Activate.ps1; python -m services.transformer" -WindowStyle Normal
Start-Process powershell -ArgumentList "-NoExit -Command .\`.venv\Scripts\Activate.ps1; python -m services.loader" -WindowStyle Normal
