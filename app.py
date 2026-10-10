"""
Dashboard Ejecutivo de Rentabilidad Comercial
Tecnologías: Python, Streamlit, Pandas, Plotly, OpenPyXL.
"""

import os
import streamlit as st
import pandas as pd
import numpy as np

# Importar módulos de la aplicación
from modules.data_loader import (
    load_file,
    auto_detect_mapping,
    prepare_and_validate_data,
    STANDARD_COLUMNS
)
from modules.metrics import (
    compute_kpis,
    aggregate_by_dimension
)
from modules.charts import (
    format_currency,
    format_percent,
    bar_chart_metric,
    comparison_bar_grouped,
    profit_matrix_chart,
    time_series_chart,
    discount_impact_chart,
    COLORS
)
from modules.recommendations import generate_recommendations
from modules.exporter import export_to_excel_workbook, export_to_csv


# Configuración de página
st.set_page_config(
    page_title="Dashboard de Rentabilidad Comercial",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS ejecutivos
st.markdown("""
<style>
    /* Estilos generales */
    .metric-card {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 16px 20px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        margin-bottom: 12px;
    }
    .metric-label {
        font-size: 0.85rem;
        font-weight: 600;
        color: #64748B;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .metric-val {
        font-size: 1.7rem;
        font-weight: 700;
        color: #0F172A;
        margin: 4px 0;
    }
    .metric-delta-pos {
        color: #059669;
        font-size: 0.85rem;
        font-weight: 600;
    }
    .metric-delta-neg {
        color: #DC2626;
        font-size: 0.85rem;
        font-weight: 600;
    }
    .badge-cat {
        display: inline-block;
        padding: 3px 8px;
        border-radius: 4px;
        font-size: 0.75rem;
        font-weight: 600;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 8px 16px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)


# Inicialización de estado de sesión
if "currency_symbol" not in st.session_state:
    st.session_state["currency_symbol"] = "$"
if "filter_reset_counter" not in st.session_state:
    st.session_state["filter_reset_counter"] = 0


# ==========================================
# SIDEBAR: FUENTE DE DATOS Y CONFIGURACIÓN
# ==========================================
st.sidebar.title("🏢 Control de Rentabilidad")
st.sidebar.markdown("Configuración y Fuentes de Información")

# Selección de símbolo monetario
moneda_opcion = st.sidebar.selectbox(
    "Moneda del Análisis:",
    options=["$ (USD / Genérica)", "€ (EUR)", "S/. (PEN)", "$ COP", "$ MXN"],
    index=0
)
simbolo = moneda_opcion.split()[0]
st.session_state["currency_symbol"] = simbolo

# Carga de datos
st.sidebar.subheader("📂 Carga de Datos")
archivo_cargado = st.sidebar.file_uploader(
    "Cargar archivo de ventas (.xlsx, .xls, .csv):",
    type=["xlsx", "xls", "csv"],
    help="Cargue un archivo propio o use la base de datos precargada de la empresa."
)

# Carga inicial o fallback a archivo local Superstore
df_raw = None
sheet_selected = None

if archivo_cargado is not None:
    try:
        sheets_dict = load_file(archivo_cargado)
        if len(sheets_dict) > 1:
            sheet_selected = st.sidebar.selectbox("Seleccione la hoja a analizar:", list(sheets_dict.keys()))
            df_raw = sheets_dict[sheet_selected]
        else:
            sheet_selected = list(sheets_dict.keys())[0]
            df_raw = sheets_dict[sheet_selected]
        st.sidebar.success(f"Archivo cargado: {len(df_raw):,} registros.")
    except Exception as e:
        st.sidebar.error(f"Error al leer el archivo: {e}")
else:
    # Cargar base por defecto si existe
    default_path = "base de datos - Superstore.xls"
    if not os.path.exists(default_path):
        default_path = r"C:\Users\Mary\Descargas\Rentabilidad\base de datos - Superstore.xls"
    
    if os.path.exists(default_path):
        st.sidebar.info("💡 Utilizando base de datos comercial por defecto (Superstore).")
        try:
            with open(default_path, "rb") as f:
                sheets_dict = load_file(f)
                sheet_selected = "Orders" if "Orders" in sheets_dict else list(sheets_dict.keys())[0]
                df_raw = sheets_dict[sheet_selected]
        except Exception as e:
            st.sidebar.error(f"No se pudo cargar la base por defecto: {e}")

if df_raw is None or df_raw.empty:
    st.warning("⚠️ No se encontraron datos para analizar. Por favor cargue un archivo CSV o Excel en la barra lateral.")
    st.stop()


# ==========================================
# MAPEO INTERACTIVO DE COLUMNAS
# ==========================================
with st.sidebar.expander("🛠️ Asignación de Columnas (Mapeo)", expanded=False):
    st.write("Verifique o modifique las columnas correspondientes:")
    auto_map = auto_detect_mapping(df_raw.columns.tolist())
    cols_opciones = ["(No disponible)"] + df_raw.columns.tolist()

    custom_mapping = {}
    for std_field, aliases in STANDARD_COLUMNS.items():
        default_col = auto_map.get(std_field)
        default_idx = cols_opciones.index(default_col) if default_col in cols_opciones else 0
        seleccion = st.selectbox(
            f"Campo: {std_field.capitalize()}",
            options=cols_opciones,
            index=default_idx,
            key=f"map_{std_field}"
        )
        custom_mapping[std_field] = None if seleccion == "(No disponible)" else seleccion


# Preparación y auditoría de calidad de datos
df_clean, diag = prepare_and_validate_data(df_raw, custom_mapping)


# ==========================================
# FILTROS GLOBALES EN SIDEBAR
# ==========================================
st.sidebar.subheader("🔍 Filtros Globales")

# Botón para restablecer filtros
if st.sidebar.button("🔄 Restablecer Filtros", use_container_width=True):
    st.session_state["filter_reset_counter"] += 1
    st.rerun()

reset_key = st.session_state["filter_reset_counter"]

# Filtro de Fechas
fecha_min = df_clean["Fecha"].min() if not df_clean["Fecha"].isna().all() else None
fecha_max = df_clean["Fecha"].max() if not df_clean["Fecha"].isna().all() else None

filtro_fechas = None
if fecha_min is not None and fecha_max is not None and pd.notna(fecha_min) and pd.notna(fecha_max):
    filtro_fechas = st.sidebar.date_input(
        "Rango de Fechas:",
        value=(fecha_min.date(), fecha_max.date()),
        min_value=fecha_min.date(),
        max_value=fecha_max.date(),
        key=f"date_filter_{reset_key}"
    )

# Filtro Categoría
categorias_disponibles = sorted(df_clean["Categoria"].unique().tolist())
sel_categorias = st.sidebar.multiselect(
    "Categoría:",
    options=categorias_disponibles,
    default=[],
    placeholder="Todas las categorías",
    key=f"cat_filter_{reset_key}"
)

# Filtro Subcategoría (dependiente de categorías seleccionadas si aplica)
subcats_disponibles = (
    df_clean[df_clean["Categoria"].isin(sel_categorias)]["Subcategoria"].unique().tolist()
    if sel_categorias else df_clean["Subcategoria"].unique().tolist()
)
sel_subcats = st.sidebar.multiselect(
    "Subcategoría:",
    options=sorted(subcats_disponibles),
    default=[],
    placeholder="Todas las subcategorías",
    key=f"subcat_filter_{reset_key}"
)

# Filtro Segmento
segmentos_disponibles = sorted(df_clean["Segmento"].unique().tolist())
sel_segmentos = st.sidebar.multiselect(
    "Segmento de Cliente:",
    options=segmentos_disponibles,
    default=[],
    placeholder="Todos los segmentos",
    key=f"seg_filter_{reset_key}"
)

# Filtro Región
regiones_disponibles = sorted(df_clean["Region"].unique().tolist())
sel_regiones = st.sidebar.multiselect(
    "Región Geográfica:",
    options=regiones_disponibles,
    default=[],
    placeholder="Todas las regiones",
    key=f"reg_filter_{reset_key}"
)

# Filtro de Productos
productos_disponibles = sorted(df_clean["Producto"].unique().tolist())
sel_productos = st.sidebar.multiselect(
    "Producto:",
    options=productos_disponibles,
    default=[],
    placeholder="Todos los productos",
    key=f"prod_filter_{reset_key}"
)


# ==========================================
# APLICACIÓN DE FILTROS AL DATAFRAME
# ==========================================
df_filtered = df_clean.copy()

# Filtrar fechas
if filtro_fechas and isinstance(filtro_fechas, tuple) and len(filtro_fechas) == 2:
    d_start, d_end = filtro_fechas
    df_filtered = df_filtered[
        (df_filtered["Fecha"].dt.date >= d_start) &
        (df_filtered["Fecha"].dt.date <= d_end)
    ]

if sel_categorias:
    df_filtered = df_filtered[df_filtered["Categoria"].isin(sel_categorias)]
if sel_subcats:
    df_filtered = df_filtered[df_filtered["Subcategoria"].isin(sel_subcats)]
if sel_segmentos:
    df_filtered = df_filtered[df_filtered["Segmento"].isin(sel_segmentos)]
if sel_regiones:
    df_filtered = df_filtered[df_filtered["Region"].isin(sel_regiones)]
if sel_productos:
    df_filtered = df_filtered[df_filtered["Producto"].isin(sel_productos)]

# Manejo de dataframe vacío tras filtros
if df_filtered.empty:
    st.error("⚠️ No hay registros que coincidan con la combinación de filtros seleccionada. Ajuste o restablezca los filtros en el panel lateral.")
    st.stop()


# Período previo para comparativas históricas (mismo número de días hacia atrás si hay fecha)
df_prev = None
if filtro_fechas and isinstance(filtro_fechas, tuple) and len(filtro_fechas) == 2:
    d_start, d_end = filtro_fechas
    duracion = (d_end - d_start).days
    prev_d_end = d_start - pd.Timedelta(days=1)
    prev_d_start = prev_d_end - pd.Timedelta(days=duracion)
    df_prev = df_clean[
        (df_clean["Fecha"].dt.date >= prev_d_start) &
        (df_clean["Fecha"].dt.date <= prev_d_end)
    ]
    if sel_categorias:
        df_prev = df_prev[df_prev["Categoria"].isin(sel_categorias)]
    if sel_subcats:
        df_prev = df_prev[df_prev["Subcategoria"].isin(sel_subcats)]
    if sel_segmentos:
        df_prev = df_prev[df_prev["Segmento"].isin(sel_segmentos)]
    if sel_regiones:
        df_prev = df_prev[df_prev["Region"].isin(sel_regiones)]
    if sel_productos:
        df_prev = df_prev[df_prev["Producto"].isin(sel_productos)]


# Cálculo de KPIs consolidados
kpis = compute_kpis(df_filtered, df_prev)


# ==========================================
# ENCABEZADO Y TARJETAS KPI EJECUTIVAS
# ==========================================
st.title("📈 Dashboard Ejecutivo de Rentabilidad Comercial")

# Subtítulo con contexto del período y filtros activos
sub_txt = f"**Registros Analizados:** {len(df_filtered):,} | **Total Base:** {len(df_clean):,}"
if filtro_fechas and isinstance(filtro_fechas, tuple) and len(filtro_fechas) == 2:
    sub_txt += f" | **Período:** {filtro_fechas[0].strftime('%d/%m/%Y')} al {filtro_fechas[1].strftime('%d/%m/%Y')}"
st.caption(sub_txt)

# Render de Tarjetas KPI
k1, k2, k3, k4, k5, k6 = st.columns(6)

with k1:
    delta_v_txt = f"{kpis['var_ventas']:+.1f}% vs ant." if kpis['var_ventas'] is not None else None
    st.metric(
        label="Ventas Totales",
        value=format_currency(kpis["ventas"], simbolo),
        delta=delta_v_txt
    )

with k2:
    st.metric(
        label="Costo Total",
        value=format_currency(kpis["costo"], simbolo),
        delta=None
    )

with k3:
    delta_u_txt = f"{kpis['var_utilidad']:+.1f}% vs ant." if kpis['var_utilidad'] is not None else None
    st.metric(
        label="Utilidad Bruta",
        value=format_currency(kpis["utilidad"], simbolo),
        delta=delta_u_txt
    )

with k4:
    delta_m_txt = f"{kpis['var_margen']:+.1f} pts" if kpis['var_margen'] is not None else None
    st.metric(
        label="Margen de Utilidad",
        value=format_percent(kpis["margen"]),
        delta=delta_m_txt
    )

with k5:
    st.metric(
        label="Unidades Vendidas",
        value=f"{kpis['cantidad']:,.0f}"
    )

with k6:
    st.metric(
        label="Ticket Promedio",
        value=format_currency(kpis["ticket_promedio"], simbolo)
    )

st.divider()


# ==========================================
# PESTAÑAS PRINCIPALES DEL DASHBOARD
# ==========================================
tab_cat, tab_seg, tab_reg, tab_prod, tab_matriz, tab_tiempo, tab_hallazgos, tab_calidad, tab_export = st.tabs([
    "📦 Categorías y Subcategorías",
    "👥 Segmentos de Cliente",
    "🗺️ Análisis Regional",
    "🏷️ Rentabilidad de Productos",
    "🎯 Matriz Volumen vs Margen",
    "📅 Evolución Temporal",
    "💡 Hallazgos y Recomendaciones",
    "🛡️ Calidad de Datos",
    "📥 Exportar Resultados"
])


# ----------------------------------------------------
# 1. PESTAÑA: CATEGORÍAS Y SUBCATEGORÍAS
# ----------------------------------------------------
with tab_cat:
    st.subheader("Rentabilidad por Categoría y Subcategoría de Producto")
    st.markdown("Evalúe qué líneas de negocio generan el mayor margen neto versus aquellas de alto volumen con márgenes deprimidos.")

    df_cat = aggregate_by_dimension(df_filtered, ["Categoria"])
    df_subcat = aggregate_by_dimension(df_filtered, ["Categoria", "Subcategoria"])

    c_c1, c_c2 = st.columns(2)
    with c_c1:
        fig_cat_util = bar_chart_metric(df_cat, "Categoria", "Utilidad", "Utilidad por Categoría", False, simbolo)
        st.plotly_chart(fig_cat_util, use_container_width=True)
    with c_c2:
        fig_cat_margen = bar_chart_metric(df_cat, "Categoria", "Margen_%", "Margen de Utilidad (%) por Categoría", True, simbolo)
        st.plotly_chart(fig_cat_margen, use_container_width=True)

    st.plotly_chart(comparison_bar_grouped(df_cat, "Categoria", simbolo), use_container_width=True)

    st.markdown("#### Tabla Comparativa Consolidada por Categoría")
    df_cat_display = df_cat[[
        "Categoria", "Ventas", "Costo", "Utilidad", "Margen_%", "Cantidad",
        "Part_Ventas_%", "Part_Utilidad_%"
    ]].copy()
    
    st.dataframe(
        df_cat_display.style.format({
            "Ventas": lambda v: format_currency(v, simbolo),
            "Costo": lambda v: format_currency(v, simbolo),
            "Utilidad": lambda v: format_currency(v, simbolo),
            "Margen_%": lambda v: format_percent(v),
            "Cantidad": "{:,.0f}",
            "Part_Ventas_%": lambda v: format_percent(v),
            "Part_Utilidad_%": lambda v: format_percent(v) if pd.notna(v) else "N/D"
        }).background_gradient(subset=["Margen_%"], cmap="RdYlGn"),
        use_container_width=True
    )

    st.divider()
    st.markdown("#### Desglose por Subcategorías")

    # Rankings de subcategorías
    sc_col1, sc_col2 = st.columns(2)
    with sc_col1:
        st.markdown("**Top 5 Subcategorías con Mayor Utilidad:**")
        top_subcats = df_subcat.sort_values(by="Utilidad", ascending=False).head(5)
        st.dataframe(
            top_subcats[["Subcategoria", "Categoria", "Ventas", "Utilidad", "Margen_%"]].style.format({
                "Ventas": lambda v: format_currency(v, simbolo),
                "Utilidad": lambda v: format_currency(v, simbolo),
                "Margen_%": lambda v: format_percent(v)
            }),
            use_container_width=True
        )

    with sc_col2:
        st.markdown("**Top 5 Subcategorías con Menor Utilidad / Pérdidas:**")
        worst_subcats = df_subcat.sort_values(by="Utilidad", ascending=True).head(5)
        st.dataframe(
            worst_subcats[["Subcategoria", "Categoria", "Ventas", "Utilidad", "Margen_%"]].style.format({
                "Ventas": lambda v: format_currency(v, simbolo),
                "Utilidad": lambda v: format_currency(v, simbolo),
                "Margen_%": lambda v: format_percent(v)
            }),
            use_container_width=True
        )

    # Detalle filtrable por categoría específica
    cat_focus = st.selectbox("Explorar subcategorías y productos de una categoría específica:", ["Todas"] + categorias_disponibles)
    if cat_focus != "Todas":
        sub_drill = df_subcat[df_subcat["Categoria"] == cat_focus]
    else:
        sub_drill = df_subcat

    fig_sub_bar = bar_chart_metric(sub_drill, "Subcategoria", "Margen_%", f"Margen (%) por Subcategoría ({cat_focus})", True, simbolo)
    st.plotly_chart(fig_sub_bar, use_container_width=True)


# ----------------------------------------------------
# 2. PESTAÑA: SEGMENTOS DE CLIENTE
# ----------------------------------------------------
with tab_seg:
    st.subheader("Análisis de Rentabilidad por Segmento de Clientes")
    st.markdown("Compare el rendimiento de cada segmento en volumen de facturación, utilidad neta, ticket promedio y política de descuentos.")

    df_seg = aggregate_by_dimension(df_filtered, ["Segmento"])

    s1, s2 = st.columns(2)
    with s1:
        st.plotly_chart(bar_chart_metric(df_seg, "Segmento", "Utilidad", "Utilidad por Segmento", False, simbolo), use_container_width=True)
    with s2:
        st.plotly_chart(bar_chart_metric(df_seg, "Segmento", "Margen_%", "Margen (%) por Segmento", True, simbolo), use_container_width=True)

    st.markdown("#### Clasificación Detallada de Segmentos")
    st.dataframe(
        df_seg[[
            "Segmento", "Ventas", "Costo", "Utilidad", "Margen_%",
            "Cantidad", "Ticket_Promedio", "Descuento_Promedio", "Part_Ventas_%", "Part_Utilidad_%"
        ]].style.format({
            "Ventas": lambda v: format_currency(v, simbolo),
            "Costo": lambda v: format_currency(v, simbolo),
            "Utilidad": lambda v: format_currency(v, simbolo),
            "Margen_%": lambda v: format_percent(v),
            "Cantidad": "{:,.0f}",
            "Ticket_Promedio": lambda v: format_currency(v, simbolo),
            "Descuento_Promedio": "{:.2f}%",
            "Part_Ventas_%": lambda v: format_percent(v),
            "Part_Utilidad_%": lambda v: format_percent(v) if pd.notna(v) else "N/D"
        }).background_gradient(subset=["Margen_%"], cmap="RdYlGn"),
        use_container_width=True
    )

    # Subcategorías más rentables por segmento seleccionado
    st.markdown("#### Subcategorías más rentables según el Segmento:")
    seg_chosen = st.selectbox("Seleccione segmento para profundizar:", df_seg["Segmento"].unique())
    seg_filtered_df = df_filtered[df_filtered["Segmento"] == seg_chosen]
    seg_subcat = aggregate_by_dimension(seg_filtered_df, ["Subcategoria"]).sort_values(by="Utilidad", ascending=False).head(8)
    
    st.plotly_chart(
        bar_chart_metric(seg_subcat, "Subcategoria", "Utilidad", f"Top Subcategorías en Segmento '{seg_chosen}'", False, simbolo),
        use_container_width=True
    )


# ----------------------------------------------------
# 3. PESTAÑA: ANÁLISIS REGIONAL
# ----------------------------------------------------
with tab_reg:
    st.subheader("Evaluación de Rentabilidad Geográfica por Región")
    st.markdown("Examine el aporte de cada territorio geográfico a los ingresos y beneficios comerciales de la organización.")

    df_reg = aggregate_by_dimension(df_filtered, ["Region"])

    r1, r2 = st.columns(2)
    with r1:
        st.plotly_chart(bar_chart_metric(df_reg, "Region", "Utilidad", "Utilidad por Región", False, simbolo), use_container_width=True)
    with r2:
        st.plotly_chart(bar_chart_metric(df_reg, "Region", "Margen_%", "Margen de Utilidad (%) por Región", True, simbolo), use_container_width=True)

    st.plotly_chart(comparison_bar_grouped(df_reg, "Region", simbolo), use_container_width=True)

    st.markdown("#### Matriz Geográfica Consolidada")
    st.dataframe(
        df_reg[[
            "Region", "Ventas", "Costo", "Utilidad", "Margen_%",
            "Cantidad", "Descuento_Promedio", "Part_Ventas_%", "Part_Utilidad_%"
        ]].style.format({
            "Ventas": lambda v: format_currency(v, simbolo),
            "Costo": lambda v: format_currency(v, simbolo),
            "Utilidad": lambda v: format_currency(v, simbolo),
            "Margen_%": lambda v: format_percent(v),
            "Cantidad": "{:,.0f}",
            "Descuento_Promedio": "{:.2f}%",
            "Part_Ventas_%": lambda v: format_percent(v),
            "Part_Utilidad_%": lambda v: format_percent(v) if pd.notna(v) else "N/D"
        }).background_gradient(subset=["Margen_%"], cmap="RdYlGn"),
        use_container_width=True
    )

    # Detalle por Estado / Ciudad si están presentes
    if "Estado" in df_filtered.columns and (df_filtered["Estado"] != "No Especificado").any():
        st.markdown("#### Top 10 Estados / Provincias con Mayor y Menor Utilidad")
        df_est = aggregate_by_dimension(df_filtered, ["Estado"])
        e1, e2 = st.columns(2)
        with e1:
            st.markdown("**10 Estados con Mayor Utilidad:**")
            st.dataframe(
                df_est.sort_values(by="Utilidad", ascending=False).head(10)[["Estado", "Ventas", "Utilidad", "Margen_%"]].style.format({
                    "Ventas": lambda v: format_currency(v, simbolo),
                    "Utilidad": lambda v: format_currency(v, simbolo),
                    "Margen_%": lambda v: format_percent(v)
                }),
                use_container_width=True
            )
        with e2:
            st.markdown("**10 Estados con Menor Utilidad:**")
            st.dataframe(
                df_est.sort_values(by="Utilidad", ascending=True).head(10)[["Estado", "Ventas", "Utilidad", "Margen_%"]].style.format({
                    "Ventas": lambda v: format_currency(v, simbolo),
                    "Utilidad": lambda v: format_currency(v, simbolo),
                    "Margen_%": lambda v: format_percent(v)
                }),
                use_container_width=True
            )


# ----------------------------------------------------
# 4. PESTAÑA: RENTABILIDAD DE PRODUCTOS
# ----------------------------------------------------
with tab_prod:
    st.subheader("Análisis Individual y Rankings de Rentabilidad por Producto")
    st.markdown("Consulte el catálogo de productos con desglose comercial exhaustivo, identificando referencias tractoras y destructoras de margen.")

    df_prod = aggregate_by_dimension(df_filtered, ["Producto", "Categoria", "Subcategoria"])

    # Rankings
    rk1, rk2 = st.columns(2)
    with rk1:
        st.markdown("🏆 **Top 10 Productos con Mayor Utilidad (Generadores Clave):**")
        top10_prod = df_prod.sort_values(by="Utilidad", ascending=False).head(10)
        st.dataframe(
            top10_prod[["Producto", "Subcategoria", "Ventas", "Utilidad", "Margen_%", "Cantidad"]].style.format({
                "Ventas": lambda v: format_currency(v, simbolo),
                "Utilidad": lambda v: format_currency(v, simbolo),
                "Margen_%": lambda v: format_percent(v),
                "Cantidad": "{:,.0f}"
            }),
            use_container_width=True
        )

    with rk2:
        st.markdown("🚨 **Top 10 Productos con Menor Utilidad / Mayor Pérdida:**")
        worst10_prod = df_prod.sort_values(by="Utilidad", ascending=True).head(10)
        st.dataframe(
            worst10_prod[["Producto", "Subcategoria", "Ventas", "Utilidad", "Margen_%", "Cantidad"]].style.format({
                "Ventas": lambda v: format_currency(v, simbolo),
                "Utilidad": lambda v: format_currency(v, simbolo),
                "Margen_%": lambda v: format_percent(v),
                "Cantidad": "{:,.0f}"
            }),
            use_container_width=True
        )

    st.markdown("#### Catálogo Completo de Productos Filtrados")
    busqueda_prod = st.text_input("Filtrar por nombre de producto:", placeholder="Ej: Copier, Phone, Chair...")
    
    prod_view = df_prod.copy()
    if busqueda_prod:
        prod_view = prod_view[prod_view["Producto"].str.contains(busqueda_prod, case=False, na=False)]

    st.dataframe(
        prod_view[[
            "Producto", "Categoria", "Subcategoria", "Ventas", "Costo",
            "Utilidad", "Margen_%", "Cantidad", "Precio_Promedio", "Descuento_Promedio", "Part_Ventas_%", "Part_Utilidad_%"
        ]].sort_values(by="Utilidad", ascending=False).style.format({
            "Ventas": lambda v: format_currency(v, simbolo),
            "Costo": lambda v: format_currency(v, simbolo),
            "Utilidad": lambda v: format_currency(v, simbolo),
            "Margen_%": lambda v: format_percent(v),
            "Cantidad": "{:,.0f}",
            "Precio_Promedio": lambda v: format_currency(v, simbolo),
            "Descuento_Promedio": "{:.2f}%",
            "Part_Ventas_%": lambda v: format_percent(v),
            "Part_Utilidad_%": lambda v: format_percent(v) if pd.notna(v) else "N/D"
        }).background_gradient(subset=["Margen_%"], cmap="RdYlGn"),
        use_container_width=True
    )


# ----------------------------------------------------
# 5. PESTAÑA: MATRIZ DE RENTABILIDAD (VOLUMEN VS MARGEN)
# ----------------------------------------------------
with tab_matriz:
    st.subheader("Matriz Estratégica de Rentabilidad (Volumen vs Margen)")
    st.markdown("""
    Esta matriz clasifica los elementos en 4 cuadrantes estratégicos para la toma de decisiones comerciales:
    1. **Alto Volumen / Alto Margen (Estrellas):** Máxima prioridad de abastecimiento y protección competitiva.
    2. **Alto Volumen / Bajo Margen (Generadores de Flujo):** Revisar precios y descuentos sin estrangular la rotación.
    3. **Bajo Volumen / Alto Margen (Nichos Rentables):** Oportunidades para escalar con inversión en visibilidad o promociones selectivas.
    4. **Bajo Volumen / Bajo Margen (Revisión Crítica):** Evaluar liquidación, sustitución o rediseño de oferta.
    """)

    m_col1, m_col2, m_col3 = st.columns(3)
    with m_col1:
        nivel_analisis = st.radio("Nivel de Análisis:", ["Subcategorías", "Categorías", "Productos"], horizontal=True)
    with m_col2:
        tipo_umbral_ventas = st.selectbox("Criterio Umbral Ventas:", ["Mediana (Recomendado)", "Media Aritmética"])
    with m_col3:
        umbral_margen_fijo = st.slider("Umbral Mínimo de Margen Deseado (%):", min_value=-20.0, max_value=50.0, value=15.0, step=1.0)

    use_median_sales = (tipo_umbral_ventas == "Mediana (Recomendado)")

    if nivel_analisis == "Subcategorías":
        df_matrix_input = aggregate_by_dimension(df_filtered, ["Subcategoria"])
        dim_matrix_col = "Subcategoria"
    elif nivel_analisis == "Categorías":
        df_matrix_input = aggregate_by_dimension(df_filtered, ["Categoria"])
        dim_matrix_col = "Categoria"
    else:
        df_matrix_input = aggregate_by_dimension(df_filtered, ["Producto"])
        dim_matrix_col = "Producto"

    fig_matrix, s_th, m_th = profit_matrix_chart(
        df_matrix_input,
        dim_matrix_col,
        simbolo,
        split_sales_median=use_median_sales,
        split_margin_median=False,
        margin_threshold=umbral_margen_fijo
    )
    st.plotly_chart(fig_matrix, use_container_width=True)

    st.info(f"📌 **Parámetros de segmentación aplicados:** Umbral de Ventas = {format_currency(s_th, simbolo)} | Umbral de Margen = {m_th:.1f}%")


# ----------------------------------------------------
# 6. PESTAÑA: EVOLUCIÓN TEMPORAL
# ----------------------------------------------------
with tab_tiempo:
    st.subheader("Análisis de Tendencias y Evolución Temporal")
    if df_filtered["Fecha"].isna().all():
        st.warning("No se cuenta con fechas válidas para trazar la evolución temporal.")
    else:
        st.markdown("Evalúe el comportamiento histórico mensual o trimestral de ventas, utilidades, costos y márgenes.")
        
        t_col1, t_col2 = st.columns(2)
        with t_col1:
            frecuencia_sel = st.radio("Periodicidad de Agrupación:", ["Mensual (Año_Mes)", "Trimestral (Trimestre)"], horizontal=True)
            freq_col_name = "Año_Mes" if "Mensual" in frecuencia_sel else "Trimestre"

        fig_time = time_series_chart(df_filtered, freq_col_name, simbolo)
        st.plotly_chart(fig_time, use_container_width=True)

        st.divider()
        st.markdown("#### Sensibilidad Comercial: Efecto de los Descuentos en el Margen")
        st.plotly_chart(discount_impact_chart(df_filtered, simbolo), use_container_width=True)


# ----------------------------------------------------
# 7. PESTAÑA: HALLAZGOS Y RECOMENDACIONES
# ----------------------------------------------------
with tab_hallazgos:
    st.subheader("Hallazgos Automatizados y Recomendaciones de Decisión")
    st.markdown("Diagnóstico comercial sintetizado directamente de la evidencia empírica de los datos filtrados:")

    findings_list = generate_recommendations(df_filtered, simbolo)

    for item in findings_list:
        with st.container():
            st.markdown(f"### {item['titulo']}")
            badge_color = "#DC2626" if item["badge"] == "danger" else "#D97706" if item["badge"] == "warning" else "#059669"
            st.markdown(f"<span style='background-color:{badge_color}; color:white; padding:3px 8px; border-radius:4px; font-size:0.8rem;'>{item['tipo']}</span> — <b>{item['categoria']}</b>", unsafe_allow_html=True)
            st.markdown(f"**Dato Cuantitativo Clave:** `{item['cifra']}`")
            st.write(item["detalle"])
            st.markdown(f"**💡 Hipótesis / Plan de Acción Recomendado:** _{item['hipotesis']}_")
            st.divider()


# ----------------------------------------------------
# 8. PESTAÑA: CALIDAD DE DATOS Y DIAGNÓSTICO
# ----------------------------------------------------
with tab_calidad:
    st.subheader("Auditoría y Control de Calidad de Datos")
    st.markdown("Transparencia en la consistencia de la información procesada:")

    q1, q2, q3, q4 = st.columns(4)
    with q1:
        st.metric("Total Registros", f"{diag['total_registros']:,}")
    with q2:
        st.metric("Registros Duplicados", f"{diag['duplicados']:,}")
    with q3:
        st.metric("Ventas <= 0", f"{diag['ventas_cero_o_negativas']:,}")
    with q4:
        st.metric("Registros con Pérdida", f"{diag['registros_con_perdida']:,}")

    if diag["advertencias"]:
        st.warning("⚠️ **Observaciones encontradas durante el proceso de carga:**")
        for adv in diag["advertencias"]:
            st.write(f"- {adv}")
    else:
        st.success("✅ Estructura de datos íntegra y sin inconsistencias críticas detectadas.")

    if diag["nulos_por_campo"]:
        st.write("Valores nulos identificados por columna:")
        st.json(diag["nulos_por_campo"])

    st.markdown("#### Muestra de Registros Procesados")
    st.dataframe(df_filtered.head(15), use_container_width=True)


# ----------------------------------------------------
# 9. PESTAÑA: EXPORTACIÓN DE RESULTADOS
# ----------------------------------------------------
with tab_export:
    st.subheader("Exportación de Datos e Informes Ejecutivos")
    st.markdown("Descargue los resultados analizados con los filtros aplicados en formatos compatibles con Excel y herramientas de BI.")

    # Generar DataFrames agregados para exportar
    exp_resumen = pd.DataFrame([{
        "Ventas Totales": kpis["ventas"],
        "Costo Total": kpis["costo"],
        "Utilidad Neta": kpis["utilidad"],
        "Margen (%)": kpis["margen"],
        "Cantidad Unidades": kpis["cantidad"],
        "Ticket Promedio": kpis["ticket_promedio"],
        "Registros": len(df_filtered)
    }])

    exp_cat = aggregate_by_dimension(df_filtered, ["Categoria"])
    exp_subcat = aggregate_by_dimension(df_filtered, ["Categoria", "Subcategoria"])
    exp_seg = aggregate_by_dimension(df_filtered, ["Segmento"])
    exp_reg = aggregate_by_dimension(df_filtered, ["Region"])
    exp_prod = aggregate_by_dimension(df_filtered, ["Producto", "Categoria", "Subcategoria"]).sort_values(by="Utilidad", ascending=False).head(100)

    # Botón descarga Excel multipestaña
    excel_bytes = export_to_excel_workbook(
        exp_resumen, exp_cat, exp_subcat, exp_seg, exp_reg, exp_prod
    )

    st.download_button(
        label="📊 Descargar Informe Ejecutivo Completo en Excel (.xlsx)",
        data=excel_bytes,
        file_name="Informe_Rentabilidad_Ejecutivo.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )

    st.divider()
    st.markdown("#### Exportar Base de Datos Filtrada a CSV:")
    csv_bytes = export_to_csv(df_filtered)
    st.download_button(
        label="📄 Descargar Base de Datos Filtrada (.csv)",
        data=csv_bytes,
        file_name="Base_Ventas_Rentabilidad_Filtrada.csv",
        mime="text/csv",
        use_container_width=True
    )
