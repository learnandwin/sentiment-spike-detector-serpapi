# Real-Time Sentiment Spike Detector with SerpAPI

Monitors spikes in sentiment from Reddit and Google News in real time for stocks or crypto.

## Setup

1. Install dependencies  
```
pip install -r requirements.txt
```

2. Set your SerpAPI key as an environment variable:  
```
export SERPAPI_API_KEY=your_key_here
```

3. Run the app  
```
streamlit run app.py
```