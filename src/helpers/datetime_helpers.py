from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, date, time
import re
import polars as pl

# -------------------------
# PARSERS Python (strings -> date/time/datetime)
# -------------------------

WEB_CREATION_FMT = "%d/%m/%Y %H:%M" 

def parse_web_creation_dt(text: str) -> datetime:
    if text is None:
        raise ValueError("creation datetime text is None")
    return datetime.strptime(text.strip(), WEB_CREATION_FMT)

def parse_excel_date_text(text: str) -> date | None:
    """
    Soporta:
    - '30/12/2025'
    - '30-12-2025'
    - '2025-12-30' (por isoformat)
    - '2025-12-30T00:00:00' (por isoformat datetime)
    """
    if text is None:
        return None
    s = str(text).strip()
    if not s:
        return None

    m = re.search(r"(\d{4}-\d{2}-\d{2})", s)
    if m:
        return datetime.strptime(m.group(1), "%Y-%m-%d").date()

    s2 = s.replace("-", "/")
    try:
        return datetime.strptime(s2, "%d/%m/%Y").date()
    except ValueError:
        return None

def parse_excel_time_text(text: str) -> time | None:
    """
    Soporta:
    - '15:01'
    - '15:01:00'
    - '15:01:00.000'
    """
    if text is None:
        return None
    s = str(text).strip()
    if not s:
        return None

    m = re.search(r"(\d{2}:\d{2})(:\d{2})?", s)
    if not m:
        return None

    hhmm = m.group(1)        # HH:MM
    ss = m.group(2) or ":00" # si no hay segundos, agrega :00
    return datetime.strptime(hhmm + ss, "%H:%M:%S").time()

def split_web_creation_dt(text: str) -> tuple[date, time]:
    dt = parse_web_creation_dt(text)
    return dt.date(), dt.time()

# -------------------------
# NORMALIZACIÓN EN POLARS (columnas -> Date/Time)
# -------------------------

def normalize_fecha_hora_polars(df: pl.DataFrame, fecha_col: str = "FECHA", hora_col: str = "HORA") -> pl.DataFrame:
    exprs: list[pl.Expr] = []

    if fecha_col in df.columns:
        fecha_txt = (
            pl.col(fecha_col)
            .cast(pl.Utf8, strict=False)
            .str.strip_chars()
        )

        exprs.append(
            pl.coalesce(
                fecha_txt
                    .str.extract(r"(\d{4}-\d{2}-\d{2})")
                    .str.strptime(pl.Date, "%Y-%m-%d", strict=False),

                fecha_txt
                    .str.replace_all("-", "/")
                    .str.strptime(pl.Date, "%d/%m/%Y", strict=False),

                pl.col(fecha_col).cast(pl.Date, strict=False),

                pl.col(fecha_col).cast(pl.Datetime, strict=False).dt.date()
            ).alias(fecha_col)
        )

    if hora_col in df.columns:
        hora_txt = (
            pl.col(hora_col)
            .cast(pl.Utf8, strict=False)
            .str.strip_chars()
            .str.extract(r"(\d{2}:\d{2}(:\d{2})?)")
        )
        # si viene HH:MM, lo convertimos a HH:MM:SS
        hora_txt = pl.when(hora_txt.str.len_chars() == 5).then(hora_txt + ":00").otherwise(hora_txt)

        exprs.append(
            hora_txt.str.strptime(pl.Time, "%H:%M:%S", strict=False).alias(hora_col)
        )

    return df.with_columns(exprs)
