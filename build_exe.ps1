param(
    [string]$ExeName = "StatisticApp"
)

$ErrorActionPreference = "Stop"

python -m pip install --upgrade pip
python -m pip install pyinstaller -r requirements.txt

python -m PyInstaller `
  --noconfirm `
  --clean `
  --onefile `
  --copy-metadata streamlit `
  --collect-all streamlit `
  --collect-all statsmodels `
  --collect-all scipy `
  --collect-all pandas `
  --collect-all seaborn `
  --collect-all matplotlib `
  --name $ExeName `
  --add-data "app.py;." `
  --add-data "src;src" `
  --add-data "data;data" `
  launcher.py

Write-Host ""
Write-Host "Build tamamlandi: dist/$ExeName.exe"
