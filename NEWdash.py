!pip install dash plotly

from plotly.data import gapminder
from dash import dcc, html, Dash, callback, Input, Output, State
import plotly.express as px
import plotly.graph_objects as go

# 初始化 APP
css = ["https://cdn.jsdelivr.net/npm/bootstrap@5.3.1/dist/css/bootstrap.min.css"]
app = Dash(name="Gapminder Dashboard", external_stylesheets=css)
server = app.server  # 兼容部署

# 自定义 HTML + CSS
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>Gapminder Dashboard</title>
        {%favicon%}
        {%css%}
        <style>
            .header-description {
                color: #CFCFCF;
                margin: 4px auto;
                text-align: center;
                max-width: 384px;
                font-size: 18px;
                font-style: italic;
            }
            .toggle-btn {
                border-radius: 12px;
                padding: 6px 16px;
                border: none;
                cursor: pointer;
                transition: all 0.3s ease;
            }
            .toggle-btn:hover {
                opacity: 0.8;
            }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

# 数据
gapminder_df = gapminder(datetimes=True, centroids=True, pretty_names=True)
gapminder_df["Year"] = gapminder_df.Year.dt.year

# 工具函数
def create_table(theme):
    fig = go.Figure(data=[go.Table(
        header=dict(values=gapminder_df.columns, align='left'),
        cells=dict(values=gapminder_df.values.T, align='left'))
    ])
    fig.update_layout(
        paper_bgcolor="#1e1e1e" if theme == "dark" else "#e5ecf6",
        font_color="white" if theme == "dark" else "black",
        margin={"t":0, "l":0, "r":0, "b":0}, height=700)
    return fig

def create_bar_chart(continent, year, yvar, title, theme):
    filtered_df = gapminder_df[(gapminder_df.Continent==continent) & (gapminder_df.Year==year)]
    filtered_df = filtered_df.sort_values(by=yvar, ascending=False).head(15)
    fig = px.bar(filtered_df, x="Country", y=yvar, color="Country",
                 title=f"{title} in {continent}, {year}", text_auto=True)
    fig.update_layout(
        paper_bgcolor="#1e1e1e" if theme == "dark" else "#e5ecf6",
        plot_bgcolor="#1e1e1e" if theme == "dark" else "#e5ecf6",
        font_color="white" if theme == "dark" else "black",
        height=600)
    return fig

def create_choropleth_map(variable, year, theme):
    filtered_df = gapminder_df[gapminder_df.Year==year]
    fig = px.choropleth(filtered_df, color=variable,
                        locations="ISO Alpha Country Code", locationmode="ISO-3",
                        color_continuous_scale="RdYlBu", hover_data=["Country", variable],
                        title=f"{variable} Choropleth Map [{year}]")
    fig.update_layout(
        dragmode=False,
        paper_bgcolor="#1e1e1e" if theme == "dark" else "#e5ecf6",
        font_color="white" if theme == "dark" else "black",
        margin={"l":0, "r":0}, height=600)
    return fig

# 控件
continents = gapminder_df.Continent.unique()
years = gapminder_df.Year.unique()

def dropdown(id, options, value):
    return dcc.Dropdown(id=id, options=options, value=value, clearable=False)

# 布局
app.layout = html.Div([
    html.Div([
        html.H1("🌍 Gapminder Dashboard", className="text-center fw-bold m-2", id="title"),
        html.P("Explore global development trends — Population, GDP, and Life Expectancy.",
               className="header-description", id="desc"),
        html.Div([
            html.Button("🌞 Light Mode", id="theme-toggle", className="toggle-btn btn btn-outline-secondary")
        ], style={"textAlign": "center", "marginBottom": "10px"}),
        dcc.Store(id="theme-store", data="light"),
        html.Br(),
        dcc.Tabs([
            dcc.Tab([dcc.Graph(id="dataset")], label="Dataset"),
            dcc.Tab([
                "Continent", dropdown("cont_pop", continents, "Asia"),
                "Year", dropdown("year_pop", years, 1952),
                dcc.Graph(id="population")
            ], label="Population"),
            dcc.Tab([
                "Continent", dropdown("cont_gdp", continents, "Asia"),
                "Year", dropdown("year_gdp", years, 1952),
                dcc.Graph(id="gdp")
            ], label="GDP per Capita"),
            dcc.Tab([
                "Continent", dropdown("cont_life_exp", continents, "Asia"),
                "Year", dropdown("year_life_exp", years, 1952),
                dcc.Graph(id="life_expectancy")
            ], label="Life Expectancy"),
            dcc.Tab([
                "Variable", dropdown("var_map", ["Population", "GDP per Capita", "Life Expectancy"], "Life Expectancy"),
                "Year", dropdown("year_map", years, 1952),
                dcc.Graph(id="choropleth_map")
            ], label="Choropleth Map")
        ])
    ], className="col-8 mx-auto"),
], style={"background-color": "#e5ecf6", "height": "100vh"}, id="page-wrapper")

# 回调：主题切换
@callback(
    Output("theme-store", "data"),
    Output("theme-toggle", "children"),
    Output("page-wrapper", "style"),
    Output("title", "style"),
    Output("desc", "style"),
    Input("theme-toggle", "n_clicks"),
    State("theme-store", "data"),
    prevent_initial_call=True
)
def toggle_theme(n, current):
    if current == "light":
        return "dark", "🌙 Dark Mode", {"background-color": "#1e1e1e", "height": "100vh"}, \
               {"color": "white"}, {"color": "#CFCFCF"}
    else:
        return "light", "🌞 Light Mode", {"background-color": "#e5ecf6", "height": "100vh"}, \
               {"color": "black"}, {"color": "#666"}

# 其他图表动态更新
@callback(Output("dataset", "figure"), Input("theme-store", "data"))
def update_table(theme): return create_table(theme)

@callback(Output("population", "figure"),
          [Input("cont_pop", "value"), Input("year_pop", "value"), Input("theme-store", "data")])
def update_pop(c, y, theme): return create_bar_chart(c, y, "Population", "Population", theme)

@callback(Output("gdp", "figure"),
          [Input("cont_gdp", "value"), Input("year_gdp", "value"), Input("theme-store", "data")])
def update_gdp(c, y, theme): return create_bar_chart(c, y, "GDP per Capita", "GDP per Capita", theme)

@callback(Output("life_expectancy", "figure"),
          [Input("cont_life_exp", "value"), Input("year_life_exp", "value"), Input("theme-store", "data")])
def update_life_exp(c, y, theme): return create_bar_chart(c, y, "Life Expectancy", "Life Expectancy", theme)

@callback(Output("choropleth_map", "figure"),
          [Input("var_map", "value"), Input("year_map", "value"), Input("theme-store", "data")])
def update_map(var, y, theme): return create_choropleth_map(var, y, theme)

if __name__ == "__main__":
    app.run(debug=True)
