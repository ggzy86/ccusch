import io
import pandas as pd


def export_excel(grid: pd.DataFrame) -> bytes:
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        grid.to_excel(writer, sheet_name="Schedule")
    return buffer.getvalue()


def export_pdf(grid: pd.DataFrame) -> bytes:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import landscape, A4
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4))

    data = [["Nurse"] + [str(c) for c in grid.columns]]
    for nurse, row in grid.iterrows():
        data.append([nurse] + list(row))

    SHIFT_COLORS = {
        "D": colors.HexColor("#7A9ED2"),
        "E": colors.HexColor("#D2A87A"),
        "N": colors.HexColor("#A496C6"),
        "LD": colors.HexColor("#77C591"),
        "LN": colors.HexColor("#B2774D"),
        "OFF": colors.HexColor("#DA9090"),
    }

    table = Table(data, repeatRows=1)
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#333333")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
        ("FONTSIZE", (0, 0), (-1, -1), 6),
    ]

    for row_idx, (nurse, row) in enumerate(grid.iterrows(), start=1):
        for col_idx, val in enumerate(row, start=1):
            color = SHIFT_COLORS.get(val)
            if color:
                style.append(("BACKGROUND", (col_idx, row_idx), (col_idx, row_idx), color))

    table.setStyle(TableStyle(style))
    doc.build([table])
    return buffer.getvalue()
