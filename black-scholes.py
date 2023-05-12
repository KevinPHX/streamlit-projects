import yfinance as yf
import math
import numpy as np
import streamlit as st
import yahooquery as yq

def cdf(x):
    return (1 + math.erf(x))/2
def blackscholes(spot, strike, risk_free, time, volatility, iscall=True):
    def d1():
        if ((volatility * math.sqrt(time)) > 0 and strike > 0):
            return (math.log(spot/strike) + (risk_free + (volatility**2)/2)*time)/(volatility * math.sqrt(time))
        else:
            return 0
    def d2():
        first = d1()
        return first - volatility * math.sqrt(time)
    first = d1()
    second = d2()
    if iscall:
        return cdf(first) * spot - cdf(second)* strike * math.exp(-1 * risk_free * time)
    else:
        return cdf(-second)* strike * math.exp(-1 * risk_free * time) - cdf(-first) * spot

st.title("Black Scholes")
with st.sidebar:
    spot = st.number_input('Spot price')
    strike = st.number_input('Strike price')
    risk_free = st.number_input('Risk Free')
    time = st.number_input('Time')
    volatility = st.number_input('Volatility')

cols = st.columns(2)
with cols[0]:
    st.text(blackscholes(spot, strike, risk_free, time, volatility))





