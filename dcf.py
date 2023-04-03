import yahooquery as yq
import pandas as pd
import numpy as np
import streamlit as st




st.title("DCF")
with st.sidebar:
    name = st.text_input('Stock Ticker', value='MSFT')
    years = int(st.number_input('Forecast (years)',value=5))






asset = yq.Ticker(name)

incm_stmt = asset.income_statement()
incm_stmt.index = incm_stmt.asOfDate 
cash_flow = asset.cash_flow()
cash_flow.index = cash_flow.asOfDate 
bln_sht = asset.balance_sheet()
bln_sht.index = bln_sht.asOfDate 
stats = asset.key_stats

historical_revenue = incm_stmt.TotalRevenue
ebitda = incm_stmt.ReconciledDepreciation + incm_stmt.EBIT
d_and_a = ebitda - incm_stmt.EBIT

if 'CapitalExpenditureReported' in cash_flow.columns:
    capex = cash_flow['CapitalExpenditureReported']
else:
    capex = cash_flow.NetPPEPurchaseAndSale + incm_stmt.ReconciledDepreciation
    
chng_work_cap = cash_flow.ChangeInWorkingCapital
tax_rate = incm_stmt.TaxRateForCalcs[-1]

risk_free_rate = yq.Ticker('^FVX').history().close.iloc[-1]/100
market_risk_premium = yq.Ticker('^GSPC').history(interval='1mo', period='10y').close.pct_change(12).mean()
equity_beta = stats[name]['beta']
return_on_debt = incm_stmt.InterestExpense[-1]/bln_sht.TotalDebt[-1]
total_debt = bln_sht.TotalDebt[-1]
market_value_equity = asset.history(interval='1mo', period='10y').close.iloc[-1]*stats[name]['sharesOutstanding']
cash = bln_sht['CashAndCashEquivalents'][-1]
shares_outstanding = stats[name]['sharesOutstanding']


ret_on_equity = risk_free_rate + equity_beta*(market_risk_premium)
discount_rate = ret_on_equity * market_value_equity / (market_value_equity + total_debt) + return_on_debt * (1 - tax_rate) * total_debt/(market_value_equity + total_debt)
with st.sidebar:
    st.text("##Key Assumptions")

    wacc = st.number_input('Discount Rate',value=discount_rate)
    exit_multiple = st.number_input("Exit Multiple", value=stats[name]['enterpriseValue']/ebitda[-1])
    st.text("##Income Statement Assumptions")

    revenue_growth_rate= st.number_input('Revenue Growth Rate',value=-1.0)
    ebitda_growth_rate = st.number_input('EBITDA Margin',value=-1.0)
    d_and_a_growth_rate = st.number_input('Depreciation Margin',value=-1.0)
    st.text("##Cash Flow Assumptions")
    capex_growth_rate = st.number_input('Capex Margin',value=-1.0)
    working_cap_growth_rate = st.number_input('Working Cap Margin',value=-1.0)




def revenue_forecast(historical_revenue, years, growth_rate = -1):
    historical_revenue_growth = np.diff(historical_revenue)/historical_revenue[:-1]
    average_revenue_growth = historical_revenue_growth.mean()
    if growth_rate != -1:
        average_revenue_growth = growth_rate
    forecast_revenue = [historical_revenue[-1]]
    for i in range (0, years):
        forecast_revenue.append(forecast_revenue[i]*(1 + average_revenue_growth))
    forecast_revenue = forecast_revenue[1:]
    return forecast_revenue
def ebitda_forecast(ebitda, historical_revenue, forecast_revenue, years,growth_rate = -1):
    ebitda_margin = ebitda/historical_revenue
    average_ebitda_margin = ebitda_margin.mean()
    if growth_rate != -1:
        average_ebitda_margin = growth_rate
    forecast_ebitda = []
    for i in range (0, years):
        forecast_ebitda.append(forecast_revenue[i]* average_ebitda_margin )
    return forecast_ebitda
def d_and_a_forecast(d_and_a, historical_revenue, forecast_revenue, years,growth_rate = -1):
    d_and_a_margin = d_and_a/historical_revenue
    average_d_and_a_margin = d_and_a_margin.mean()
    if growth_rate != -1:
        d_and_a_margin = growth_rate
    forecast_d_and_a = []
    for i in range (0, years):
        forecast_d_and_a.append(forecast_revenue[i]* average_d_and_a_margin )
    return forecast_d_and_a
def capex_forecast(capex, historical_revenue, forecast_revenue, years,growth_rate = -1):
    capex_margin = capex/historical_revenue
    average_capex_margin = capex_margin.mean()
    if growth_rate != -1:
        average_capex_margin = growth_rate
    forecast_capex = []
    for i in range (0, years):
        forecast_capex.append(forecast_revenue[i]* average_capex_margin )
    return forecast_capex
def work_cap_forecast(chng_work_cap, historical_revenue, forecast_revenue, years, growth_rate = -1):
    chng_work_cap_margin = chng_work_cap/historical_revenue
    average_chng_work_cap_margin = chng_work_cap_margin.mean()
    if growth_rate != -1:
        average_chng_work_cap_margin = growth_rate
    forecast_chng_work_cap = []
    for i in range (0, years):
        forecast_chng_work_cap.append(forecast_revenue[i]* average_chng_work_cap_margin )
    return forecast_chng_work_cap

forecast_revenue = revenue_forecast(historical_revenue, years, growth_rate=revenue_growth_rate)
forecast_ebitda = ebitda_forecast(ebitda, historical_revenue, forecast_revenue, years, growth_rate=ebitda_growth_rate)
forecast_d_and_a = d_and_a_forecast(d_and_a, historical_revenue, forecast_revenue, years, growth_rate=d_and_a_growth_rate)
forecast_capex = capex_forecast(capex, historical_revenue, forecast_revenue, years, growth_rate=capex_growth_rate)
forecast_chng_work_cap = work_cap_forecast(chng_work_cap, historical_revenue, forecast_revenue, years, growth_rate=working_cap_growth_rate)



def net_income_calc(forecast_ebitda, forecast_d_and_a, tax_rate):
    pre_tax_income = forecast_ebitda  - np.array(forecast_d_and_a)
    taxes = pre_tax_income * tax_rate
    net_income = pre_tax_income - taxes
    return net_income

# def terminal_value_calc(forecast_ebitda, exit_multiple):
#     final_ebitda = forecast_ebitda[-1]
#     terminal_value = final_ebitda * exit_multiple
#     return terminal_value


net_income = net_income_calc(forecast_ebitda, forecast_d_and_a, tax_rate)
unlevered_fcf = net_income + forecast_d_and_a + forecast_capex - forecast_chng_work_cap


# def dcf(exit_multiple, wacc, forecast_ebitda, forecast_d_and_a, forecast_capex, forecast_chng_work_cap, years, tax_rate, total_debt, cash, shares_outstanding):
def dcf(wacc, exit_multiple):

    # pre_tax_income = forecast_ebitda  - np.array(forecast_d_and_a)
    # taxes = pre_tax_income * tax_rate
    # net_income = pre_tax_income - taxes

    unlevered_fcf = net_income + forecast_d_and_a + forecast_capex - forecast_chng_work_cap
    final_ebitda = forecast_ebitda[-1]
    terminal_value = final_ebitda * exit_multiple
    total_unlevered_fcf = unlevered_fcf.copy()
    total_unlevered_fcf[-1] += terminal_value
    discount_period = np.arange(1, years+1)
    discount_factors = 1/(1 + wacc)**discount_period
    discounted_cash_flows = discount_factors * total_unlevered_fcf
    pv_ev = np.sum(discounted_cash_flows)
    pv_tv = discount_factors[-1] * terminal_value
    tv_pct_ev = pv_tv/pv_ev


    equity_value = pv_ev - total_debt + cash
    equity_val_share = equity_value/shares_outstanding
    growth_rate = (wacc * terminal_value - unlevered_fcf[-1])/(terminal_value + unlevered_fcf[-1])
    return (growth_rate, equity_val_share, tv_pct_ev, terminal_value, total_unlevered_fcf, discount_factors, pv_ev, pv_tv)
def what_if(x_inc, y_inc, x_median, y_median, count, function, value):
    print(x_median)
    X = np.arange(x_median - count//2*x_inc, x_median+ x_inc + count//2*x_inc, x_inc)[:count]
    print(X)
    Y = np.arange(y_median - count//2*y_inc, y_median + y_inc + count//2*y_inc, y_inc)[:count]
    print(Y)

    ret = []
    for i in range(0, count):
        add = []
        for j in range(0, count):
            add.append(function(X[i], Y[j])[value])
        ret.append(add)
    df = pd.DataFrame(ret, index=X, columns= Y)
    return df


income_values_index = ['Revenue', 'EBITDA', 'Depreciation and Amortization', 'Net Income']
forecast_years = pd.date_range(start=incm_stmt.index[-1], periods = years+1, freq = 'Y')[1:]
income_values = pd.DataFrame(np.array([forecast_revenue, forecast_ebitda, forecast_d_and_a, net_income]), index=income_values_index, columns=forecast_years)

st.table(income_values)


cash_flow_values_index = ['Net Income', 'Depreciation Add Back', 'Less: Capex', 'Less: Change in Working Capital', 'Unlevered Free Cash Flow']
cash_flow_values = pd.DataFrame(np.array([net_income, forecast_d_and_a, forecast_capex, forecast_chng_work_cap, unlevered_fcf]), index=cash_flow_values_index, columns=forecast_years)

st.table(cash_flow_values)

st.table(what_if(0.01, 1, wacc, exit_multiple, 5, dcf, 0))
st.table(what_if(0.01, 1, wacc, exit_multiple, 5, dcf, 1))