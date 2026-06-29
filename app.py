"""
Main app file for the University Fit-Finder dashboard.
"""
from dash import Dash, html, dcc, html, Input, Output, ctx, callback, State, no_update
import dash_bootstrap_components as dbc
import dash_ag_grid as dag
import plotly.express as px

import mysql_utils
import mongodb_utils
import neo4j_utils

app = Dash(external_stylesheets=[dbc.themes.BOOTSTRAP])

df_universities = mysql_utils.get_universities_list()
uni_column_defs = [
    {"field": "University", "headerName": "University", "filter": True},
    {"field": "Photo", "headerName": "Photo", "cellRenderer": "markdown", "cellRendererParams": {"dangerously_allow_code": True}},
    {"field": "Number of Publications", "headerName": "Publications"},
    {"field": "Total Citations", "headerName": "Citations"},
    {"field": "Citations per Publication", "headerName": "Citations per Publication"},
    {"field": "Top Research Interest", "headerName": "Top Research Interest", "filter": True},
    # Uses a custom JavaScript button to add a button to each row
    {"field": "Follow", "headerName": "", "cellRenderer": "Button", "cellRendererParams": {"className": "btn btn-follow"}}
]

df_universities_favs = mysql_utils.get_or_create_favorite_universities()
uni_favs_column_defs = [
    {"field": "University", "headerName": "University", "filter": True},
    {"field": "Photo", "headerName": "Photo", "cellRenderer": "markdown", "cellRendererParams": {"dangerously_allow_code": True}},
    {
        "field": "rating",
        "headerName": "Rating (0-5)",
        "editable": True,
        "type": "numericColumn",
        "cellEditorParams": {"min": 0, "max": 5},
        "enableCellChangeFlash": True,
        "filter": True
    }
]

df_professors = mysql_utils.get_professors_list()
prof_column_defs = [
    {"field": "id", "headerName": "id", "hide": True},
    {"field": "Professor", "headerName": "Professor", "filter": True},
    {"field": "Research Interests", "headerName": "Research Interests", "filter": True},
    {"field": "Affiliation", "headerName": "Affiliation", "filter": True},
    {"field": "Total Citations", "headerName": "Total Citations", "filter": True},
    {"field": "Show More", "headerName": "", "cellRenderer": "Button", "cellRendererParams": {"className": "btn btn-follow"}},
    {"field": "Follow", "headerName": "", "cellRenderer": "Button", "cellRendererParams": {"className": "btn btn-follow"}}
]

app.layout = [
    html.H1(
        'University Fit-Finder',
        style={
            'textAlign': 'center',
            'color': '#646566',
            'padding': '10px',
            'fontWeight': 'bold',
            'fontFamily': 'Arial, sans-serif'
    }),
    dbc.Row([
        dbc.Col(
            html.Div([
                html.H5("All Universities", style={"textAlign": "center", "marginBottom": "5px"}),
                dag.AgGrid(
                    id="universities-table",
                    rowData=df_universities.to_dict('records'),
                    columnDefs=uni_column_defs,
                    columnSize="sizeToFit",
                    dashGridOptions={"rowHeight": 75}
                )
            ])
        ),
        dbc.Col(
            html.Div([
                html.H5("Your Followed Universities", style={"textAlign": "center", "marginBottom": "5px"}),
                dag.AgGrid(
                    id="favorite-universities-table",
                    rowData=df_universities_favs.to_dict('records'),
                    columnDefs=uni_favs_column_defs,
                    columnSize="sizeToFit",
                    dashGridOptions={"rowHeight": 75, "stopEditingWhenCellsLoseFocus": True},
                )
            ])
        )
    ]),
    html.H5("University Citations Per Year", style={"textAlign": "center", "marginBottom": "5px", "marginTop": "7px"}),
    dcc.Dropdown(
        mongodb_utils.get_all_universities(),
        ["American University"],
        id='university-trends-dropdown',
        multi=True
    ),
    dcc.Button('Submit', id='university-trends-submit', n_clicks=0),
    dcc.Loading(
        type="circle",
        children=dcc.Graph(figure={}, id="university-trends-graph")
    ),
    dbc.Row([
        dbc.Col(
            html.Div([
                html.H5("Professors", style={"textAlign": "center", "marginBottom": "5px"}),
                dag.AgGrid(
                    id="professors-table",
                    rowData=df_professors.to_dict('records'),
                    columnDefs=prof_column_defs,
                    columnSize="sizeToFit",
                    dashGridOptions={
                        "rowHeight": 75,
                    }
                )
            ])
        ),
        dbc.Col(
            html.Div([
                html.H5("Your Followed Professors", style={"textAlign": "center", "marginBottom": "5px"}),
                dag.AgGrid(
                    id="favorite-professors-table",
                    # rowData=mysql_utils.get_or_create_favorite_professors().to_dict('records'),
                    rowData=[],
                    columnDefs=[
                        {"field": "Professor", "headerName": "Professor"},
                        {"field": "Research Interests", "headerName": "Research Interests"},
                        {"field": "Affiliation", "headerName": "Affiliation"},
                        {
                            "field": "rating",
                            "headerName": "Rating (0-5)",
                            "editable": True,
                            "type": "numericColumn",
                            "cellEditorParams": {"min": 0, "max": 5},
                            "enableCellChangeFlash": True,
                        },
                        {"field": "Remove", "headerName": "", "cellRenderer": "Button", "cellRendererParams": {"className": "btn btn-danger"}}
                    ],
                    columnSize="sizeToFit",
                    dashGridOptions={"rowHeight": 75, "stopEditingWhenCellsLoseFocus": True}
                )
            ])
        )
    ]),
    dbc.Row([
        dbc.Col(
            html.Div([
                html.Div(
                    id="professor-detail-grid",
                    style={"display": "none"},
                    children=[
                        html.Hr(),
                        dbc.Button("✕ Close", id="close-professor-detail", color="secondary", size="sm",
                                   style={"float": "right", "marginBottom": "10px"}),
                        html.Div(id="professor-detail-content")
                    ]
                )
            ])
        )
    ]),
    dbc.Row([
        dbc.Col(
            html.Div([
                html.H5("Find Professors by Keywords", style={"textAlign": "center", "marginBottom": "5px", "marginTop": "20px"}),
                dcc.Input(
                    id="keyword-search-input",
                    type="text",
                    placeholder="Enter keywords separated by commas...",
                    style={"width": "100%", "marginBottom": "10px", "padding": "5px"}
                ),
                dbc.Button("Search", id="keyword-search-submit", style={"marginBottom": "10px"}),
                dag.AgGrid(
                    id="keyword-search-results",
                    rowData=[],
                    columnDefs=[
                        {"field": "Professor", "headerName": "Professor"},
                        {"field": "MatchedKeywords", "headerName": "Matched Keywords"},
                    ],
                    columnSize="sizeToFit",
                    dashGridOptions={
                        "rowHeight": 75,
                        "rowSelection": "single"
                    }
                )
            ])
        ),
        dbc.Col(
            html.Div([
                html.H5("Related Professors", style={"textAlign": "center", "marginBottom": "5px", "marginTop": "20px"}),
                dag.AgGrid(
                    id="related-professors-results",
                    rowData=[],
                    columnDefs=[
                        {"field": "Professor", "headerName": "Professor"},
                        {"field": "SharedKeywords", "headerName": "Shared Keywords"},
                    ],
                    columnSize="sizeToFit",
                    dashGridOptions={"rowHeight": 75}
                )
            ])
        )
    ]),
    dcc.Interval(id="page-load", interval=1, n_intervals=0, max_intervals=1),
    html.Div(id='container-button-timestamp')
]


@callback(
    Output("keyword-search-results", "rowData"),
    Input("keyword-search-submit", "n_clicks"),
    State("keyword-search-input", "value"),
    prevent_initial_call=True
)
def search_by_keywords(_, keywords):
    print("search_by_keywords happeneda okjsasdkjfalkdsj", keywords)
    if not keywords:
        return []
    keyword_list = [k.strip() for k in keywords.split(",")]
    results = neo4j_utils.get_professors_by_keywords(keyword_list)
    return results

@callback(
    Output("related-professors-results", "rowData"),
    Input("keyword-search-results", "selectedRows"),
    prevent_initial_call=True
)
def show_related_professors(selected_rows):
    if not selected_rows:
        return []
    professor_name = selected_rows[0]["Professor"]
    results = neo4j_utils.get_related_professors(professor_name)
    return results

@callback(
    Output("professor-detail-grid", "style"),
    Output("professor-detail-content", "children"),
    Input("professors-table", "cellRendererData"),
    Input("close-professor-detail", "n_clicks"),
    State("professor-detail-grid", "style"),
    State("professor-detail-content", "children"),
    prevent_initial_call=True
)
def show_professor_detail(cell_data, close_clicks, style, curr_content):
    if ctx.triggered_id == "close-professor-detail":
        return {"display": "none"}, []
    
    if cell_data is None or cell_data.get("colId") != "Show More":
        return no_update, no_update

    row_index = cell_data["rowIndex"]
    professor_row = df_professors.iloc[row_index]
    professor_name = professor_row["Professor"]

    # todo: the db call thing
    df_details = mysql_utils.get_professor_details(professor_name)
    papers_column_defs = [
        {"field": "Title", "headerName": "Title", "wrapText": True, "autoHeight": True},
        {"field": "Publication Year", "headerName": "Year"},
        {"field": "Number of Citations", "headerName": "Citations"},
        {"field": "Keywords", "headerName": "Keywords", "wrapText": True, "autoHeight": True},
    ]

    df_keyword_trends = mysql_utils.get_professor_keyword_trends(professor_name)
    df_keyword_trends['year'] = df_keyword_trends['year'].astype(int)
    df_keyword_trends = df_keyword_trends.sort_values('year')

    top_keywords = df_keyword_trends.groupby('keyword')['count'].sum().nlargest(20).index
    df_keyword_trends = df_keyword_trends[df_keyword_trends['keyword'].isin(top_keywords)]

    fig = px.bar(
        df_keyword_trends,
        x="year",
        y="count",
        color="keyword",
        barmode="stack",
        labels={"year": "Year", "count": "Publications", "keyword": "Keyword"}
    )
    fig.update_layout(margin=dict(l=0, r=0, t=30, b=0), legend_title_text="Keywords")

    content = html.Div([
        html.H4(professor_name, style={"marginBottom": "5px"}),
        html.P(f"Affiliation: {professor_row['Affiliation']}"),
        html.P(f"Research Interests: {professor_row['Research Interests']}"),
        html.Hr(),
        html.H6("Publications"),
        dag.AgGrid(
            id="professor-papers-table",
            rowData=df_details.to_dict('records'),
            columnDefs=papers_column_defs,
            columnSize="sizeToFit",
        ),
        html.H6("Keyword Trends Over Time (for top 20 keywords)", style={"marginTop": "25px", "fontWeight": "bold", "fontSize": "18px", "textAlign": "center"}),
        dcc.Graph(figure=fig, id="professor-keyword-trends-graph"),
    ])

    return {"display": "block", "marginTop": "20px", "padding": "15px", "border": "1px solid #dee2e6", "borderRadius": "5px"}, content

@callback(
    Output("favorite-professors-table", "rowData"),
    Input("professors-table", "cellRendererData"),
    Input("favorite-professors-table", "cellRendererData"),
    Input("favorite-professors-table", "cellValueChanged"),
    Input("page-load", "n_intervals"),
    prevent_initial_call=False
)
def follow_professor(new_row, fav_cell_data, edited_rows, intervals):
    if new_row is not None and new_row.get("colId") == "Follow":
        # make sure it was the follow button that was clicked, not the show more button
        # if new_row.get("colId") == "Follow":
        prof_row = df_professors.iloc[new_row["rowIndex"]]
        mysql_utils.upsert_favorite_professor(prof_row["id"])

    if fav_cell_data is not None and fav_cell_data.get("colId") == "Remove":
        df_favs = mysql_utils.get_or_create_favorite_professors()
        prof_id = df_favs.iloc[fav_cell_data["rowIndex"]]["faculty_id"]
        mysql_utils.delete_favorite_professor(prof_id)
    
    if edited_rows is not None:
        for row in edited_rows:
            prof_id = row["data"]["faculty_id"]
            rating = row["data"]["rating"]
            mysql_utils.upsert_favorite_professor(prof_id, rating=rating)
    
    return mysql_utils.get_or_create_favorite_professors().to_dict('records')

@callback(
    Output("favorite-universities-table", "rowData"),
    Input("universities-table", "cellRendererData"),
    Input("favorite-universities-table", "cellValueChanged"),
)
def followUniversity(new_row, edited_rows):
    # Adding a new followed university
    if new_row is not None:
        uni_row = df_universities.iloc[new_row["rowIndex"]]
        print("following", uni_row["University"], "with id", uni_row["id"])
        mysql_utils.upsert_favorite_university(uni_row["id"])

    # Updating the rating for a followed university
    if edited_rows is not None:
        for row in edited_rows:
            uni_id = row["data"]["university_id"]
            rating = row.get("value", 0.0)
            print("upserting rating", rating, "for university id", uni_id, row["data"]["University"])
            mysql_utils.upsert_favorite_university(uni_id, rating=rating)

    # Always return the most up-to-date list of followed universities after edits in above code
    return mysql_utils.get_or_create_favorite_universities().to_dict('records')


@callback(
    Output('university-trends-graph', 'figure'),
    Input('university-trends-submit', 'n_clicks'),
    State('university-trends-dropdown', 'value')
)
def universityTrendsSubmit(_, universities):
    print("getting citation trends for", universities)
    df_citation_hist = mongodb_utils.get_university_citation_trends(universities)
    lines = px.line(df_citation_hist, x='year', y='totalCitations', color="university")
    return lines

# Run the app
if __name__ == '__main__':
    app.run(debug=True)
