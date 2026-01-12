import polars as pl
from typing import List, Tuple, Set

def clean_headers(headers: List[str]) -> List[str]:
    return [
        h.strip()
        for h in headers
        if h and str(h).strip().upper() != "NONE"
    ]

def detect_header_row(df_raw: pl.DataFrame) -> int:
    for i, row in enumerate(df_raw.iter_rows()):
        normalized = {
            str(c).strip().upper()
            for c in row
            if c
        }
        if "FECHA" in normalized and "HORA" in normalized:
            return i
    
    raise ValueError("No se pudo detectar la fila de encabezados")

def detect_format(headers: List[str]) -> str:
    normalized = {h.upper() for h in headers}

    if "TKT" in normalized and "TICKET" not in normalized:
        return "OLD"
    
    if "TICKET" in normalized and "EDIFICIO" in normalized:
        return "NEW"
    
    raise ValueError("Formato de planilla no reconocido")

def validate_required_columns( headers: List[str], required: Set[str], ticket_aliases: Set[str]) -> str:
    normalized = {h.upper(): h for h in headers}
    missing = [
        col for col in required
        if col not in normalized
    ]
    if missing:
        raise ValueError(f"Faltan columnas requeridas: {', '.join(missing)}")
    
    for alias in ticket_aliases:
        if alias in normalized:
            return normalized[alias]
        
    raise ValueError("No se encontro columna de ticket (TKT o Ticket)")

def normalize_datetime_column(df: pl.DataFrame, fecha_col: str = "FECHA", hora_col: str = "HORA") -> pl.DataFrame:
    exprs = []

    if fecha_col in df.columns:
        exprs.append(
            pl.coalesce(
                pl.col(fecha_col)
                  .cast(pl.Utf8, strict=False)
                  .str.extract(r"(\d{4}-\d{2}-\d{2})")
                  .str.strptime(pl.Date, format="%Y-%m-%d", strict=False),

                pl.col(fecha_col)
                  .cast(pl.Datetime, strict=False)
                  .dt.date(),

                pl.col(fecha_col)
                  .cast(pl.Date, strict=False)
            ).alias(fecha_col)
        )

    if hora_col in df.columns:
        hora_str = (
            pl.col(hora_col)
            .cast(pl.Utf8, strict=False)
            .str.extract(r"(\d{2}:\d{2}(:\d{2})?)")
        )

        exprs.append(
            hora_str
            .str.strptime(pl.Time, format="%H:%M:%S", strict=False)
            .alias(hora_col)
        )

    return df.with_columns(exprs)

from src.config import CORE_COLUMNS

def reduce_to_core_columns(df: pl.DataFrame, ticket_col: str) -> pl.DataFrame:

    # Normalizar nombre del ticket
    if ticket_col != "TICKET":
        df = df.rename({ticket_col: "TICKET"})

    missing = [c for c in CORE_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"Columnas críticas faltantes: {', '.join(missing)}")

    return df.select(CORE_COLUMNS)


