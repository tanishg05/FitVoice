"""FitVoice - Streamlit Web UI with Live Agent Activity Panel and Judge Benchmarks."""

import streamlit as st
import pandas as pd
import json
from datetime import datetime
from fitvoice.orchestrator.runner import run_pipeline
from fitvoice.db.seed_data import seed_benchmark_data
from fitvoice.db.repository import FitnessRepository
from fitvoice.config import settings

# Page Configuration
st.set_page_config(
    page_title="FitVoice | Multi-Agent AI Intelligence",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom Styling
st.markdown("""
<style>
    .main-header { font-size: 2.2rem; font-weight: 800; color: #1E3A8A; margin-bottom: 0.2rem; }
    .sub-header { font-size: 1.05rem; color: #4B5563; margin-bottom: 1.5rem; }
    .agent-card {
        background: #F8FAFC;
        border-left: 4px solid #3B82F6;
        padding: 12px 16px;
        margin-bottom: 10px;
        border-radius: 6px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .badge-success { background: #DCFCE7; color: #166534; padding: 2px 8px; border-radius: 4px; font-weight: 600; font-size: 0.8rem; }
    .badge-approved { background: #DBEAFE; color: #1E40AF; padding: 2px 8px; border-radius: 4px; font-weight: 600; font-size: 0.8rem; }
    .badge-caveat { background: #FEF9C3; color: #854D0E; padding: 2px 8px; border-radius: 4px; font-weight: 600; font-size: 0.8rem; }
    .metric-box { background: #EFF6FF; border-radius: 8px; padding: 12px; text-align: center; }
</style>
""", unsafe_allow_html=True)

# Initialize Session State
if "messages" not in st.session_state:
    st.session_state.messages = []
if "last_pipeline_result" not in st.session_state:
    st.session_state.last_pipeline_result = None
if "pending_confirmation" not in st.session_state:
    st.session_state.pending_confirmation = None

repo = FitnessRepository()

# Sidebar Controls
with st.sidebar:
    st.image("https://images.unsplash.com/photo-1517838277536-f5f99be501cd?w=400&auto=format&fit=crop&q=60", use_container_width=True)
    st.title("FitVoice Control")
    st.markdown("**Genuine 6-Agent AI System**\nOrchestrated by LangGraph & Sarvam AI")

    st.divider()

    st.subheader("👤 User Profile")
    selected_user = st.selectbox(
        "Active Athlete",
        options=["alex_lifter", "newbie_sam"],
        format_func=lambda x: "Alex Lifter (4-Week Plateau Benchmark)" if x == "alex_lifter" else "Sam Newbie (Insufficient Data Scenario)"
    )

    preferred_lang = st.selectbox(
        "Preferred Language",
        options=["en-IN", "hi-IN", "te-IN", "ta-IN"],
        format_func=lambda x: {"en-IN": "English (India)", "hi-IN": "Hindi (हिंदी)", "te-IN": "Telugu (తెలుగు)", "ta-IN": "Tamil (தமிழ்)"}.get(x, x)
    )

    st.divider()
    st.subheader("⚡ 1-Click Judge Scenarios")

    scenario_1 = st.button("🎯 Flagship: Plateau Investigation", use_container_width=True)
    scenario_2 = st.button("🎙️ Voice Logging: Review & Confirm", use_container_width=True)
    scenario_3 = st.button("📊 Simple Question: Max 1RM", use_container_width=True)
    scenario_4 = st.button("⚠️ Insufficient Data: Transparent Audit", use_container_width=True)

    st.divider()
    if st.button("🔄 Reset & Seed Benchmark Database", use_container_width=True):
        seed_benchmark_data()
        st.success("Database seeded with reproducible 4-week benchmark data.")

# Main Panel
st.markdown('<div class="main-header">FitVoice Multi-Agent Intelligence Core</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Voice-First Fitness Data Science & Recovery Auditing with LangGraph & Sarvam AI</div>', unsafe_allow_html=True)

# Query Input logic
default_query = ""
if scenario_1:
    default_query = "Why has my bench press plateaued over the last 4 weeks despite working out consistently?"
elif scenario_2:
    default_query = "Log bench press 3 sets of 5 reps at 95 kg, felt solid RPE 8.5"
elif scenario_3:
    default_query = "What is my peak bench press and volume?"
elif scenario_4:
    selected_user = "newbie_sam"
    default_query = "Why am I not making progress on my bench press?"

user_query = st.text_input(
    "Spoken or Written Fitness Inquiry:",
    value=default_query,
    placeholder="Ask a question or log a workout (e.g. 'Why has my bench press plateaued over the last 4 weeks?')"
)

col_run, col_audio, col_status = st.columns([1.5, 2, 4])
with col_run:
    execute_button = st.button("🚀 Run Multi-Agent System", type="primary", use_container_width=True)

with col_audio:
    voice_mode = st.toggle("Simulate Sarvam Saaras v4 STT", value=False)

# Execution Handler
if execute_button and user_query:
    with st.spinner("LangGraph coordinating specialized agents..."):
        audio_path = "demo_audio.wav" if voice_mode else None
        res = run_pipeline(
            user_query=user_query,
            user_id=selected_user,
            preferred_language=preferred_lang,
            raw_audio_path=audio_path,
        )
        st.session_state.last_pipeline_result = res
        if res.get("requires_user_confirmation") and res.get("candidate_records"):
            st.session_state.pending_confirmation = res.get("candidate_records")
        else:
            st.session_state.pending_confirmation = None

# Display Results if Available
res = st.session_state.last_pipeline_result
if res:
    tab_response, tab_activity, tab_records = st.tabs([
        "💬 Intelligence Response",
        "🕵️ Observable Agent Activity Panel",
        "🗄️ Supporting Verified Records",
    ])

    # -------------------------------------------------------------
    # TAB 1: Response & Confirmation
    # -------------------------------------------------------------
    with tab_response:
        st.markdown(res.get("final_response", ""))

        # Review & Confirm workflow if candidate records pending
        if st.session_state.pending_confirmation:
            st.warning("⚠️ **Review-and-Confirm Required**: FitVoice never writes unconfirmed records directly to persistent storage.")
            c_yes, c_no = st.columns([2, 5])
            with c_yes:
                if st.button("✅ Confirm & Save to Database", type="primary"):
                    candidates = st.session_state.pending_confirmation
                    saved_count = 0
                    for w in candidates.get("workout_candidates", []):
                        repo.save_workout_session(
                            user_id=selected_user,
                            session_name=w["session_name"],
                            date=w["date"],
                            sets=w["sets"],
                            duration_minutes=w.get("duration_minutes", 45),
                            status="CONFIRMED"
                        )
                        saved_count += 1
                    for r in candidates.get("recovery_candidates", []):
                        repo.save_recovery_log(
                            user_id=selected_user,
                            date=r["date"],
                            sleep_hours=r["sleep_hours"],
                            soreness_score=r.get("soreness_score"),
                        )
                        saved_count += 1
                    st.success(f"Successfully committed {saved_count} record(s) to verified storage!")
                    st.session_state.pending_confirmation = None
                    st.rerun()

    # -------------------------------------------------------------
    # TAB 2: Real-time Observable Agent Activity Panel
    # -------------------------------------------------------------
    with tab_activity:
        st.subheader("Real Backend Execution Events")
        st.caption("Displays strictly the agents that actually ran, their execution duration, consulted tools, and validation verdicts.")

        trace = res.get("agent_execution_trace", [])
        if not trace:
            st.info("No execution trace available.")
        else:
            # Stage pills overview
            agent_pill_str = " ➔ ".join([f"`{e['agent_name']}`" for e in trace])
            st.markdown(f"**Execution Pipeline**: {agent_pill_str}")
            st.divider()

            for idx, evt in enumerate(trace):
                v_badge = evt.get("validation_status", "NOT_APPLICABLE")
                v_color = {
                    "APPROVED": "#166534",
                    "APPROVED_WITH_CAVEATS": "#854D0E",
                    "REQUIRES_REVISION": "#C2410C",
                    "BLOCKED": "#991B1B",
                }.get(v_badge, "#1E40AF")

                with st.expander(f"**Step {idx+1}: {evt['agent_name']}** — *{evt['stage']}* ({evt['duration_ms']} ms)", expanded=True):
                    c1, c2, c3 = st.columns([3, 2, 2])
                    with c1:
                        st.markdown(f"**Task Assigned**: {evt['task_assigned']}")
                    with c2:
                        st.markdown(f"**Status**: <span class='badge-success'>{evt['status']}</span>", unsafe_allow_html=True)
                    with c3:
                        st.markdown(f"**Validation**: <span style='background: #E0E7FF; color: {v_color}; padding: 2px 8px; border-radius: 4px; font-weight: 600;'>{v_badge}</span>", unsafe_allow_html=True)

                    st.markdown(f"**Tools & Data Sources Consulted**: `{', '.join(evt.get('tools_consulted', []))}`")
                    st.markdown(f"**Result Summary**: {evt['result_summary']}")

    # -------------------------------------------------------------
    # TAB 3: Supporting Records & Deterministic Calculations
    # -------------------------------------------------------------
    with tab_records:
        st.subheader("Verified Database Records & Deterministic Outputs")
        st.caption("Inspect the historical sets, recovery entries, and deterministic mathematical calculations used by the agents.")

        col_w, col_r = st.columns(2)
        with col_w:
            st.markdown("#### 🏋️ Verified Workout Sets (Last 28 Days)")
            sets = repo.get_workout_sets(user_id=selected_user, exercise="Bench Press")
            if sets:
                df_sets = pd.DataFrame(sets)[["date", "exercise", "weight_kg", "reps", "rpe", "session_name", "status"]]
                st.dataframe(df_sets, use_container_width=True)
            else:
                st.info("No workout sets found for this user.")

        with col_r:
            st.markdown("#### 🛌 Verified Recovery Logs")
            recs = repo.get_recovery_logs(user_id=selected_user)
            if recs:
                df_recs = pd.DataFrame(recs)[["date", "sleep_hours", "soreness_score", "energy_score", "readiness_score"]]
                st.dataframe(df_recs, use_container_width=True)
            else:
                st.info("No recovery logs found for this user.")

        # Show analytical breakdown if present
        if "analytical_results" in res and res["analytical_results"]:
            st.divider()
            st.markdown("#### 🔢 Fitness Data Scientist Tool Metrics")
            st.json(res["analytical_results"].get("progression", {}))
