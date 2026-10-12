import os
import gradio as gr
from dotenv import load_dotenv

from models.schemas import IncidentReport
from guardrails.safety_filters import (
    validate_incident_input,
    is_high_risk_incident,
)
from incident_agents.orchestrator_agent import orchestrate_incident

load_dotenv()


def process_incident(
    incident_id: str,
    description: str,
    category: str,
    priority: str,
    affected_user: str,
):
    try:
        incident = IncidentReport(
            incident_id=incident_id.strip(),
            description=description.strip(),
            category=category,
            priority=priority,
            affected_user=affected_user.strip() or "unknown",
        )

        valid, message = validate_incident_input(incident)
        if not valid:
            return {"status": "blocked_by_guardrail", "message": message}

        if is_high_risk_incident(incident):
            return {
                "incident_id": incident.incident_id,
                "status": "pending_human_review",
                "requires_human": True,
                "resolution_applied": False,
                "message": (
                    "This incident requires authorized human review. "
                    "Automated diagnostics were not started."
                ),
            }

        if not os.getenv("OPENAI_API_KEY"):
            return {
                "status": "configuration_required",
                "message": (
                    "OPENAI_API_KEY is missing. Configure it in a local .env "
                    "file before running the AI workflow. No real IT action "
                    "has been performed."
                ),
            }

        result = orchestrate_incident(incident)
        return result

    except Exception as exc:
        # Avoid displaying credentials, environment details, or stack traces.
        return {
            "status": "error",
            "message": (
                f"Could not process the incident ({type(exc).__name__}). "
                "Check the local terminal for debugging information."
            ),
        }


with gr.Blocks(title="AI IT Incident Response") as demo:
    gr.Markdown(
        """
        # AI IT Incident Response Assistant
        Submit an IT incident for triage and diagnostic recommendations.

        **Demo safety:** diagnostic tools return simulated information.
        The application does not connect to or modify real IT systems.
        Security and critical incidents require human review.
        """
    )

    with gr.Row():
        incident_id = gr.Textbox(
            label="Incident ID", value="INC-001"
        )
        affected_user = gr.Textbox(
            label="Affected user", value="demo-user"
        )

    description = gr.Textbox(
        label="Incident description",
        placeholder="Example: Office Wi-Fi is not working",
        lines=4,
    )

    with gr.Row():
        category = gr.Dropdown(
            choices=[
                "network", "account", "device",
                "vpn", "security", "other",
            ],
            value="network",
            label="Category",
        )
        priority = gr.Dropdown(
            choices=["low", "medium", "high", "critical"],
            value="medium",
            label="Priority",
        )

    submit = gr.Button("Analyze Incident", variant="primary")
    output = gr.JSON(label="Incident response")

    submit.click(
        fn=process_incident,
        inputs=[
            incident_id,
            description,
            category,
            priority,
            affected_user,
        ],
        outputs=output,
    )


if __name__ == "__main__":
    demo.launch()
