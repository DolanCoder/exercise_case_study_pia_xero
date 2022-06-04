'''
helper file consisting of helper functions
'''

from datetime import date,  datetime, timedelta
import pandas as pd


def filter_by_time(df, start_date, end_date):

    dff = df[
        (df["datetime"].dt.date > datetime.strptime(start_date, "%Y-%m-%d").date())
        & (df["datetime"].dt.date < datetime.strptime(end_date, "%Y-%m-%d").date())
    ]
    return dff

def filter_by_payingflag(df, paying_status):
    return df[df['payingflag'].isin(list(map(int, paying_status)))]

def filter_by_status(df, status):
    return df[df['organisationstatus'].isin(list(map(int, status)))]