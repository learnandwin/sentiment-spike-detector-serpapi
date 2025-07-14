import streamlit as st
import pandas as pd
import requests
import plotly.graph_objs as go
import os
import datetime
from textblob import TextBlob

# --- Configuracion ---
SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY")
QUERY = st.sidebar.text_input("🔍 Buscar acción o criptomoneda", value="Bitcoin")
NUM_RESULTS = 20
SENTIMENT_SPIKE_THRESHOLD = 0.3  # Umbral para alertas

st.title("📈 Detector de Picos de Sentimiento en Tiempo Real")
st.caption("Datos desde Google News y Reddit usando SerpAPI")

@st.cache_data(show_spinner=False)
def analyze_sentiment(text):
    return TextBlob(text).sentiment.polarity

@st.cache_data(show_spinner=False)
def fetch_news(query):
    url = "https://serpapi.com/search.json"
    params = {
        "engine": "google_news",
        "q": query,
        "api_key": SERPAPI_API_KEY,
        "num": NUM_RESULTS,
        "hl": "en"
    }
    res = requests.get(url, params=params)
    return res.json().get("news_results", [])

@st.cache_data(show_spinner=False)
def fetch_reddit(query):
    url = "https://serpapi.com/search.json"
    params = {
        "engine": "reddit",
        "q": query,
        "api_key": SERPAPI_API_KEY,
        "num": NUM_RESULTS
    }
    res = requests.get(url, params=params)
    return res.json().get("organic_results", [])

def build_dataframe():
    news_data = fetch_news(QUERY)
    reddit_data = fetch_reddit(QUERY)

    entries = []
    for item in news_data:
        entries.append({
            "title": item.get("title"),
            "source": "Google News",
            "link": item.get("link"),
            "published": item.get("date") or str(datetime.datetime.now()),
            "sentiment": analyze_sentiment(item.get("title", ""))
        })

    for item in reddit_data:
        entries.append({
            "title": item.get("title"),
            "source": "Reddit",
            "link": item.get("link"),
            "published": item.get("date") or str(datetime.datetime.now()),
            "sentiment": analyze_sentiment(item.get("title", ""))
        })

    df = pd.DataFrame(entries)
    df["published"] = pd.to_datetime(df["published"], errors="coerce")
    df = df.dropna(subset=["published"])
    df = df.sort_values("published")
    return df

df = build_dataframe()

# Calcular promedio de sentimiento por hora/minuto
df["minute"] = df["published"].dt.floor("min")
sentiment_over_time = df.groupby("minute")["sentiment"].mean().reset_index()
sentiment_over_time["change"] = sentiment_over_time["sentiment"].diff()

# Detectar picos
spikes = sentiment_over_time[abs(sentiment_over_time["change"]) > SENTIMENT_SPIKE_THRESHOLD]

# --- ALERTAS ---
if not spikes.empty:
    for _, row in spikes.iterrows():
        if row["change"] > 0:
            st.success(f"📈 Sentimiento subió bruscamente a las {row['minute'].strftime('%H:%M')}")
        else:
            st.error(f"📉 Sentimiento bajó bruscamente a las {row['minute'].strftime('%H:%M')}")

# --- GRAFICO ---
fig = go.Figure()
fig.add_trace(go.Scatter(x=sentiment_over_time["minute"], y=sentiment_over_time["sentiment"],
                         mode="lines+markers", name="Sentimiento"))

# Anotar titulares en picos
for _, row in spikes.iterrows():
    spike_time = row["minute"]
    related_titles = df[df["minute"] == spike_time].sort_values("sentiment", ascending=False).head(2)
    for _, article in related_titles.iterrows():
        fig.add_trace(go.Scatter(
            x=[spike_time],
            y=[row["sentiment"]],
            mode="markers+text",
            text=[article["title"]],
            textposition="top center",
            marker=dict(size=10, color="red"),
            showlegend=False
        ))

fig.update_layout(title="Evolución del Sentimiento", xaxis_title="Hora", yaxis_title="Sentimiento")
st.plotly_chart(fig, use_container_width=True)

# --- Mostrar tabla de titulares ---
st.subheader("📰 Titulares recientes")
st.dataframe(df[["published", "source", "title", "sentiment"]].sort_values("published", ascending=False), use_container_width=True)
