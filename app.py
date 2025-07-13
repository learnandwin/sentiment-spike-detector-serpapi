import streamlit as st
import pandas as pd
from serpapi import GoogleSearch
from textblob import TextBlob
import plotly.express as px
import datetime

st.set_page_config(page_title="📈 Real-Time Sentiment Spike Detector", layout="centered")
st.title("📈 Real-Time Sentiment Spike Detector")
st.markdown("Monitor sentiment from **Reddit** and **Google News** about **stocks** or **crypto**, using SerpAPI.")

query = st.text_input("🔍 Enter a stock or crypto keyword", value="Bitcoin")

@st.cache_data(ttl=300)
def fetch_google_news(query):
    params = {
        "engine": "google_news",
        "q": query,
        "api_key": st.secrets["SERPAPI_KEY"],
        "hl": "en"
    }
    search = GoogleSearch(params)
    return search.get("news_results", [])

@st.cache_data(ttl=300)
def fetch_reddit(query):
    params = {
        "engine": "reddit",
        "q": query,
        "api_key": st.secrets["SERPAPI_KEY"]
    }
    search = GoogleSearch(params)
    return search.get("organic_results", [])

def get_sentiment(text):
    blob = TextBlob(text)
    return round(blob.sentiment.polarity, 2)

def detect_spikes(scores, threshold=0.8):
    spikes = []
    for i in range(1, len(scores)):
        diff = abs(scores[i] - scores[i - 1])
        if diff >= threshold:
            spikes.append(i)
    return spikes

if query:
    st.info("Collecting real-time sentiment data...")

    google_results = fetch_google_news(query)
    reddit_results = fetch_reddit(query)

    all_data = []
    now = datetime.datetime.now()

    for res in google_results:
        title = res.get("title", "")
        score = get_sentiment(title)
        all_data.append({"title": title, "score": score, "source": "Google News", "time": now})

    for res in reddit_results:
        title = res.get("title", "")
        score = get_sentiment(title)
        all_data.append({"title": title, "score": score, "source": "Reddit", "time": now})

    if not all_data:
        st.warning("No data found. Try a different keyword.")
    else:
        df = pd.DataFrame(all_data)

        spikes = detect_spikes(df["score"].tolist())

        fig = px.line(df, x="time", y="score", color="source", markers=True, title=f"Sentiment Trend for '{query}'")
        st.plotly_chart(fig, use_container_width=True)

        if spikes:
            st.warning("⚠️ Sentiment spike detected!")
            for i in spikes:
                spike_row = df.iloc[i]
                st.markdown(f"**{spike_row['source']}** spike at **{spike_row['time'].strftime('%H:%M:%S')}**: {spike_row['title']}")

        with st.expander("📰 View all headlines"):
            for row in all_data:
                st.write(f"• ({row['source']}) {row['title']} — Sentiment: {row['score']}")
