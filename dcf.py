import yahooquery as yq
import pandas as pd
import numpy as np
import streamlit as st
import seaborn as sns
import matplotlib.pyplot as plt
from  matplotlib.colors import LinearSegmentedColormap
cmap=LinearSegmentedColormap.from_list('rg',["r", "w", "g"], N=256) 

def calculate_beta(asset, market):
    return np.cov([asset, market])[0, 1]/np.var(market)

st.markdown(
        """
       <style>
        @media screen and (min-width: 600px) {
            [data-testid="stSidebar"][aria-expanded="true"]{
                min-width: 550px;
            }
        }
       """,
        unsafe_allow_html=True,
    )   
# st.title("DCF")
with st.sidebar:
    name = st.text_input('Stock Ticker', value='MSFT')
    years = int(st.number_input('Forecast (years)',value=5, min_value=1))
    inMM = st.checkbox('Numbers in MM')


try:

    asset = yq.Ticker(name)
    if asset.quote_type[name]['quoteType'] != 'EQUITY':
        st.header('Please use a stock ticker')
    else:
        st.title(f"DCF for {asset.quote_type[name]['longName']}")
        

        incm_stmt = asset.income_statement()
        incm_stmt = incm_stmt[incm_stmt.periodType=='12M']
        incm_stmt.index = incm_stmt.asOfDate 
        cash_flow = asset.cash_flow()
        cash_flow = cash_flow[cash_flow.periodType=='12M']
        cash_flow.index = cash_flow.asOfDate 
        bln_sht = asset.balance_sheet()
        bln_sht = bln_sht[bln_sht.periodType=='12M']
        bln_sht.index = bln_sht.asOfDate 
        stats = asset.key_stats
        fin_data = asset.financial_data
        historical_revenue = incm_stmt.TotalRevenue
        summary = asset.summary_detail
        # if 'EBIT' in incm_stmt.columns:
        if "ReconciledDepreciation" in incm_stmt.columns:
            d_and_a = incm_stmt.ReconciledDepreciation
        else:
            d_and_a = np.zeros(len(incm_stmt.index))
        ebitda = d_and_a + incm_stmt.EBIT
        # elif 'OperatingIncome' in incm_stmt.columns:
        #     ebitda = incm_stmt.OperatingIncome
        # elif 'GrossProfit' in incm_stmt.columns:
        #     ebitda = incm_stmt.GrossProfit
        # elif 'PretaxIncome' in incm_stmt.columns:
        #     ebitda = incm_stmt.PretaxIncome
        # else:
        #     ebitda = historical_revenue
        

        if 'CapitalExpenditureReported' in cash_flow.columns:
            capex = cash_flow['CapitalExpenditureReported']
        elif 'NetPPEPurchaseAndSale' in cash_flow.columns:
            capex = cash_flow.NetPPEPurchaseAndSale + d_and_a
        else:
            capex = d_and_a
            
        chng_work_cap = cash_flow.ChangeInWorkingCapital
        tax_rate = incm_stmt.TaxRateForCalcs[-1]

        risk_free_rate = yq.Ticker('^IRX').history().close.iloc[-1]/100
        market_risk_premium = yq.Ticker('^GSPC').history(interval='1mo', period='10y').close.pct_change(12).mean()
        equity_beta = 1
        if 'beta' in stats[name].keys():
            equity_beta = stats[name]['beta']
        else:
            market = yq.Ticker('^GSPC')
            asst = asset.history(period='max').reset_index(level=[0,1])
            asst.index = asst['date']
            asst = asst['close'].to_frame()
            asst.columns = ['asset']
            mkt = market.history(period='max').reset_index(level=[0,1])
            mkt.index = mkt['date']
            mkt = mkt['close'].to_frame()
            mkt.columns = ['market']
            df = pd.concat([asst, mkt], join='inner', axis = 1).pct_change(1).dropna()
            equity_beta = calculate_beta(df['asset'], df['market'])
        if "totalDebt" in fin_data[name].keys():
            total_debt = fin_data[name]['totalDebt']
        else:
            total_debt = bln_sht.TotalDebt[-1]
        if 'InterestExpense' in incm_stmt:
            return_on_debt = incm_stmt.InterestExpense.fillna(0)[-1]/total_debt
        else:
            return_on_debt = np.zeros(len(incm_stmt.index))
        market_value_equity = summary[name]['marketCap']
        if "totalCash" in fin_data[name].keys():
            cash = fin_data[name]['totalCash']
        elif 'CashCashEquivalentsAndShortTermInvestments' in bln_sht.columns:
             cash = bln_sht['CashCashEquivalentsAndShortTermInvestments'][-1]
        else:
            cash = bln_sht['CashAndCashEquivalents'][-1]
        shares_outstanding = stats[name]['sharesOutstanding']
        forecast_years = pd.date_range(start=incm_stmt.index[-1]+pd.DateOffset(years=1), periods = years, freq = 'Y').date

        # if "returnOnEquity" in fin_data[name].keys():
        #     ret_on_equity = fin_data[name]['returnOnEquity']
        # else:
        ret_on_equity = risk_free_rate + equity_beta*(market_risk_premium)
        current_multiple = stats[name]['enterpriseValue']/ebitda[-1]
        with st.sidebar:
            st.header("Key Assumptions")

            
            tax = st.number_input("Tax Rate", value = tax_rate)
            equ_debt = total_debt + market_value_equity
            e_discount_rate = ret_on_equity * market_value_equity / (equ_debt) 
            d_discount_rate = return_on_debt * (1 - tax) * (total_debt)/(equ_debt)
            discount_rate = e_discount_rate + d_discount_rate
            if "before" not in st.session_state:
                st.session_state.before = discount_rate
            wacc = st.number_input('Discount Rate',value=st.session_state.before, step=1e-4, format="%.4f", key='asdf')
            exit_multiple = st.number_input("Exit Multiple", value=current_multiple)


        historical_revenue_growth = np.diff(historical_revenue)/historical_revenue[:-1]
        historical_revenue_growth.replace([np.inf, -np.inf], 0, inplace=True)
        average_revenue_growth = historical_revenue_growth.mean()
        ebitda_margin = ebitda/historical_revenue
        ebitda_margin.replace([np.inf, -np.inf], 0, inplace=True)
        average_ebitda_margin = ebitda_margin.mean()
        d_and_a_margin = d_and_a/historical_revenue
        d_and_a_margin.replace([np.inf, -np.inf], 0, inplace=True)
        average_d_and_a_margin = d_and_a_margin.mean()
        capex_margin = capex/historical_revenue
        capex_margin.replace([np.inf, -np.inf], 0, inplace=True)
        average_capex_margin = capex_margin.mean()
        chng_work_cap_margin = chng_work_cap/historical_revenue
        chng_work_cap_margin.replace([np.inf, -np.inf], 0, inplace=True)
        average_chng_work_cap_margin = chng_work_cap_margin.mean()
        with st.sidebar:
            st.header("Income Statement Assumptions")
            st.text("Adjust Forecasted Revenues")

            revenue_growth_rate= st.number_input('Revenue Growth Rate',value=average_revenue_growth, step=1e-5, format="%.5f")


        with st.sidebar:
            st.text("Yearly Forecasted Revenues")

        forecast_revenue = [historical_revenue[-1]]
        for i in range (0, years):
            current_year = str(forecast_years[i])
            with st.sidebar:
                cols_rev=st.sidebar.columns(2)
                with cols_rev[0]:
                    rev_rate = st.number_input(f'Revenue Margin for {current_year}',value=(revenue_growth_rate), step=1e-5, format="%.5f")
                with cols_rev[1]:
                    new_rev = st.number_input(f'Revenue for {current_year}',value=forecast_revenue[i]*(1 + rev_rate))
                forecast_revenue.append(new_rev)
        forecast_revenue = forecast_revenue[1:]
        with st.sidebar:
            st.text("Adjust Forecasted EBITDA")
            ebitda_growth_rate = st.number_input('EBITDA Margin',value=average_ebitda_margin, step=1e-5, format="%.5f")


        with st.sidebar:
            st.text("Yearly Forecasted EBITDA")
        forecast_ebitda = []
        for i in range (0, years):
            current_year = str(forecast_years[i])
            with st.sidebar:
                cols_ebitda=st.sidebar.columns(2)
                with cols_ebitda[0]:
                    ebitda_rates = st.number_input(f'EBITDA margin for {current_year}',value=ebitda_growth_rate, step=1e-5, format="%.5f")
                with cols_ebitda[1]:
                    new_ebitda = st.number_input(f'EBITDA for {current_year}', value=forecast_revenue[i]* ebitda_rates)
                    forecast_ebitda.append(new_ebitda)

        with st.sidebar:
            st.text("Adjust Forecasted Depreciation and Amortization ")
            d_and_a_growth_rate = st.number_input('Depreciation Margin',value=average_d_and_a_margin, step=1e-5, format="%.5f")
            
        with st.sidebar:
            st.text("Yearly Forecasted Depreciation and Amortization")
        forecast_d_and_a = []
        for i in range (0, years):
            current_year = str(forecast_years[i])
            with st.sidebar:
                cols_d_a=st.sidebar.columns(2)
                with cols_d_a[0]:
                    new_d_a = st.number_input(f'Depreciation Margin for {current_year}',value= d_and_a_growth_rate, step=1e-5, format="%.5f")
                with cols_d_a[1]:
                    forecast_d_and_a.append(st.number_input(f'Depreciation for {current_year}', value = new_d_a*forecast_revenue[i]))


        with st.sidebar:
            st.header("Cash Flow Assumptions")
            st.text('Adjust Forecasted Capex')
            capex_growth_rate = st.number_input('Capex Margin',value=average_capex_margin, step=1e-5, format="%.5f")
            
        with st.sidebar:
            st.text("Yearly Forecasted Capex")
        forecast_capex = []
        for i in range (0, years):
            current_year = str(forecast_years[i])
            with st.sidebar:
                cols_capex=st.sidebar.columns(2)
                with cols_capex[0]:
                    rate = st.number_input(f'Capex Margin for {current_year}',value= capex_growth_rate, step=1e-5, format="%.5f")
                with cols_capex[1]:
                    new_capex = rate*forecast_revenue[i]
                    forecast_capex.append(st.number_input(f'Capex for {current_year}', value = new_capex))


        with st.sidebar:
            st.text('Adjust Forecasted Change in Working Capital')
            working_cap_growth_rate = st.number_input('Working Cap Margin',value=average_chng_work_cap_margin, step=1e-5, format="%.5f")


        with st.sidebar:
            st.text("Yearly Forecasted Change in Working Capital")
        forecast_chng_work_cap = []
        for i in range (0, years):
            current_year = str(forecast_years[i])
            with st.sidebar:
                cols_wrk_cap=st.sidebar.columns(2)
                with cols_wrk_cap[0]:
                    work_cap_rate = st.number_input(f'Chng in Working Cap Margin for {current_year}',value= working_cap_growth_rate, step=1e-5, format="%.5f")
                with cols_wrk_cap[1]:
                    new_work_cap_rate = st.number_input(f'Chng in Working Cap for {current_year}', value =forecast_revenue[i]*work_cap_rate)
                    forecast_chng_work_cap.append(new_work_cap_rate)
            # forecast_chng_work_cap.append(forecast_revenue[i]* average_chng_work_cap_margin )



        def net_income_calc(forecast_ebitda, forecast_d_and_a, tax_rate):
            pre_tax_income = forecast_ebitda  - np.array(forecast_d_and_a)
            taxes = pre_tax_income * tax_rate
            net_income = pre_tax_income - taxes
            return net_income


        net_income = net_income_calc(forecast_ebitda, forecast_d_and_a, tax)
        unlevered_fcf = net_income + forecast_d_and_a + forecast_capex - forecast_chng_work_cap


        def dcf(wacc, exit_multiple):


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
            equity_val_share = np.maximum(0,equity_value/shares_outstanding)
            growth_rate = (wacc * terminal_value - unlevered_fcf[-1])/(terminal_value + unlevered_fcf[-1])
            return (growth_rate, equity_val_share, tv_pct_ev, terminal_value, total_unlevered_fcf, discount_factors, pv_ev, pv_tv)
        def what_if(x_inc, y_inc, x_median, y_median, count, function, value):
            X = np.arange(x_median - count//2*x_inc, x_median+ x_inc + count//2*x_inc, x_inc)[:count]
            Y = np.arange(y_median - count//2*y_inc, y_median + y_inc + count//2*y_inc, y_inc)[:count]

            ret = []
            for i in range(0, count):
                add = []
                for j in range(0, count):
                    add.append(function(X[i], Y[j])[value])
                ret.append(add)
            df = pd.DataFrame(ret, index=np.round(X, 3), columns= np.round(Y, 2)).T
            return df
        with st.sidebar:
            st.header("Sensitivity Analysis Settings")
            value_range = st.number_input("Range", value = 5)
            multiple_increment = st.number_input("Increment Exit Multiple", value = 1.0)
            growth_increment = st.number_input("Increment Growth", value = 0.01)

        income_values_index = ['Revenue', 'EBITDA', 'Depreciation and Amortization', 'Net Income']
        income_values = pd.DataFrame(np.array([forecast_revenue, forecast_ebitda, forecast_d_and_a, net_income]), index=income_values_index, columns=forecast_years)
        cash_flow_values_index = ['Net Income', 'Depreciation Add Back', 'Less: Capex', 'Less: Change in Working Capital', 'Unlevered Free Cash Flow']
        cash_flow_values = pd.DataFrame(np.array([net_income, forecast_d_and_a, forecast_capex, forecast_chng_work_cap, unlevered_fcf]), index=cash_flow_values_index, columns=forecast_years)
        growth_rates = what_if(growth_increment, multiple_increment, wacc, exit_multiple, value_range, dcf, 0)
        prices = what_if(growth_increment, multiple_increment, wacc, exit_multiple, value_range, dcf, 1)
        prices = prices.style
        if inMM:
            income_values = (income_values/1000000).round(3)
            cash_flow_values = (cash_flow_values/1000000).round(3)

        st.header('Income')
        st.table(income_values)

        st.header('Cash Flow')

        st.table(cash_flow_values)



        st.header('Sensativity Analysis')
        st.text('Growth Rates')

        st.table(growth_rates.style.background_gradient(cmap='RdYlGn', axis=None))
        st.text('Stock Price')


        st.table(prices.background_gradient(cmap='RdYlGn', axis=None))

except Exception as e:
    st.header('Something went wrong. Please try a different ticker')
    print(e)
