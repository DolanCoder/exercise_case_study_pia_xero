'''
Main file that takes care of the View and Controller component of the dashboard
'''

from matplotlib.pyplot import title
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
fullbas['datetime'] = fullbas['datetime'].astype('datetime64').dt.tz_localize('GMT').dt.tz_convert('Australia/Sydney')

simplebas = pd.read_csv('data/simplebas.csv')
simplebas['datetime'] = simplebas['datetime'].astype('datetime64[s]').dt.tz_localize('GMT').dt.tz_convert('Australia/Sydney')


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
                html.P('We can see the above usage graph is highly periodic. We can extract its period by performing a Fourier Transform on the signal. This works best when there is at least 1 year of data'),
                html.B('The location of the peak in the below plot shows how often (in days) the pattern repeats'),
                dcc.Graph(id = 'FFT_graph'),

               
                html.P('To see the cumulative monthly usage, we can look at the usage month by month'),
                dcc.Graph(id = 'monthlyusage_graph'),


                html.H3('Maintenance window'),
                html.P('In order to find 2 hour in a month with low usage, we can look at hour usage across days every month'),
                html.P('Click on the legend to activate/deactive particular days'),
                daq.BooleanSwitch(
                                id='simplefulltoggle',
                                on=False,
                                label="Simple / Full BAS Usage",
                                labelPosition="bottom",
                                style = {'width': 'fit-content'}
                                ),
                dcc.Graph(id = 'maintenacewindow_graph'),

                html.H3('Users & Organisationss'),
                html.Div(
                            [
                                html.Div(
                                    [html.H6(id="org_both_text", style={'margin':"20px"}), html.P("No. of orgs that ran both reports\u002A")],
                                    id="org_both",
                                    className="mini_container",
                                ),
                                html.Div(
                                    [html.H6(id="user_both_text", style={'margin':"20px"}), html.P("No. of users that ran both reports")],
                                    id="user_both",
                                    className="mini_container",
                                ),
                                html.Div(
                                    [html.H6(id="user_either_text", style={'margin':"20px"}), html.P("No. of users that ran either reports")],
                                    id="user_either",
                                    className="mini_container",
                                )
                            ],
                            id="info-container",
                            className="row container-display",
                        ),
                html.P('\u002A Due to lacking org details in the simple bas dataset, we are assuming the same user ran both BAS system for the same orgnanisation'),
                dcc.Graph(id = 'userorganisation_graph'),

                html.H3('Popular Pricing Plans'),
                html.P('Options with less than 50 customers are grouped together under "Other". '),
                dcc.Graph(id = 'plans_piegraph'),



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


@app.callback(
    Output("maintenacewindow_graph", "figure"), 
    Input("date_picker", "start_date"),
    Input("date_picker", "end_date"),
    Input("payment_status", "value"),
    Input("simplefulltoggle", "on")
    )
def update_maintenancewindow_graph(start_date, end_date, payment_status, simplefulltoggle):
        
    fullbas_w_org = pd.merge(fullbas, orgdetails, left_on='orgid', right_on='organisationid', how="inner")
    fullbas_w_org = helper.filter_by_payingflag(fullbas_w_org,payment_status)
    fullbas_w_org = helper.filter_by_time(fullbas_w_org, start_date, end_date)

    simpledf = helper.filter_by_time(simplebas, start_date, end_date)


    figure = go.Figure()

    if simplefulltoggle:
        figure.update_layout(title='Full BAS Hourly Usage', title_font_size=20)
        monthly_usage = list(fullbas.groupby(fullbas_w_org['datetime'].dt.day)['datetime'])
    else:
        figure.update_layout(title='Simple BAS Hourly Usage', title_font_size=20)
        monthly_usage = list(simpledf.groupby(simpledf['datetime'].dt.day)['datetime'])

    for index, item, in enumerate(monthly_usage):
        
        daily = item[1].groupby(item[1].dt.hour).count().reset_index(name='count')
        figure.add_trace(
        go.Scatter(x=daily['datetime'], y = daily['count'], name = 'Day %s' % (index+1))
        )
    
    figure.update_xaxes(title_text='Time (UTC+11 Time Zone)')
    figure.update_yaxes(title_text='Count')

        
    return figure


@app.callback(
    Output("monthlyusage_graph", "figure"), 
    Input("date_picker", "start_date"),
    Input("date_picker", "end_date"),
    Input("payment_status", "value"),
    )
def update_monthlyusage_graph(start_date, end_date, payment_status):
        
    fullbas_w_org = pd.merge(fullbas, orgdetails, left_on='orgid', right_on='organisationid', how="inner")
    fullbas_w_org = helper.filter_by_payingflag(fullbas_w_org,payment_status)
    fullbas_w_org = helper.filter_by_time(fullbas_w_org, start_date, end_date)

    simpledf = helper.filter_by_time(simplebas, start_date, end_date)


    simpledf_monthly = (simpledf.groupby(simpledf['datetime'].dt.month)).size().reset_index(name='count')
    fulldf_monthly = (fullbas.groupby(fullbas_w_org['datetime'].dt.month)).size().reset_index(name='count')

    figure = go.Figure()


    figure.add_trace(
    go.Scatter(x=fulldf_monthly['datetime'], y = fulldf_monthly['count'], name = 'Full BAS' )
    )
    figure.add_trace(
    go.Scatter(x=simpledf_monthly['datetime'], y = simpledf_monthly['count'], name = 'Simple BAS' )
    )  
    figure.update_xaxes(title_text='Month')
    figure.update_yaxes(title_text='Count')

        
    return figure

@app.callback(
    [
    Output("org_both_text", "children"),
    Output("user_both_text", "children"),
    Output("user_either_text", "children"),
    Output("userorganisation_graph", "figure")
    ],
    [ Input("date_picker", "start_date"),
    Input("date_picker", "end_date"),
    Input("payment_status", "value")],
)
def update_userorg(start_date, end_date, payment_status):

    fullbas_w_org = pd.merge(fullbas, orgdetails, left_on='orgid', right_on='organisationid', how="inner")
    fullbas_w_org = helper.filter_by_payingflag(fullbas_w_org,payment_status)
    fullbas_w_org = helper.filter_by_time(fullbas_w_org, start_date, end_date)

    simpledf = helper.filter_by_time(simplebas, start_date, end_date)


    inner_res = pd.merge(simpledf, fullbas_w_org, left_on='userid', right_on='userid', how="inner")
    outer_res = pd.merge(simpledf, fullbas_w_org, left_on='userid', right_on='userid', how="outer")


    org_both = len(inner_res[['userid', 'orgid']].drop_duplicates())
    user_both = len(inner_res[['userid', 'orgid']].drop_duplicates())
    user_either = len(outer_res[['userid', 'orgid']].drop_duplicates())

    hist = outer_res[['userid', 'orgid']].drop_duplicates().dropna().groupby('userid').size().reset_index(name='count')

    figure = go.Figure(data =[ go.Histogram(x=hist['count'].values)])
    figure.update_yaxes(type='log', title_text='Count')
    figure.update_xaxes(title_text='No. of organisation user ran report for in the sample')


    return org_both, user_both, user_either, figure


# Selectors, main graph -> pie graph
@app.callback(
    Output("plans_piegraph", "figure"),
    [
    Input("date_picker", "start_date"),
    Input("date_picker", "end_date")
    ],
)
def make_pie_figure(start_date, end_date):
    product_pie = orgdetails['productoption'].groupby(orgdetails['productoption']).count().reset_index(name='count')
    product_pie.loc[product_pie['count']<50, 'productoption'] = 'Other'

    fig = go.Figure(
        data=[
            go.Pie(
                labels=product_pie['productoption'], 
                values=product_pie['count'], 
                hole=0.4)
                ]
        )
    fig.update_traces(textposition='inside', textinfo='percent+label')

    return fig







if __name__ == '__main__':
    
    app.run_server(debug=True, port=5000)

