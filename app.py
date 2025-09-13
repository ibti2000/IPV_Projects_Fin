import streamlit as st
from bsm import blackscholes
import pandas as pd
import altair as alt
import yfinance as yf

st.sidebar.markdown("[View Source Code](https://github.com/ibti2000/IPV_Projects_Fin)")

st.title("Independent Price Verification Tool - BSM Option Pricer")

spot_choice = st.radio("Select Spot Price Input Method:",
                       ["Manual Input", "Live Market Price"])


if spot_choice == "Manual Input":
    S_live = st.number_input("Spot Price (S)", value = 100.0)
else:
    ticker_symbol = st.text_input("Enter Stock Ticker", value="")
    if ticker_symbol:
        try:
            stock = yf.Ticker(ticker_symbol)
            S_live = stock.history(period="1d")["Close"].iloc[-1]
            st.info(f"Live Spot Price for {ticker_symbol}:{S_live:.2f}")
        except Exception as e:
            st.error(f"Could not fetch live price: {e}")
            S_live = st.number_input("Spot Price (S) AS fallback", value = 100.0)
        

#S = st.number_input("Spot Price (S)", value = 100.0)
K = st.number_input("Excercise Price (K)", value = 95.0)
T = st.number_input("Time to Maturity (T)", value = 2.0)
r = st.number_input("Risk Free Rate (put decimal)", value = 0.05)
sigma = st.number_input("Volatility (put decimal)", value = 0.5)
option_type = st.selectbox("Option Type", ["call", "put"])

#Calculate now

if st.button("Calculate Option Price"):
    price, delta, gamma, vega = blackscholes(S_live, K, T, r, sigma, option_type)
    st.success(f"BSM Price {option_type.capitalize()} Price: {price:.2f}") #colon needed
    st.write(f"BSM {option_type.capitalize()} Price: {price:.2f}")
    st.write(f"**Delta:** {delta:.4f}")
    st.write(f"**Gamma:** {gamma:.4f}")
    st.write(f"**Vega:** {vega:.4f}")

uploaded_file = st.file_uploader("Upload Trader Data", type="csv") #file upload button


if uploaded_file: #to tell if there is a uploaded file then make it a variable df
    df = pd.read_csv(uploaded_file) #now name of the file is df; also naturally pandas convert it to dataframe
    df["Spot"] = S_live
    df[["BSM Price", "Delta", "Gamma", "Vega"]] = df.apply(lambda row: pd.Series(blackscholes(S_live, row["Strike"], row["Time"], row["Rate"], row["Volatility"], row["Type"])), axis=1)
    df["difference"] = df["TraderPrice"] - df["BSM Price"]
    #st.subheader("Trader Prices vs BSM Prices")
    #st.dataframe(df) #this will now show the df in streamlit as dataframe

    st.subheader("Filtering")

    option_types = df["Type"].dropna().unique().tolist()

    selected_types = st.multiselect("Select Option Type", options = option_types, default= option_types)

    min_strike = float(df["Strike"].min())
    max_strike = float(df["Strike"].max())
    strike_range = st.slider("Strike Price Range",
                             min_value = min_strike,
                             max_value= max_strike,
                             value = (min_strike, max_strike))
    
    filtered_df = df[(df["Type"].isin(selected_types)) &
                     (df["Strike"].between(strike_range[0],
                    strike_range[1]))]    
    
    st.subheader("Filtered Data Preview")
    st.dataframe(filtered_df)

    st.subheader("Mispricing Summary")

    max_diff = filtered_df["difference"].max()
    min_diff = filtered_df["difference"].min()
    avg_diff = filtered_df["difference"].mean()
    overpriced_count = (filtered_df["difference"] > 0).sum()
    underpriced_count = (filtered_df["difference"] < 0).sum()

    summary_df = pd.DataFrame({
        "Metric" : ["Max Mispricing", "Min Mispricing", "Avg Mispricing", "Number Overpriced", "Number Underpriced"],
        "Value" : [max_diff, min_diff, avg_diff, overpriced_count, underpriced_count]
    })

    st.table(summary_df)

    col1, col2, col3, col4, col5 = st.columns(5) #col1 is variable name

    col1.metric("Max Mispricing", f"{max_diff:.2f}")
    col2.metric("Min Mispricing", f"{min_diff:.2f}")
    col3.metric("Avg Mispricing", f"{avg_diff:.2f}")
    col4.metric("Overpriced Count", overpriced_count)
    col5.metric("Underpriced Count", underpriced_count)


    st.subheader("Option Type Breakdown")

    option_group = filtered_df.groupby("Type")["difference"].agg(["mean", "max", "min", "count"])
    option_group = option_group.rename(columns= {"mean": "Avg Diff", "max": "Max Diff", "min": "Min Diff", "count": "Trade Count"})

    st.dataframe(option_group)

    st.subheader("Trader vs BSM Price Chart")

    chart = alt.Chart(filtered_df).mark_bar().encode(
    x = alt.X("Type:N", title = "Option Type"),
    y = alt.Y("difference:Q", title = "Trader - BSM Price"),
    color = alt.condition(
        alt.datum.difference > 0,
        alt.value("green"),
        alt.value("red")
    ),
    tooltip=["Spot", "Strike", "TraderPrice", "BSM Price", "difference", "Delta", "Gamma", "Vega"]
    ).properties(
    width = 600,
    height = 400,
    title = "Trader vs Model Price difference"
    )

    st.altair_chart(chart)

    st.subheader("Top 5 OverPriced Options")

    #Top Mispriced table
    st.dataframe(filtered_df.nlargest(5, "difference")
                 [["Spot", "Strike", "TraderPrice", "BSM Price", "difference"]]
                 )
    st.dataframe(filtered_df.nsmallest(5, "difference")
                 [["Spot", "Strike", "TraderPrice", "BSM Price", "difference"]]
                ) #double brackt picks multiple column [[]]
    
    
    #a histogram showing mispricing differences on histo

    st.subheader("Mispricing distribution")
    hist_chart = alt.Chart(filtered_df).mark_bar().encode(
    x= alt.X("difference:Q", bin = alt.Bin(maxbins=30), title = "Mispriced Values"),
    y = "count()",
    tooltip = ["count()"]
    ).properties(width=600, height = 400)
    st.altair_chart(hist_chart)

    st.download_button(
        "Download Filtered Data",
        filtered_df.to_csv(index = False).encode("utf-8"),
        "filtered_data.csv", #<--filename
        "text/csv"
    )
    #encode utf-8 is general for conversion browser friendly
    #text/csv to tell its a csv file 
    #download_button - a st feature





