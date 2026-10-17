import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)


import asyncio

from agents import (
    Agent,
    Runner,
    SQLiteSession,
    trace,
    ModelSettings,
    InputGuardrailTripwireTriggered,
    OutputGuardrailTripwireTriggered,
)
from openai.types.shared import Reasoning

from incident_agents.llm_setup import build_model, MODEL_NAME
from incident_agents.models import (
    TriageResult,
    IncidentReport,
    InvestigationPlan,
)
from incident_agents.guardrails import (
    incident_input_guardrail,
    incident_output_guardrail,
)
from incident_agents.json_utils import json_instruction, safe_json, parse_model
from tools.it_tools import (
    check_account_status,
    check_vpn_status,
    check_device_status,
    check_network_status,
    search_it_knowledge,
    create_support_ticket,
    request_human_review,
)

MODEL = build_model()

# Reasoning tokens count toward max_tokens, so gpt-oss needs a bigger budget.
if "gpt-oss" in (MODEL_NAME or ""):
    MODEL_SETTINGS = ModelSettings(
        reasoning=Reasoning(effort="low"), max_tokens=2500
    )
else:
    MODEL_SETTINGS = ModelSettings(max_tokens=2000)


# --------------------------------------------------
# AGENTS
# --------------------------------------------------

triage_agent = Agent(
    name="Incident Triage Agent",
    model=MODEL,
    model_settings=MODEL_SETTINGS,
    input_guardrails=[incident_input_guardrail],
    instructions=(
        "Classify an employee IT incident. Return a structured TriageResult. "
        "Choose category from account, network, device, security, unknown. "
        "Choose severity from low, medium, high, critical. "
        "Critical means suspected compromise, active attack, or an outage affecting many employees. "
        "High is rare: only for a business-critical system down for a team or department. "
        "Medium means one employee is blocked from working, even with several ordinary "
        "problems at once (locked account, VPN, slow device). "
        "Low means a minor inconvenience. "
        "Use category security ONLY for signs of unauthorized access, malware, phishing, "
        "or data theft. A locked account, forgotten password, VPN failure or slow device "
        "is NOT security by itself. "
        "Set needs_human_review true only for critical severity or category security. "
        "Never ask for passwords, OTPs, or secrets."
    )
    + json_instruction(TriageResult),
)

account_worker = Agent(
    name="Account Investigation Worker",
    model=MODEL,
    model_settings=MODEL_SETTINGS,
    instructions=(
        "Investigate account and sign-in issues using tool results. "
        "Never ask for credentials. Never claim an action not performed."
    ),
    tools=[check_account_status, search_it_knowledge],
)

network_worker = Agent(
    name="Network Investigation Worker",
    model=MODEL,
    model_settings=MODEL_SETTINGS,
    instructions=(
        "Investigate VPN and network issues using tool results. "
        "Never recommend disabling security controls. "
        "Do not claim you changed any configuration."
    ),
    tools=[check_vpn_status, check_network_status, search_it_knowledge],
)

device_worker = Agent(
    name="Device Investigation Worker",
    model=MODEL,
    model_settings=MODEL_SETTINGS,
    instructions=(
        "Investigate device issues using tool results. "
        "Never recommend disabling security controls."
    ),
    tools=[check_device_status, search_it_knowledge],
)

orchestrator_agent = Agent(
    name="Incident Orchestrator",
    model=MODEL,
    model_settings=MODEL_SETTINGS,
    instructions=(
        "Consolidate specialist findings into an evidence-based summary. "
        "Do not invent diagnostic results. Security incidents must be escalated. "
        "Never claim real-world actions occurred."
    ),
    handoffs=[account_worker, network_worker, device_worker],
)

plan_agent = Agent(
    name="Investigation Planning Agent",
    model=MODEL,
    model_settings=MODEL_SETTINGS,
    instructions=(
        "Select the relevant specialists for an IT incident. "
        "Choose from account, network, device. "
        "Return an InvestigationPlan with 1 to 3 specialists and a short reason."
    )
    + json_instruction(InvestigationPlan),
)

troubleshooter_agent = Agent(
    name="Troubleshooting Agent",
    model=MODEL,
    model_settings=MODEL_SETTINGS,
    instructions=(
        "Write safe, concise troubleshooting recommendations based only on "
        "the supplied triage and investigation evidence. "
        "Distinguish confirmed facts from suggestions. "
        "Never claim the incident is fixed without evidence."
    ),
)

evaluator_agent = Agent(
    name="Resolution Evaluator",
    model=MODEL,
    model_settings=MODEL_SETTINGS,
    instructions=(
        "Evaluate the recommendations against the evidence. Return JSON with "
        "approved (boolean), issues (array of strings), and "
        "improved_recommendations (array of strings). "
        "Reject unsafe steps, unsupported claims, and requests for credentials."
    ),
)

final_report_agent = Agent(
    name="Final Incident Report Agent",
    model=MODEL,
    model_settings=MODEL_SETTINGS,
    output_guardrails=[incident_output_guardrail],
    instructions=(
        "Create a structured IncidentReport using only the supplied evidence. "
        "Use the provided severity, route, human_review value, findings, and "
        "recommendations. Do not invent tool results or claim real actions occurred. "
        "Include the required safety_note explaining that this is a simulated demo. "
        "Critical and security incidents must require human review. "
        "Recommendations must be safe and evidence-based."
    )
    + json_instruction(IncidentReport),
)


# --------------------------------------------------
# HELPERS
# --------------------------------------------------

def _run_agent(agent, prompt, session=None):
    try:
        return asyncio.run(Runner.run(agent, prompt, session=session))
    except (InputGuardrailTripwireTriggered, OutputGuardrailTripwireTriggered):
        raise
    except Exception as exc:
        raise RuntimeError(
            f"Agent stage '{agent.name}' failed: "
            f"{type(exc).__name__}: {exc}"
        ) from exc


def _run_structured(agent, prompt, model_cls, session=None, attempts=2):
    """Run an agent that returns JSON, retrying once if parsing fails."""
    last_error = None
    for _ in range(attempts):
        result = _run_agent(agent, prompt, session)
        try:
            return parse_model(result.final_output, model_cls)
        except Exception as exc:
            last_error = exc
    raise RuntimeError(
        f"Agent stage '{agent.name}' did not return valid {model_cls.__name__} "
        f"JSON after {attempts} attempts: {last_error}"
    )


def _guardrail_reason(exc):
    try:
        info = exc.guardrail_result.output.output_info
        return getattr(info, "reason", None) or str(info)
    except Exception:
        return "unknown reason"


def _blocked_report(reason):
    return {
        "severity": "high",
        "route": "human review",
        "human_review": True,
        "summary": "Automated processing was stopped by a safety guardrail.",
        "findings": [],
        "recommendations": [
            "Stop automated troubleshooting and ask authorized IT staff to review the request."
        ],
        "safety_note": (
            "No real account, device, network, or ticket system was changed. "
            f"Reason: {reason}"
        )[:500],
        "audit_log": [
            "Guardrail blocked automated processing.",
            "Human review is required.",
        ],
    }


# --------------------------------------------------
# MAIN WORKFLOW
# --------------------------------------------------

def investigate_incident(user_text: str) -> dict:
    audit = ["Investigation started."]
    session = SQLiteSession("it_incident_demo_session")

    with trace("it_incident_response"):

        # 1. Input guardrail runs before triage.
        try:
            triage = _run_structured(triage_agent, user_text, TriageResult)
        except InputGuardrailTripwireTriggered as exc:
            return _blocked_report(
                f"Input guardrail: {_guardrail_reason(exc)}"
            )

        audit.append(
            f"Input guardrail passed. Triage: {triage.category}/{triage.severity}."
        )

        needs_human = (
            triage.needs_human_review
            or triage.severity in ("high", "critical")
            or triage.category == "security"
        )

        audit.append(
            "Code-orchestrated routing: human review required."
            if needs_human
            else "Code-orchestrated routing: normal investigation allowed."
        )

        # 2. Planning.
        plan = _run_structured(
            plan_agent,
            (
                "Plan the investigation.\n"
                f"Triage: {triage.model_dump_json()}\n"
                f"Incident: {user_text}"
            ),
            InvestigationPlan,
        )

        selected = set(plan.specialists)
        if triage.category == "security":
            selected.update({"account", "device"})

        audit.append(
            f"Investigation plan: {', '.join(sorted(selected))}. "
            f"Reason: {plan.reason}"
        )

        # 3. Parallel specialist workers.
        worker_map = {
            "account": account_worker,
            "network": network_worker,
            "device": device_worker,
        }
        names = [n for n in ("account", "network", "device") if n in selected]

        async def run_workers():
            tasks = [
                Runner.run(
                    worker_map[name],
                    f"Investigate this incident using relevant tools: {user_text}",
                )
                for name in names
            ]
            return await asyncio.gather(*tasks, return_exceptions=True)

        worker_results = asyncio.run(run_workers())

        findings = []
        for name, result in zip(names, worker_results):
            if isinstance(result, Exception):
                findings.append(f"{name} worker failed: {type(result).__name__}.")
                audit.append(f"{name} worker failed; recovery applied.")
            else:
                findings.append(
                    f"{name} worker: {str(result.final_output)[:1800]}"
                )
                audit.append(f"Parallel worker completed: {name}.")

        # 4. Orchestrator consolidates the findings.
        consolidated = "\n".join(findings) or "No diagnostic findings were returned."

        orchestrated = _run_agent(
            orchestrator_agent,
            (
                f"Incident: {user_text}\n"
                f"Triage: {triage.model_dump_json()}\n"
                f"Specialist findings:\n{consolidated}"
            ),
            session,
        )
        findings.append(
            f"Orchestrator summary: {str(orchestrated.final_output)[:1800]}"
        )
        audit.append("Orchestrator-workers pattern: findings consolidated.")

        # 5. Draft recommendations.
        draft = _run_agent(
            troubleshooter_agent,
            (
                f"Incident: {user_text}\n"
                f"Triage: {triage.model_dump_json()}\n"
                f"Evidence:\n{chr(10).join(findings)}\n"
                "Provide safe troubleshooting recommendations."
            ),
            session,
        )
        recommendations_text = str(draft.final_output)
        audit.append("Troubleshooting draft generated.")

        # 6. Evaluator-optimizer, limited to two attempts.
        final_recommendations = [
            "Follow the approved IT troubleshooting procedure.",
            "If the issue persists, contact authorized IT support.",
        ]

        for attempt in range(2):
            evaluated = _run_agent(
                evaluator_agent,
                (
                    f"Incident: {user_text}\n"
                    f"Evidence:\n{chr(10).join(findings)}\n"
                    f"Draft:\n{recommendations_text}\n"
                    'Return JSON only: {"approved": true/false, '
                    '"issues": [], "improved_recommendations": []}'
                ),
            )

            parsed = safe_json(str(evaluated.final_output))

            if parsed and parsed.get("approved") is True:
                improvements = parsed.get("improved_recommendations")
                if improvements:
                    final_recommendations = improvements
                audit.append(f"Evaluator approved result on attempt {attempt + 1}.")
                break

            if parsed and parsed.get("improved_recommendations"):
                recommendations_text = "\n".join(parsed["improved_recommendations"])

            audit.append(f"Evaluator requested improvement on attempt {attempt + 1}.")
        else:
            audit.append("Evaluator retry limit reached; safe fallback used.")

        # 7. Final report (output guardrail runs on this agent).
        route = "human review" if needs_human else "normal investigation"

        report_prompt = (
            f"Incident: {user_text}\n"
            f"Severity: {triage.severity}\n"
            f"Route: {route}\n"
            f"Human review required: {needs_human}\n"
            f"Summary: {triage.summary}\n"
            f"Findings:\n{chr(10).join(findings)}\n"
            f"Recommendations:\n{chr(10).join(final_recommendations)}\n"
            "Create the final structured incident report. "
            "The report must accurately describe this as a simulated demo."
        )

        try:
            report_model = _run_structured(
                final_report_agent,
                report_prompt,
                IncidentReport,
                session,
            )
            audit.append("Output guardrail passed.")
        except OutputGuardrailTripwireTriggered as exc:
            reason = _guardrail_reason(exc)
            audit.append(f"Output guardrail blocked the report: {reason}")
            return _blocked_report(f"Output guardrail: {reason}")

        report = report_model.model_dump()
        report["audit_log"] = audit

        # 8. Human review or simulated ticket action.
        if needs_human:
            review_agent = Agent(
                name="Review Request Agent",
                model=MODEL,
                model_settings=MODEL_SETTINGS,
                instructions=(
                    "Call request_human_review with a concise incident summary "
                    "and a clear reason for escalation. The action is simulated."
                ),
                tools=[request_human_review],
            )
            review = _run_agent(
                review_agent,
                (
                    "Request simulated human review. "
                    "Reason: high-risk or security incident. "
                    f"Incident: {user_text}"
                ),
            )
            report["audit_log"].append(
                f"Human review requested (simulated): {str(review.final_output)[:300]}"
            )
        else:
            ticket_agent = Agent(
                name="Ticket Agent",
                model=MODEL,
                model_settings=MODEL_SETTINGS,
                instructions=(
                    "Create a simulated support ticket using the available tool. "
                    "Never claim a real ticket exists."
                ),
                tools=[create_support_ticket],
            )
            ticket = _run_agent(
                ticket_agent,
                (
                    "Create a simulated ticket. "
                    f"Title: {triage.category} incident. "
                    f"Description: {triage.summary}. "
                    f"Priority: {triage.severity}."
                ),
            )
            report["audit_log"].append(
                f"Ticket action result: {str(ticket.final_output)[:300]}"
            )

        return report 
