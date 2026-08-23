from __future__ import annotations

import io
import re
import zipfile
from collections import defaultdict
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

from .parser import PaymentSlip, ValidationError, parse_workbook
from .pdfs import build_work_order_pdf

MAX_UPLOAD_BYTES = 15 * 1024 * 1024
app = FastAPI(title="Payment Slip Generator")
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1):\d+",
    allow_methods=["*"],
    allow_headers=["*"],
)


def check_file(upload: UploadFile, content: bytes) -> None:
    if Path(upload.filename or "").suffix.lower() not in {".xlsx", ".xls", ".xlsm"}:
        raise HTTPException(400, "Please choose an Excel .xlsx or .xls file.")
    if not content:
        raise HTTPException(400, "The Excel file is empty.")
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(400, "The Excel file is larger than 15 MB.")


def as_error(error: ValidationError) -> HTTPException:
    return HTTPException(422, {"message": error.message, "rows": error.rows})


def make_outputs(slips: list[PaymentSlip]) -> dict[str, bytes]:
    grouped: dict[str, list[PaymentSlip]] = defaultdict(list)
    for slip in slips:
        grouped[slip.work_order].append(slip)
    return {work_order: build_work_order_pdf(records) for work_order, records in grouped.items()}


@app.post("/api/inspect")
async def inspect(file: UploadFile = File(...)):
    content = await file.read()
    check_file(file, content)
    try:
        slips = parse_workbook(content)
    except ValidationError as error:
        raise as_error(error)
    groups: dict[str, int] = defaultdict(int)
    for slip in slips:
        groups[slip.work_order] += 1
    return {"filename": file.filename, "records": len(slips), "workOrders": len(groups), "preview": [slip.public() for slip in slips[:5]], "orders": [{"workOrder": key, "records": value} for key, value in sorted(groups.items())]}


@app.post("/api/generate")
async def generate(file: UploadFile = File(...)):
    content = await file.read()
    check_file(file, content)
    try:
        slips = parse_workbook(content)
    except ValidationError as error:
        raise as_error(error)
    outputs = make_outputs(slips)
    archive = io.BytesIO()
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for work_order, pdf in sorted(outputs.items()):
            zip_file.writestr(f"{safe_filename(work_order)}.pdf", pdf)
    return Response(archive.getvalue(), media_type="application/zip", headers={"Content-Disposition": "attachment; filename=payment_slips.zip", "X-Work-Orders": str(len(outputs)), "X-Payment-Slips": str(len(slips))})


@app.post("/api/work-order-pdf")
async def work_order_pdf(work_order: str = Query(...), file: UploadFile = File(...)):
    content = await file.read()
    check_file(file, content)
    try:
        slips = [slip for slip in parse_workbook(content) if slip.work_order == work_order]
    except ValidationError as error:
        raise as_error(error)
    if not slips:
        raise HTTPException(404, "That Work Order was not found in this file.")
    filename = f"{safe_filename(work_order)}.pdf"
    return Response(build_work_order_pdf(slips), media_type="application/pdf", headers={"Content-Disposition": f'attachment; filename="{filename}"'})


def safe_filename(value: str) -> str:
    return re.sub(r'[<>:"/\\|?*]+', "-", value).strip(" .-") or "work-order"
