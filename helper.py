'''
helper file consisting of helper functions
'''

from datetime import date,  datetime, timedelta
import pandas as pd
import scipy.signal
import numpy as np


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


def fft(series):
    '''
    input: pandas data column
    output: fft and the frequency of the fft
    '''
    L = series.dropna()
    # L = np.round(L, 1)
    # Remove DC component
    L -= np.mean(L)
    # Window signal
    L *= scipy.signal.windows.hann(len(L))

    fft = np.fft.rfft(L, norm="forward")
    freq = np.fft.fftfreq(len(L), d=1)

    return fft, freq
