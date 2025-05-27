import pandas as pd
import plotly.express as px
from dash import Dash, dcc, html
from dash.dependencies import Input, Output

# Carga y preparación de datos
ventas = pd.read_csv('Ventas.csv', dtype=str, encoding='utf-8', sep=',')
vendedor = pd.read_csv('Vendedor.csv', dtype=str, encoding='utf-8', sep=';')
proveedor = pd.read_csv('Proveedores.csv', dtype=str, encoding='utf-8', sep=';')
producto = pd.read_csv('Estructura_Comercial.csv', dtype=str, encoding='utf-8', sep=';')
cliente = pd.read_csv('Clientes.csv', dtype=str, encoding='utf-8', sep=';')

# Copias para evitar modificar originales
ventas = ventas.copy()
vendedor = vendedor.copy()
proveedor = proveedor.copy()
producto = producto.copy()
cliente = cliente.copy()

# Selección columnas necesarias
cliente = cliente[['nit', 'nombre']]
producto = producto[['CODIGO', 'NOMBRE']]

# Merge para integrar nombres
ventas = ventas.merge(vendedor, how='left', left_on='Vendedor', right_on='codigo')
ventas = ventas.merge(cliente, how='left', left_on='Nit', right_on='nit')
ventas = ventas.merge(producto, how='left', left_on='Producto', right_on='CODIGO')

# Selección columnas finales y limpieza
ventas = ventas[['Fecha', 'nombre', 'NOMBRE', 'Nombre_Vendedor', 'TCantidad', 'TNeto', 'Mes', 'Anio']]
ventas["TCantidad"] = ventas["TCantidad"].str.replace(",", ".").str.strip()
ventas["TNeto"] = ventas["TNeto"].str.replace(",", ".").str.strip()
ventas["TCantidad"] = pd.to_numeric(ventas["TCantidad"], errors="coerce")
ventas["TNeto"] = pd.to_numeric(ventas["TNeto"], errors="coerce")
ventas.columns = ['Fecha', 'Cliente', 'Producto', 'Vendedor', 'Cantidad', 'Valor', 'Mes', 'Anio']

# Filtrar año 2024
ventas2024 = ventas[ventas['Anio'] == '2024']

# Agregados para gráficos
ventas_producto24 = ventas2024.groupby("Producto").agg(
    Unidades=("Cantidad", "sum"),
    Pesos=("Valor", "sum")
).reset_index()

ventas_cliente24 = ventas2024.groupby("Cliente").agg(
    Unidades=("Cantidad", "sum"),
    Pesos=("Valor", "sum")
).reset_index()

ventas_x_mes = ventas2024.groupby("Mes").agg(
    Pesos=("Valor", "sum")
).reset_index()
ventas_x_mes['Mes'] = ventas_x_mes['Mes'].astype(int)
ventas_x_mes = ventas_x_mes.sort_values('Mes').reset_index(drop=True)
ventas_x_mes['Mes'] = ventas_x_mes['Mes'].map({
    1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril', 5: 'Mayo', 6: 'Junio',
    7: 'Julio', 8: 'Agosto', 9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
})

ventas_vendedor24 = ventas2024.groupby("Vendedor").agg(
    Pesos=("Valor", "sum")
).reset_index()
ventas_vendedor24 = ventas_vendedor24.sort_values('Pesos', ascending=False).head(10).reset_index(drop=True)

# Pie chart vendedores
fig_vendedores = px.pie(
    ventas_vendedor24,
    names="Vendedor",
    values="Pesos",
    hole=0.3
)
fig_vendedores.update_traces(textposition='inside', textinfo='percent+label')
fig_vendedores.update_layout(
    height=500,
    margin=dict(l=40, r=40, t=50, b=40),
    font_color="black",
    font_family="Lato"
)

# Dash app
app = Dash(__name__)
server = app.server
app.title = "Dashboard de Ventas"

app.layout = html.Div([
    html.H1("Análisis de Ventas 2024", style={"textAlign": "center"}),

    html.Div([
        html.Label("Agrupar por:"),
        dcc.RadioItems(
            id="grupo-selector",
            options=[
                {"label": "Producto", "value": "producto"},
                {"label": "Cliente", "value": "Cliente"}
            ],
            value="producto",
            inline=True,
        ),
    ], style={"margin": "20px"}),

    html.Div([
        html.Label("Métrica:"),
        dcc.RadioItems(
            id="metrica-selector",
            options=[
                {"label": "Unidades", "value": "Unidades"},
                {"label": "Pesos", "value": "Pesos"}
            ],
            value="Unidades",
            inline=True
        ),
    ], style={"margin": "20px"}),

    html.Div([
        html.Label("Ver desde el número:"),
        dcc.Slider(
            id='inicio-slider',
            min=0,
            max=90,
            step=1,
            value=0,
            marks={0: "0", 25: "25", 50: "50", 75: "75"},
            tooltip={"placement": "bottom", "always_visible": True}
        )
    ], style={"margin": "30px"}),

    dcc.Graph(id="grafico-ventas"),

    html.H2("Ventas Mensuales Totales (Pesos)", style={"textAlign": "center", "marginTop": "60px"}),
    dcc.Graph(
        id="grafico-lineas-mensual",
        figure=px.line(ventas_x_mes, x="Mes", y="Pesos", markers=True).update_layout(
            xaxis_title="Mes",
            yaxis_title="Ventas en Pesos",
            height=400,
            margin=dict(l=40, r=40, t=40, b=40)
        )
    ),

    html.H2("Participación de Vendedores (2024)", style={"textAlign": "center", "marginTop": "60px"}),
    dcc.Graph(id="grafico-vendedores-pie", figure=fig_vendedores)

], style={'height': '1000px', "color": "black", "fontFamily": "'Nunito', sans-serif"})

@app.callback(
    Output("grafico-ventas", "figure"),
    Input("grupo-selector", "value"),
    Input("metrica-selector", "value"),
    Input("inicio-slider", "value")
)
def actualizar_grafico(grupo, metrica, inicio):
    if grupo == "producto":
        df = ventas_producto24.sort_values(by=metrica, ascending=False)
        eje_x = "Producto"
    else:
        df = ventas_cliente24.sort_values(by=metrica, ascending=False)
        eje_x = "Cliente"

    fin = inicio + 10
    df_vista = df.iloc[inicio:fin]

    fig = px.bar(df_vista, x=eje_x, y=metrica, title=f"Ventas por {grupo.capitalize()} ({metrica})")
    fig.update_layout(
        xaxis_title=eje_x,
        yaxis_title=metrica,
        xaxis_tickangle=-45,
        height=500,
        margin=dict(l=20, r=20, t=50, b=250),
    )
    fig.update_xaxes(tickfont=dict(size=10), automargin=True)

    return fig

if __name__ == '__main__':
    app.run(debug=True, port=8050)
