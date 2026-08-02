from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import pandas as pd
import requests
import streamlit as st
from dotenv import load_dotenv


ROOT_DIR = Path(__file__).resolve().parents[1]
load_dotenv(ROOT_DIR / ".env")
load_dotenv(ROOT_DIR / "backend" / ".env")

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
WRITE_API_KEY = os.getenv("WRITE_API_KEY", "")

PRODUCT_SEGMENTS = [
    "Industrial Vacuum Cleaning Systems",
    "Warehouse & Storage Solutions",
    "GFRP Rebar",
]

PAGE_OPTIONS = [
    "Dashboard",
    "Lead Discovery",
    "Lead Review",
    "Email Drafts",
    "Send Emails",
    "Analytics",
    "Settings",
]


def api_request(method: str, path: str, *, json: dict[str, Any] | list[dict[str, Any]] | None = None, files=None):
    headers = {}
    if method.upper() not in {"GET", "HEAD"} and WRITE_API_KEY:
        headers["X-API-Key"] = WRITE_API_KEY
    response = requests.request(method, f"{API_BASE_URL}{path}", json=json, files=files, headers=headers, timeout=60)
    response.raise_for_status()
    if response.status_code == 204:
        return None
    return response.json()


def api_get(path: str):
    return api_request("GET", path)


def api_post(path: str, *, json: dict[str, Any] | list[dict[str, Any]] | None = None, files=None):
    return api_request("POST", path, json=json, files=files)


def api_put(path: str, *, json: dict[str, Any] | list[dict[str, Any]] | None = None):
    return api_request("PUT", path, json=json)


def api_delete(path: str):
    return api_request("DELETE", path)


def fetch_json(path: str, fallback: Any):
    try:
        return api_get(path)
    except Exception as exc:  # pragma: no cover - UI guardrail
        st.error(f"Unable to load {path}: {exc}")
        return fallback


def contact_table_frame(contacts: list[dict[str, Any]]) -> pd.DataFrame:
    frame = pd.DataFrame(contacts)
    if frame.empty:
        return frame
    if "selected" not in frame.columns:
        frame.insert(0, "selected", False)
    preferred = [
        "selected",
        "id",
        "name",
        "title",
        "company_name",
        "email",
        "phone",
        "linkedin_url",
        "lead_score",
        "source",
        "verification_status",
        "do_not_contact",
        "latest_message_status",
    ]
    ordered = [column for column in preferred if column in frame.columns]
    ordered.extend([column for column in frame.columns if column not in ordered])
    return frame[ordered]


def selected_ids_from_editor(frame: pd.DataFrame) -> list[int]:
    if frame.empty or "selected" not in frame.columns or "id" not in frame.columns:
        return []
    selected = frame[frame["selected"].fillna(False)]
    return [int(value) for value in selected["id"].tolist()]


def render_metrics_row(metrics: list[tuple[str, Any]]) -> None:
    columns = st.columns(len(metrics))
    for column, (label, value) in zip(columns, metrics):
        column.metric(label, value)


def render_dashboard() -> None:
    stats = fetch_json("/dashboard/stats", {})
    discovery = fetch_json("/discovery/summary", {})
    if not stats:
        return
    today_leads_total = sum(int(value.get("current", 0)) for value in stats.get("today_leads", {}).values())

    st.subheader("Today")
    render_metrics_row(
        [
            ("Today's Leads", today_leads_total),
            ("Emails Sent", stats.get("today_emails_sent", 0)),
            ("Replies", stats.get("today_replies", 0)),
            ("Reply Rate", f"{stats.get('reply_rate', 0.0):.0%}"),
            ("Bounce Rate", f"{stats.get('bounce_rate', 0.0):.0%}"),
            ("Apollo Credits", stats.get("apollo_credits_remaining", 0)),
        ]
    )

    st.subheader("Product Targets")
    target_rows = pd.DataFrame(
        [
            {
                "product_segment": key,
                "target": value.get("target", 0),
                "current": value.get("current", 0),
                "remaining": value.get("remaining", 0),
                "progress": 0 if value.get("target", 0) == 0 else round((value.get("current", 0) / value.get("target", 1)) * 100, 1),
            }
            for key, value in stats.get("today_leads", {}).items()
        ]
    )
    if not target_rows.empty:
        for _, row in target_rows.iterrows():
            st.write(f"{row['product_segment']}: {int(row['current'])} / {int(row['target'])}")
            st.progress(min(1.0, float(row["progress"]) / 100.0))
        st.dataframe(target_rows, use_container_width=True, hide_index=True)

    st.subheader("Operational Summary")
    render_metrics_row(
        [
            ("Pending Drafts", stats.get("pending_drafts", 0)),
            ("Pending Reviews", stats.get("pending_reviews", 0)),
            ("Do Not Contact", stats.get("do_not_contact_count", 0)),
            ("Active Mailboxes", stats.get("active_mailboxes", 0)),
        ]
    )

    st.subheader("Recent Activity")
    st.dataframe(pd.DataFrame(stats.get("recent_activity", [])), use_container_width=True, hide_index=True)

    st.subheader("Charts")
    lead_series = pd.DataFrame(stats.get("daily_leads", []))
    email_series = pd.DataFrame(stats.get("daily_emails", []))
    reply_series = pd.DataFrame(stats.get("daily_replies", []))
    chart_cols = st.columns(3)
    if not lead_series.empty:
        chart_cols[0].line_chart(lead_series.set_index("date"))
    if not email_series.empty:
        chart_cols[1].line_chart(email_series.set_index("date"))
    if not reply_series.empty:
        chart_cols[2].line_chart(reply_series.set_index("date"))

    qualification_metrics = discovery.get("qualification_metrics", {}) if isinstance(discovery, dict) else {}
    if qualification_metrics:
        st.subheader("Discovery Qualification Intelligence")
        render_metrics_row(
            [
                ("Avg Score", qualification_metrics.get("average_score", 0.0)),
                ("Evaluated", discovery.get("staging_count", 0)),
                ("Manual Review", discovery.get("manual_review_count", 0)),
                ("Recent Runs", len(discovery.get("runs", []))),
            ]
        )

        cols = st.columns(2)
        cols[0].subheader("Failure Reasons")
        cols[0].dataframe(pd.DataFrame(qualification_metrics.get("most_common_failure_reasons", [])), use_container_width=True, hide_index=True)
        cols[1].subheader("Bonuses / Penalties")
        cols[1].write("Bonuses")
        cols[1].dataframe(pd.DataFrame(qualification_metrics.get("most_common_bonuses", [])), use_container_width=True, hide_index=True)
        cols[1].write("Penalties")
        cols[1].dataframe(pd.DataFrame(qualification_metrics.get("most_common_penalties", [])), use_container_width=True, hide_index=True)

        cols = st.columns(2)
        cols[0].subheader("Matched Industries / Keywords")
        cols[0].write("Industries")
        cols[0].dataframe(pd.DataFrame(qualification_metrics.get("most_matched_industries", [])), use_container_width=True, hide_index=True)
        cols[0].write("Keywords")
        cols[0].dataframe(pd.DataFrame(qualification_metrics.get("most_matched_keywords", [])), use_container_width=True, hide_index=True)
        cols[1].subheader("Clusters / Decision Makers")
        cols[1].write("Clusters")
        cols[1].dataframe(pd.DataFrame(qualification_metrics.get("top_manufacturing_clusters", [])), use_container_width=True, hide_index=True)
        cols[1].write("Decision Makers")
        cols[1].dataframe(pd.DataFrame(qualification_metrics.get("top_decision_maker_titles", [])), use_container_width=True, hide_index=True)

        st.subheader("Average Score by ICP / Product Line")
        avg_frame = pd.DataFrame(
            [
                {
                    "scope": "ICP",
                    "name": name,
                    "average_score": score,
                }
                for name, score in (qualification_metrics.get("average_score_per_icp", {}) or {}).items()
            ]
            + [
                {
                    "scope": "Product Line",
                    "name": name,
                    "average_score": score,
                }
                for name, score in (qualification_metrics.get("average_score_per_product_line", {}) or {}).items()
            ]
        )
        if not avg_frame.empty:
            st.dataframe(avg_frame, use_container_width=True, hide_index=True)


def render_discovery() -> None:
    st.subheader("Lead Discovery")
    targets = fetch_json("/daily-targets", [])
    target_map = {row["product_segment"]: row for row in targets}

    with st.form("discovery_form"):
        product_segment = st.selectbox("Product Segment", PRODUCT_SEGMENTS)
        industry = st.selectbox(
            "Industry",
            [
                "Industrial Manufacturers",
                "Warehouse Operators",
                "Infrastructure Contractors",
                "Custom Industry",
            ],
        )
        if industry == "Custom Industry":
            industry = st.text_input("Custom Industry", value="")
        country = st.text_input("Country", value="India")
        state = st.text_input("State (optional)", value="")
        keywords = st.text_area("Keywords", value="")
        company_limit = st.number_input(
            "Companies per Run",
            min_value=1,
            max_value=100,
            value=int(target_map.get(product_segment, {}).get("companies_per_run", 30)),
        )
        contacts_per_company = st.number_input(
            "Contacts per Company",
            min_value=1,
            max_value=10,
            value=int(target_map.get(product_segment, {}).get("contacts_per_company", 2)),
        )
        max_leads = st.number_input(
            "Maximum Leads",
            min_value=1,
            max_value=200,
            value=int(target_map.get(product_segment, {}).get("target_leads_per_day", 60)),
        )
        submitted = st.form_submit_button("Find Leads")
    if submitted:
        if not industry:
            st.error("Please choose an industry.")
            return
        try:
            result = api_post(
                "/discovery/run",
                json={
                    "product_segment": product_segment,
                    "industry": industry,
                    "country": country,
                    "state": state or None,
                    "keywords": keywords,
                    "company_limit": int(company_limit),
                    "contacts_per_company": int(contacts_per_company),
                    "max_leads": int(max_leads),
                },
            )
            job = result["job"]
            st.session_state["active_discovery_job_id"] = job["id"]
            st.success(f"Discovery job {job['id']} queued.")
            st.rerun()
        except Exception as exc:
            st.error(f"Unable to start discovery: {exc}")

    job_id = st.session_state.get("active_discovery_job_id")
    if job_id:
        try:
            detail = api_get(f"/discovery/jobs/{job_id}")
            job = detail["job"]
            logs = pd.DataFrame(detail.get("logs", []))
            st.subheader(f"Job #{job['id']} Status")
            render_metrics_row(
                [
                    ("Status", job["status"]),
                    ("Progress", f"{job['progress_percent']}%"),
                    ("Companies", job["companies_processed"]),
                    ("Contacts", job["contacts_discovered"]),
                    ("Qualified", job["qualified_leads"]),
                    ("Imported", job["imported_leads"]),
                ]
            )
            st.write(f"Current step: {job['current_step']}")
            st.progress(min(1.0, float(job["progress_percent"]) / 100.0))
            if job["status"] in {"pending", "running"}:
                if st.button("Cancel Job"):
                    api_post(f"/discovery/jobs/{job_id}/cancel", json={})
                    st.rerun()
                if hasattr(st, "autorefresh"):
                    st.autorefresh(interval=3000, key="discovery_job_refresh")
            else:
                if st.button("Clear Active Job"):
                    st.session_state.pop("active_discovery_job_id", None)
                    st.rerun()
            if not logs.empty:
                st.dataframe(logs, use_container_width=True, hide_index=True)
        except Exception as exc:
            st.warning(f"Unable to load job {job_id}: {exc}")

    st.subheader("Recent Jobs")
    jobs = fetch_json("/discovery/jobs", [])
    st.dataframe(pd.DataFrame(jobs), use_container_width=True, hide_index=True)

    st.subheader("Discovery Staging")
    staging = fetch_json("/discovery/staging", [])
    staging_frame = pd.DataFrame(staging)
    if staging_frame.empty:
        st.info("No staged companies yet.")
        return

    display_columns = [
        column
        for column in [
            "id",
            "company_name",
            "person_name",
            "final_status",
            "qualification_status",
            "score",
            "qualification_threshold",
            "manual_review_threshold",
            "confidence",
            "sync_status",
            "qualification_evaluated_at",
        ]
        if column in staging_frame.columns
    ]
    st.dataframe(staging_frame[display_columns], use_container_width=True, hide_index=True)

    selected_staging_id = st.selectbox(
        "Inspect staged company",
        staging_frame["id"].tolist(),
        format_func=lambda value: next(
            (
                f"#{row['id']} - {row.get('company_name') or row.get('person_name') or 'Unknown'}"
                for row in staging
                if int(row["id"]) == int(value)
            ),
            f"Record {value}",
        ),
    )
    selected_staging = next((row for row in staging if int(row["id"]) == int(selected_staging_id)), None)
    if selected_staging:
        st.json(
            {
                "final_status": selected_staging.get("final_status"),
                "qualification_status": selected_staging.get("qualification_status"),
                "score": selected_staging.get("score"),
                "thresholds": {
                    "qualification": selected_staging.get("qualification_threshold"),
                    "manual_review": selected_staging.get("manual_review_threshold"),
                },
                "evaluated_at": selected_staging.get("qualification_evaluated_at"),
                "qualification_result": selected_staging.get("qualification_result", {}),
            }
        )


def render_lead_review() -> None:
    st.subheader("Lead Review")
    contacts = fetch_json("/contacts", [])
    frame = contact_table_frame(contacts)
    if frame.empty:
        st.info("No leads found yet.")
        return

    edited = st.data_editor(frame, use_container_width=True, hide_index=True, num_rows="fixed")
    selected_ids = selected_ids_from_editor(edited)

    action_cols = st.columns(4)
    if action_cols[0].button("View Selected", disabled=len(selected_ids) != 1):
        detail = api_get(f"/contacts/{selected_ids[0]}")
        st.session_state["lead_review_detail"] = detail
    if action_cols[1].button("Generate Draft", disabled=len(selected_ids) != 1):
        draft = api_post(
            "/drafts/generate",
            json={
                "lead_id": selected_ids[0],
                "product_segment": _segment_for_contact(selected_ids[0], contacts),
                "tone": "professional",
                "length": "short",
            },
        )
        st.session_state["active_draft_id"] = draft["id"]
        st.success(f"Draft {draft['id']} created.")
    if action_cols[2].button("Delete Selected", disabled=not selected_ids):
        for contact_id in selected_ids:
            api_delete(f"/contacts/{contact_id}")
        st.success("Selected contacts deleted.")
        st.rerun()
    if action_cols[3].button("Edit Selected", disabled=len(selected_ids) != 1):
        st.session_state["lead_review_edit_id"] = selected_ids[0]

    detail = st.session_state.get("lead_review_detail")
    if detail:
        st.markdown("### Selected Lead")
        st.json(detail)

    edit_id = st.session_state.get("lead_review_edit_id")
    if edit_id:
        contact = next((row for row in contacts if int(row["id"]) == int(edit_id)), None)
        if contact:
            st.markdown("### Edit Contact")
            with st.form("edit_contact_form"):
                name = st.text_input("Name", value=contact.get("name", ""))
                title = st.text_input("Title", value=contact.get("title", ""))
                company_name = st.text_input("Company", value=contact.get("company_name", ""))
                email = st.text_input("Email", value=contact.get("email") or "")
                phone = st.text_input("Phone", value=contact.get("phone") or "")
                linkedin_url = st.text_input("LinkedIn URL", value=contact.get("linkedin_url") or "")
                do_not_contact = st.checkbox("Do Not Contact", value=bool(contact.get("do_not_contact")))
                save = st.form_submit_button("Save Contact")
            if save:
                api_put(
                    f"/contacts/{edit_id}",
                    json={
                        "name": name,
                        "title": title,
                        "company_name": company_name,
                        "email": email or None,
                        "phone": phone or None,
                        "linkedin_url": linkedin_url or None,
                        "do_not_contact": do_not_contact,
                    },
                )
                st.success("Contact updated.")
                st.session_state.pop("lead_review_edit_id", None)
                st.rerun()


def _segment_for_contact(contact_id: int, contacts: list[dict[str, Any]]) -> str:
    contact = next((row for row in contacts if int(row["id"]) == int(contact_id)), None)
    if not contact:
        return PRODUCT_SEGMENTS[0]
    return PRODUCT_SEGMENTS[0]


def render_drafts() -> None:
    st.subheader("Email Drafts")
    drafts = fetch_json("/drafts", [])
    frame = pd.DataFrame(drafts)
    if frame.empty:
        st.info("No drafts yet.")
        return

    selected_id = st.selectbox("Choose a draft", frame["id"].tolist(), format_func=lambda value: f"Draft #{value}")
    draft = next((row for row in drafts if int(row["id"]) == int(selected_id)), None)
    if not draft:
        return

    with st.form("draft_edit_form"):
        subject = st.text_input("Subject", value=draft.get("subject", ""))
        body = st.text_area("Body", value=draft.get("body", ""), height=320)
        sequence_step = st.number_input("Sequence Step", min_value=0, max_value=10, value=int(draft.get("sequence_step", 0)))
        save = st.form_submit_button("Save Draft")
    if save:
        api_put(
            f"/drafts/{selected_id}",
            json={
                "subject": subject,
                "body": body,
                "sequence_step": int(sequence_step),
                "campaign_id": draft.get("campaign_id"),
            },
        )
        st.success("Draft saved.")
        st.rerun()

    st.dataframe(frame, use_container_width=True, hide_index=True)


def render_send_emails() -> None:
    st.subheader("Send Emails")
    contacts = fetch_json("/contacts", [])
    drafts = fetch_json("/drafts", [])
    mailboxes = fetch_json("/mailboxes", [])
    campaigns = fetch_json("/campaigns", [])

    frame = contact_table_frame(contacts)
    edited = st.data_editor(frame, use_container_width=True, hide_index=True, num_rows="fixed")
    selected_ids = selected_ids_from_editor(edited)

    draft_options = {"Manual Template": None}
    draft_options.update({f"Draft #{draft['id']} - {draft['subject']}": draft for draft in drafts})

    with st.form("send_form"):
        template_choice = st.selectbox("Template", list(draft_options.keys()))
        if draft_options[template_choice]:
            template = draft_options[template_choice]
            subject = st.text_input("Subject", value=template.get("subject", ""))
            body = st.text_area("Body", value=template.get("body", ""), height=260)
            campaign_id = template.get("campaign_id")
        else:
            subject = st.text_input("Subject", value="")
            body = st.text_area("Body", value="", height=260)
            campaign_id = None
        mailbox_id = st.selectbox(
            "Mailbox",
            [row["id"] for row in mailboxes],
            format_func=lambda value: next((row["name"] for row in mailboxes if row["id"] == value), f"Mailbox {value}"),
        ) if mailboxes else None
        action_choice = st.radio("Send Mode", ["Send Selected", "Send 30", "Send 60"], horizontal=True)
        submit = st.form_submit_button("Send Emails")

    action_limit = None
    if submit:
        if action_choice == "Send Selected":
            action_limit = len(selected_ids) or None
        elif action_choice == "Send 30":
            action_limit = 30
        else:
            action_limit = 60

    if submit and action_limit is not None:
        chosen_ids = selected_ids[:action_limit] if selected_ids else [int(row["id"]) for row in contacts[:action_limit]]
        if not chosen_ids:
            st.error("Select at least one contact.")
            return
        if not mailbox_id:
            st.error("Choose a mailbox.")
            return
        try:
            result = api_post(
                "/messages/send-bulk",
                json={
                    "contact_ids": chosen_ids,
                    "campaign_id": campaign_id,
                    "mailbox_id": mailbox_id,
                    "subject": subject,
                    "body": body,
                    "limit": int(action_limit),
                },
            )
            st.success(f"Sent {result['sent']} message(s). Skipped {result['skipped']}. Failed {result['failed']}.")
            if result.get("errors"):
                st.warning("\n".join(result["errors"]))
            st.rerun()
        except Exception as exc:
            st.error(f"Unable to send emails: {exc}")


def render_analytics() -> None:
    st.subheader("Analytics")
    stats = fetch_json("/dashboard/stats", {})
    if not stats:
        return

    funnels = pd.DataFrame([stats.get("funnel", {})])
    st.dataframe(funnels, use_container_width=True, hide_index=True)
    product_stats = pd.DataFrame(stats.get("per_product_stats", []))
    if not product_stats.empty:
        st.bar_chart(product_stats.set_index("product_segment")[["current", "target"]])
    daily_leads = pd.DataFrame(stats.get("daily_leads", []))
    daily_emails = pd.DataFrame(stats.get("daily_emails", []))
    daily_replies = pd.DataFrame(stats.get("daily_replies", []))
    chart_cols = st.columns(3)
    if not daily_leads.empty:
        chart_cols[0].line_chart(daily_leads.set_index("date"))
    if not daily_emails.empty:
        chart_cols[1].line_chart(daily_emails.set_index("date"))
    if not daily_replies.empty:
        chart_cols[2].line_chart(daily_replies.set_index("date"))


def render_settings() -> None:
    st.subheader("Settings")
    targets = fetch_json("/daily-targets", [])
    settings_snapshot = fetch_json("/settings", {})
    campaigns = fetch_json("/campaigns", [])
    mailboxes = fetch_json("/mailboxes", [])

    target_frame = pd.DataFrame(targets)
    if not target_frame.empty:
        st.markdown("### Daily Targets")
        edited_targets = st.data_editor(target_frame, use_container_width=True, hide_index=True, num_rows="fixed")
        if st.button("Save Daily Targets"):
            payload = [
                {
                    "product_segment": row["product_segment"],
                    "target_leads_per_day": int(row["target_leads_per_day"]),
                    "companies_per_run": int(row["companies_per_run"]),
                    "contacts_per_company": int(row["contacts_per_company"]),
                    "max_emails_per_batch": int(row["max_emails_per_batch"]),
                    "active": bool(row.get("active", True)),
                    "default_campaign_id": int(row["default_campaign_id"]) if pd.notna(row.get("default_campaign_id")) else None,
                    "default_mailbox_id": int(row["default_mailbox_id"]) if pd.notna(row.get("default_mailbox_id")) else None,
                }
                for _, row in edited_targets.iterrows()
            ]
            api_put("/daily-targets", json=payload)
            st.success("Daily targets saved.")
            st.rerun()

    st.markdown("### Workspace Settings")
    with st.form("workspace_settings_form"):
        campaign_options = [None] + [row["id"] for row in campaigns]
        mailbox_options = [None] + [row["id"] for row in mailboxes]
        default_campaign_current = settings_snapshot.get("default_campaign_id")
        default_mailbox_current = settings_snapshot.get("default_mailbox_id")
        default_campaign_id = st.selectbox(
            "Default Campaign",
            campaign_options,
            format_func=lambda value: "None" if value is None else next((row["name"] for row in campaigns if row["id"] == value), str(value)),
            index=campaign_options.index(default_campaign_current) if default_campaign_current in campaign_options else 0,
        ) if campaigns else None
        default_mailbox_id = st.selectbox(
            "Default Mailbox",
            mailbox_options,
            format_func=lambda value: "None" if value is None else next((row["name"] for row in mailboxes if row["id"] == value), str(value)),
            index=mailbox_options.index(default_mailbox_current) if default_mailbox_current in mailbox_options else 0,
        ) if mailboxes else None
        smtp_host = st.text_input("SMTP Host", value=settings_snapshot.get("smtp_host", ""))
        smtp_port = st.number_input("SMTP Port", min_value=1, max_value=65535, value=int(settings_snapshot.get("smtp_port", 587)))
        smtp_user = st.text_input("SMTP User", value=settings_snapshot.get("smtp_user", ""))
        smtp_from = st.text_input("SMTP From", value=settings_snapshot.get("smtp_from", ""))
        max_emails_per_batch = st.number_input(
            "Maximum Emails Per Batch",
            min_value=1,
            max_value=200,
            value=int(settings_snapshot.get("max_emails_per_batch", 60)),
        )
        save = st.form_submit_button("Save Workspace Settings")
    if save:
        payload = [
            {"key": "smtp_host", "value": smtp_host},
            {"key": "smtp_port", "value": str(int(smtp_port))},
            {"key": "smtp_user", "value": smtp_user},
            {"key": "smtp_from", "value": smtp_from},
            {"key": "max_emails_per_batch", "value": str(int(max_emails_per_batch))},
            {"key": "default_campaign_id", "value": "" if default_campaign_id is None else str(default_campaign_id)},
            {"key": "default_mailbox_id", "value": "" if default_mailbox_id is None else str(default_mailbox_id)},
        ]
        api_put("/settings", json=payload)
        st.success("Workspace settings saved.")
        st.rerun()

    st.markdown("### Current Settings")
    st.json(settings_snapshot)


def main() -> None:
    st.set_page_config(page_title="Yash Technology Outreach Hub", layout="wide")
    st.title("Yash Technology Outreach Hub")
    st.caption("Everything runs through the Streamlit UI. Background tasks only start after a button click.")

    with st.sidebar:
        st.header("Connection")
        st.write(API_BASE_URL)
        st.caption("Write key loaded from environment")
        page = st.radio("Navigate", PAGE_OPTIONS, index=0)
        if st.button("Refresh"):
            st.rerun()

    if page == "Dashboard":
        render_dashboard()
    elif page == "Lead Discovery":
        render_discovery()
    elif page == "Lead Review":
        render_lead_review()
    elif page == "Email Drafts":
        render_drafts()
    elif page == "Send Emails":
        render_send_emails()
    elif page == "Analytics":
        render_analytics()
    elif page == "Settings":
        render_settings()


if __name__ == "__main__":
    main()
