import streamlit as st
import requests
import datetime
import pandas as pd
import plotly.express as px
import os

st.set_page_config(page_title="Sentiment Spike Detector", layout="wide")

st.title("📈 Real-Time Sentiment Spike Detector")
st.markdown("Monitor sentiment from **Reddit** and **Google News** about **stocks** or **crypto**, using SerpAPI.")

# API key from Streamlit secrets
api_key = os.getenv("SERPAPI_API_KEY") or st.secrets.get("SERPAPI_API_KEY")

query = st.text_input("🔍 Enter a stock or crypto keyword", "Bitcoin")

if not api_key:
    st.error("❌ API key not found. Please set SERPAPI_API_KEY in your Streamlit secrets.")
    st.stop()

@st.cache_data(ttl=300)
def fetch_results(source):
    params = {
        "q": query,
        "api_key": api_key,
        "num": "50"
    }

    if source == "news":
        url = "https://serpapi.com/search.json?engine=google_news"
    elif source == "reddit":
        url = "https://serpapi.com/search.json?engine=reddit"
    else:
        return []

    response = requests.get(url, params=params)
    data = response.json()
    return data.get("news_results" if source == "news" else "organic_results", [])

def mock_sentiment(text):
    score = sum([1 if w in text.lower() else -1 for w in ["bullish", "buy", "surge", "moon", "gain"]])
    score -= sum([1 if w in text.lower() else -1 for w in ["crash", "sell", "bearish", "drop", "loss"]])
    return max(-1, min(1, score))

# Fetch and process
news = fetch_results("news")
reddit = fetch_results("reddit")

def process(results, source):
    rows = []
    for r in results:
        text = r.get("title") + " " + r.get("snippet", "")
        date_str = r.get("date") or r.get("published_date") or ""
        try:
            time = pd.to_datetime(date_str)
        except:
            time = pd.Timestamp.now()
        rows.append({
            "source": source,
            "text": text,
            "sentiment": mock_sentiment(text),
            "time": time
        })
    return rows

df = pd.DataFrame(process(news, "Google News") + process(reddit, "Reddit"))
df = df.sort_values("time")

# Plot
if df.empty:
    st.warning("No data found. Try another keyword.")
else:
    fig = px.line(df, x="time", y="sentiment", color="source", markers=True,
                  title=f"Sentiment Trend for '{query}'", labels={"sentiment": "Sentiment Score"})
    st.plotly_chart(fig, use_container_width=True)

    # Optional: display raw data
    with st.expander("See raw data"):
        st.dataframe(df[["time", "source", "text", "sentiment"]])