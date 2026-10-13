# DataSure — Business Data Validation & Reporting Automation

A portfolio project built with Python, Pandas, and Streamlit. Upload CSV or Excel business data, run configurable quality checks, review issues, and export validation reports.

## Features
- CSV and Excel upload
- Column-name normalization for common business-data aliases
- Configurable checks for missing values, duplicate IDs, email format, negative/non-numeric amounts, and invalid dates
- Record-level issue explanations
- Valid/invalid record counts and a simple data-quality score
- Issue summary chart
- CSV exports for all records, clean records, issues, and summary metrics
- Sample dataset to test the workflow

## Tech stack
- Python
- Streamlit
- Pandas
- OpenPyXL

## Run locally
```bash
python -m venv .venv
# Windows PowerShell:
.venv\\Scripts\\Activate.ps1
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
streamlit run app.py
```

## How to use
1. Start the app.
2. Download the sample CSV or upload your own CSV/XLSX.
3. Select validation rules in the sidebar.
4. Review the records and issue summary.
5. Download the reports.

## Data and limitations
The included rows are fictional demo data. The quality score is the percentage of records with no detected issues under the selected checks; it is not a universal data-quality standard. The app does not automatically delete invalid records or guarantee that all business rules are covered. Checks are skipped when their required column is absent. Avoid uploading confidential or personal data to an untrusted deployment.

## Suggested future improvements
- Add configurable rules per business/team
- Add downloadable Excel workbook with multiple sheets
- Add unit tests and CI checks
- Add audit history and role-based access for a production version
- Add row-level correction suggestions with user approval
