import polars as pl
from pathlib import Path

from src.helpers import excel_helpers
from src.config import REQUIRED_COLUMNS, TICKET_COLUMNS

from datetime import datetime, date, time as dtime

from openpyxl import load_workbook

from pathlib import Path
from openpyxl import load_workbook
from datetime import datetime, date, time as dtime
import polars as pl

def read_excel_with_excel_row(path: Path, sheet_name: str | None = None) -> pl.DataFrame:
    wb = load_workbook(path, read_only=True, data_only=True)
    ws = wb[sheet_name] if sheet_name else wb.worksheets[0]

    max_row, max_col = ws.max_row, ws.max_column

    used_cols = [False] * max_col   # marca columnas que tienen algún dato real
    rows = []

    for r_idx, row in enumerate(
        ws.iter_rows(min_row=1, max_row=max_row, max_col=max_col, values_only=True),
        start=1
    ):
        if all(v is None or v == "" for v in row):
            continue

        vals = []
        for j, v in enumerate(row, start=1):
            if v is None or v == "":
                vals.append(None)
                continue

            # hay valor real => esta columna se usa
            used_cols[j - 1] = True

            if isinstance(v, (datetime, date, dtime)):
                vals.append(v.isoformat())
            else:
                s = str(v).strip()
                vals.append(s if s != "" else None)
                # si era solo espacios, no cuenta como dato real
                if s == "":
                    used_cols[j - 1] = False

        rows.append([r_idx, *vals])

    # qué columnas conservar (1-based, col_1..col_n)
    keep = [i + 1 for i, ok in enumerate(used_cols) if ok]

    # recorta cada fila a solo esas columnas
    cropped = []
    for r in rows:
        excel_row = r[0]
        data = r[1:]  # col_1..col_max
        cropped.append([excel_row] + [data[i - 1] for i in keep])

    schema = ["excel_row"] + [f"col_{i}" for i in keep]
    return pl.DataFrame(cropped, schema=schema, orient="row")



class ExcelController:
    def __init__(self, excel_path: Path):
        self.excel_path = excel_path
        self.df = None

        self.format = None
        self.ticket_column = None

        self._run()

    def _run(self):
        self._validate_file()
        self._load_excel()
        # self._validate_structure()
        # self._filter_pending()

    def _validate_file(self):
        if not self.excel_path.exists():
            raise FileNotFoundError("El archivo Excel no existe")
        
    def _load_excel(self):
        df_raw = read_excel_with_excel_row(self.excel_path)

        if df_raw.is_empty():
            raise ValueError("El archivo Excel no contiene datos")
        
        print("df_raw")
        print(df_raw)
        
        header_row = excel_helpers.detect_header_row(df_raw)
        print("header_row")
        print(header_row)
        
        raw_headers = list(df_raw.row(header_row))
        print("raw_header")
        print(raw_headers)

        headers = excel_helpers.clean_headers([str(h) for h in raw_headers])
        print("headers")
        print(headers)

        self.format = excel_helpers.detect_format(headers)
        print("format")
        print(self.format)

        self.ticket_column = excel_helpers.validate_required_columns(headers, REQUIRED_COLUMNS, TICKET_COLUMNS)
        print("ticket_column")
        print(self.ticket_column)
        
        df_data = df_raw.slice(header_row + 1)
        if self.format == "NEW":
            df_data = df_data.slice(1)

        print("df_data")
        print(df_data)

        df_data = df_data.select(df_data.columns[:len(headers)])
        print("df_data.select")
        print(df_data)

        df_data.columns = headers
        df_data = df_data.filter(pl.any_horizontal(pl.all().is_not_null()))

        df_data = excel_helpers.normalize_datetime_column(df_data)

        df_data = excel_helpers.reduce_to_core_columns(df = df_data, ticket_col= self.ticket_column)

        df_data = excel_helpers.filter_pending_tickets(df=df_data, ticket_col="TICKET")

        if df_data.is_empty():
            raise ValueError("La planilla no contiene ticket pendientes para cargar")

        self.df = df_data

        print("df_data")
        print(df_data)

        self.df.write_csv("debug_output.csv")

    def add_ticket(self, job):
        print(f"✍️ Registrando ticket en Excel fila {job.row_id}")


    def return_excel(self):
        pass