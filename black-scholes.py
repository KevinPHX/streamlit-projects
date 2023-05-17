from scipy.stats import norm
import math
import numpy as np
import pandas as pd
import streamlit as st
import yahooquery as yq
import matplotlib.pyplot as plt



st.title("Black Scholes")
with st.sidebar:
    custom = st.checkbox('Make custom Option')
    if custom:
        S_0 = st.number_input('Spot price')
        strike = st.number_input('Strike price')
        risk_free = st.number_input('Risk Free')
        T = st.number_input('Time')/356
        sigma = st.number_input('Volatility')
        iscall = st.checkbox('Call Option')
    else:
        name = st.text_input("Stock Ticker", value='MSFT')
        asset = yq.Ticker(name)
        options = asset.option_chain.reset_index(level=[0,1,2])
        date = st.selectbox(
         'Select a date',
        options.expiration.drop_duplicates())
        option_name = st.selectbox(
         'Select an option',
        options[options.expiration == date].contractSymbol)
        option = options[options.contractSymbol==option_name]
        S_0 = st.number_input('Spot price', value = asset.history().close.iloc[-1])
        strike = st.number_input('Strike price', value = option.strike.values[0])
        time = (option.expiration.values[0] - pd.Timestamp.today()).days
        risk_free = st.number_input('Risk Free')
        expiry = st.number_input('Time in Days', value = time)
        T = expiry/365
        sigma = st.number_input('Volatility', value = asset.history().close.pct_change(1).dropna().std()*math.sqrt(time))
        iscall = st.checkbox('Call Option', value = option.optionType.values[0] == 'calls')


    sample_size = st.number_input("Sample Size", value=50)
    N = st.number_input("Random Variables", value=1000)
    

current_time = 0




# sample_size = 50
# N = 1000
# # Share specific info
# risk_free = 0.1
# S_0 = 100
# sigma = 0.3

# # Option specific info
# strike = 110
# T = 1
# current_time = 0

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
        return norm.cdf(first) * spot - norm.cdf(second)* strike * math.exp(-1 * risk_free * time)
    else:
        return norm.cdf(-second)* strike * math.exp(-1 * risk_free * time) - norm.cdf(-first) * spot

def terminal_spot_price(current_spot, risk_free, volatility, time, z):
    return current_spot*np.exp((risk_free - volatility**2/2)*time + volatility * np.sqrt(time) * z )
def risk_neutral_pricing(terminal_spot, strike, risk_free, time, iscall):
    if iscall:
        return np.maximum(0, np.exp(-risk_free*time)*(terminal_spot - strike))
    else:
        return np.maximum(0, np.exp(-risk_free*time)*(strike-terminal_spot))

call_val = [None]*sample_size
call_std = [None]*sample_size
for i in range(1, sample_size+1):
    
    norm_array = norm.rvs(size = N*i)

    term_val = terminal_spot_price(S_0, risk_free, sigma, T-current_time, norm_array)

    mcall_val = risk_neutral_pricing(term_val, strike, risk_free, T-current_time, iscall)
    
    # store the mean and SD of these call values
    call_val[i-1] = np.mean(mcall_val)
    call_std[i-1] = np.std(mcall_val)/np.sqrt(i*N)


# cols=st.columns(2)
# with cols[0]:
#     plt.figure(figsize=(15,8))
#     plt.title("Distribution of Terminal Stock Prices Calculated using the Monte Carlo Simulation")
#     plt.xlabel("Terminal Stock Prices Calculates")
#     plt.ylabel("Times Calculated")
#     plt.hist(call_val, bins=30, ec="black")
#     st.pyplot(plt)


# with cols[1]:
bs = blackscholes(S_0, strike, risk_free, T-current_time, sigma, iscall)
# plotting the graph
plt.figure(figsize=(15,8))
plt.plot([bs]*sample_size)


plt.plot(call_val, ".")
plt.plot(bs+3*np.array(call_std), "r")
plt.plot(bs-3*np.array(call_std), "r")
to_table = {"Black-Scholes Pricing Model": bs,  "Monte-Carlo Simulation Mean":   sum(call_val) / len(call_val), "Monte-Carlo Simulation Std":  sum(call_std)/len(call_std)}

if not custom:
    plt.plot([option.lastPrice]*sample_size)
    to_table['Last Traded Price'] = option.lastPrice.values[0]
plt.xlabel("Sample Size")
plt.ylabel("Value")
st.table(pd.DataFrame(to_table, index=['Results']))
st.pyplot(plt)



