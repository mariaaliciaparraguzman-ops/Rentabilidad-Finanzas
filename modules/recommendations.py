"""
Módulo de Generación de Hallazgos y Recomendaciones Automáticas
Sustentadas estrictamente con datos cuantitativos observados.
Distingue hechos observados, posibles causas e hipótesis.
"""

import pandas as pd
import numpy as np
from typing import List, Dict


def generate_recommendations(df: pd.DataFrame, symbol: str = "$") -> List[Dict[str, str]]:
    """
    Analiza los datos filtrados y produce hallazgos comerciales y financieros fundamentados.
    """
    findings = []
    if df.empty:
        return findings

    total_ventas = df["Ventas"].sum()
    total_utilidad = df["Utilidad"].sum()
    margen_global = (total_utilidad / total_ventas * 100.0) if total_ventas > 0 else 0.0

    # 1. Concentración de Utilidad por Categoría
    cat_summary = df.groupby("Categoria").agg(
        Ventas=("Ventas", "sum"),
        Utilidad=("Utilidad", "sum")
    ).reset_index()
    cat_summary["Margen_%"] = (cat_summary["Utilidad"] / cat_summary["Ventas"]) * 100
    cat_top = cat_summary.sort_values(by="Utilidad", ascending=False).iloc[0]
    cat_worst_margin = cat_summary.sort_values(by="Margen_%").iloc[0]
    
    part_top_cat = (cat_top["Utilidad"] / total_utilidad * 100) if total_utilidad > 0 else 0
    findings.append({
        "categoria": "Concentración de Categorías",
        "tipo": "Hecho Observado",
        "badge": "info",
        "titulo": f"Concentración de Utilidad en {cat_top['Categoria']}",
        "cifra": f"{part_top_cat:.1f}% de la utilidad total ({symbol} {cat_top['Utilidad']:,.2f})",
        "detalle": (
            f"La categoría '{cat_top['Categoria']}' aporta {part_top_cat:.1f}% de la utilidad neta con un margen de {cat_top['Margen_%']:.1f}%. "
            f"En contraste, la categoría '{cat_worst_margin['Categoria']}' reporta el margen más bajo ({cat_worst_margin['Margen_%']:.1f}%) "
            f"a pesar de generar ventas por {symbol} {cat_worst_margin['Ventas']:,.2f}."
        ),
        "hipotesis": "Evaluar si la categoría de bajo margen tiene costos de insumos elevados o una política de descuentos excesiva."
    })

    # 2. Subcategorías Críticas con Pérdida o Márgenes Mínimos
    sub_summary = df.groupby("Subcategoria").agg(
        Ventas=("Ventas", "sum"),
        Utilidad=("Utilidad", "sum")
    ).reset_index()
    sub_summary["Margen_%"] = (sub_summary["Utilidad"] / sub_summary["Ventas"]) * 100
    sub_perdidas = sub_summary[sub_summary["Utilidad"] < 0].sort_values(by="Utilidad")

    if not sub_perdidas.empty:
        peor_sub = sub_perdidas.iloc[0]
        findings.append({
            "categoria": "Subcategorías Críticas",
            "tipo": "Alerta Financiera",
            "badge": "danger",
            "titulo": f"Subcategoría con Pérdida Neta: {peor_sub['Subcategoria']}",
            "cifra": f"Pérdida acumulada: {symbol} {abs(peor_sub['Utilidad']):,.2f} (Margen {peor_sub['Margen_%']:.1f}%)",
            "detalle": (
                f"Existen {len(sub_perdidas)} subcategorías operando con pérdidas en el período filtrado. "
                f"La más comprometida es '{peor_sub['Subcategoria']}', que a pesar de facturar {symbol} {peor_sub['Ventas']:,.2f}, destruye valor comercial."
            ),
            "hipotesis": "Revisar la estructura de costos directos, renegociar con proveedores o suprimir referencias no estratégicas dentro de esta subcategoría."
        })

    # 3. Productos individuales con mayor destrucción de valor (pérdidas)
    prod_summary = df.groupby(["Producto", "Categoria", "Subcategoria"]).agg(
        Ventas=("Ventas", "sum"),
        Utilidad=("Utilidad", "sum"),
        Cantidad=("Cantidad", "sum"),
        Descuento_Medio=("Descuento", "mean")
    ).reset_index()
    prods_perdida = prod_summary[prod_summary["Utilidad"] < 0].sort_values(by="Utilidad")

    if not prods_perdida.empty:
        peor_prod = prods_perdida.iloc[0]
        total_perdida_prods = prods_perdida["Utilidad"].sum()
        findings.append({
            "categoria": "Productos en Pérdida",
            "tipo": "Hecho Observado",
            "badge": "danger",
            "titulo": f"{len(prods_perdida)} Productos Generan Pérdidas Comerciales",
            "cifra": f"Impacto total negativo: {symbol} {abs(total_perdida_prods):,.2f}",
            "detalle": (
                f"El producto con mayor pérdida es '{peor_prod['Producto']}' ({peor_prod['Subcategoria']}) con una pérdida de {symbol} {abs(peor_prod['Utilidad']):,.2f} "
                f"y un descuento promedio aplicado del {peor_prod['Descuento_Medio']*100:.1f}%."
            ),
            "hipotesis": "Validar si el precio de venta unitario está por debajo del costo de adquisición o si las promociones comerciales redujeron el precio bajo el umbral de rentabilidad."
        })

    # 4. Impacto directo de Descuentos en la Rentabilidad
    if "Descuento" in df.columns:
        sin_desc = df[df["Descuento"] == 0]
        con_desc = df[df["Descuento"] > 0]
        
        margen_sin_desc = (sin_desc["Utilidad"].sum() / sin_desc["Ventas"].sum() * 100) if not sin_desc.empty and sin_desc["Ventas"].sum() > 0 else 0
        margen_con_desc = (con_desc["Utilidad"].sum() / con_desc["Ventas"].sum() * 100) if not con_desc.empty and con_desc["Ventas"].sum() > 0 else 0
        
        # Descuentos altos > 20%
        altos_desc = df[df["Descuento"] >= 0.30]
        utilidad_altos_desc = altos_desc["Utilidad"].sum() if not altos_desc.empty else 0
        
        findings.append({
            "categoria": "Política de Descuentos",
            "tipo": "Hecho Observado",
            "badge": "warning",
            "titulo": "Erosión de Margen por Descuentos Comerciales",
            "cifra": f"Margen sin descuento: {margen_sin_desc:.1f}% vs Con descuento: {margen_con_desc:.1f}%",
            "detalle": (
                f"Las ventas sin descuento mantienen un margen del {margen_sin_desc:.1f}%, mientras que los pedidos con descuento caen a {margen_con_desc:.1f}%. "
                f"Además, en ventas con descuento igual o superior al 30%, la utilidad neta es de {symbol} {utilidad_altos_desc:,.2f}."
            ),
            "hipotesis": "Fijar un tope máximo de descuento del 20% en pedidos ordinarios para evitar que la operación comercial entre en zona de margen negativo."
        })

    # 5. Segmentos de Clientes con Mejor Desempeño
    if "Segmento" in df.columns and df["Segmento"].nunique() > 1:
        seg_summary = df.groupby("Segmento").agg(
            Ventas=("Ventas", "sum"),
            Utilidad=("Utilidad", "sum")
        ).reset_index()
        seg_summary["Margen_%"] = (seg_summary["Utilidad"] / seg_summary["Ventas"]) * 100
        seg_best = seg_summary.sort_values(by="Margen_%", ascending=False).iloc[0]
        
        findings.append({
            "categoria": "Segmentación de Clientes",
            "tipo": "Hecho Observado",
            "badge": "success",
            "titulo": f"Segmento Más Rentable: {seg_best['Segmento']}",
            "cifra": f"Margen de {seg_best['Margen_%']:.1f}% (Utilidad: {symbol} {seg_best['Utilidad']:,.2f})",
            "detalle": (
                f"El segmento '{seg_best['Segmento']}' ofrece la mayor eficiencia de margen sobre ventas, superando el promedio general de {margen_global:.1f}%."
            ),
            "hipotesis": "Focalizar estrategias de fidelización e inversión comercial en este segmento para maximizar el retorno sobre la inversión en marketing."
        })

    # 6. Región con Oportunidades de Mejora
    if "Region" in df.columns and df["Region"].nunique() > 1:
        reg_summary = df.groupby("Region").agg(
            Ventas=("Ventas", "sum"),
            Utilidad=("Utilidad", "sum")
        ).reset_index()
        reg_summary["Margen_%"] = (reg_summary["Utilidad"] / reg_summary["Ventas"]) * 100
        reg_peor = reg_summary.sort_values(by="Margen_%").iloc[0]
        
        findings.append({
            "categoria": "Geografía Comercial",
            "tipo": "Hecho Observado",
            "badge": "warning",
            "titulo": f"Bajo Margen en Región {reg_peor['Region']}",
            "cifra": f"Margen de {reg_peor['Margen_%']:.1f}% frente al global de {margen_global:.1f}%",
            "detalle": (
                f"La región '{reg_peor['Region']}' genera {symbol} {reg_peor['Ventas']:,.2f} en ventas pero su rentabilidad relativa está rezagada respecto a las demás zonas."
            ),
            "hipotesis": "Verificar si existen sobrecostos de flete/logística o condiciones de descuento regionales más agresivas que deterioren el margen."
        })

    return findings
