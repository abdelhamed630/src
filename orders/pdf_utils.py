"""
Professional PDF invoice generator using ReportLab.
"""
from io import BytesIO
from decimal import Decimal
from django.utils import timezone


def generate_invoice_pdf(order, seller_filter=None):
    """
    Generate a professional invoice PDF for an order.
    If seller_filter is provided, only includes that seller's items.
    Returns a BytesIO buffer.
    """
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.lib.units import mm
        from reportlab.platypus import (
            SimpleDocTemplate, Table, TableStyle, Paragraph,
            Spacer, HRFlowable
        )
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.enums import TA_RIGHT, TA_CENTER, TA_LEFT
    except ImportError:
        # Fallback minimal PDF if reportlab not installed
        return _minimal_pdf(order)

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        rightMargin=15*mm, leftMargin=15*mm,
        topMargin=15*mm, bottomMargin=15*mm
    )

    styles = getSampleStyleSheet()
    PRIMARY_COLOR = colors.HexColor('#1a1a2e')
    ACCENT_COLOR  = colors.HexColor('#e94560')
    LIGHT_GRAY    = colors.HexColor('#f5f5f5')
    MED_GRAY      = colors.HexColor('#888888')

    title_style = ParagraphStyle('Title', parent=styles['Normal'],
        fontSize=26, fontName='Helvetica-Bold', textColor=PRIMARY_COLOR)
    h2_style    = ParagraphStyle('H2', parent=styles['Normal'],
        fontSize=12, fontName='Helvetica-Bold', textColor=PRIMARY_COLOR)
    normal      = ParagraphStyle('N', parent=styles['Normal'], fontSize=9)
    small_gray  = ParagraphStyle('SG', parent=styles['Normal'],
        fontSize=8, textColor=MED_GRAY)
    right_style = ParagraphStyle('R', parent=styles['Normal'],
        fontSize=9, alignment=TA_RIGHT)
    total_style = ParagraphStyle('T', parent=styles['Normal'],
        fontSize=14, fontName='Helvetica-Bold', textColor=ACCENT_COLOR, alignment=TA_RIGHT)

    story = []

    # ── Header ─────────────────────────────────────────────────────────
    header_data = [[
        Paragraph('<b>🛒 ShopZone</b>', title_style),
        Paragraph(f'<b>INVOICE</b><br/><font size=10 color=grey># {order.order_number}</font>', 
                  ParagraphStyle('IR', parent=styles['Normal'], fontSize=20, 
                                 fontName='Helvetica-Bold', alignment=TA_RIGHT, textColor=PRIMARY_COLOR))
    ]]
    header_table = Table(header_data, colWidths=[90*mm, 90*mm])
    header_table.setStyle(TableStyle([
        ('ALIGN', (1,0), (1,0), 'RIGHT'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ]))
    story.append(header_table)
    story.append(HRFlowable(width='100%', thickness=2, color=ACCENT_COLOR, spaceAfter=6))

    # ── Date & Status ──────────────────────────────────────────────────
    info_data = [[
        Paragraph(f'<b>Date:</b> {order.created_at.strftime("%B %d, %Y")}', normal),
        Paragraph(f'<b>Status:</b> {order.get_status_display()}', normal),
        Paragraph(f'<b>Payment:</b> {order.get_payment_method_display()}', normal),
    ]]
    info_table = Table(info_data, colWidths=[60*mm, 60*mm, 60*mm])
    info_table.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP')]))
    story.append(info_table)
    story.append(Spacer(1, 8*mm))

    # ── Billing / Shipping ─────────────────────────────────────────────
    addr_data = [[
        [Paragraph('<b>Bill To / Ship To:</b>', h2_style),
         Paragraph(order.shipping_name, normal),
         Paragraph(order.shipping_phone, normal),
         Paragraph(order.shipping_address1, normal),
         Paragraph(f'{order.shipping_city}, {order.shipping_country}', normal)],
        [Paragraph('<b>Order Summary</b>', h2_style),
         Paragraph(f'Order #: {order.order_number}', normal),
         Paragraph(f'Date: {order.created_at.strftime("%d/%m/%Y")}', normal),
         Paragraph(f'Items: {order.items.count()}', normal)],
    ]]
    addr_table = Table(addr_data, colWidths=[90*mm, 90*mm])
    addr_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (0,0), LIGHT_GRAY),
        ('BACKGROUND', (1,0), (1,0), LIGHT_GRAY),
        ('BOX', (0,0), (0,0), 0.5, colors.lightgrey),
        ('BOX', (1,0), (1,0), 0.5, colors.lightgrey),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ]))
    story.append(addr_table)
    story.append(Spacer(1, 8*mm))

    # ── Items Table ────────────────────────────────────────────────────
    items = order.items.all()
    if seller_filter:
        items = items.filter(seller=seller_filter)

    table_data = [[
        Paragraph('<b>#</b>', normal),
        Paragraph('<b>Product</b>', normal),
        Paragraph('<b>Variant</b>', normal),
        Paragraph('<b>Qty</b>', normal),
        Paragraph('<b>Unit Price</b>', normal),
        Paragraph('<b>Total</b>', normal),
    ]]

    for i, item in enumerate(items, 1):
        attrs_str = ', '.join(f'{k}: {v}' for k, v in item.variant_attrs.items()) if item.variant_attrs else '-'
        table_data.append([
            Paragraph(str(i), normal),
            Paragraph(item.product_name, normal),
            Paragraph(attrs_str, small_gray),
            Paragraph(str(item.quantity), normal),
            Paragraph(f'${item.unit_price}', normal),
            Paragraph(f'${item.total_price}', normal),
        ])

    col_w = [10*mm, 65*mm, 35*mm, 12*mm, 22*mm, 22*mm]
    items_table = Table(table_data, colWidths=col_w, repeatRows=1)
    items_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), PRIMARY_COLOR),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 9),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, LIGHT_GRAY]),
        ('GRID', (0,0), (-1,-1), 0.3, colors.lightgrey),
        ('ALIGN', (3,0), (-1,-1), 'RIGHT'),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
        ('RIGHTPADDING', (0,0), (-1,-1), 4),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(items_table)
    story.append(Spacer(1, 6*mm))

    # ── Totals ─────────────────────────────────────────────────────────
    totals_data = []
    if order.discount_amount > 0:
        totals_data.append(['', Paragraph('Subtotal:', right_style), Paragraph(f'${order.subtotal}', right_style)])
        totals_data.append(['', Paragraph(f'Discount ({order.coupon_code}):', right_style),
                            Paragraph(f'-${order.discount_amount}', ParagraphStyle('D', parent=styles['Normal'],
                                fontSize=9, textColor=colors.green, alignment=TA_RIGHT))])
    if order.shipping_cost > 0:
        totals_data.append(['', Paragraph('Shipping:', right_style), Paragraph(f'${order.shipping_cost}', right_style)])

    totals_data.append(['', Paragraph('<b>TOTAL:</b>', 
                        ParagraphStyle('TL', parent=styles['Normal'], fontSize=13, fontName='Helvetica-Bold', alignment=TA_RIGHT)),
                        Paragraph(f'<b>${order.total}</b>', total_style)])

    totals_table = Table(totals_data, colWidths=[120*mm, 35*mm, 25*mm])
    totals_table.setStyle(TableStyle([
        ('LINEABOVE', (1,-1), (-1,-1), 1.5, ACCENT_COLOR),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(totals_table)

    # ── Footer ─────────────────────────────────────────────────────────
    story.append(Spacer(1, 12*mm))
    story.append(HRFlowable(width='100%', thickness=0.5, color=colors.lightgrey))
    story.append(Spacer(1, 4*mm))
    story.append(Paragraph(
        'Thank you for shopping with ShopZone! For any questions contact: support@shopzone.com',
        ParagraphStyle('F', parent=styles['Normal'], fontSize=8, textColor=MED_GRAY, alignment=TA_CENTER)
    ))
    story.append(Paragraph(
        f'Generated: {timezone.now().strftime("%Y-%m-%d %H:%M UTC")}',
        ParagraphStyle('FD', parent=styles['Normal'], fontSize=7, textColor=MED_GRAY, alignment=TA_CENTER)
    ))

    doc.build(story)
    buffer.seek(0)
    return buffer


def _minimal_pdf(order):
    """Ultra-minimal PDF fallback if reportlab missing."""
    content = f"""%PDF-1.4
1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj
2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj
3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R/Contents 4 0 R/Resources<</Font<</F1 5 0 R>>>>>>endobj
4 0 obj<</Length 200>>
stream
BT /F1 16 Tf 50 750 Td (INVOICE - {order.order_number}) Tj
0 -25 Td /F1 10 Tf (Buyer: {order.buyer.email}) Tj
0 -20 Td (Total: ${order.total}) Tj
ET
endstream
endobj
5 0 obj<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>endobj
xref
0 6
trailer<</Size 6/Root 1 0 R>>
startxref 0
%%EOF"""
    buf = BytesIO(content.encode())
    buf.seek(0)
    return buf
