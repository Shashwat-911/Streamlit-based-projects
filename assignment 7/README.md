# life-os

```
$ whoami
a wellbeing dashboard, not a guilt machine

$ cat mission.txt
Digital addiction is a modern epidemic.
This is a tool that helps you see the pattern — and fix it.
```

## > overview

**Life-OS** is a Streamlit dashboard that visualizes 14 days of screen time
data and hands it to Gemini, which plays the role of a brutal-but-fair life
coach: it doesn't just say "use your phone less" — it looks at what you
actually did with your time and suggests real-world replacements.

## > stack

```
frontend   : streamlit
data       : pandas + screentime.csv (synthetic)
ai         : google-genai (Gemini 2.0 Flash)
secrets    : python-dotenv
```

## > run it locally

```bash
$ git clone <this-repo-url>
$ cd life-os
$ python -m venv venv && source venv/bin/activate
$ pip install -r requirements.txt
$ cp .env.example .env        # then paste in your GEMINI_API_KEY
$ streamlit run app.py
```

## > features

```
[x] sidebar day selector + adjustable daily goal slider
[x] KPI row: total time / most used app / delta vs goal
[x] 14-day trend bar chart + per-category breakdown
[x] AI coach: aggregates the day's data, sends it to Gemini,
    returns specific, physical-world replacement activities
[x] shareable accountability link via st.query_params
```

## > project structure

```
life-os/
├── app.py              # main streamlit app
├── screentime.csv       # synthetic 14-day dataset
├── gen_data.py          # script that generated screentime.csv
├── requirements.txt
├── .env.example
└── README.md
```

## > deploy

Pushed to Streamlit Community Cloud. Set `GEMINI_API_KEY` under
**App settings → Secrets** as:

```toml
GEMINI_API_KEY = "your_key_here"
```

---

built for the MirAI School of Technology "AI Builder" summer internship —
capstone: Life-OS Wellbeing Dashboard.
