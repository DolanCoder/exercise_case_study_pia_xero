'''
Main file that takes care of the View and Controller component of the dashboard
'''

from dash import html, Input, Output, State
from dash import dcc, dash_table
import dash
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import plotly.express as px

from flask import Flask, request,jsonify
from flask_cors import CORS

from datetime import date,  datetime, timedelta
import pandas as pd
import numpy as np
import copy 

from controls import ORGSTATUS, PRODUCTOPTIONS
# import helper


server = Flask(__name__)
app = dash.Dash(__name__, server=server,
                title="Xero Data Explorer",
                update_title='Updating...',
                suppress_callback_exceptions=True,
                external_stylesheets=[dbc.themes.BOOTSTRAP])
CORS(server) 

plot_layout = dict(
    autosize=True,
    automargin=True,
    margin=dict(l=50, r=30, b=100, t=40),
    hovermode="closest",
    plot_bgcolor="#F9F9F9",
    paper_bgcolor="#F9F9F9",
    legend=dict(font=dict(size=10), orientation="h"),
)


app.layout = html.Div(
    [
        dcc.Store(id="aggregate_data"),
        # empty Div to trigger javascript file for graph resizing
        html.Div(id="output-clientside"),
        # Headersection
        html.Div(
            [
                html.Div(
                    [
                        html.Img(
                            src=app.get_asset_url("logo.png"),
                            id="plotly-image",
                            style={
                                "height": "80px",
                                "width": "auto",
                                "marginBottom": "25px",
                            },
                        )
                    ],
                    className="one-third column",
                ),
                html.Div(
                    [
                        html.Div(
                            [
                                html.H3(
                                    "Xero BAS Analytics",
                                    style={"marginBottom": "0px"},
                                )

                            ]
                        )
                    ],
                    className="one-third column",
                    id="title",
                ),

            ],
            id="header",
            className="row flex-display",
            style={"marginBottom": "25px"},
        ),
        html.Div([ dcc.Loading(id="loading-1", type="default", children=html.Div(id="loading-output"))]), 
        
        html.Div([
        # FilterSection
        html.Div(
            [
                html.H3("Date", className="control_label"),
                html.P("Filter data by date:", className="control_label"),
                dcc.DatePickerRange(
                    id="date_picker",
                    end_date=date.today(),
                    display_format='MMM Do, YY',
                    start_date_placeholder_text='MMM Do, YY'
                ),
                html.H3("Status", className="control_label"),
                html.P("Filter organisations by status:", className="control_label"),
                dcc.Dropdown(
                    id="org_status",
                    options=ORGSTATUS,
                    multi=True,
                    value=list(ORGSTATUS.keys()),
                    className="dcc_control",
                ),
                html.H3("Payment Status", className="control_label"),
                html.P("Filter organisations by payment status:", className="control_label"),
                dcc.Checklist(
                    id="payment_status",
                    options={
                            '1': 'Paying',
                            '0': 'Non-Paying',
                    },
                    value=['1']
                    ),
                html.H3("Product Option", className="control_label"),
                html.P("Filter to select any organisation with any of the following production options:", className="control_label"),
                dcc.Dropdown(
                    id="product_options",
                    options=PRODUCTOPTIONS,
                    multi=True,
                    value=list(PRODUCTOPTIONS.keys()),
                    className="dcc_control",
                ),



            ],
            className="pretty_container four columns",
            id="cross-filter-options"
        ),
        # ContentSection

         
        ],
        style={"display": "flex", "flexDirection": "row"})
    ],
    id="page-content",
    style={"display": "flex", "flexDirection": "column"},
)


if __name__ == '__main__':
    
    app.run_server(debug=True, port=5000)

