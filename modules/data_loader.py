"""
Módulo de Carga, Mapeo y Calidad de Datos
Permite cargar archivos Excel (.xlsx, .xls) y CSV con detección inteligente de columnas,
mapeo interactivo y diagnósticos de calidad.
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple, List, Optional

# Diccionario de sinónimos comunes para mapeo automático
STANDARD_COLUMNS = {
    "fecha": ["order date", "fecha", "order_date", "fecha de pedido", "fecha pedido", "date", "fecha de venta"],
    "pedido_id": ["order id", "pedido id", "order_id", "id_pedido", "codigo pedido", "num pedido", "factura"],
    "producto": ["product name", "producto", "product_name", "nombre producto", "item", "articulo", "descripcion"],
    "producto_id": ["product id", "id producto", "product_id", "codigo", "sku"],
    "categoria": ["category", "categoria", "categoría", "linea", "departamento"],
    "subcategoria": ["sub-category", "subcategory", "subcategoria", "subcategoría", "familia", "grupo"],
    "segmento": ["segment", "segmento", "segmento cliente", "tipo cliente", "customer segment"],
    "region": ["region", "región", "zona", "territorio", "area"],
    "pais": ["country", "pais", "país", "nacion"],
    "estado": ["state", "estado", "departamento_geo", "provincia"],
    "ciudad": ["city", "ciudad", "municipio", "poblacion"],
    "cantidad": ["quantity", "cantidad", "unidades", "qty", "volumen"],
    "ventas": ["sales", "ventas", "ingresos", "revenue", "monto", "total_ventas", "importe"],
    "costo": ["cost", "costo", "costos", "costo de ventas", "costo_total", "costo_producto", "cogs"],
    "utilidad": ["profit", "utilidad", "ganancia", "margen_bruto_monto", "beneficio", "income"],
    "descuento": ["discount", "descuento", "rebaja", "dto"]
}


def auto_detect_mapping(df_columns: List[str]) -> Dict[str, Optional[str]]:
    """Identifica las columnas equivalentes basándose en coincidencia de nombres."""
    mapping = {}
    normalized_cols = {col.strip().lower(): col for col in df_columns}
    
    for std_field, aliases in STANDARD_COLUMNS.items():
        matched = None
        for alias in aliases:
            if alias in normalized_cols:
                matched = normalized_cols[alias]
                break
        mapping[std_field] = matched
    return mapping


def load_file(file_obj) -> Dict[str, pd.DataFrame]:
    """Carga un archivo Excel o CSV retornando un dict de DataFrames por hoja."""
    filename = file_obj.name.lower()
    if filename.endswith(".csv"):
        # Intenta UTF-8 y luego latin-1
        try:
            df = pd.read_csv(file_obj, encoding="utf-8")
        except UnicodeDecodeError:
            file_obj.seek(0)
            df = pd.read_csv(file_obj, encoding="latin-1")
        return {"Datos": df}
    elif filename.endswith((".xlsx", ".xls")):
        excel_file = pd.ExcelFile(file_obj)
        sheets_dict = {}
        for sheet_name in excel_file.sheet_names:
            sheets_dict[sheet_name] = pd.read_excel(file_obj, sheet_name=sheet_name)
        return sheets_dict
    else:
        raise ValueError("Formato de archivo no soportado. Cargue un archivo CSV o Excel (.xls, .xlsx).")


def prepare_and_validate_data(
    df: pd.DataFrame,
    mapping: Dict[str, Optional[str]]
) -> Tuple[pd.DataFrame, Dict]:
    """
    Estandariza los nombres de columnas, realiza conversiones de tipos y
    ejecuta auditoría de calidad de datos.
    """
    diagnostics = {
        "total_registros": len(df),
        "nulos_por_campo": {},
        "duplicados": int(df.duplicated().sum()),
        "ventas_cero_o_negativas": 0,
        "cantidades_cero_o_negativas": 0,
        "registros_con_perdida": 0,
        "fechas_invalidas": 0,
        "costo_imputado": False,
        "advertencias": []
    }
    
    clean_df = pd.DataFrame()
    
    # Mapear y procesar campos
    # 1. Fecha
    col_fecha = mapping.get("fecha")
    if col_fecha and col_fecha in df.columns:
        clean_df["Fecha"] = pd.to_datetime(df[col_fecha], errors="coerce")
        nulos_fecha = int(clean_df["Fecha"].isna().sum())
        diagnostics["fechas_invalidas"] = nulos_fecha
        if nulos_fecha > 0:
            diagnostics["advertencias"].append(f"Se encontraron {nulos_fecha} fechas inválidas o vacías.")
    else:
        clean_df["Fecha"] = pd.NaT
        diagnostics["advertencias"].append("No se asignó columna de Fecha. El análisis temporal estará limitado.")

    # 2. Textos clasificatorios
    for std_name, col_key, default_val in [
        ("Pedido_ID", "pedido_id", "Sin ID"),
        ("Producto", "producto", "Producto No Especificado"),
        ("Producto_ID", "producto_id", "N/A"),
        ("Categoria", "categoria", "General"),
        ("Subcategoria", "subcategoria", "General"),
        ("Segmento", "segmento", "Sin Segmento"),
        ("Region", "region", "Sin Región"),
        ("Pais", "pais", "No Especificado"),
        ("Estado", "estado", "No Especificado"),
        ("Ciudad", "ciudad", "No Especificado")
    ]:
        col_act = mapping.get(col_key)
        if col_act and col_act in df.columns:
            clean_df[std_name] = df[col_act].fillna(default_val).astype(str)
        else:
            clean_df[std_name] = default_val

    # 3. Métricas Numéricas
    # Ventas
    col_ventas = mapping.get("ventas")
    if col_ventas and col_ventas in df.columns:
        clean_df["Ventas"] = pd.to_numeric(df[col_ventas], errors="coerce").fillna(0.0)
    else:
        clean_df["Ventas"] = 0.0
        diagnostics["advertencias"].append("¡Atención! No se asignó columna de Ventas.")

    # Cantidad
    col_cant = mapping.get("cantidad")
    if col_cant and col_cant in df.columns:
        clean_df["Cantidad"] = pd.to_numeric(df[col_cant], errors="coerce").fillna(0).astype(float)
    else:
        clean_df["Cantidad"] = 1.0

    # Descuento
    col_desc = mapping.get("descuento")
    if col_desc and col_desc in df.columns:
        clean_df["Descuento"] = pd.to_numeric(df[col_desc], errors="coerce").fillna(0.0)
    else:
        clean_df["Descuento"] = 0.0

    # Utilidad y Costos
    col_utilidad = mapping.get("utilidad")
    col_costo = mapping.get("costo")
    
    if col_utilidad and col_utilidad in df.columns:
        clean_df["Utilidad"] = pd.to_numeric(df[col_utilidad], errors="coerce").fillna(0.0)
        if col_costo and col_costo in df.columns:
            clean_df["Costo"] = pd.to_numeric(df[col_costo], errors="coerce").fillna(0.0)
        else:
            # Si hay ventas y utilidad, el costo de ventas = Ventas - Utilidad
            clean_df["Costo"] = clean_df["Ventas"] - clean_df["Utilidad"]
            diagnostics["costo_imputado"] = True
    elif col_costo and col_costo in df.columns:
        clean_df["Costo"] = pd.to_numeric(df[col_costo], errors="coerce").fillna(0.0)
        clean_df["Utilidad"] = clean_df["Ventas"] - clean_df["Costo"]
    else:
        # Ni costo ni utilidad
        clean_df["Costo"] = 0.0
        clean_df["Utilidad"] = clean_df["Ventas"]
        diagnostics["advertencias"].append("No se encontró columna de Costo ni de Utilidad. Se asume margen del 100%.")

    # Auditoría de anomalías numéricas
    diagnostics["ventas_cero_o_negativas"] = int((clean_df["Ventas"] <= 0).sum())
    diagnostics["cantidades_cero_o_negativas"] = int((clean_df["Cantidad"] <= 0).sum())
    diagnostics["registros_con_perdida"] = int((clean_df["Utilidad"] < 0).sum())
    
    # Conteo de nulos
    for col in clean_df.columns:
        n_nulos = int(clean_df[col].isna().sum())
        if n_nulos > 0:
            diagnostics["nulos_por_campo"][col] = n_nulos

    # Campos de fecha derivados
    if not clean_df["Fecha"].isna().all():
        clean_df["Año"] = clean_df["Fecha"].dt.year
        clean_df["Año_Mes"] = clean_df["Fecha"].dt.to_period("M").astype(str)
        clean_df["Trimestre"] = clean_df["Fecha"].dt.to_period("Q").astype(str)
    else:
        clean_df["Año"] = None
        clean_df["Año_Mes"] = None
        clean_df["Trimestre"] = None

    return clean_df, diagnostics
