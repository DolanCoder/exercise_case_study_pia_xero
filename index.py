'''
Main file that takes care of the View and Controller component of the dashboard
'''

from dash import html, Input, Output, State
from dash import dcc, dash_table
import dash
import dash_bootstrap_components as dbc
import dash_daq as daq
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
                html.P('You can also smoothen the plot by looking at 7-day rolling average rather than daily'),

                daq.BooleanSwitch(
                                id='dailyweeklytoggle',
                                on=False,
                                label="7-Day Rolling Average",
                                labelPosition="bottom",
                                style = {'width': 'fit-content'}
                                ),
                dcc.Graph(id="usage_graph"),
                
                html.H3('Seasonality'),
                html.P('We can see the above usage graph is highly periodic. We can extract its period by performing a Fourier Transform on the signal'),
                html.B('The location of the peak in the below plot shows how often (in days) the pattern repeats'),
                dcc.Graph(id = 'FFT_graph')

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
    
    fullbas_w_org = pd.merge(fullbas, orgdetails, left_on='orgid', right_on='organisationid', how="inner")
    fullbas_w_org = helper.filter_by_payingflag(fullbas_w_org,payment_status)

    simpledf = simplebas.groupby(pd.Grouper(freq='D', key='datetime')).size().reset_index(name='count')
    fulldf = fullbas_w_org.groupby(pd.Grouper(freq='D', key='datetime')).size().reset_index(name='count')
    
    if dailyweeklytoggle:
        simpledf['count'] = simpledf.rolling(window = 7).mean()
        fulldf['count'] = fulldf.rolling(window = 7).mean()

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
    fig.update_xaxes(title_text='Date')
    fig.update_yaxes(title_text='Run Count')

    return fig


@app.callback(
    Output("FFT_graph", "figure"), 
    Input("date_picker", "start_date"),
    Input("date_picker", "end_date"),
    Input("payment_status", "value"),
    )
def update_fft_graph(start_date, end_date, payment_status): 
    
    fullbas_w_org = pd.merge(fullbas, orgdetails, left_on='orgid', right_on='organisationid', how="inner")
    fullbas_w_org = helper.filter_by_payingflag(fullbas_w_org,payment_status)
    fullbas_w_org = helper.filter_by_time(fullbas_w_org, start_date, end_date)

    simpledf = helper.filter_by_time(simplebas, start_date, end_date)

    simpledf = simpledf.groupby(pd.Grouper(freq='D', key='datetime')).size().reset_index(name='count')
    fulldf = fullbas_w_org.groupby(pd.Grouper(freq='D', key='datetime')).size().reset_index(name='count')
    
    simpledf['rolling_mean'] = simpledf.rolling(window = 7).mean()
    fulldf['rolling_mean'] = fulldf.rolling(window = 7).mean()

    simplebas_fft, simplebas_freq = helper.fft(simpledf['rolling_mean'])
    fullbas_fft, fullbas_freq = helper.fft(fulldf['rolling_mean'])

    fig = go.Figure(
        layout=go.Layout(
            plot_bgcolor="#F9F9F9",
            paper_bgcolor="#F9F9F9",
            legend=dict(font=dict(size=10), orientation="h"),
            ))
    fig.add_trace(
        go.Scatter(
            x=1/fullbas_freq,
            y=abs(fullbas_fft),
            mode='lines',
            name="Full",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=1/simplebas_freq,
            y=abs(simplebas_fft),
            mode='lines',
            name="Simple",
        )
    )
    fig.update_xaxes(title_text='Period measured in days')
    fig.update_yaxes(title_text='Count')

    return fig

if __name__ == '__main__':
    
    app.run_server(debug=True, port=5000)

