import pandas as pd
import plotly.express as px
from dash import Dash, dcc, html, Input, Output, dash_table
import dash_bootstrap_components as dbc

# ── Data loading ──────────────────────────────────────────────────────────────

def load_data(path="data/project-maintainers.csv"):
    df = pd.read_csv(path, header=0)
    df.columns = ["Status", "Project", "Maintainer", "Company", "GitHub", "OwnersURL"]
    df["Status"]  = df["Status"].replace("", pd.NA).ffill()
    df["Project"] = df["Project"].replace("", pd.NA).ffill()
    for col in df.columns:
        if df[col].dtype == object:
            df[col] = df[col].str.strip()
    df = df[df["Maintainer"].notna() & (df["Maintainer"] != "")]
    df["Company"] = df["Company"].fillna("Independent")
    df.loc[df["Company"] == "", "Company"] = "Independent"
    df["Company"] = df["Company"].replace({"Nvidia": "NVIDIA", "RedHat": "Red Hat"})
    return df

df = load_data()

STATUS_COLORS = {"Graduated": "#2E86AB", "Incubating": "#F6AE2D", "Sandbox": "#A23B72"}

# ── Layout ────────────────────────────────────────────────────────────────────
app = Dash(__name__, external_stylesheets=[dbc.themes.FLATLY], title="CNCF Maintainers Dashboard")

SIDEBAR = {
    "position": "fixed", "top": 0, "left": 0, "bottom": 0,
    "width": "260px", "padding": "1.5rem 1rem",
    "background-color": "#1a1a2e", "color": "white", "overflow-y": "auto",
}
CONTENT = {"margin-left": "280px", "padding": "2rem 1rem"}

sidebar = html.Div([
    html.H4("CNCF Dashboard", className="text-center mb-1",
            style={"color": "#61dafb", "fontWeight": "bold"}),
    html.P("Maintainer insights", className="text-center mb-3",
           style={"fontSize": "0.8rem", "color": "#aaa"}),
    html.Hr(style={"borderColor": "#444"}),

    html.P("Filter by Status", style={"color": "#ccc", "fontSize": "0.8rem", "marginBottom": "4px"}),
    dcc.Checklist(
        id="status-filter",
        options=[{"label": f"  {s}", "value": s} for s in ["Graduated", "Incubating", "Sandbox"]],
        value=["Graduated", "Incubating", "Sandbox"],
        inputStyle={"marginRight": "6px"},
        labelStyle={"display": "block", "color": "white", "marginBottom": "4px"},
    ),
    html.Hr(style={"borderColor": "#444", "marginTop": "12px"}),

    html.P("Filter by Project", style={"color": "#ccc", "fontSize": "0.8rem", "marginBottom": "4px"}),
    dcc.Dropdown(
        id="project-filter", options=[], multi=True,
        placeholder="All projects", style={"fontSize": "0.8rem"},
    ),
    html.Hr(style={"borderColor": "#444", "marginTop": "12px"}),

    html.P("Search Company", style={"color": "#ccc", "fontSize": "0.8rem", "marginBottom": "4px"}),
    dcc.Input(
        id="company-search", type="text", placeholder="e.g. Google", debounce=True,
        style={"width": "100%", "borderRadius": "4px", "padding": "4px 8px",
               "fontSize": "0.85rem", "color": "#000", "backgroundColor": "#fff"},
    ),
    html.Hr(style={"borderColor": "#444", "marginTop": "12px"}),
    html.Div(id="sidebar-stats", style={"color": "#ccc", "fontSize": "0.8rem"}),
], style=SIDEBAR)

content = html.Div([
    dbc.Row(id="kpi-cards", className="mb-4"),
    dbc.Tabs([
        dbc.Tab(label="Company Overview",          tab_id="tab-company"),
        dbc.Tab(label="Project Overview",          tab_id="tab-project"),
        dbc.Tab(label="Cross-Project Maintainers", tab_id="tab-multi"),
        dbc.Tab(label="Maintainers Table",         tab_id="tab-table"),
    ], id="tabs", active_tab="tab-company", className="mb-3"),
    html.Div(id="tab-content"),
], style=CONTENT)

app.layout = html.Div([sidebar, content])


# ── Helpers ───────────────────────────────────────────────────────────────────

def filter_df(status_vals, projects, company_search):
    filtered = df[df["Status"].isin(status_vals or [])]
    if projects:
        filtered = filtered[filtered["Project"].isin(projects)]
    if company_search and company_search.strip():
        term = company_search.strip()
        filtered = filtered[filtered["Company"].str.contains(term, case=False, na=False, regex=False)]
    return filtered


def make_table(data, columns, page_size=25):
    return dash_table.DataTable(
        data=data, columns=columns,
        sort_action="native", filter_action="native", page_size=page_size,
        style_table={"overflowX": "auto"},
        style_cell={"textAlign": "left", "fontSize": "0.85rem", "padding": "6px"},
        style_header={"fontWeight": "bold", "backgroundColor": "#1a1a2e", "color": "white"},
        style_data_conditional=[{"if": {"row_index": "odd"}, "backgroundColor": "#f9fbff"}],
    )


# ── Callbacks ─────────────────────────────────────────────────────────────────

@app.callback(
    Output("project-filter", "options"),
    Input("status-filter", "value"),
)
def update_project_options(status_vals):
    available = df[df["Status"].isin(status_vals or [])]["Project"].dropna().unique()
    return [{"label": p, "value": p} for p in sorted(available)]


@app.callback(
    Output("kpi-cards", "children"),
    Output("sidebar-stats", "children"),
    Input("status-filter", "value"),
    Input("project-filter", "value"),
    Input("company-search", "value"),
)
def update_kpis(status_vals, projects, company_search):
    f = filter_df(status_vals, projects, company_search)
    n_m  = len(f)
    n_c  = f["Company"].nunique()
    n_p  = f["Project"].nunique()
    top  = f["Company"].value_counts().idxmax() if n_m else "—"
    top_n = f["Company"].value_counts().max() if n_m else 0

    def kpi(title, val, color):
        return dbc.Col(dbc.Card(dbc.CardBody([
            html.H2(str(val), className="card-title mb-0",
                    style={"color": color, "fontWeight": "bold"}),
            html.P(title, className="card-text text-muted", style={"fontSize": "0.82rem"}),
        ]), className="shadow-sm"), md=3)

    return (
        [kpi("Total Maintainers", n_m, "#2E86AB"),
         kpi("Unique Companies", n_c, "#F6AE2D"),
         kpi("Projects", n_p, "#A23B72"),
         kpi(f"Top Company ({top})", top_n, "#28a745")],
        [html.P(f"{n_m} maintainers", style={"marginBottom": "2px"}),
         html.P(f"{n_c} companies",   style={"marginBottom": "2px"}),
         html.P(f"{n_p} projects")],
    )


@app.callback(
    Output("tab-content", "children"),
    Input("tabs", "active_tab"),
    Input("status-filter", "value"),
    Input("project-filter", "value"),
    Input("company-search", "value"),
)
def render_tab(active_tab, status_vals, projects, company_search):
    filtered = filter_df(status_vals, projects, company_search)
    if filtered.empty:
        return dbc.Alert("No data matches the current filters.", color="warning")

    # ── Company Overview ──
    if active_tab == "tab-company":
        co = (
            filtered.groupby("Company")["Maintainer"].count().reset_index()
            .rename(columns={"Maintainer": "Maintainers"})
            .sort_values("Maintainers", ascending=False).head(30)
        )
        fig = px.bar(co, x="Maintainers", y="Company", orientation="h",
                     title=f"Top {len(co)} Companies by Maintainer Count",
                     color="Maintainers", color_continuous_scale="Blues", text="Maintainers")
        fig.update_traces(textposition="outside")
        fig.update_layout(yaxis={"autorange": "reversed"}, height=650,
                          coloraxis_showscale=False, margin={"l": 180, "r": 60})

        if company_search and company_search.strip():
            pb = (
                filtered.groupby(["Project", "Status"])["Maintainer"].count().reset_index()
                .rename(columns={"Maintainer": "Maintainers"})
                .sort_values("Maintainers", ascending=False)
            )
            fig2 = px.bar(pb, x="Maintainers", y="Project", orientation="h",
                          color="Status", color_discrete_map=STATUS_COLORS,
                          title=f"Projects where '{company_search.strip()}' maintainers are active",
                          text="Maintainers")
            fig2.update_traces(textposition="outside")
            fig2.update_layout(yaxis={"autorange": "reversed"},
                               height=max(350, len(pb) * 30),
                               margin={"l": 220, "r": 60})
            return html.Div([dcc.Graph(figure=fig), html.Hr(), dcc.Graph(figure=fig2)])
        return dcc.Graph(figure=fig)

    # ── Project Overview ──
    elif active_tab == "tab-project":
        pc = (
            filtered.groupby(["Project", "Status"])["Maintainer"].count().reset_index()
            .rename(columns={"Maintainer": "Maintainers"})
            .sort_values("Maintainers", ascending=False)
        )
        fig_p = px.bar(pc, x="Maintainers", y="Project", orientation="h",
                       color="Status", color_discrete_map=STATUS_COLORS,
                       title="Maintainers per Project", text="Maintainers")
        fig_p.update_traces(textposition="outside")
        fig_p.update_layout(yaxis={"autorange": "reversed"},
                            height=max(500, len(pc) * 26), margin={"l": 220, "r": 60})

        sc = filtered.drop_duplicates("Project").groupby("Status")["Project"].count().reset_index()
        fig_d = px.pie(sc, names="Status", values="Project", hole=0.5,
                       title="Project Count by Status",
                       color="Status", color_discrete_map=STATUS_COLORS)
        fig_d.update_layout(height=360)

        return html.Div([dbc.Row([
            dbc.Col(dcc.Graph(figure=fig_d), md=4),
            dbc.Col(dcc.Graph(figure=fig_p), md=8),
        ])])

    # ── Cross-Project Maintainers ──
    elif active_tab == "tab-multi":
        m = (
            filtered.groupby("GitHub")
            .agg(Maintainer=("Maintainer", "first"),
                 Company=("Company", "first"),
                 Projects=("Project", lambda x: sorted(x.unique())))
            .reset_index()
        )
        m["ProjectCount"] = m["Projects"].apply(len)
        m["Projects"]     = m["Projects"].apply(", ".join)
        m = m[m["ProjectCount"] > 1].sort_values("ProjectCount", ascending=False)
        if m.empty:
            return dbc.Alert("No maintainers span multiple projects with the current filters.", color="info")

        fig = px.bar(m.head(30), x="Maintainer", y="ProjectCount", color="Company",
                     title=f"Maintainers active in multiple projects ({len(m)} total)",
                     text="ProjectCount", hover_data=["GitHub", "Company", "Projects"])
        fig.update_layout(xaxis={"tickangle": -40}, height=480)

        return html.Div([
            dcc.Graph(figure=fig), html.Hr(),
            make_table(m.to_dict("records"), [
                {"name": "Maintainer",  "id": "Maintainer"},
                {"name": "GitHub",      "id": "GitHub"},
                {"name": "Company",     "id": "Company"},
                {"name": "# Projects",  "id": "ProjectCount"},
                {"name": "Projects",    "id": "Projects"},
            ], page_size=20),
        ])

    # ── Maintainers Table ──
    elif active_tab == "tab-table":
        tdf = filtered[["Maintainer", "GitHub", "Company", "Project", "Status"]].copy()
        return make_table(tdf.to_dict("records"),
                          [{"name": c, "id": c} for c in tdf.columns])

    return html.Div("Select a tab.")


# ── Run ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print(f"\nLoaded {len(df)} maintainer records")
    print(f"Projects: {df['Project'].nunique()} | Companies: {df['Company'].nunique()}")
    app.run(debug=False, port=8050)
