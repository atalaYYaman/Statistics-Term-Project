# Housing Price Analysis Automation

This project collects and validates housing data for 3 selected cities, runs statistical analyses, and automatically generates report outputs.
The interface runs on `Streamlit`, and reports are produced in Excel and Word formats.

## Features

- Selection and validation of 3 different cities
- Bulk data upload via Excel (`data/templates/input_template.xlsx`)
- Manual row entry through the form
- Automatic data validation (required fields + minimum 30 records per city)
- Statistical analysis and chart generation
- Bundled Excel output and Word report generation

## Requirements

- Python 3.10+ (recommended)
- Windows (for exe/setup packaging steps)

Installation:

```bash
python -m pip install -r requirements.txt
```

## Run the Application

In development mode:

```bash
python -m streamlit run app.py
```

Alternative:

```bash
python launcher.py
```

By default, the app opens at `http://localhost:8501`.

## Usage Flow

1. Select and confirm 3 different cities.
2. Upload data via Excel or add manual rows.
3. Check data preview and record counts.
4. Run the analysis.
5. Download Excel/Word outputs.

## Quick Test (Smoke Test)

```bash
python smoke_test.py
```

This command runs an end-to-end test of the full analysis and reporting pipeline using synthetic data.

## Packaging (Windows)

### Build EXE

```powershell
.\build_exe.ps1
```

Generated file:

```text
dist/StatisticApp.exe
```

### Build Setup

```powershell
.\build_setup.ps1
```

Generated file:

```text
installer-dist/StatisticApp-Setup.exe
```

## Project Structure

```text
Statistic/
|-- app.py
|-- launcher.py
|-- smoke_test.py
|-- requirements.txt
|-- data/
|   |-- city_assignments.csv
|   `-- templates/
|       `-- input_template.xlsx
`-- src/
    |-- analysis/
    |-- reporting/
    |-- validation.py
    `-- data_ingestion.py
```

## Note for GitHub

Only source code and essential project files should be committed. Generated outputs and local documentation assets are excluded via `.gitignore`.
