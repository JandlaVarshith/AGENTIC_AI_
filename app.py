from flask import Flask, request, render_template_string, jsonify
import os
import re
import json
from datetime import datetime

app = Flask(__name__)

# Optional OpenAI-compatible API support.
# Set OPENAI_API_KEY and optionally OPENAI_MODEL in your environment.
# Without an API key, the app runs a local demo pipeline so the UI can still be tested.
try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

HTML = r"""
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>Prompt Chaining Summarization Agent</title>
  <style>
    body{font-family:Arial,sans-serif;background:#f5f7fb;margin:0;color:#172033}
    .wrap{max-width:1100px;margin:35px auto;padding:0 18px}
    .card{background:white;border-radius:14px;padding:22px;margin-bottom:18px;box-shadow:0 4px 18px #00000010}
    h1{margin:0 0 8px}.muted{color:#657084}
    textarea{width:100%;min-height:260px;box-sizing:border-box;border:1px solid #d8deea;border-radius:10px;padding:13px;font-size:15px}
    button{background:#111827;color:white;border:0;border-radius:9px;padding:12px 18px;cursor:pointer;margin-top:12px}
    button:disabled{opacity:.6}
    .grid{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}
    .step{border:1px solid #e0e5ee;border-radius:10px;padding:14px}
    pre{white-space:pre-wrap;background:#f7f8fb;border-radius:10px;padding:15px;overflow:auto}
    .tag{display:inline-block;background:#eef2ff;padding:5px 9px;border-radius:99px;font-size:12px}
    @media(max-width:800px){.grid{grid-template-columns:1fr}}
  </style>
</head>
<body>
<div class="wrap">
  <div class="card">
    <span class="tag">Agentic AI • Prompt Chaining</span>
    <h1>Multi-Step Summarization Agent</h1>
    <p class="muted">A Flask application demonstrating an agent-style prompt pipeline: analyze → extract → compress → refine → final summary.</p>
    <form id="form">
      <textarea id="text" placeholder="Paste an article, report, research paper, incident report, or other long text here..."></textarea>
      <br><button id="run">Run Summarization Pipeline</button>
    </form>
  </div>

  <div id="result" style="display:none">
    <div class="card">
      <h2>Final Summary</h2>
      <pre id="final"></pre>
    </div>
    <div class="card">
      <h2>Pipeline Trace</h2>
      <div class="grid">
        <div class="step"><b>1. Analyze</b><pre id="analysis"></pre></div>
        <div class="step"><b>2. Extract</b><pre id="extraction"></pre></div>
        <div class="step"><b>3. Compress</b><pre id="compression"></pre></div>
        <div class="step"><b>4. Refine</b><pre id="refinement"></pre></div>
        <div class="step"><b>5. Finalize</b><pre id="finalize"></pre></div>
        <div class="step"><b>Metadata</b><pre id="metadata"></pre></div>
      </div>
    </div>
  </div>
</div>

<script>
document.getElementById("form").addEventListener("submit", async (e)=>{
  e.preventDefault();
  const text=document.getElementById("text").value.trim();
  if(!text){alert("Please enter some text.");return;}
  const btn=document.getElementById("run");
  btn.disabled=true; btn.textContent="Running pipeline...";
  try{
    const r=await fetch("/summarize",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({text})});
    const data=await r.json();
    if(!r.ok) throw new Error(data.error||"Request failed");
    document.getElementById("result").style.display="block";
    for(const k of ["final","analysis","extraction","compression","refinement","finalize","metadata"]){
      document.getElementById(k).textContent=typeof data[k]==="string"?data[k]:JSON.stringify(data[k],null,2);
    }
  }catch(err){alert(err.message)}
  finally{btn.disabled=false;btn.textContent="Run Summarization Pipeline";}
});
</script>
</body>
</html>
"""

def local_fallback(text):
    """Deterministic fallback for testing without an LLM API."""
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    sentences = [s.strip() for s in sentences if s.strip()]
    keywords = []
    words = re.findall(r"\b[A-Za-z][A-Za-z'-]{4,}\b", text.lower())
    stop = set("""about after again against among because before being between could
    first from have into more other should their there these they this through using
    which while would with""".split())
    freq = {}
    for w in words:
        if w not in stop:
            freq[w] = freq.get(w,0)+1
    keywords = [w for w,_ in sorted(freq.items(), key=lambda x:x[1], reverse=True)[:8]]
    selected = sentences[:3]
    summary = " ".join(selected)
    if len(summary) > 700:
        summary = summary[:697] + "..."
    return {
        "analysis": "The document was segmented into sentences and its recurring content terms were identified.",
        "extraction": "Key terms: " + ", ".join(keywords),
        "compression": " ".join(sentences[:5])[:1200],
        "refinement": summary,
        "final": summary,
        "metadata": {"mode":"local_fallback","sentences":len(sentences),"characters":len(text)}
    }

def llm_pipeline(text):
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or OpenAI is None:
        return local_fallback(text)

    client = OpenAI(api_key=api_key)
    model = os.getenv("OPENAI_MODEL", "gpt-5-mini")

    def ask(instruction, content):
        response = client.responses.create(
            model=model,
            input=[
                {"role":"system","content":instruction},
                {"role":"user","content":content}
            ]
        )
        return response.output_text.strip()

    analysis = ask(
        "You are the analysis agent in a summarization pipeline. Analyze the document structure, purpose, audience, major sections, and the information that must not be lost. Do not write the final summary.",
        text
    )

    extraction = ask(
        "You are the evidence extraction agent. Extract only the most important factual claims, entities, dates, numbers, causes, effects, and conclusions from the source. Avoid adding information not present in the source.",
        f"SOURCE:\n{text}\n\nANALYSIS:\n{analysis}"
    )

    compression = ask(
        "You are the compression agent. Convert the extracted evidence into a compact factual draft. Preserve critical details and remove repetition. Do not invent facts.",
        extraction
    )

    refinement = ask(
        "You are the refinement agent. Improve clarity, logical order, factual consistency, and readability. Keep the result concise and faithful to the supplied evidence.",
        compression
    )

    final = ask(
        "You are the final summarization agent. Produce a polished summary in 1-3 short paragraphs. Include the central topic, the most important findings, and the main conclusion. Do not introduce information that is absent from the source.",
        refinement
    )

    return {
        "analysis": analysis,
        "extraction": extraction,
        "compression": compression,
        "refinement": refinement,
        "final": final,
        "metadata": {
            "mode":"llm",
            "model":model,
            "timestamp":datetime.now().isoformat(timespec="seconds")
        }
    }

@app.get("/")
def index():
    return render_template_string(HTML)

@app.post("/summarize")
def summarize():
    data = request.get_json(silent=True) or {}
    text = (data.get("text") or "").strip()
    if not text:
        return jsonify({"error":"Text is required."}), 400
    if len(text) > 50000:
        return jsonify({"error":"Text is too long. Keep it below 50,000 characters for this demo."}), 400
    try:
        return jsonify(llm_pipeline(text))
    except Exception as exc:
        return jsonify({"error":f"Pipeline error: {exc}"}), 500

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
