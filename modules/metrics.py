"""
Módulo de Métricas e Indicadores Financieros y Comerciales.
Calcula KPIs consolidados, agrupaciones, tasas de variación y distribuciones de rentabilidad.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any


def compute_kpis(df: pd.DataFrame, prev_df: pd.DataFrame = None) -> Dict[str, Any]:
    """
    Calcula los KPIs financieros principales y variaciones respecto al período anterior.
    """
    total_ventas = float(df["Ventas"].sum()) if not df.empty else 0.0
    total_costo = float(df["Costo"].sum()) if not df.empty else 0.0
    total_utilidad = float(df["Utilidad"].sum()) if not df.empty else 0.0
    total_cantidad = float(df["Cantidad"].sum()) if not df.empty else 0.0
    
    # Margen de utilidad (%) = Utilidad / Ventas * 100
    margen_utilidad = (total_utilidad / total_ventas * 100.0) if total_ventas > 0 else 0.0
    
    # Precio y costo promedio unitario
    precio_promedio = (total_ventas / total_cantidad) if total_cantidad > 0 else 0.0
    costo_promedio = (total_costo / total_cantidad) if total_cantidad > 0 else 0.0
    
    # Descuento promedio ponderado o aritmético
    descuento_promedio = float(df["Descuento"].mean() * 100.0) if not df.empty and "Descuento" in df.columns else 0.0
    
    # Ticket promedio (si existe Pedido_ID válido y diferente de 'Sin ID')
    if not df.empty and (df["Pedido_ID"] != "Sin ID").any():
        pedidos_unicos = df[df["Pedido_ID"] != "Sin ID"]["Pedido_ID"].nunique()
        ticket_promedio = (total_ventas / pedidos_unicos) if pedidos_unicos > 0 else total_ventas
    else:
        pedidos_unicos = len(df)
        ticket_promedio = (total_ventas / pedidos_unicos) if pedidos_unicos > 0 else 0.0

    # Variaciones respecto al período anterior
    variacion_utilidad = None
    variacion_ventas = None
    variacion_margen = None
    
    if prev_df is not None and not prev_df.empty:
        prev_ventas = float(prev_df["Ventas"].sum())
        prev_utilidad = float(prev_df["Utilidad"].sum())
        prev_margen = (prev_utilidad / prev_ventas * 100.0) if prev_ventas > 0 else 0.0
        
        if prev_ventas > 0:
            variacion_ventas = ((total_ventas - prev_ventas) / prev_ventas) * 100.0
        if prev_utilidad != 0:
            variacion_utilidad = ((total_utilidad - prev_utilidad) / abs(prev_utilidad)) * 100.0
        variacion_margen = margen_utilidad - prev_margen

    return {
        "ventas": total_ventas,
        "costo": total_costo,
        "utilidad": total_utilidad,
        "margen": margen_utilidad,
        "cantidad": total_cantidad,
        "precio_promedio": precio_promedio,
        "costo_promedio": costo_promedio,
        "descuento_promedio": descuento_promedio,
        "ticket_promedio": ticket_promedio,
        "pedidos_unicos": pedidos_unicos,
        "var_ventas": variacion_ventas,
        "var_utilidad": variacion_utilidad,
        "var_margen": variacion_margen
    }


def aggregate_by_dimension(df: pd.DataFrame, group_cols: list) -> pd.DataFrame:
    """
    Agrupa por una o varias dimensiones calculando métricas comerciales y financieras:
    Ventas, Costos, Utilidad, Margen %, Unidades, Precio Promedio, Descuento Promedio,
    Participación en Ventas (%) y Participación en Utilidad (%).
    """
    if df.empty:
        return pd.DataFrame()
        
    total_global_ventas = df["Ventas"].sum()
    total_global_utilidad = df["Utilidad"].sum()

    agg_df = df.groupby(group_cols).agg(
        Ventas=("Ventas", "sum"),
        Costo=("Costo", "sum"),
        Utilidad=("Utilidad", "sum"),
        Cantidad=("Cantidad", "sum"),
        Descuento_Promedio=("Descuento", lambda s: s.mean() * 100.0),
        Registros=("Ventas", "count"),
        Pedidos=("Pedido_ID", lambda s: s[s != "Sin ID"].nunique() if (s != "Sin ID").any() else s.count())
    ).reset_index()

    # Margen porcentual seguro
    agg_df["Margen_%"] = np.where(
        agg_df["Ventas"] > 0,
        (agg_df["Utilidad"] / agg_df["Ventas"]) * 100.0,
        0.0
    )
    
    # Precio y costo promedio unitario
    agg_df["Precio_Promedio"] = np.where(
        agg_df["Cantidad"] > 0,
        agg_df["Ventas"] / agg_df["Cantidad"],
        0.0
    )
    agg_df["Costo_Promedio"] = np.where(
        agg_df["Cantidad"] > 0,
        agg_df["Costo"] / agg_df["Cantidad"],
        0.0
    )

    # Ticket promedio
    agg_df["Ticket_Promedio"] = np.where(
        agg_df["Pedidos"] > 0,
        agg_df["Ventas"] / agg_df["Pedidos"],
        agg_df["Ventas"]
    )

    # Participación en ventas (%)
    agg_df["Part_Ventas_%"] = (agg_df["Ventas"] / total_global_ventas * 100.0) if total_global_ventas > 0 else 0.0

    # Participación en utilidad (%) - Manejando casos de utilidad total <= 0
    if total_global_utilidad > 0:
        agg_df["Part_Utilidad_%"] = (agg_df["Utilidad"] / total_global_utilidad * 100.0)
    else:
        agg_df["Part_Utilidad_%"] = np.nan

    return agg_df
