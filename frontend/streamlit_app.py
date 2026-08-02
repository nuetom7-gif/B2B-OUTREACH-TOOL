import os
from pathlib import Path

import requests
import streamlit as st
from dotenv import load_dotenv


load_dotenv(Path(__file__).resolve().parents[1] / "backend" / ".env")

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
WRITE_API_KEY = os.getenv("WRITE_API_KEY", "")


def api_get(path: str):
    return requests.get(f"{API_BASE_URL}{path}", timeout=30)


def api_post(path: str, json=None, files=None):
    headers = {"X-API-Key": WRITE_API_KEY} if WRITE_API_KEY else {}
    return requests.post(f"{API_BASE_URL}{path}", json=json, files=files, headers=headers, timeout=30)


st.set_page_config(page_title="Yash Technology Outreach Hub", layout="wide")
st.title("Yash Technology Outreach Hub")
st.caption("Frontend talks only to the FastAPI backend.")

with st.sidebar:
    st.header("Connection")
    st.write(API_BASE_URL)
    st.caption("Write key loaded from backend/.env")
    if st.button("Refresh"):
        st.rerun()

dashboard = api_get("/dashboard").json()
col1, col2, col3, col4 = st.columns(4)
col1.metric("Contacts", dashboard["total_contacts"])
col2.metric("Sent this month", dashboard["messages_sent_this_month"])
col3.metric("Reply rate", f"{dashboard['reply_rate']:.0%}")
col4.metric("Active mailboxes", dashboard["active_mailboxes"])

st.subheader("Recent activity")
st.dataframe(dashboard["recent_messages"], use_container_width=True, hide_index=True)

tab1, tab2, tab3, tab4, tab5 = st.tabs(["Companies", "Contacts", "Mailboxes", "Messages", "Discovery"])

with tab1:
    st.markdown("### Add company")
    with st.form("company_form"):
        name = st.text_input("Company name")
        industry = st.text_input("Industry")
        source = st.text_input("Source")
        notes = st.text_area("Notes")
        fits = st.text_input("Product fit comma-separated")
        submitted = st.form_submit_button("Save company")
        if submitted:
            payload = {
                "name": name,
                "industry": industry,
                "source": source,
                "notes": notes,
                "product_fits": [item.strip() for item in fits.split(",") if item.strip()],
            }
            response = api_post("/companies", json=payload)
            st.write(response.json())
    st.markdown("### Companies")
    st.dataframe(api_get("/companies").json(), use_container_width=True, hide_index=True)

with tab2:
    st.markdown("### Add contact")
    companies = api_get("/companies").json()
    existing_contacts = api_get("/contacts").json()
    company_map = {f"{row['name']} ({row['id']})": row["id"] for row in companies}
    with st.form("contact_form"):
        name = st.text_input("Name")
        title = st.text_input("Title")
        company_label = st.selectbox("Company", list(company_map.keys()) if company_map else [""])
        source = st.text_input("Source")
        email = st.text_input("Email")
        phone = st.text_input("Phone")
        linkedin_url = st.text_input("LinkedIn URL")
        if email:
            matches = [row for row in existing_contacts if (row.get("email") or "").lower() == email.lower()]
            if matches:
                match_labels = ", ".join(
                    f"{row['name']} at {row['company_name']}" for row in matches[:3]
                )
                st.warning(f"A contact with this email already exists: {match_labels}. Saving will create a duplicate manually.")
        submitted = st.form_submit_button("Save contact")
        if submitted and company_label:
            payload = {
                "name": name,
                "title": title,
                "company_id": company_map[company_label],
                "source": source,
                "email": email or None,
                "phone": phone or None,
                "linkedin_url": linkedin_url or None,
            }
            response = api_post("/contacts", json=payload)
            st.write(response.json())
    st.markdown("### Contacts")
    st.dataframe(api_get("/contacts").json(), use_container_width=True, hide_index=True)

with tab3:
    st.markdown("### Add mailbox")
    with st.form("mailbox_form"):
        name = st.text_input("Mailbox name")
        email = st.text_input("Mailbox email")
        daily_limit = st.number_input("Daily limit", min_value=1, max_value=100, value=30)
        submitted = st.form_submit_button("Save mailbox")
        if submitted:
            response = api_post("/mailboxes", json={"name": name, "email": email, "daily_limit": daily_limit, "active": True})
            st.write(response.json())
    st.markdown("### Mailboxes")
    st.dataframe(api_get("/mailboxes").json(), use_container_width=True, hide_index=True)

with tab4:
    st.markdown("### Messages")
    st.dataframe(api_get("/messages").json(), use_container_width=True, hide_index=True)

with tab5:
    st.markdown("### Discovery Summary")
    summary = api_get("/discovery/summary").json()
    c1, c2 = st.columns(2)
    c1.metric("Staging records", summary["staging_count"])
    c2.metric("Manual review", summary["manual_review_count"])

    if st.button("Run Discovery Now"):
        result = api_post("/discovery/run", json={"force": True})
        st.write(result.json())
        st.rerun()

    st.markdown("### Recent Runs")
    st.dataframe(summary["runs"], use_container_width=True, hide_index=True)
    failed_runs = [run for run in summary["runs"] if run.get("status") == "failed"]
    if failed_runs:
        latest_failed = failed_runs[0]
        st.error(
            f"{len(failed_runs)} recent discovery run(s) failed. "
            f"Latest failure: {latest_failed.get('product_name')} (run #{latest_failed.get('id')})"
        )

    st.markdown("### Manual Review Queue")
    st.dataframe(summary["recent_manual_review"], use_container_width=True, hide_index=True)
