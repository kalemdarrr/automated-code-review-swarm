# Automated Code Review & Security Swarm

Automated Code Review & Security Swarm is a local-first agentic LLM application for professional code review and security auditing. Developers paste or upload source code, and a multi-agent swarm analyzes it as text only. The system retrieves evidence from a ChromaDB-backed RAG knowledge base, uses a locally loaded HuggingFace-compatible Transformer model, monitors risk, and returns a report-ready Markdown review.

Not OpenAI, Anthropic, Gemini, or remote LLM API calls are used. The language model is loaded from `models/local_llm/` with `local_files_only=True`.

## Problem Definition

Manual code review is slow and inconsistent, especially when reviewers must simultaneously check security, maintainability, architecture, and performance. This project builds a local AI review system that combines specialized agents, retrieval over trusted engineering references, risk controls, and an evaluation pipeline.

The system does not execute submitted code, does not run shell commands from code, and does not send code to external services.

## Academic Requirement Mapping

| Requirement | Implementation |
|---|---|
| Multi-agent system | CodeReviewerAgent, SecurityAuditorAgent, RAGResearchAgent, RiskMonitorAgent, SeniorDeveloperAgent |
| RAG | ChromaDB vector database over Clean Code, OWASP, Python/PyTorch docs |
| Transformer architecture | Local HuggingFace-compatible Transformer model loaded from models/local_llm/ |
| Monitoring | RiskMonitorAgent, hallucination checker, command safety filter |
| Evaluation | Benchmark-based extrinsic evaluation pipeline |
| UI | Streamlit interface |
| Report | Markdown/PDF-ready final report format |

## Architecture

```text
Developer
  |
  v
Streamlit UI or FastAPI /review
  |
  v
ReviewService
  |
  v
SwarmOrchestrator
  |-- RAGResearchAgent -> Retriever -> ChromaDB -> knowledge_base/raw
  |-- CodeReviewerAgent -> LocalLLMClient -> Local Transformer model
  |-- SecurityAuditorAgent -> LocalLLMClient -> Local Transformer model
  |-- RiskMonitorAgent -> OutputGuard + HallucinationChecker + CommandSafetyFilter
  |-- SeniorDeveloperAgent -> ReportBuilder
  |
  v
Markdown report + risk score + RAG sources + agent trace
```

## Agents

`RAGResearchAgent` retrieves Clean Code, SOLID, OWASP, secure coding, Python, and PyTorch context from ChromaDB.

`CodeReviewerAgent` detects code smells, maintainability problems, performance issues, and architecture/SOLID violations.

`SecurityAuditorAgent` detects SQL injection, unsafe eval, hardcoded secrets, path traversal, insecure subprocess use, unsafe deserialization, and related OWASP issues.

`RiskMonitorAgent` checks unsupported claims, dangerous command suggestions, unsafe fixes, and computes a 0 to 100 risk score.

`SeniorDeveloperAgent` deduplicates findings, prioritizes issues, and builds the final professional Markdown report.

## Local Model Setup

Place a complete HuggingFace-compatible causal language model under:

```text
models/local_llm/
  config.json
  tokenizer.json or tokenizer.model
  model.safetensors or pytorch_model.bin
```

Examples of compatible local model families include CodeLlama, DeepSeek-Coder, StarCoder, Mistral, Llama-based instruct models, and other causal language models supported by `AutoModelForCausalLM`.

The loader in `app/core/llm/local_model_loader.py` uses:

```python
AutoTokenizer.from_pretrained(path, local_files_only=True)
AutoModelForCausalLM.from_pretrained(path, local_files_only=True)
```

If CUDA is available, it uses `device_map="auto"` and half precision (`float16` or `bfloat16` when supported). If CUDA is unavailable, it falls back to CPU with a warning.

The project also includes a downloader:

```bash
python scripts/download_models.py
```

Default model ids:

- LLM: `Qwen/Qwen2.5-Coder-0.5B-Instruct`
- Embedding: `sentence-transformers/all-MiniLM-L6-v2`

You can override them in `.env`:

```env
HF_LLM_MODEL_ID=Qwen/Qwen2.5-Coder-0.5B-Instruct
HF_EMBEDDING_MODEL_ID=sentence-transformers/all-MiniLM-L6-v2
```

## CUDA Setup

Install a PyTorch build that matches your CUDA version. Then verify:

```bash
python -c "import torch; print(torch.cuda.is_available()); print(torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'cpu')"
```

The `/health` endpoint reports CUDA availability, model file presence, model loaded state, and vector DB status.

## RAG Knowledge Base

Raw knowledge lives under `knowledge_base/raw/`:

```text
clean_code/
owasp/
python_docs/
pytorch_docs/
secure_coding/
```

The ingestion pipeline loads `.md`, `.txt`, and optional `.pdf` files, extracts metadata, chunks documents with overlap, embeds chunks locally, and stores them in ChromaDB under `knowledge_base/chroma_db/`.

For embeddings, the system first looks for a local SentenceTransformer model at `models/local_embedding/`. If none is supplied, it uses deterministic local hashing embeddings so the RAG pipeline remains local and testable. For stronger retrieval, place a local SentenceTransformer model in `models/local_embedding/`.

Ingest the knowledge base:

```bash
python scripts/ingest_knowledge_base.py
```

## Running the Backend

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/download_models.py
python scripts/ingest_knowledge_base.py
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

API endpoints:

```text
GET  /health
POST /review
POST /rag/ingest
GET  /rag/status
POST /evaluation/run
```

## Running the UI

```bash
streamlit run ui/streamlit_app.py
```

The UI calls the FastAPI backend by default. If the backend is unavailable, it can call the local service layer directly for a demo.

## Running Evaluation

```bash
python scripts/run_evaluation.py
```

## Full Bootstrap And Verification

```bash
bash scripts/bootstrap_local.sh
```

The bootstrap script performs:

- virtual environment creation (if missing)
- dependency installation
- local model download
- RAG ingestion
- end-to-end stack verification via `scripts/verify_stack.py`

The benchmark includes at least 10 examples: SQL injection, hardcoded password, unsafe eval, path traversal, insecure subprocess usage, bad exception handling, duplicated code, long function, missing input validation, and inefficient loop.

Evaluation reports:

- total examples
- detected vulnerabilities
- missed vulnerabilities
- false positives
- RAG relevance average
- latency average
- final score

Perplexity is left as an optional placeholder because the core requirement is extrinsic task evaluation for an agentic application. The project uses an existing local Transformer model rather than training from scratch. Domain performance is improved through RAG, and evaluation measures review task performance rather than model pretraining quality.

## Risk Management Strategy

The system analyzes code as text only. It never executes submitted code, never runs commands found in code, and never sends code to remote APIs.

Risk controls include:

- command safety filtering for destructive commands such as `rm -rf`, `curl | sh`, `chmod 777`, `sudo`, and destructive database commands
- hallucination checks that compare agent claims against RAG snippets
- confidence reduction for unsupported claims
- risk scoring from severity, confidence, source support, dangerous suggestions, and patch risk
- JSONL audit logs containing timestamp, language, agent steps, retrieved sources, risk score, and final decision

If RAG evidence is weak, the final report includes: "Knowledge base confidence is low for this specific claim."

## Example Output

```text
# Automated Code Review & Security Report

## 1. Executive Summary
The swarm identified security and clean-code findings. Overall monitored risk is HIGH.

## 2. Risk Score
Score: 72/100

## 3. Security Findings
- SQL injection risk
- Unsafe eval execution
- Hardcoded secret

## 7. Monitoring Summary
- Unsupported claims are listed when RAG support is weak.
- Dangerous suggestions are blocked before final output.
```

## Demo Scenario

Run:

```bash
python scripts/run_demo.py
```

The bundled vulnerable sample includes a hardcoded password, SQL injection, unsafe eval, path traversal, insecure subprocess usage, and poor function design. The demo writes a Markdown report to `reports/sample_outputs/demo_report.md`.

## Clean Architecture Notes

The project separates API routes, domain services, core LLM/RAG/agent logic, monitoring, evaluation, reporting, and UI. Routes are thin, services are injectable, agents are separate classes, and model loading is controlled through a local client abstraction.

## Team Role Section

- AI Software Architect: system architecture, local LLM pipeline, RAG design, agent workflow
- Security Engineer: OWASP mapping, command safety filtering, vulnerability taxonomy
- Backend Engineer: FastAPI routes, services, schemas, orchestration
- ML Engineer: local Transformer loading, CUDA inference, embedding and vector storage
- QA Engineer: benchmark cases, pytest suite, evaluation metrics
