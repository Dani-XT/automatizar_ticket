import polars as pl
from pathlib import Path

from src.utils import excel_utils

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
        df_raw = pl.read_excel(self.excel_path, has_header=False)
        
        if df_raw is None:
            raise RuntimeError("El archivo Excel no fue cargado correctamente")

        if df_raw.is_empty():
            raise ValueError("El archivo Excel no contiene datos")

        header_row = excel_utils.detect_header_row(df_raw)

        raw_headers = list(df_raw.row(header_row))

        headers = excel_utils.clean_headers([str(h) for h in raw_headers])

        self.format = excel_utils.detect_format(headers)

        print("\n Header Row")
        print(header_row)
        print("\n Raw Headers")
        print(raw_headers)
        print("\n Headers")
        print(headers)
        print("\n Format")
        print(self.format)


        
        self.df = pl.read_excel(self.excel_path, has_header=True, read_csv_options={"skip_rows": header_row})

