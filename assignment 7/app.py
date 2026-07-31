"""
Life-OS Wellbeing Dashboard
MirAI School of Technology — AI Builder Track Capstone

A Streamlit dashboard that visualizes daily screen time data and uses the
Gemini API to act as a personalized, brutal-but-fair productivity coach.
"""

import os
import datetime

import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from google import genai

load_dotenv()

# ----------------------------------------------------------------------
# Page config
# ----------------------------------------------------------------------
st.set_page_config(
    page_title="Life-OS | Wellbeing Dashboard",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ----------------------------------------------------------------------
# Minimal SaaS-style CSS polish
# ----------------------------------------------------------------------
st.markdown(
    """
    <style>
    .main { background-color: #0e1117; }
    div[data-testid="stMetric"] {
        background-color: #161b22;
        border: 1px solid #30363d;
        padding: 1rem;
        border-radius: 10px;
    }
    .block-container { padding-top: 2rem; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ----------------------------------------------------------------------
# Data ingestion (Phase 1)
# ----------------------------------------------------------------------
@st.cache_data
def load_data() -> pd.DataFrame:
    df = pd.read_csv("screentime.csv")
    df["Date"] = pd.to_datetime(df["Date"]).dt.date
    return df


df = load_data()
all_dates = sorted(df["Date"].unique())

# ----------------------------------------------------------------------
# Sidebar controls (Phase 2.5)
# ----------------------------------------------------------------------
st.sidebar.title("🧠 Life-OS")
st.sidebar.caption("Your wellbeing command center")

selected_date = st.sidebar.selectbox(
    "Select a day to review",
    options=all_dates,
    index=len(all_dates) - 1,
    format_func=lambda d: d.strftime("%a, %b %d %Y"),
)

daily_goal_minutes = st.sidebar.slider(
    "Daily screen time goal (minutes)",
    min_value=60,
    max_value=600,
    value=240,
    step=15,
    help="The amount of screen time you're aiming to stay under each day.",
)

st.sidebar.divider()
gemini_api_key = st.sidebar.text_input(
    "Gemini API Key",
    value=os.getenv("GEMINI_API_KEY", ""),
    type="password",
    help="Stored only for this session. Prefer setting GEMINI_API_KEY in a .env file.",
)

st.sidebar.divider()
st.sidebar.markdown("**Legend**")
st.sidebar.caption("🟢 Under goal · 🟡 Near goal · 🔴 Over goal")

# ----------------------------------------------------------------------
# Filtered data for the selected day
# ----------------------------------------------------------------------
day_df = df[df["Date"] == selected_date]
total_today = int(day_df["Minutes_Used"].sum())

# Previous day for the delta comparison
prev_dates = [d for d in all_dates if d < selected_date]
prev_total = int(df[df["Date"] == prev_dates[-1]]["Minutes_Used"].sum()) if prev_dates else total_today

most_used_row = day_df.sort_values("Minutes_Used", ascending=False).iloc[0] if not day_df.empty else None

# ----------------------------------------------------------------------
# Header
# ----------------------------------------------------------------------
st.title("📊 Life-OS Wellbeing Dashboard")
st.caption(f"Reviewing **{selected_date.strftime('%A, %B %d, %Y')}**")

# ----------------------------------------------------------------------
# KPI Row (Phase 2.6)
# ----------------------------------------------------------------------
col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        label="Total Screen Time Today",
        value=f"{total_today // 60}h {total_today % 60}m",
        delta=f"{total_today - prev_total:+d} min vs. yesterday",
        delta_color="inverse",
    )

with col2:
    if most_used_row is not None:
        st.metric(
            label="Most Used App",
            value=most_used_row["App_Name"],
            delta=f"{int(most_used_row['Minutes_Used'])} min ({most_used_row['Category']})",
            delta_color="off",
        )
    else:
        st.metric(label="Most Used App", value="—")

with col3:
    diff_from_goal = total_today - daily_goal_minutes
    st.metric(
        label="Vs. Daily Goal",
        value=f"{daily_goal_minutes} min goal",
        delta=f"{diff_from_goal:+d} min",
        delta_color="inverse",
    )

st.divider()

# ----------------------------------------------------------------------
# Visualizations (Phase 2.7)
# ----------------------------------------------------------------------
viz_col1, viz_col2 = st.columns([2, 1])

with viz_col1:
    st.subheader("14-Day Trend")
    trend = df.groupby("Date")["Minutes_Used"].sum().reset_index()
    trend = trend.set_index("Date")
    st.bar_chart(trend, height=320)

with viz_col2:
    st.subheader(f"{selected_date.strftime('%b %d')} — By Category")
    cat_breakdown = day_df.groupby("Category")["Minutes_Used"].sum().sort_values(ascending=False)
    st.bar_chart(cat_breakdown, height=320)

st.divider()

# ----------------------------------------------------------------------
# Data bridge: aggregate day's data into a clean string for the LLM (Phase 3.8)
# ----------------------------------------------------------------------
def build_daily_summary(day_data: pd.DataFrame, goal_minutes: int) -> str:
    by_category = day_data.groupby("Category")["Minutes_Used"].sum().sort_values(ascending=False)
    by_app = day_data.sort_values("Minutes_Used", ascending=False)

    summary_lines = [
        f"Total screen time: {int(day_data['Minutes_Used'].sum())} minutes",
        f"Daily goal: {goal_minutes} minutes",
        "",
        "Time by category:",
        by_category.to_string(),
        "",
        "Time by individual app:",
        by_app[["App_Name", "Category", "Minutes_Used"]].to_string(index=False),
    ]
    return "\n".join(summary_lines)


daily_summary_str = build_daily_summary(day_df, daily_goal_minutes)

with st.expander("🔍 View the data sent to the AI coach"):
    st.code(daily_summary_str, language="text")

# ----------------------------------------------------------------------
# System prompt + Gemini call (Phase 3.9 / 3.10)
# ----------------------------------------------------------------------
def get_coaching_advice(summary: str, api_key: str) -> str:
    client = genai.Client(api_key=api_key)

    prompt = f"""
You are a holistic life coach embedded in a wellbeing dashboard called Life-OS.
You are brutally honest but fundamentally supportive — like a coach who respects
the user enough to tell them the truth, then hands them a real plan.

Here is today's screen time data, broken down by category and app:

{summary}

Your task:
1. Give a short, direct verdict on today's screen time (1-2 sentences). Do not
   just say "use your phone less" — be specific about WHAT was overused.
2. Identify the single biggest opportunity for improvement (the category or app
   eating the most time relative to its value).
3. Suggest 2-3 concrete, physical, real-world replacement activities for that
   wasted time. Be specific (e.g., "swap 45 minutes of TikTok for a walk plus
   meal-prepping tomorrow's lunch" rather than "exercise more").
4. End with one encouraging, forward-looking sentence.

Keep the entire response under 180 words. Format it in Markdown with short
paragraphs or a small bullet list — no headers.
"""

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt,
    )
    return response.text


st.subheader("🤖 Your AI Coach")

if not gemini_api_key:
    st.warning(
        "Add your Gemini API key in the sidebar (or set GEMINI_API_KEY in a .env file) "
        "to unlock personalized coaching."
    )
else:
    if st.button("Get today's coaching", type="primary"):
        with st.spinner("Your coach is reviewing today's data..."):
            try:
                advice = get_coaching_advice(daily_summary_str, gemini_api_key)

                if total_today > daily_goal_minutes * 1.25:
                    st.error(f"⚠️ {int((total_today/daily_goal_minutes - 1)*100)}% over goal today.")
                elif total_today > daily_goal_minutes:
                    st.warning("You're over your goal today.")
                else:
                    st.success("You're within your goal today. Nice work.")

                st.markdown(advice)
            except Exception as e:
                st.error(f"Couldn't reach Gemini: {e}")

st.divider()

# ----------------------------------------------------------------------
# Phase 4 — Innovation Deliverable: Shareable Accountability Link
# ----------------------------------------------------------------------
st.subheader("🔗 Accountability Link")

query_params = st.query_params
if st.button("Generate shareable link for today's stats"):
    st.query_params["date"] = str(selected_date)
    st.query_params["total_minutes"] = str(total_today)
    st.query_params["goal_minutes"] = str(daily_goal_minutes)

if "total_minutes" in st.query_params:
    shared_date = st.query_params.get("date", str(selected_date))
    shared_total = st.query_params.get("total_minutes", "0")
    shared_goal = st.query_params.get("goal_minutes", "0")
    st.info(
        f"📎 Shareable snapshot active — **{shared_date}**: "
        f"{shared_total} min used vs. a {shared_goal} min goal. "
        "Copy this page's URL to send it to an accountability partner."
    )
else:
    st.caption("Click the button above, then copy the URL from your browser's address bar to share it.")
