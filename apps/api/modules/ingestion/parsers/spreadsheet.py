import csv
import io
from typing import Any, Dict, List
import openpyxl


def parse_csv(content_bytes: bytes) -> List[Dict[str, Any]]:
    text = content_bytes.decode("utf-8", errors="replace")
    if not text.strip():
        return []

    delimiter = ","
    try:
        sample = text[:2048]
        if "\t" in sample and "," not in sample:
            delimiter = "\t"
        elif ";" in sample and "," not in sample:
            delimiter = ";"
        else:
            dialect = csv.Sniffer().sniff(sample, delimiters=",\t;|")
            delimiter = dialect.delimiter
    except Exception:
        delimiter = ","

    reader = csv.reader(io.StringIO(text), delimiter=delimiter)
    rows = list(reader)
    if not rows:
        return []

    headers = [h.strip() for h in rows[0]]
    elements: List[Dict[str, Any]] = []

    if len(rows) == 1:
        elements.append({
            "kind": "table_row",
            "content": "Headers: " + ", ".join(headers),
            "locator": {
                "row_range": [1, 1],
                "sheet": "Sheet1",
            },
        })
        return elements

    # Batch rows in groups of 10 for table context
    batch_size = 10
    for i in range(1, len(rows), batch_size):
        batch = rows[i : i + batch_size]
        batch_lines = []
        for r_idx, row in enumerate(batch):
            actual_row_num = i + r_idx + 1
            row_items = []
            for col_idx, val in enumerate(row):
                header_name = headers[col_idx] if col_idx < len(headers) else f"Col_{col_idx+1}"
                row_items.append(f"{header_name}: {val.strip()}")
            batch_lines.append(f"Row {actual_row_num}: " + ", ".join(row_items))

        content = "\n".join(batch_lines)
        elements.append({
            "kind": "table_row",
            "content": content,
            "locator": {
                "row_range": [i + 1, min(len(rows), i + batch_size)],
                "sheet": "Sheet1",
            },
        })

    return elements


def parse_xlsx(content_bytes: bytes) -> List[Dict[str, Any]]:
    wb = openpyxl.load_workbook(io.BytesIO(content_bytes), data_only=True)
    elements: List[Dict[str, Any]] = []

    for sheet_name in wb.sheetnames:
        sheet = wb[sheet_name]
        rows = list(sheet.iter_rows(values_only=True))
        if not rows:
            continue

        headers = [str(h or f"Col_{i+1}").strip() for i, h in enumerate(rows[0])]
        if len(rows) == 1:
            elements.append({
                "kind": "table_row",
                "content": "Headers: " + ", ".join(headers),
                "locator": {
                    "row_range": [1, 1],
                    "sheet": sheet_name,
                },
            })
            continue

        batch_size = 10
        for i in range(1, len(rows), batch_size):
            batch = rows[i : i + batch_size]
            batch_lines = []
            for r_idx, row in enumerate(batch):
                actual_row_num = i + r_idx + 1
                row_items = []
                for col_idx, val in enumerate(row):
                    header_name = headers[col_idx] if col_idx < len(headers) else f"Col_{col_idx+1}"
                    row_items.append(f"{header_name}: {str(val).strip() if val is not None else ''}")
                batch_lines.append(f"Row {actual_row_num}: " + ", ".join(row_items))

            content = "\n".join(batch_lines)
            elements.append({
                "kind": "table_row",
                "content": content,
                "locator": {
                    "row_range": [i + 1, min(len(rows), i + batch_size)],
                    "sheet": sheet_name,
                },
            })

    return elements
