import polars as pl
from pathlib import Path

from src.utils import excel_utils
from src.config import REQUIRED_COLUMNS, TICKET_COLUMNS

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

        if df_raw.is_empty():
            raise ValueError("El archivo Excel no contiene datos")
        
        header_row = excel_utils.detect_header_row(df_raw)
        raw_headers = list(df_raw.row(header_row))
        headers = excel_utils.clean_headers([str(h) for h in raw_headers])
        self.format = excel_utils.detect_format(headers)
        self.ticket_column = excel_utils.validate_required_columns(headers, REQUIRED_COLUMNS, TICKET_COLUMNS)

        df_data = df_raw.slice(header_row + 1)

        if self.format == "NEW":
            df_data = df_data.slice(1)

        df_data = df_data.select(df_data.columns[:len(headers)])
        df_data.columns = headers
        df_data = df_data.filter(pl.any_horizontal(pl.all().is_not_null()))

        df_data = excel_utils.normalize_datetime_column(df_data)

        df_data = excel_utils.reduce_to_core_columns(df = df_data, ticket_col= self.ticket_column)

        self.df = df_data


        print(self.df)
        self.df.write_csv("debug_output.csv")


