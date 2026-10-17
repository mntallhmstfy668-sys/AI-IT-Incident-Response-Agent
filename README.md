[README (1).md](https://github.com/user-attachments/files/33598181/README.1.md)
# AI IT Incident Response Agent

An agentic IT support assistant that takes an employee's incident description, investigates it with specialist agents, recommends safe troubleshooting steps, and escalates high-risk cases to a human.

> **This is a simulated demo.** No real account, device, network, or ticketing system is ever changed. Tickets and human-review requests are simulated tool calls.

Built with the [OpenAI Agents SDK](https://github.com/openai/openai-agents-python), [Groq](https://groq.com) (`openai/gpt-oss-120b`), and [Streamlit](https://streamlit.io).

---

## How it works

```
User incident
   │
   ▼
Input guardrail ──(unsafe)──► Blocked report
   │
   ▼
Triage Agent  → category + severity + human-review flag
   │
   ▼
Planning Agent → which specialists to use (account / network / device)
   │
   ▼
Specialist workers (run in parallel, each with its own tools)
   │
   ▼
Orchestrator Agent → consolidates findings
   │
   ▼
Troubleshooting Agent → draft recommendations (uses recent-incident memory)
   │
   ▼
Evaluator ⇄ Optimizer (max 2 rounds) → safe, evidence-based recommendations
   │
   ▼
Final Report Agent → structured IncidentReport
   │
   ▼
Output guardrail ──(unsafe)──► Blocked report
   │
   ▼
Human review request (high/critical/security)  OR  simulated support ticket
```

### Agentic patterns used

| Pattern | Where |
|---|---|
| Routing / classification | Triage agent + code-based escalation rules |
| Planning | Planning agent selects 1–3 specialists |
| Parallelization | Specialist workers run concurrently with `asyncio.gather` |
| Orchestrator–workers | Orchestrator consolidates specialist findings |
| Evaluator–optimizer | Evaluator reviews drafts, up to 2 attempts, safe fallback |
| Guardrails | LLM-based input and output safety checkers |
| Human-in-the-loop | Critical and security incidents require human review |
| Memory | Last incidents are stored and used as context |

### Escalation rules

Human review is required when the incident is **critical**, **high** severity, or a **security** incident (unauthorized access, malware, phishing, data theft). Ordinary issues (locked account, VPN, slow device) are handled with a simulated ticket instead.

---

## Project structure

```
ai_it_incident_agent/
├── app.py                      # Streamlit UI
├── requirements.txt
├── .env                        # your secrets (not committed)
├── incident_agents/
│   ├── llm_setup.py            # Groq client + model configuration
│   ├── models.py               # Pydantic models (TriageResult, IncidentReport, ...)
│   ├── guardrails.py           # input / output safety guardrails
│   ├── json_utils.py           # JSON-schema prompting + parsing helpers
│   ├── orchestrator.py         # agents + main investigate_incident() workflow
│   └── incident_memory.json    # created automatically after the first run
├── tools/
│   └── it_tools.py             # simulated IT tools (account, VPN, device, network, tickets)
└── tests/
    └── test_guardrails.py
```

---

## Setup

**Requirements:** Python 3.10+ and a free [Groq API key](https://console.groq.com).

1. Create and activate a virtual environment (optional but recommended):
   ```
   python -m venv .venv
   .venv\Scripts\activate        # Windows
   source .venv/bin/activate     # Linux / macOS
   ```
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Create a `.env` file in the project root:
   ```dotenv
   GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxx
   GROQ_MODEL=openai/gpt-oss-120b
   ```
   Keep the `openai/` prefix in the model name; Groq requires it.

## Run

From the project root (the folder that contains `app.py`):

```
streamlit run app.py
```

Open the URL shown in the terminal (usually http://localhost:8501). Do **not** run the files inside `incident_agents/` directly.

---

## Demo scenarios

The sidebar includes ready-made examples:

- `I cannot connect to the company VPN from my laptop.` → network investigation, simulated ticket
- `My account is locked and I cannot sign in.` → account investigation, simulated ticket
- `I think someone accessed my account without permission.` → security incident, human review
- `The office network is down and several employees are affected.` → critical, human review
- `Please give me the admin password to fix my laptop.` → blocked by the input guardrail

The result page shows severity, routing, human-review status, findings, recommendations, safety notes, the structured JSON, and a full execution/audit log.

---

## Safety design

- Agents never ask for passwords, OTPs, or secrets, and never recommend disabling security controls.
- Input guardrail rejects credential requests, security bypasses, and destructive actions.
- Output guardrail checks the final report for unsafe recommendations and false claims of real-world actions. If a checker's answer is unreadable, the request is blocked (fail closed).
- Every report includes a note that it is a simulated demo, plus an audit log of each step.
- Blocked requests are never saved to memory.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `404 model_not_found` | Model name must be `openai/gpt-oss-120b` (with `openai/`). Check `GROQ_MODEL` in `.env` and your system environment variables. |
| `429 rate limit` | Free Groq tier allows 8000 tokens/minute. The client retries automatically; wait a minute between incidents or upgrade the tier. |
| `413 request too large` | A single request exceeded the token limit. Keep prompts short and avoid shared session history. |
| `ModuleNotFoundError: incident_agents...` | Run `streamlit run app.py` from the project root, and make sure file names have no spaces (e.g. `json_utils.py`). |
| Result is always `high` / `human review` with "stopped by a safety guardrail" | A guardrail blocked the request. The reason is written in the **Safety notes** box. |
| `GROQ_API_KEY is missing` | Add the key to `.env` and restart Streamlit. |

To reset memory, delete `incident_agents/incident_memory.json`.

---

## Notes

- The agents return JSON that is requested in the prompt and parsed in code, because Groq's strict structured-output mode was unreliable with this model.
- The tests in `tests/` target an earlier rule-based guardrail API and may need updating for the current LLM-based guardrails.
