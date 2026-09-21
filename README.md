# Prompt Chaining Summarization Agent

A small Agentic AI demonstration built with Python + Flask.

## What it demonstrates

Instead of asking one prompt to summarize a document, the application passes the output through multiple specialized prompt stages:

1. **Analyze Agent** — understands document structure and what matters.
2. **Evidence Extraction Agent** — extracts important factual claims.
3. **Compression Agent** — creates a compact draft.
4. **Refinement Agent** — improves coherence and removes repetition.
5. **Final Summarization Agent** — produces the final user-facing summary.

This is called **prompt chaining** because the output of one LLM step becomes the input/context for the next step.

## Architecture

```text
User Text
   |
   v
[Analyze]
   |
   v
[Extract Evidence]
   |
   v
[Compress]
   |
   v
[Refine]
   |
   v
[Final Summary]
   |
   v
Flask Web UI
```

## Run locally

### Windows

```powershell
cd prompt_chaining_summarization_agent
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
$env:OPENAI_API_KEY="YOUR_API_KEY"
python app.py
```

### Linux / Kali

```bash
cd prompt_chaining_summarization_agent
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
export OPENAI_API_KEY="YOUR_API_KEY"
python3 app.py
```

Then open:

```text
http://127.0.0.1:5000
```

## No API key?

The application automatically uses a deterministic local fallback. This lets you test the Flask UI and pipeline concept without an LLM API. For the actual Agentic AI experiment, configure `OPENAI_API_KEY`.

Optional model:

```bash
export OPENAI_MODEL="gpt-5-mini"
```

## Suggested experiment

Run the same document through:

### Experiment A — Single prompt
Ask an LLM directly for a summary.

### Experiment B — Prompt chain
Use the five-stage pipeline in this project.

Compare:
- factual coverage
- hallucinations
- compression ratio
- readability
- latency
- number of model calls
- consistency

## Project objective

The objective is to experimentally demonstrate whether decomposing summarization into multiple specialized prompt steps can improve control and quality compared with a single summarization prompt.

## Future upgrades

- Add PDF/TXT/DOCX upload
- Add chunking for very long documents
- Add LangGraph orchestration
- Add evaluation agent
- Add ROUGE/BERTScore evaluation
- Add summary length controls
- Add PostgreSQL experiment history
- Add charts for single-prompt vs chained-prompt results
- Add human approval before final output
