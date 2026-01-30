import pandas as pd
from config import SPREADSHEET_ID

def read_sheet(sheets_service):
    result = sheets_service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID,
        range="A1:ZZ"
    ).execute()

    values = result.get("values", [])
    if not values:
        return pd.DataFrame()

    header = values[0]
    rows = values[1:]

    fixed_rows = []
    header_len = len(header)

    for row in rows:
        if len(row) < header_len:
            row = row + [""] * (header_len - len(row))
        fixed_rows.append(row)

    return pd.DataFrame(fixed_rows, columns=header)
