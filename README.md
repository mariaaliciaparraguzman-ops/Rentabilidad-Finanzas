# 📊 Dashboard de Rentabilidad Comercial de Productos

Aplicación web analítica interactiva desarrollada con **Python, Streamlit, Pandas y Plotly**, diseñada para la evaluación exhaustiva de la rentabilidad comercial desde 5 perspectivas estratégicas: **General, Categorías, Subcategorías, Segmentos de Clientes y Regiones Geográficas**.

---

## 🚀 1. Ejecución Rápida en Windows

La aplicación está lista para ejecutarse inmediatamente.

### Opción A (Doble Clic):
Haga doble clic en el archivo:
```text
C:\Users\DELL\Rentabilidad\ejecutar_dashboard.bat
```

### Opción B (Línea de Comandos / PowerShell):
```powershell
cd C:\Users\DELL\Rentabilidad
& "C:\Users\DELL\python311\python.exe" -m streamlit run app.py --server.port 8502
```
Luego abra en su navegador web: [http://localhost:8502](http://localhost:8502)

*(Nota: Se asignó el puerto 8502 para mantener activo en paralelo el dashboard existente de Empresa Andina sin conflictos).*

---

## 📂 2. Carga y Preparación de Datos

1. **Base de Datos Precargada:** El dashboard detecta e inicia automáticamente con los 9,994 registros del archivo comercial `base de datos - Superstore.xls`.
2. **Carga de Archivos Propios:** En la barra lateral izquierda, puede cargar cualquier archivo **Excel (.xlsx, .xls)** o **CSV**.
3. **Mapeo Inteligente y Flexible:** Si sus columnas tienen nombres distintos, el sistema cuenta con un expansor de **Asignación de Columnas** que permite seleccionar equivalencias en tiempo real sin modificar su archivo original.
4. **Auditoría de Calidad:** La pestaña **🛡️ Calidad de Datos** audita nulos, duplicados, registros con pérdidas, ventas <= 0 y fechas inválidas sin borrar datos silenciosamente.

---

## 🧮 3. Definición y Fórmulas Financieras Implementadas

- **Ventas Totales:** Suma de ingresos netos (\( \sum \text{Ventas} \)).
- **Costo Total:** Costo de ventas (\( \sum \text{Costo} = \sum (\text{Ventas} - \text{Utilidad}) \)).
- **Utilidad Bruta:** Beneficio económico comercial (\( \sum \text{Utilidad} \)).
- **Margen de Utilidad (%):**
  $$\text{Margen (\%)} = \left(\frac{\text{Utilidad}}{\text{Ventas}}\right) \times 100$$
- **Cantidad Total:** Suma de unidades físicas vendidas (\( \sum \text{Cantidad} \)).
- **Precio Promedio Unitario:** \( \frac{\text{Ventas Totales}}{\text{Cantidad Total}} \)
- **Costo Promedio Unitario:** \( \frac{\text{Costo Total}}{\text{Cantidad Total}} \)
- **Ticket Promedio por Pedido:** \( \frac{\text{Ventas Totales}}{\text{Número de Pedidos Únicos}} \)
- **Participación en Ventas (%):** \( \frac{\text{Ventas Dimensión}}{\text{Ventas Totales Filtradas}} \times 100 \)
- **Participación en Utilidad (%):** \( \frac{\text{Utilidad Dimensión}}{\text{Utilidad Total Filtrada}} \times 100 \)
- **Variación Temporal (%):** \( \frac{\text{Valor Actual} - \text{Valor Anterior}}{|\text{Valor Anterior}|} \times 100 \)

---

## 🧩 4. Módulos y Funcionalidades del Dashboard

1. **Tarjetas KPI Ejecutivas:** Ventas, Costos, Utilidad, Margen %, Unidades y Ticket Promedio con comparativa histórica.
2. **Filtros Globales Dinámicos:** Selector de rango de fechas, categorías, subcategorías en cascada, segmentos, regiones geográficas y productos, con botón de restablecimiento total.
3. **Pestaña Categorías y Subcategorías:** Barras comparativas de ventas vs costos vs utilidades, ranking de subcategorías más y menos rentables, y drill-down interactivo.
4. **Pestaña Segmentos de Cliente:** Evaluación de márgenes, ticket promedio, descuentos aplicados y subcategorías preferidas por segmento.
5. **Pestaña Análisis Regional:** Comparativa territorial de margen y utilidad, con desglose a nivel de estados/ciudades.
6. **Pestaña Catálogo de Productos:** Top 10 productos con mayor utilidad, Top 10 destructores de margen (pérdidas) y buscador general.
7. **Pestaña Matriz Volumen vs Margen:** Diagrama de dispersión de 4 cuadrantes (Estrellas, Flujo, Nicho y Revisión) con umbrales configurables por mediana o media.
8. **Pestaña Evolución Temporal y Descuentos:** Gráfico mensual y trimestral combinado de ingresos vs margen %, junto a la curva de sensibilidad de descuentos.
9. **Pestaña Hallazgos y Recomendaciones:** Diagnóstico cuantitativo automatizado con diferenciación entre hechos observados e hipótesis de acción.
10. **Pestaña Exportación:** Generador de reportes consolidados en Excel multipestaña (`.xlsx`) y descarga de base filtrada (`.csv`).

---

## 📁 5. Estructura del Código

```text
Rentabilidad/
├── app.py                      # Aplicación principal Streamlit
├── requirements.txt            # Dependencias del proyecto
├── ejecutar_dashboard.bat      # Script de lanzamiento para Windows
├── README.md                   # Documentación técnica completa
├── .streamlit/
│   └── config.toml             # Configuración de tema visual y servidor
├── modules/
│   ├── data_loader.py          # Ingesta, mapeo inteligente y calidad de datos
│   ├── metrics.py              # Cálculos financieros, KPIs y agregaciones
│   ├── charts.py               # Visualizaciones ejecutivas con Plotly
│   ├── recommendations.py      # Generador de hallazgos y recomendaciones cuantitativas
│   └── exporter.py             # Exportador a Excel multipestaña y CSV
└── base de datos - Superstore.xls  # Dataset comercial integrado
```
