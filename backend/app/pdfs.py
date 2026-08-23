from __future__ import annotations

import io
from decimal import Decimal

from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas

from .parser import PaymentSlip, money

COMPANY_ADDRESS = "HIG-37 L-SECTOR AYODHYA NAGAR BHOPAL (M.P.) - 462041"
CONTACT_PHONE = "9301130200"

SLIPS_PER_PAGE = 4
PAGE_MARGIN = 8 * mm
SLIP_GAP = 4 * mm


def currency(value: Decimal) -> str:
    return f"Rs. {money(value)}"


def draw_label_value(c, x, y, label, value, bold=False, size=10.5):
    """Draws label+value starting at x, growing rightward."""
    label_font = "Helvetica-Bold" if bold else "Helvetica"
    c.setFont(label_font, size)
    c.drawString(x, y, label)
    offset = stringWidth(label, label_font, size)
    c.setFont("Helvetica", size)
    c.drawString(x + offset, y, str(value))
    return offset + stringWidth(str(value), "Helvetica", size)


def draw_label_value_right(c, right_x, y, label, value, bold=False, size=10.5):
    """Draws label+value ending flush at right_x, growing leftward.
    Prevents overflow for long numbers (e.g. large 'Total' amounts)."""
    label_font = "Helvetica-Bold" if bold else "Helvetica"
    value_w = stringWidth(str(value), "Helvetica", size)
    label_w = stringWidth(label, label_font, size)
    start_x = right_x - label_w - value_w
    c.setFont(label_font, size)
    c.drawString(start_x, y, label)
    c.setFont("Helvetica", size)
    c.drawString(start_x + label_w, y, str(value))
    return start_x


def fit_text(text, font, size, max_width):
    """Truncate text with an ellipsis if it won't fit in max_width."""
    if stringWidth(text, font, size) <= max_width:
        return text
    ell = "..."
    while text and stringWidth(text + ell, font, size) > max_width:
        text = text[:-1]
    return text + ell


def draw_slip(c: canvas.Canvas, slip: PaymentSlip, top_y: float, slot_height: float):
    """Draw one wage slip inside the box [top_y - slot_height, top_y]."""
    width, _ = A4
    margin = PAGE_MARGIN
    box_top = top_y
    box_bottom = top_y - slot_height
    inner_width = width - 2 * margin

    c.setStrokeColor(HexColor("#1e293b"))
    c.setLineWidth(0.8)
    c.roundRect(margin, box_bottom, inner_width, slot_height, 2.5 * mm, stroke=1, fill=0)

    pad = 8 * mm
    x = margin + pad
    right_edge = width - margin - pad
    y = box_top - 16

    # Header
    c.setFillColor(HexColor("#0f172a"))
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(width / 2, y, slip.establishment.upper() or "M/S TECHNO CREATIONS")
    y -= 13
    c.setFont("Helvetica", 9)
    c.drawCentredString(width / 2, y, COMPANY_ADDRESS)
    y -= 14
    c.setFont("Helvetica-Bold", 10.5)
    c.drawCentredString(width / 2, y, "(Wage Slip)")
    y -= 9
    c.setStrokeColor(HexColor("#64748b"))
    c.setLineWidth(0.5)
    c.line(x, y, right_edge, y)
    y -= 19

    # Row 1: Name of Employee (full width, own row, truncated if needed)
    label = "1. Name of Employee: "
    label_w = stringWidth(label, "Helvetica-Bold", 10.5)
    name_max_w = (right_edge - x) - label_w
    name = fit_text(slip.employee, "Helvetica", 10.5, name_max_w)
    draw_label_value(c, x, y, label, name, True)
    y -= 18

    # Row 2: Designation / Days / Rate per day
    draw_label_value(c, x, y, "2. Designation: ", slip.designation or "-", True)
    draw_label_value(c, x + 180, y, "3. Days: ", money(slip.days), True)
    draw_label_value(c, x + 280, y, "4. Rate Per Day: ", currency(slip.daily_rate), True)
    y -= 18

    # Row 3: Pay (Total is right-aligned so long amounts never overflow the box)
    c.setFont("Helvetica-Bold", 10.5)
    c.drawString(x, y, "5. Pay")
    draw_label_value(c, x + 46, y, "a. Basic Wages: ", currency(slip.basic_wages))
    draw_label_value(c, x + 225, y, "b. Special Reward: ", currency(slip.special_reward))
    draw_label_value_right(c, right_edge, y, "c. Total: ", currency(slip.total_pay))
    y -= 18

    # Row 4: Deductions (Total is right-aligned so long amounts never overflow the box)
    c.setFont("Helvetica-Bold", 10.5)
    c.drawString(x, y, "6. Deductions")
    draw_label_value(c, x + 75, y, "a. PF: ", currency(slip.pf))
    draw_label_value(c, x + 195, y, "b. ESIC: ", currency(slip.esic))
    draw_label_value_right(c, right_edge, y, "c. Total: ", currency(slip.total_deduction))
    y -= 18

    # Row 5: Net paid / Wage period
    draw_label_value(c, x, y, "7. Net Amount Paid: ", currency(slip.net_paid), True)
    draw_label_value(c, x + 260, y, "8. Wage Period: ", slip.wage_period or "-", True)
    y -= 16

    # Footer disclaimer
    c.setStrokeColor(HexColor("#cbd5e1"))
    c.setLineWidth(0.5)
    c.line(x, y, right_edge, y)
    y -= 12
    c.setFillColor(HexColor("#475569"))
    c.setFont("Helvetica-Oblique", 8)
    c.drawCentredString(
        width / 2,
        y,
        f"This is a computer-generated document and does not require a signature. "
        f"For any inquiries, please contact: {CONTACT_PHONE}",
    )


def build_work_order_pdf(slips: list[PaymentSlip]) -> bytes:
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4, pageCompression=1)
    pdf.setTitle(f"Payment slips - {slips[0].work_order}")

    width, height = A4
    usable_height = height - 2 * PAGE_MARGIN
    slot_height = (usable_height - (SLIPS_PER_PAGE - 1) * SLIP_GAP) / SLIPS_PER_PAGE

    for i, slip in enumerate(slips):
        pos = i % SLIPS_PER_PAGE
        if pos == 0 and i != 0:
            pdf.showPage()

        top_y = height - PAGE_MARGIN - pos * (slot_height + SLIP_GAP)
        draw_slip(pdf, slip, top_y, slot_height)

    pdf.showPage()
    pdf.save()
    return buffer.getvalue()
