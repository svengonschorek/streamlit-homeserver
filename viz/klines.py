import streamlit as st
import pandas
from datetime import datetime
import os

import sqlalchemy
from sqlalchemy.engine.url import URL
import plotly.graph_objs as go
 
engine = sqlalchemy.create_engine(
    URL.create(
        drivername="postgresql",
        username=os.environ['USERNAME'],
        password=os.environ['PASSWORD'],
        host=os.environ['HOST'],
        port=os.environ['PORT'],
        database=os.environ['DATABASE'],
    ),
    echo_pool=True,
)

connection = engine.connect()

def get_coins():
    query = f"""
        SELECT
            crypto_coin_kline.coin as coin
        FROM crypto_coin_kline
        WHERE coin NOT IN ('EUR', 'TORN', 'RNDR')
        GROUP BY 1
        ORDER BY coin
    """

    df = pandas.read_sql_query(query, connection)
    return df['coin'].array

def get_kline_data(coin="SOL", aggregation="day", start_time='2021-01-01', end_time=datetime.now()):
    query = f"""
        SELECT
            DATE_TRUNC('{aggregation}', crypto_coin_kline.kline_open_at) as open_at,
            MEASURE(crypto_coin_kline.open_coin_price) as open_price,
            MEASURE(crypto_coin_kline.close_coin_price) as close_price,
            MEASURE(crypto_coin_kline.max_coin_price) as high_price,
            MEASURE(crypto_coin_kline.min_coin_price) as low_price
        FROM crypto_coin_kline
        WHERE
            crypto_coin_kline.coin = '{coin}'
            and crypto_coin_kline.kline_open_at >= cast('{start_time}' as timestamp)
            and crypto_coin_kline.kline_open_at <= cast('{end_time}' as timestamp)
        GROUP BY 1
        ORDER BY 1 desc
        LIMIT 500;
    """
    df = pandas.read_sql_query(query, connection)
    return df

# Setup page configuration
st.set_page_config(layout="wide")

# Sidebar
st.sidebar.title("Crypto K-Lines per Coin")

# Select coin
coin = st.sidebar.selectbox("Select Crypto Coin", get_coins())

# Select time aggregation
aggregation = st.sidebar.selectbox("Select Time Aggregation", ["hour", "day", "week", "month", "year"], index=1)

# Select date range
start_time = st.sidebar.date_input("Start Date", value=datetime(2025, 1, 1))
end_time = st.sidebar.date_input("End Date", value=datetime.now())

# Get data from Semantic Layer
kline_data = get_kline_data(coin, aggregation, start_time, end_time)

# Display candlestick chart
if kline_data is not None:
    dates = kline_data['open_at'].array
    open_prices = kline_data['open_price'].array
    high_prices = kline_data['high_price'].array
    low_prices = kline_data['low_price'].array
    close_prices = kline_data['close_price'].array

    # Create candlestick chart using Plotly
    candlestick = go.Candlestick(
        x=dates,
        open=open_prices,
        high=high_prices,
        low=low_prices,
        close=close_prices
    )

    layout = go.Layout(
        title=f'K-Line Chart for {coin}',
        xaxis=dict(title='Timeline'),
        yaxis=dict(title='Price in USD')
    )

    fig = go.Figure(data=[candlestick], layout=layout)

    # Display the chart using Streamlit
    st.plotly_chart(fig, use_container_width=False)

else:
    st.error("Failed to fetch K-Line data.")
