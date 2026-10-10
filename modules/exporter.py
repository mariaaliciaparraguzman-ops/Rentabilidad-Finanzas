"""
Módulo de Exportación Multiformato
Permite exportar a Excel consolidado (múltiples hojas) y CSV respetando filtros aplicados.
"""

import io
import pandas as pd
from typing import Dict


def export_to_excel_workbook(
    resumen_df: pd.DataFrame,
    categorias_df: pd.DataFrame,
    subcategorias_df: pd.DataFrame,
    segmentos_df: pd.DataFrame,
    regiones_df: pd.DataFrame,
    productos_df: pd.DataFrame
) -> bytes:
    """
    Genera un archivo Excel (.xlsx) en memoria con hojas organizadas:
    - Resumen Ejecutivo
    - Categorías
    - Subcategorías
    - Segmentos
    - Regiones
    - Top Productos
    """
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        if not resumen_df.empty:
            resumen_df.to_excel(writer, sheet_name="Resumen", index=False)
        if not categorias_df.empty:
            categorias_df.to_excel(writer, sheet_name="Categorias", index=False)
        if not subcategorias_df.empty:
            subcategorias_df.to_excel(writer, sheet_name="Subcategorias", index=False)
        if not segmentos_df.empty:
            segmentos_df.to_excel(writer, sheet_name="Segmentos", index=False)
        if not regiones_df.empty:
            regiones_df.to_excel(writer, sheet_name="Regiones", index=False)
        if not productos_df.empty:
            productos_df.to_excel(writer, sheet_name="Productos", index=False)
            
    output.seek(0)
    return output.getvalue()


def export_to_csv(df: pd.DataFrame) -> bytes:
    """Exporta un DataFrame a formato CSV con codificación UTF-8 con BOM para Excel."""
    return df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
