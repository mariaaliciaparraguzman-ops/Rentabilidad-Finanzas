"""
Módulo de Visualizaciones Interactivas con Plotly
Genera gráficos ejecutivos para análisis de rentabilidad, volumen vs margen,
mapas geográficos, evolución temporal y matrices de rentabilidad.
"""

from typing import Tuple
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np


# Paleta corporativa elegante para Business Intelligence
COLORS = {
    "primary": "#1E3A8A",      # Azul marino profundo
    "secondary": "#0284C7",    # Azul cian
    "success": "#059669",      # Verde esmeralda (ganancias)
    "danger": "#DC2626",       # Rojo coral (pérdidas)
    "warning": "#D97706",      # Ámbar
    "neutral": "#64748B",      # Gris pizarra
    "background": "#F8FAFC",
    "card": "#FFFFFF",
    "text": "#0F172A"
}


def format_currency(val: float, symbol: str = "$") -> str:
    """Formatea valores numéricos a formato de moneda con separador de miles."""
    if pd.isna(val):
        return "N/D"
    return f"{symbol} {val:,.2f}"


def format_percent(val: float) -> str:
    """Formatea valores porcentuales."""
    if pd.isna(val):
        return "N/D"
    return f"{val:,.2f}%"


def bar_chart_metric(
    df: pd.DataFrame,
    x_col: str,
    y_col: str,
    title: str,
    is_percent: bool = False,
    symbol: str = "$",
    color_by_sign: bool = True
) -> go.Figure:
    """Gráfico de barras ordenado para métricas financieras (Ventas, Utilidad, Margen)."""
    sorted_df = df.sort_values(by=y_col, ascending=False).copy()
    
    if color_by_sign:
        colors = [COLORS["success"] if v >= 0 else COLORS["danger"] for v in sorted_df[y_col]]
    else:
        colors = COLORS["primary"]

    fig = go.Figure(
        data=[
            go.Bar(
                x=sorted_df[x_col],
                y=sorted_df[y_col],
                marker_color=colors,
                text=[format_percent(v) if is_percent else format_currency(v, symbol) for v in sorted_df[y_col]],
                textposition="auto",
                hovertemplate="<b>%{x}</b><br>" + title + ": %{text}<extra></extra>"
            )
        ]
    )
    
    fig.update_layout(
        title={"text": f"<b>{title}</b>", "x": 0.05, "xanchor": "left"},
        template="plotly_white",
        margin=dict(l=20, r=20, t=50, b=40),
        xaxis_title=x_col,
        yaxis_title=title,
        height=400,
        yaxis=dict(showgrid=True, gridcolor="#E2E8F0")
    )
    return fig


def comparison_bar_grouped(
    df: pd.DataFrame,
    cat_col: str,
    symbol: str = "$"
) -> go.Figure:
    """Comparativa grupal de Ventas vs Costos vs Utilidad por categoría/región."""
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        name="Ventas",
        x=df[cat_col],
        y=df["Ventas"],
        marker_color=COLORS["primary"],
        hovertemplate="Ventas: " + symbol + " %{y:,.2f}<extra></extra>"
    ))
    
    fig.add_trace(go.Bar(
        name="Costo",
        x=df[cat_col],
        y=df["Costo"],
        marker_color=COLORS["warning"],
        hovertemplate="Costo: " + symbol + " %{y:,.2f}<extra></extra>"
    ))

    fig.add_trace(go.Bar(
        name="Utilidad",
        x=df[cat_col],
        y=df["Utilidad"],
        marker_color=[COLORS["success"] if u >= 0 else COLORS["danger"] for u in df["Utilidad"]],
        hovertemplate="Utilidad: " + symbol + " %{y:,.2f}<extra></extra>"
    ))

    fig.update_layout(
        barmode="group",
        title={"text": f"<b>Estructura Financiera: Ventas, Costos y Utilidad por {cat_col}</b>", "x": 0.05},
        template="plotly_white",
        margin=dict(l=20, r=20, t=50, b=40),
        yaxis=dict(title=f"Monto ({symbol})", showgrid=True, gridcolor="#E2E8F0"),
        height=420,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    return fig


def profit_matrix_chart(
    df: pd.DataFrame,
    dim_name: str,
    symbol: str = "$",
    split_sales_median: bool = True,
    split_margin_median: bool = False,
    margin_threshold: float = 15.0
) -> Tuple[go.Figure, float, float]:
    """
    Matriz de Rentabilidad (Volumen vs Margen %):
    Divide los elementos en 4 cuadrantes:
    1. Alto Volumen / Alto Margen (Estrellas / Claves)
    2. Alto Volumen / Bajo Margen (Generadores de flujo / Riesgo de margen)
    3. Bajo Volumen / Alto Margen (Oportunidad de nicho / Potencial)
    4. Bajo Volumen / Bajo Margen (En revisión / Críticos)
    """
    if df.empty:
        return go.Figure(), 0.0, 0.0

    # Determinar umbrales
    sales_th = df["Ventas"].median() if split_sales_median else df["Ventas"].mean()
    margin_th = df["Margen_%"].median() if split_margin_median else margin_threshold

    # Clasificar cada registro
    def classify(row):
        high_sales = row["Ventas"] >= sales_th
        high_margin = row["Margen_%"] >= margin_th
        if high_sales and high_margin:
            return "Alto Volumen / Alto Margen"
        elif high_sales and not high_margin:
            return "Alto Volumen / Bajo Margen"
        elif not high_sales and high_margin:
            return "Bajo Volumen / Alto Margen"
        else:
            return "Bajo Volumen / Bajo Margen"

    plot_df = df.copy()
    plot_df["Cuadrante"] = plot_df.apply(classify, axis=1)

    color_map = {
        "Alto Volumen / Alto Margen": "#059669",  # Verde
        "Alto Volumen / Bajo Margen": "#2563EB",  # Azul
        "Bajo Volumen / Alto Margen": "#D97706",  # Ámbar
        "Bajo Volumen / Bajo Margen": "#DC2626"   # Rojo
    }

    fig = px.scatter(
        plot_df,
        x="Ventas",
        y="Margen_%",
        color="Cuadrante",
        color_discrete_map=color_map,
        hover_name=dim_name,
        size=plot_df["Cantidad"].apply(lambda q: max(q, 1)),
        hover_data={
            "Ventas": f":{symbol},.2f",
            "Margen_%": ":.2f%",
            "Utilidad": f":{symbol},.2f",
            "Cantidad": ":,.0f",
            "Cuadrante": True
        },
        title=f"<b>Matriz de Rentabilidad: Volumen de Ventas vs Margen de Utilidad ({dim_name})</b>"
    )

    # Añadir líneas de umbral
    fig.add_vline(x=sales_th, line_dash="dash", line_color="#94A3B8", annotation_text=f"Umbral Ventas: {format_currency(sales_th, symbol)}")
    fig.add_hline(y=margin_th, line_dash="dash", line_color="#94A3B8", annotation_text=f"Umbral Margen: {margin_th:.1f}%")

    fig.update_layout(
        template="plotly_white",
        height=520,
        xaxis_title=f"Volumen de Ventas ({symbol})",
        yaxis_title="Margen de Utilidad (%)",
        margin=dict(l=20, r=20, t=60, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0)
    )
    return fig, sales_th, margin_th


def time_series_chart(
    df: pd.DataFrame,
    freq_col: str,
    symbol: str = "$"
) -> go.Figure:
    """Evolución temporal de Ventas, Costos, Utilidad y Margen %."""
    time_agg = df.groupby(freq_col).agg(
        Ventas=("Ventas", "sum"),
        Costo=("Costo", "sum"),
        Utilidad=("Utilidad", "sum")
    ).reset_index()

    time_agg["Margen_%"] = np.where(time_agg["Ventas"] > 0, (time_agg["Utilidad"] / time_agg["Ventas"]) * 100, 0.0)
    time_agg = time_agg.sort_values(by=freq_col)

    fig = go.Figure()

    # Barras de Ventas y Utilidad
    fig.add_trace(go.Bar(
        x=time_agg[freq_col],
        y=time_agg["Ventas"],
        name="Ventas",
        marker_color="#93C5FD",
        yaxis="y1"
    ))

    fig.add_trace(go.Bar(
        x=time_agg[freq_col],
        y=time_agg["Utilidad"],
        name="Utilidad",
        marker_color=[COLORS["success"] if u >= 0 else COLORS["danger"] for u in time_agg["Utilidad"]],
        yaxis="y1"
    ))

    # Línea de Margen % en eje secundario
    fig.add_trace(go.Scatter(
        x=time_agg[freq_col],
        y=time_agg["Margen_%"],
        name="Margen (%)",
        mode="lines+markers",
        line=dict(color="#1E3A8A", width=3),
        marker=dict(size=7),
        yaxis="y2"
    ))

    fig.update_layout(
        title={"text": f"<b>Evolución Temporal de Ventas, Utilidad y Margen ({freq_col})</b>", "x": 0.05},
        template="plotly_white",
        height=450,
        margin=dict(l=20, r=20, t=60, b=40),
        yaxis=dict(title=f"Monto ({symbol})", showgrid=True, gridcolor="#E2E8F0"),
        yaxis2=dict(
            title="Margen de Utilidad (%)",
            overlaying="y",
            side="right",
            ticksuffix="%",
            showgrid=False
        ),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    return fig


def discount_impact_chart(df: pd.DataFrame, symbol: str = "$") -> go.Figure:
    """Analiza el efecto del descuento sobre el margen porcentual y la utilidad."""
    # Agrupar en tramos de descuento si no son discretos
    df_temp = df.copy()
    df_temp["Tramo_Descuento"] = pd.cut(
        df_temp["Descuento"],
        bins=[-0.01, 0.00, 0.10, 0.20, 0.35, 0.50, 1.0],
        labels=["0% (Sin Descuento)", "1% - 10%", "11% - 20%", "21% - 35%", "36% - 50%", "> 50%"]
    )
    
    disc_summary = df_temp.groupby("Tramo_Descuento", observed=False).agg(
        Ventas=("Ventas", "sum"),
        Utilidad=("Utilidad", "sum"),
        Registros=("Ventas", "count")
    ).reset_index()

    disc_summary["Margen_%"] = np.where(
        disc_summary["Ventas"] > 0,
        (disc_summary["Utilidad"] / disc_summary["Ventas"]) * 100,
        0.0
    )

    fig = go.Figure()
    
    # Barra de margen %
    colors = [COLORS["success"] if m >= 0 else COLORS["danger"] for m in disc_summary["Margen_%"]]
    
    fig.add_trace(go.Bar(
        x=disc_summary["Tramo_Descuento"].astype(str),
        y=disc_summary["Margen_%"],
        marker_color=colors,
        text=[f"{m:.1f}%" for m in disc_summary["Margen_%"]],
        textposition="auto",
        name="Margen %"
    ))

    fig.update_layout(
        title={"text": "<b>Impacto del Nivel de Descuento en el Margen de Utilidad</b>", "x": 0.05},
        template="plotly_white",
        height=380,
        xaxis_title="Nivel de Descuento Otorgado",
        yaxis_title="Margen de Utilidad (%)",
        yaxis=dict(ticksuffix="%", showgrid=True, gridcolor="#E2E8F0"),
        margin=dict(l=20, r=20, t=50, b=40)
    )
    return fig
