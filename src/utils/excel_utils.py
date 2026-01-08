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
