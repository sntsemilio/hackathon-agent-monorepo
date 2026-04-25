from __future__ import annotations


def render_admin_dashboard_html(backend_api_url: str) -> str:
    return f"""<!doctype html>
<html lang=\"en\">
  <head>
    <meta charset=\"utf-8\" />
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
    <title>Admin Dashboard</title>
    <style>
      :root {{
        --bg: #fef3e8;
        --surface: #fff;
        --ink: #1b2230;
        --accent: #0f6cbd;
      }}
      body {{
        margin: 0;
        font-family: \"Fraunces\", \"Segoe UI\", sans-serif;
        background: linear-gradient(135deg, #fde4d0 0%, var(--bg) 55%, #dceaf9 100%);
        color: var(--ink);
      }}
      main {{ max-width: 980px; margin: 2rem auto; padding: 0 1rem; }}
      .card {{
        background: var(--surface);
        border-radius: 18px;
        padding: 1.1rem;
        box-shadow: 0 16px 35px rgba(0, 0, 0, 0.12);
      }}
      input {{ width: 100%; padding: 0.65rem; border-radius: 10px; border: 1px solid #9ab0c9; }}
      button {{
        margin-top: 0.7rem;
        border: 0;
        border-radius: 10px;
        padding: 0.6rem 1rem;
        font: inherit;
        background: var(--accent);
        color: white;
      }}
      pre {{
        margin-top: 1rem;
        background: #0f172a;
        color: #f8fafc;
        border-radius: 12px;
        min-height: 180px;
        padding: 0.75rem;
        white-space: pre-wrap;
      }}
    </style>
  </head>
  <body>
    <main>
      <section class=\"card\">
        <h1>RBAC Admin Dashboard</h1>
        <p>Monitors token usage, delegation traces, and RAG metrics.</p>
        <label for=\"token\">Admin JWT</label>
        <input id=\"token\" placeholder=\"Paste a token with role=admin\" />
        <button id=\"refresh\">Refresh Metrics</button>
        <button id=\"run-evals\">Run Ragas Evals</button>
        <pre id=\"output\">No data yet.</pre>
      </section>
    </main>
    <script>
      const baseUrl = \"{backend_api_url}\";
      const tokenInput = document.getElementById(\"token\");
      const output = document.getElementById(\"output\");

      async function fetchJson(path, method = \"GET\") {{
        const token = tokenInput.value.trim();
        const response = await fetch(baseUrl + path, {{
          method,
          headers: {{
            \"Authorization\": `Bearer ${{token}}`
          }}
        }});
        const text = await response.text();
        try {{
          return JSON.parse(text);
        }} catch (_error) {{
          return {{ status: response.status, raw: text }};
        }}
      }}

      document.getElementById(\"refresh\").addEventListener(\"click\", async () => {{
        const metrics = await fetchJson(\"/admin/metrics\");
        const evals = await fetchJson(\"/admin/evals/ragas\");
        output.textContent = JSON.stringify({{ metrics, evals }}, null, 2);
      }});

      document.getElementById(\"run-evals\").addEventListener(\"click\", async () => {{
        const result = await fetchJson(\"/admin/evals/ragas/run\", \"POST\");
        output.textContent = JSON.stringify(result, null, 2);
      }});
    </script>
  </body>
</html>
"""
