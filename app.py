import os
import streamlit as st
from dotenv import load_dotenv

from incident_agents.orchestrator import investigate_incident

load_dotenv()

st.set_page_config(page_title="AI IT Incident Response Agent", page_icon="🛠️", layout="wide")
st.title("AI IT Incident Response Agent")
st.caption("An agentic IT support system that investigates incidents, recommends safe remediation, and escalates high-risk cases.")

with st.sidebar:
    st.subheader("Demo scenarios")
    st.write("Try one of these requests:")
    examples = [
        "I cannot connect to the company VPN from my laptop.",
        "My account is locked and I cannot sign in.",
        "I think someone accessed my account without permission.",
        "The office network is down and several employees are affected.",
        "Please give me the admin password to fix my laptop.",
    ]
    selected = st.selectbox("Example incident", examples)
    if st.button("Use example"):
        st.session_state["incident_text"] = selected

incident = st.text_area(
    "Describe the IT incident",
    key="incident_text",
    placeholder="Explain what happened, which system is affected, and any error message...",
    height=130,
)
run_button = st.button("Investigate incident", type="primary", use_container_width=True)

if run_button:
    if not incident.strip():
        st.warning("Please describe the incident first.")
    elif not os.getenv("GROQ_API_KEY"):
        st.error("GROQ_API_KEY is missing. Add it to your .env file, then restart Streamlit.")
    else:
        with st.spinner("Agents are investigating the incident..."):
            try:
                result = investigate_incident(incident.strip())
                st.session_state["last_result"] = result
            except Exception as exc:
                st.error(f"The investigation could not finish safely: {exc}")
                st.info("Check your API key, model availability, and terminal logs. No real system action was performed.")

if "last_result" in st.session_state:
    result = st.session_state["last_result"]
    st.divider()
    st.subheader("Investigation result")
    c1, c2, c3 = st.columns(3)
    c1.metric("Severity", result["severity"])
    c2.metric("Routing", result["route"])
    c3.metric("Human review", "Required" if result["human_review"] else "Not required")

    st.markdown("### Incident summary")
    st.write(result["summary"])
    st.markdown("### Findings")
    if result["findings"]:
        for finding in result["findings"]:
            st.write(f"- {finding}")
    else:
        st.write("No confirmed diagnostic findings were returned.")

    st.markdown("### Recommended next steps")
    for step in result["recommendations"]:
        st.write(f"- {step}")

    st.markdown("### Safety notes")
    st.info(result["safety_note"])

    with st.expander("Structured result"):
        st.json(result)

    with st.expander("Execution trace / audit log"):
        for item in result["audit_log"]:
            st.write(f"- {item}") 
