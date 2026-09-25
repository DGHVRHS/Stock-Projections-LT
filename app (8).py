import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

st.set_page_config(page_title="Student Stock & Portfolio Analyzer", layout="wide")

# Pre-populated Stock List
STOCKS_DICT = {
    "Apple Inc.": "AAPL",
    "Microsoft Corp.": "MSFT",
    "Alphabet Inc. (Google)": "GOOGL",
    "Amazon.com Inc.": "AMZN",
    "NVIDIA Corp.": "NVDA",
    "Tesla Inc.": "TSLA",
    "JPMorgan Chase & Co.": "JPM",
    "Walmart Inc.": "WMT",
    "Coca-Cola Co.": "KO",
    "Disney (Walt) Co.": "DIS"
}

st.title("📈 Student Stock & Portfolio Analyzer")
st.markdown("Analyze individual stock metrics, project potential returns, and assemble a practice portfolio.")

tab1, tab2 = st.tabs(["📊 Single Stock Analysis", "💼 Portfolio Builder"])

# ==========================================
# TAB 1: SINGLE STOCK ANALYSIS
# ==========================================
with tab1:
    st.header("Single Stock Deep Dive")
    
    col_sel1, col_sel2 = st.columns([2, 1])
    with col_sel1:
        selected_name = st.selectbox("Select a Company", list(STOCKS_DICT.keys()))
        ticker_symbol = STOCKS_DICT[selected_name]
    with col_sel2:
        custom_ticker = st.text_input("Or enter custom Ticker (e.g., SPY, AMD):").upper()
        if custom_ticker:
            ticker_symbol = custom_ticker
            selected_name = custom_ticker

    ticker_data = yf.Ticker(ticker_symbol)

    # Fetch YTD Data
    ytd_df = ticker_data.history(period="ytd")
    
    if not ytd_df.empty:
        # Key Metrics Overview
        info = ticker_data.info
        
        current_price = ytd_df['Close'].iloc[-1]
        start_price_ytd = ytd_df['Close'].iloc[0]
        ytd_return = ((current_price - start_price_ytd) / start_price_ytd) * 100

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Current Price", f"${current_price:.2f}")
        m2.metric("YTD Performance", f"{ytd_return:.2f}%")
        m3.metric("Market Cap", f"${info.get('marketCap', 0):,}")
        m4.metric("P/E Ratio", f"{info.get('trailingPE', 'N/A')}")

        # YTD Price Chart
        st.subheader("YTD Price Movement")
        fig_ytd = px.line(ytd_df, x=ytd_df.index, y='Close', title=f"{selected_name} ({ticker_symbol}) - Year to Date")
        st.plotly_chart(fig_ytd, use_container_width=True)

        # Average Historical Return Calculation (5-Year CAGR)
        st.subheader("Historical Rate of Return")
        hist_5y = ticker_data.history(period="5y")
        
        if len(hist_5y) > 0:
            start_val = hist_5y['Close'].iloc[0]
            end_val = hist_5y['Close'].iloc[-1]
            years = (hist_5y.index[-1] - hist_5y.index[0]).days / 365.25
            
            # Compound Annual Growth Rate (CAGR) formula: ((End/Start)^(1/n)) - 1
            cagr = ((end_val / start_val) ** (1 / years) - 1) * 100
            st.info(f"The 5-Year Compound Annual Growth Rate (CAGR) for **{ticker_symbol}** is **{cagr:.2f}%** per year.")

            # Investment Simulator
            st.subheader("💰 Investment Simulator")
            col_inv1, col_inv2 = st.columns(2)
            with col_inv1:
                initial_investment = st.number_input("Initial Investment ($)", min_value=100, value=1000, step=100)
                inv_years = st.slider("Investment Horizon (Years)", min_value=1, max_value=30, value=10)
            with col_inv2:
                custom_rate = st.number_input("Expected Annual Return (%)", value=float(round(cagr, 2)))

            # Calculate future value: FV = PV * (1 + r)^t
            time_series = list(range(0, inv_years + 1))
            projected_values = [initial_investment * ((1 + (custom_rate / 100)) ** t) for t in time_series]
            
            sim_df = pd.DataFrame({"Year": time_series, "Projected Value ($)": projected_values})
            fig_sim = px.bar(sim_df, x="Year", y="Projected Value ($)", title=f"Growth of ${initial_investment} at {custom_rate:.2f}% Return")
            st.plotly_chart(fig_sim, use_container_width=True)
            
            final_val = projected_values[-1]
            st.success(f"Estimated value after {inv_years} years: **${final_val:,.2f}** (Gain: **${final_val - initial_investment:,.2f}**) ")
    else:
        st.error("Invalid ticker or no data found. Please check your stock choice.")

# ==========================================
# TAB 2: PORTFOLIO BUILDER
# ==========================================
with tab2:
    st.header("Build & Test a Stock Portfolio")
    
    selected_portfolio = st.multiselect(
        "Select 2 to 5 Stocks for your Portfolio",
        options=list(STOCKS_DICT.values()),
        default=["AAPL", "MSFT", "GOOGL"]
    )

    if len(selected_portfolio) > 0:
        st.subheader("Set Allocation Weights")
        weights = {}
        cols = st.columns(len(selected_portfolio))
        
        default_weight = float(round(100 / len(selected_portfolio), 2))
        for i, symbol in enumerate(selected_portfolio):
            with cols[i]:
                weights[symbol] = st.number_input(f"Weight % for {symbol}", min_value=0.0, max_value=100.0, value=default_weight)

        total_weight = sum(weights.values())
        if abs(total_weight - 100.0) > 0.01:
            st.warning(f"Total allocation must equal 100%. Current total: **{total_weight:.1f}%**")
        else:
            # Download 3-year historical data for selected stocks
            portfolio_df = pd.DataFrame()
            returns_data = {}
            
            for symbol in selected_portfolio:
                data = yf.Ticker(symbol).history(period="3y")['Close']
                # Calculate annualized return
                if not data.empty:
                    cagr_i = ((data.iloc[-1] / data.iloc[0]) ** (1 / 3) - 1) * 100
                    returns_data[symbol] = cagr_i
                    portfolio_df[symbol] = data

            # Calculate Weighted Portfolio Return
            weighted_return = sum((weights[sym] / 100) * returns_data[sym] for sym in selected_portfolio)

            st.markdown("---")
            st.metric("Expected Portfolio Annual Return (3-Yr CAGR)", f"{weighted_return:.2f}%")

            # Compare individual returns
            ret_summary = pd.DataFrame({
                "Ticker": list(returns_data.keys()),
                "Weight (%)": [weights[s] for s in returns_data.keys()],
                "3-Yr CAGR (%)": [returns_data[s] for s in returns_data.keys()]
            })
            
            col_tbl, col_pie = st.columns([2, 1])
            with col_tbl:
                st.dataframe(ret_summary.style.format({"Weight (%)": "{:.1f}", "3-Yr CAGR (%)": "{:.2f}"}))
            with col_pie:
                fig_pie = px.pie(names=list(weights.keys()), values=list(weights.values()), title="Portfolio Allocation")
                st.plotly_chart(fig_pie, use_container_width=True)

            # Portfolio Investment Simulation
            st.subheader("Portfolio Growth Simulation")
            p_invest = st.number_input("Total Portfolio Investment ($)", value=10000, step=1000)
            p_years = st.slider("Simulation Period (Years)", 1, 30, 10, key="p_slider")
            
            p_values = [p_invest * ((1 + (weighted_return / 100)) ** t) for t in range(p_years + 1)]
            p_sim_df = pd.DataFrame({"Year": list(range(p_years + 1)), "Portfolio Value ($)": p_values})
            
            fig_p_sim = px.line(p_sim_df, x="Year", y="Portfolio Value ($)", title=f"Projected Portfolio Value Over {p_years} Years")
            st.plotly_chart(fig_p_sim, use_container_width=True)
