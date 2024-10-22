import pandas as pd
import math
import json
import requests
from io import StringIO
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("API_KEY")
url = "https://yfapi.net/v6/finance/quote"

stock = input("Which stock would you like to analyze?\n" +
               "(Enter ticker symbol Ex: AAPL): ").upper().strip()


try:
    response = requests.get(url, headers={"x-api-key": api_key}, params={"symbols": stock})
    response.raise_for_status()  # raise an error if the request failed
    stock_json = response.json()
    
    # check if response contains data
    if not stock_json.get("quoteResponse") or not stock_json["quoteResponse"].get("result"):
        print("Error: No data found for the provided stock symbol.")
    else:
        # create pandas df from json response
        df = pd.read_json(StringIO(json.dumps(stock_json["quoteResponse"]["result"])))
        if df.empty:
            print("Error: No valid stock information retrieved.")
        else:
            df["Target Mean Price"] = (df["priceEpsCurrentYear"] / df["forwardPE"]) * df["regularMarketPrice"]
            df = df[["symbol", "longName", "regularMarketPrice", "fiftyTwoWeekHigh", "fiftyTwoWeekLow", 'Target Mean Price']]
            df = df.rename(columns={"symbol": "Ticker", "longName": "Company Name", "regularMarketPrice": "Current Market Price", "fiftyTwoWeekHigh": "52 Week High", "fiftyTwoWeekLow": "52 Week Low"})
            
            # print stock information
            print("\nStock Information:")
            print(f"{df.iloc[0]['Company Name']} ({df.iloc[0]['Ticker']})")
            print(f"Current Market Price: ${df.iloc[0]['Current Market Price']}")
            print(f"52 Week High: ${df.iloc[0]['52 Week High']}")
            print(f"52 Week Low: ${df.iloc[0]['52 Week Low']}")
            print(f"Target Mean Price: ${math.ceil(df.iloc[0]['Target Mean Price'] * 100)/100}")
            print("")

            # save output to a csv file
            df.to_csv("output.csv", index=False)
except requests.exceptions.RequestException as e:
    print(f"Error: Failed to fetch data from API. Details: {e}")

# trending stocks request
region = input("Which region would you like to see the Top 5 trending stocks for?\n" +
               "(Options: US, AU, CA, FR, DE, IT, ES, GB, IN):").upper()
trending_url = f"https://yfapi.net/v1/finance/trending/{region}"

try:
    response = requests.get(trending_url, headers={"x-api-key": api_key})
    response.raise_for_status()  # raise error if request failed
    trending_json = response.json()
    
    # check if response contains trending data
    if not trending_json.get("finance") or not trending_json["finance"].get("result"):
        print("Error: No trending stock data found for the specified region.")
    else:
        trending_df = pd.read_json(StringIO(json.dumps(trending_json["finance"]["result"][0]["quotes"][0:5]))) # grab first 5 trending stocks

        print("\nTop 5 Trending Stocks:")
        for i in range(len(trending_df)):
            print(f"{i+1}. {trending_df.iloc[i]['symbol']}")
except requests.exceptions.RequestException as e:
    print(f"Error: Failed to fetch trending stocks data from API. Details: {e}")

# BONUS
import matplotlib.pyplot as plt

response = requests.get("https://yfapi.net/v8/finance/spark", headers={"x-api-key": api_key}, params={"symbols": stock, "range": "5d", "interval": "1d"})
response.raise_for_status()  # raise error if request failed
spark_json = response.json()

if not spark_json.get(stock) or not spark_json[stock].get("close"):
    print("Error: No historical data found for the provided stock symbol.")
else:
    spark_df = pd.read_json(StringIO(json.dumps(spark_json[stock]["close"])))
    spark_df["timestamp"] = pd.to_datetime(spark_df["timestamp"], unit="s")
    spark_df = spark_df.set_index("timestamp")

    # plot the stock price
    plt.figure(figsize=(10, 5))
    plt.plot(spark_df.index, spark_df[stock]["close"])
    plt.title(f"{stock} Stock Price Over the Last 5 Days")
    plt.xlabel("Date")
    plt.ylabel("Price (USD)")
    plt.grid()
    plt.show()
