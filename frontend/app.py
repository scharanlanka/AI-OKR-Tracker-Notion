import os
import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8001")

st.set_page_config(page_title="AI OKR Tracker", layout="wide")
st.title("AI OKR Tracker MVP")
st.caption("Sprint 1 dashboard")


def safe_get(path: str):
    try:
        return requests.get(f"{BACKEND_URL}{path}", timeout=20)
    except Exception as exc:  # noqa: BLE001
        st.error(f"Request failed for {path}: {exc}")
        return None


def safe_post(path: str, payload: dict | None = None):
    try:
        return requests.post(f"{BACKEND_URL}{path}", json=payload or {}, timeout=30)
    except Exception as exc:  # noqa: BLE001
        st.error(f"Request failed for {path}: {exc}")
        return None


col1, col2, col3 = st.columns(3)
okrs_resp = safe_get("/okrs")
risks_resp = safe_get("/okrs/risks")
deadlines_resp = safe_get("/okrs/deadlines")

okrs = okrs_resp.json() if okrs_resp and okrs_resp.ok else []
risks = risks_resp.json() if risks_resp and risks_resp.ok else []
deadlines = deadlines_resp.json() if deadlines_resp and deadlines_resp.ok else []

with col1:
    st.metric("Objectives", len(okrs))
with col2:
    total_krs = sum(len(obj.get("key_results", [])) for obj in okrs)
    st.metric("Key Results", total_krs)
with col3:
    st.metric("Risks", len(risks))

st.divider()

if st.button("Sync Notion"):
    sync_resp = safe_post("/sync/notion")
    if sync_resp and sync_resp.ok:
        st.success(sync_resp.json().get("message", "Synced"))
        st.rerun()
    elif sync_resp is not None:
        st.error(sync_resp.text)

st.subheader("Risk Report")
if risks:
    st.dataframe(risks, use_container_width=True)
else:
    st.info("No risks to show.")

st.subheader("Upcoming Deadlines")
if deadlines:
    st.dataframe(deadlines, use_container_width=True)
else:
    st.info("No upcoming deadlines.")

st.subheader("Ask Assistant")
question = st.text_input("Ask about risks, deadlines, blockers, team status...")
if st.button("Ask") and question.strip():
    ask_resp = safe_post("/ask", {"question": question})
    if ask_resp and ask_resp.ok:
        data = ask_resp.json()
        st.write(f"**Agent:** {data['agent']}")
        st.write(data["answer"])
    elif ask_resp is not None:
        st.error(ask_resp.text)
