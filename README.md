# Payment Slip Generator

A small, session-only Excel-to-PDF utility. It reads the supplied FORM-XVII workbook structure, validates every employee record, groups slips by Work Order, and downloads all Work Order PDFs as one ZIP.

## Run locally

1. Install Python 3.11+ and Node 20+.
2. In `backend`, run `python -m venv .venv`, activate it, then run `pip install -r requirements.txt`.
3. Start the API: `uvicorn app.main:app --reload --port 8000`.
4. In `frontend`, run `npm install` then `npm run dev`.
5. Open the shown Vite URL and upload an `.xlsx` or legacy `.xls` file.

## Deploy to Render

1. Push this repository to GitHub.
2. In Render, choose **New +** → **Blueprint** and select the repository.
3. Render reads `render.yaml`, builds the React frontend, installs the Python API, and deploys one web service.

The deployed app serves both the frontend and `/api` from the same URL, so no environment variables or CORS configuration are needed.

## Workbook mapping

The parser finds each `FORM-XVII` section and uses its local heading area for Work Order, establishment, location, work description, and wage period. It reads employee rows by the visible table columns: Name of Employee, Designation, No. of days worked, Daily rate, Basic Wages, Special Reward, Total, PF, ESIC, Total deductions, and Net Amount Paid.

One PDF page is created per employee. Sections that share the same Work Order are combined in one PDF. Filename-invalid characters are replaced with hyphens.

## Template adjustments

Company address and contact phone are static values from the supplied wage-slip sample and are kept in `backend/app/pdfs.py`. Update `COMPANY_ADDRESS`, `CONTACT_PHONE`, or `draw_slip` to change the visual template. The remaining values come from Excel. The service stores no uploads or generated PDFs.
