##BSM CODE WALKTHORUGH STREAMLIT CODE RIGHT BELOW
import numpy as np
from scipy.stats import norm

def blackscholes(S, K, T, r, sigma, option_type = "call"):
    #S = Spot Price, K = Strike Price, T = Maturity, r = risk free rate
    #sigma = standard deviation (volatility) option type impacts formula call or put

    d1 = (np.log(S/K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)

    #calculate option price now
    #d1: Standardized measure of how far the (forward-looking) stock price is above strike, adjusted for volatility and rf so like a bit tiled line of X on the right . STOCK SIDE CONT
    #d2 same as d1 but shift down - gives actual prob of excercise like now this is just straight X line and on the right as vol gone so chance of in the money if everyone is risk neutral EX COST OF STRIKE PMT

    if option_type.lower() == "call":   #parameter in function to decide btw call and put
        price = S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2) #call formula bsm S*N(d1) - K * e^-rt * N(d2)
        delta = norm.cdf(d1) #if option type is put as call; this will be returned and above one
    elif option_type.lower() == "put": #if put 
        price = K * np.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)
        delta = norm.cdf(d1) - 1 #n(d1) - 1
    else:
        raise ValueError("Option must be either 'call' or 'put'") #if sth else

    gamma = norm.pdf(d1) / (S * sigma * np.sqrt(T))  #this is n'(d1) / (s * vol * underoot T)
    vega = S * norm.pdf(d1) * np.sqrt(T) #this is S * N'(d1) * underoot T

    return price, delta, gamma, vega #now the values it recieves as parameters of function, these 4 are computed

#STREAMLIT CODE 
import streamlit as st
from bsm import blackscholes
import pandas as pd
import altair as alt
import yfinance as yf


st.title("Independent Price Verification Tool - BSM Option Pricer") #this is just a subheader title is our thing; st is streamlit

spot_choice = st.radio("Select Spot Price Input Method:", #spot_choice given as the name for st.radio function
                       ["Manual Input", "Live Market Price"]) #st.radio gives you # of options to choose from


if spot_choice == "Manual Input":
    S_live = st.number_input("Spot Price (S)", value = 100.0) #if we select manual input, we get the option to input a nmber with default value 100, and titled S
else:
    ticker_symbol = st.text_input("Enter Stock Ticker", value="") #else a text for stock
    if ticker_symbol: #if we reach ticker symbol
        try:
            stock = yf.Ticker(ticker_symbol)  #yf should extract the ticker symbol
            S_live = stock.history(period="1d")["Close"].iloc[-1] #go check the pricing history of daily pricing close price from the table and last price iloc -1
            st.info(f"Live Spot Price for {ticker_symbol}:{S_live:.2f}") #display as info this price and also S_live is our variable for S
        except Exception as e:
            st.error(f"Could not fetch live price: {e}") #give error if wrong stock
            S_live = st.number_input("Spot Price (S) AS fallback", value = 100.0) #back to number input
        

#S = st.number_input("Spot Price (S)", value = 100.0)
K = st.number_input("Excercise Price (K)", value = 95.0)
T = st.number_input("Time to Maturity (T)", value = 2.0)
r = st.number_input("Risk Free Rate (put decimal)", value = 0.05)
sigma = st.number_input("Volatility (put decimal)", value = 0.5) #user will input values for all these
option_type = st.selectbox("Option Type", ["call", "put"]) #option_type the string then 2 values to choose from

#Calculate now

if st.button("Calculate Option Price"): #basically if the button is pressed what happens - code is below
    price, delta, gamma, vega = blackscholes(S_live, K, T, r, sigma, option_type) #value of S_live is decided above, all values given above put in function and the 4 values are return 
    st.success(f"BSM Price {option_type.capitalize()} Price: {price:.2f}") #the value will be shown in green as success
    st.write(f"BSM {option_type.capitalize()} Price: {price:.2f}") #basically all these will come once
    st.write(f"**Delta:** {delta:.4f}") #the string in bold and value returned from function 4 decimal
    st.write(f"**Gamma:** {gamma:.4f}")
    st.write(f"**Vega:** {vega:.4f}")

uploaded_file = st.file_uploader("Upload Trader Data", type="csv") #file upload button; we upload an csv file here


if uploaded_file: #to tell if there is a uploaded file then make it a variable df
    df = pd.read_csv(uploaded_file) #now name of the file is df; also naturally pandas convert it to dataframe
    df["Spot"] = S_live #just to tell that the column of spot price would be the value put in S_live so the column is replaced
    df[["BSM Price", "Delta", "Gamma", "Vega"]] = df.apply(lambda row: pd.Series(blackscholes(S_live, row["Strike"], row["Time"], row["Rate"], row["Volatility"], row["Type"])), axis=1) #ensure sheet has these columns
    #go over each row and apply the function and apply the blackscholes function; the blackschole functions return 4 values and they are returned as 4 columns
    df["difference"] = df["TraderPrice"] - df["BSM Price"] #df["difference"] adds a new column which will compare the two price
    #purpose is to make new columns afer we upload the file; so all the calculations have now happened in the uploaded data 

    st.subheader("Filtering") #a new heading; now we will flter stuff from the file we uploaded after calculating all new columns

    option_types = df["Type"].dropna().unique().tolist() #we want to convert the two option types in our sheet into a list for our filter box

    selected_types = st.multiselect("Select Option Type", options = option_types, default= option_types) #shows an option to multiselect the two unique options

    #below process is to create a slider to filter strike prices
    min_strike = float(df["Strike"].min())  #set a float variable for min and max strike price 
    max_strike = float(df["Strike"].max())
    strike_range = st.slider("Strike Price Range",
                             min_value = min_strike,
                             max_value= max_strike,
                             value = (min_strike, max_strike)) #slider created with min and max strike on each side
    
    filtered_df = df[(df["Type"].isin(selected_types)) & #note df is basically our original sheet which is being updated and called here
                     (df["Strike"].between(strike_range[0], #between and is in is like a method for <> and = 
                    strike_range[1]))]    #now those two slider and multiselect will select stuff
    #in above we create a data frame in which we will update type column in our orig sheet which will put values from selectec_types which is the option box
    #and also strike column will updated with strike in the mentioned range which is the lower and max bound in strike range
    
    st.subheader("Filtered Data Preview")
    st.dataframe(filtered_df) #we convert the variable into a dataframe a table to be preseneted as table

    st.subheader("Mispricing Summary") #bekiw tabke creates a mispricing summary

    max_diff = filtered_df["difference"].max() 
    min_diff = filtered_df["difference"].min()
    avg_diff = filtered_df["difference"].mean()
    overpriced_count = (filtered_df["difference"] > 0).sum()
    underpriced_count = (filtered_df["difference"] < 0).sum() 
    #^Now look we have a filtered df so basically we are not applying various arthimeiic functions on the difference column in the filtered data

    summary_df = pd.DataFrame({
        "Metric" : ["Max Mispricing", "Min Mispricing", "Avg Mispricing", "Number Overpriced", "Number Underpriced"],
        "Value" : [max_diff, min_diff, avg_diff, overpriced_count, underpriced_count]
    })
    
    #now we have this dataframe, we create a dictionary using the values found from the filtered df and create a df of those; key is col name and value is the list below

    st.table(summary_df) #st.table - simple data and also this summary df is the dictionary we created above

    col1, col2, col3, col4, col5 = st.columns(5) #col1 is variable name; u create 5 vertical columns

    col1.metric("Max Mispricing", f"{max_diff:.2f}") #metric helps give them a dashboard style box type
    col2.metric("Min Mispricing", f"{min_diff:.2f}")
    col3.metric("Avg Mispricing", f"{avg_diff:.2f}")
    col4.metric("Overpriced Count", overpriced_count)
    col5.metric("Underpriced Count", underpriced_count) #the name basically f" - when u want to put a variable in a string and :2.f for 2 decimal places


    st.subheader("Option Type Breakdown")

    #below we will work again on the filtered data from our excel file; note all this is happening after if uploaded_file:
    #here we first decide we will group by the; () we use it to tell that create groups of rows of each type in Type column; like a group of rows of call and put values in type column
    #[] then in those groups; we tell python to go to to difference column for the two groups and aggregate each group and find the mean, max etc 
    # we wrote the aggregates in built funcs  in strings but could had used np.mean etc. too
    #lastly just rename the column names

    option_group = filtered_df.groupby("Type")["difference"].agg(["mean", "max", "min", "count"])
    option_group = option_group.rename(columns= {"mean": "Avg Diff", "max": "Max Diff", "min": "Min Diff", "count": "Trade Count"})

    st.dataframe(option_group)  #put the option_group filterng into a group to show put and call and their difference aggregates

    st.subheader("Trader vs BSM Price Chart")

    #here we create a chart using altair for the filtered dataframe, .mark_chartname helps decide what chart to use and then encode is just to code the chart
    #alt.X and alt.Y methods to work on the x and y axis; first parameter is to tell whichcolumn:whattype ; the type column and numerical, and then what is axis title
    #alt.condition parameters are (condition, value if true, value if false) and alt.datum lets you go over each row and check what u want like here values in diff col > 0

    chart = alt.Chart(filtered_df).mark_bar().encode(
    x = alt.X("Type:N", title = "Option Type"),
    y = alt.Y("difference:Q", title = "Trader - BSM Price"),
    color = alt.condition(
        alt.datum.difference > 0,
        alt.value("green"), #green if value in diff > 0; each row put as bars with each rows diff col checked
        alt.value("red")
    ),
    tooltip=["Spot", "Strike", "TraderPrice", "BSM Price", "difference", "Delta", "Gamma", "Vega"] #when you hover over the bar what column values u can see
    ).properties(
    width = 600,
    height = 400,
    title = "Trader vs Model Price difference"
    ) #lastly just set the size of chart and chart title

    st.altair_chart(chart) #helps streamlit dipslay the chart

    st.subheader("Top 5 OverPriced Options")

    #Top Mispriced table, .nlargest(how many, value from what column); so u put the results in a dataframe and this data is again out of the filtereddf
    st.dataframe(filtered_df.nlargest(5, "difference")
                 [["Spot", "Strike", "TraderPrice", "BSM Price", "difference"]]
                 )
    st.dataframe(filtered_df.nsmallest(5, "difference")
                 [["Spot", "Strike", "TraderPrice", "BSM Price", "difference"]]
                ) #double brackt picks multiple column [[]]
    
    
    #a histogram showing mispricing differences on hisogram

    st.subheader("Mispricing distribution")
    hist_chart = alt.Chart(filtered_df).mark_bar().encode(
    x= alt.X("difference:Q", bin = alt.Bin(maxbins=30), title = "Mispriced Values"), #how many ranges of dist u want so we want 30 interval to be made within the min max value
    y = "count()", #histogram shows frequency of the difference values so u can see the distributon
    tooltip = ["count()"] #put the count function in the tooltip
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







