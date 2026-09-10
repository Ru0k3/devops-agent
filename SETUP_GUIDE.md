# Step-by-step setup guide

## 1. Open a terminal in the unzipped folder

```bash
cd devops-agent
```

The folder must contain `README.md`, `requirements.txt`, `run_demo.py`, `dashboard_server.py`, `agent/`, `tools/`, and `rag/`.

## 2. Check Python

Use Python 3.11, 3.12, or 3.13.

```bash
python --version
# or on macOS/Linux
python3 --version
```

## 3. Create and activate a virtual environment

### Windows PowerShell

```powershell
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
```

### Windows Command Prompt

```bat
py -3.12 -m venv .venv
.venv\Scripts\activate.bat
```

### macOS/Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
```

After activation, your terminal should show `(.venv)` at the start of the prompt.

## 4. Install dependencies

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

If Windows shows `python was not found`, use `py` instead of `python`. If macOS/Linux shows `python: command not found`, use `python3`.

## 5. Create `.env`

### Windows PowerShell

```powershell
Copy-Item .env.example .env
```

### Windows Command Prompt

```bat
copy .env.example .env
```

### macOS/Linux

```bash
cp .env.example .env
```

The basic demo requires **no API keys**. You can run it with all values blank.

## 6. Optional NVIDIA NIM key

1. Open <https://build.nvidia.com/settings/api-keys>.
2. Create or sign in to an NVIDIA account.
3. Generate an API key.
4. Copy the key immediately.
5. Open `.env` and set:

```dotenv
NVIDIA_API_KEY=nvapi-your-key-here
NVIDIA_MODEL=nvidia/llama-3.1-nemotron-70b-instruct
NVIDIA_EMBEDDING_MODEL=nvidia/llama-3.2-nv-embedqa-e5-v5
```

The key enables NVIDIA-generated diagnosis and report text. It does not control deployment routing.

## 7. Optional Langfuse keys

1. Open <https://cloud.langfuse.com> or the regional Langfuse cloud URL used by your account.
2. Create an account and a project.
3. Open the project settings.
4. Create a new API key pair.
5. Copy the public key, secret key, and the host for your region into `.env`:

```dotenv
LANGFUSE_PUBLIC_KEY=pk-lf-your-public-key
LANGFUSE_SECRET_KEY=sk-lf-your-secret-key
LANGFUSE_HOST=https://cloud.langfuse.com
```

If your Langfuse project is in the US region, use the host shown by Langfuse for that project, such as `https://us.cloud.langfuse.com`.

After running an incident, open the Langfuse project and look for the new trace. The local JSON trace is still written under `logs/` even when Langfuse is configured.

## 8. Optional Slack key

Create a Slack Incoming Webhook for a test channel and set:

```dotenv
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/your/webhook
```

Do not use a production channel for the hackathon demo. If this value is blank, reports are printed/stored locally.

## 9. Keys you do not need for the seeded demo

Leave these blank:

```dotenv
GITHUB_TOKEN=
```

The current demo intentionally uses seeded commit data so it is deterministic. A real GitHub adapter can be added later.

## 10. Ingest the Chroma postmortems

Run this once after installing dependencies:

```bash
python rag/ingest.py
```

Expected output:

```text
ingested=8
```

This creates `rag/chroma_db/` and the persistent `incident-postmortems` collection.

## 11. Run the dashboard

```bash
python dashboard_server.py
```

Open <http://127.0.0.1:8765> in Chrome.

Click **Run safe path** to show `payment-regression` auto-deploying to the isolated sandbox. Click **Run escalation path** to show a risk-blocked incident. The **Stack proof** panel shows LangGraph, LangChain, FastMCP, Chroma, and Langfuse usage.

Stop the server with `Ctrl+C`.

## 12. Run the CLI demos

```bash
python run_demo.py --incident payment-regression
python run_demo.py --incident auth-risky
python run_demo.py --incident billing-calc-error
```

## 13. Run the tests and evaluation

```bash
python -m pytest -q
python eval/run_eval.py
```

Expected evaluation:

```json
{
  "cases": 7,
  "root_cause_correct": 7,
  "routing_correct": 7,
  "unsafe_auto_deploys": 0
}
```

## 14. Start the standalone MCP server

This is optional for the normal dashboard demo:

```bash
python tools/mcp_server.py
```

It starts the FastMCP stdio server. Stop it with `Ctrl+C`.

## Security reminders

Never commit `.env`, paste keys into GitHub, or show keys in the recording. If a key is exposed, revoke it and generate a replacement immediately. The hackathon demo does not require any key to prove the safety, RAG, MCP, LangGraph, or evaluation behavior.
