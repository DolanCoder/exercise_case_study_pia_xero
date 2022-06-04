'''
Main file that takes care of the View and Controller component of the dashboard
'''

from dash import html, Input, Output, State
from dash import dcc, dash_table
import dash
import dash_bootstrap_components as dbc
import dash_daq as daq
import plotly.graph_objects as go
import plotly.graph_objects as go
import plotly.express as px

from flask import Flask, request,jsonify
from flask_cors import CORS

from datetime import date,  datetime, timedelta
import copy
import pandas as pd
import numpy as np
import copy 

# from controls import ORGSTATUS, PRODUCTOPTIONS
import helper


#some minor data wrangling
orgdetails = pd.read_csv('data/orgcard.csv')
orgdetails['organisationid'] =orgdetails['organisationid'].str.lower()

fullbas = pd.read_csv('data/fullbas.csv')
fullbas['datetime'] = fullbas['datestring']+' '+fullbas['timestring']
fullbas['datetime'] = fullbas['datetime'].astype('datetime64[s]').dt.tz_localize('Australia/Sydney',ambiguous=True)

simplebas = pd.read_csv('data/simplebas.csv')
simplebas['datetime'] = simplebas['datetime'].astype('datetime64[s]')


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
                    start_date = '2016-10-01',
                    end_date=date.today(),
                    display_format='MMM Do, YY',
                    start_date_placeholder_text='MMM Do, YY'
                ),
                # html.H3("Status", className="control_label"),
                # html.P("Filter organisations by status:", className="control_label"),
                # dcc.Dropdown(
                #     id="org_status",
                #     options=ORGSTATUS,
                #     multi=True,
                #     value=list(ORGSTATUS.keys()),
                #     className="dcc_control",
                # ),
                html.H3("Payment Status", className="control_label"),
                html.P("Filter organisations by payment status, note that this only applies to Full BAS, as paymend status information is not available for Simple BAS dataset", className="control_label"),
                dcc.Checklist(
                    id="payment_status",
                    options={
                            '1': 'Paying',
                            '0': 'Non-Paying',
                    },
                    value=['1']
                    ),
                # html.H3("Product Option", className="control_label"),
                # html.P("Filter to select any organisation with any of the following production options:", className="control_label"),
                # dcc.Dropdown(
                #     id="product_options",
                #     options=PRODUCTOPTIONS,
                #     multi=True,
                #     value=list(PRODUCTOPTIONS.keys()),
                #     className="dcc_control",
                # ),

            ],
            className="pretty_container four columns",
            id="cross-filter-options"
        ),
        # ContentSection
        html.Div(
            [
                html.H2('Simple and Full BAS Usage'),
                html.P('Here we look at how the BAS systems are used in terms of frequencies. We simply look at report generation, for now we ignore multiple access, runtime etc.'),
                html.P('You can also smoothen the plot by looking at weekly activities rather than daily'),

                daq.BooleanSwitch(
                                id='dailyweeklytoggle',
                                on=True,
                                label="Daily/Weekly",
                                labelPosition="bottom"
                                ),
                dcc.Graph(id="usage_graph"),
            ],
            className="pretty_container eight columns",
            id="main-section"
        ),
         
        ],
        style={"display": "flex", "flexDirection": "row"})
    ],
    id="page-content",
    style={"display": "flex", "flexDirection": "column"},
)

@app.callback(
    Output("usage_graph", "figure"), 
    Input("date_picker", "start_date"),
    Input("date_picker", "end_date"),
    Input("payment_status", "value"),
    Input("dailyweeklytoggle","on")
    )
def update_usage_graph(start_date, end_date, payment_status, dailyweeklytoggle): 
    
    layout_aggregate = copy.deepcopy(plot_layout)


    fullbas_w_org = pd.merge(fullbas, orgdetails, left_on='orgid', right_on='organisationid', how="inner")
    fullbas_w_org = helper.filter_by_payingflag(fullbas_w_org,payment_status)

    if dailyweeklytoggle:
        simpledf = simplebas.groupby(pd.Grouper(freq='D', key='datetime')).size().reset_index(name='count')
        fulldf = fullbas_w_org.groupby(pd.Grouper(freq='D', key='datetime')).size().reset_index(name='count')
    else:

        simpledf = simplebas.groupby(pd.Grouper(freq='W', key='datetime')).size().reset_index(name='count')
        fulldf = fullbas_w_org.groupby(pd.Grouper(freq='W', key='datetime')).size().reset_index(name='count')

    simpledff = helper.filter_by_time(simpledf, start_date, end_date)
    fulldff = helper.filter_by_time(fulldf, start_date, end_date)
    
    fig = go.Figure(
        layout=go.Layout(
            plot_bgcolor="#F9F9F9",
            paper_bgcolor="#F9F9F9",
            legend=dict(font=dict(size=10), orientation="h"),
            ))
    fig.add_trace(
        go.Scatter(
            x=fulldff['datetime'],
            y=fulldff['count'],
            mode='lines',
            name="Full",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=simpledff['datetime'],
            y=simpledff['count'],
            mode='lines',
            name="Simple",
        )
    )

    data = [
            dict(
                type="line",
                name="Full",
                x=fulldff['datetime'],
                y=fulldff['count'],
                line=dict(shape="spline", smoothing=2, width=1, ),
            ),
            dict(
                type="line",
                name="Simple",
                x=simpledff['datetime'],
                y=simpledff['count'],
                line=dict(shape="spline", smoothing=2, width=1),
            ),
            ]
    fig.update_xaxes(title_text='Date')
    fig.update_yaxes(title_text='Run Count')

    return fig

if __name__ == '__main__':
    
    app.run_server(debug=True, port=5000)

