from __future__ import annotations

import os
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


HTML_TEMPLATE = """<!doctype html>
<html lang=\"en\">
  <head>
    <meta charset=\"utf-8\" />
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
    <title>Hackathon Agent User Chat</title>
    <style>
      :root {
        --bg: #f4efe4;
        --surface: #fffaf2;
        --ink: #1f1b17;
        --accent: #b63f1e;
        --muted: #6d5b4f;
      }
      * { box-sizing: border-box; }
      body {
        margin: 0;
        font-family: \"Space Grotesk\", \"Segoe UI\", sans-serif;
        background: radial-gradient(circle at 10% 10%, #fde7cc 0%, var(--bg) 45%);
        color: var(--ink);
      }
      main { max-width: 980px; margin: 2rem auto; padding: 0 1rem; }
      .card {
        background: var(--surface);
        border: 2px solid #d7c8b7;
        border-radius: 18px;
        padding: 1.25rem;
        box-shadow: 0 14px 35px rgba(122, 70, 23, 0.12);
      }
      h1 { margin: 0 0 0.3rem 0; font-size: 1.8rem; }
      .sub { color: var(--muted); margin-top: 0; }
      textarea {
        width: 100%;
        min-height: 120px;
        border-radius: 12px;
        border: 1px solid #bda992;
        padding: 0.8rem;
        font: inherit;
      }
      button {
        margin-top: 0.75rem;
        border: 0;
        border-radius: 12px;
        padding: 0.65rem 1.1rem;
        font-weight: 600;
        background: var(--accent);
        color: #fff;
        cursor: pointer;
      }
      pre {
        margin-top: 1rem;
        background: #211a17;
        color: #f4eee7;
        border-radius: 12px;
        min-height: 180px;
        padding: 0.8rem;
        white-space: pre-wrap;
      }
      a { color: var(--accent); }
    </style>
  </head>
  <body>
    <main>
      <section class=\"card\">
        <h1>AI Agent User Chat</h1>
        <p class=\"sub\">Streaming endpoint: __BACKEND_STREAM_URL__</p>
        <p class=\"sub\"><a href=\"/admin\">Open Admin Dashboard</a></p>
        <form id=\"chat-form\">
          <textarea id=\"prompt\" placeholder=\"Ask a research question or request tool execution\"></textarea>
          <button type=\"submit\">Stream</button>
        </form>
        <pre id=\"trace\">Waiting for input...</pre>
      </section>
    </main>

    <script>
      const streamUrl = \"__BACKEND_STREAM_URL__\";
      const form = document.getElementById(\"chat-form\");
      const promptInput = document.getElementById(\"prompt\");
      const trace = document.getElementById(\"trace\");

      function appendLine(text) {
        trace.textContent += \"\\n\" + text;
      }

      function parseSse(chunk) {
        const blocks = chunk.split(\"\\n\\n\");
        const complete = blocks.slice(0, -1);
        const remainder = blocks[blocks.length - 1] || \"\";

        for (const block of complete) {
          if (!block.trim()) continue;
          const lines = block.split(\"\\n\");
          let eventName = \"message\";
          let data = \"\";
          for (const line of lines) {
            if (line.startsWith(\"event:\")) eventName = line.replace(\"event:\", \"\").trim();
            if (line.startsWith(\"data:\")) data += line.replace(\"data:\", \"\").trim();
          }
          appendLine(`[${eventName}] ${data}`);
        }

        return remainder;
      }

      form.addEventListener(\"submit\", async (event) => {
        event.preventDefault();
        const message = promptInput.value.trim();
        if (!message) return;

        trace.textContent = \"Streaming...\";

        const response = await fetch(streamUrl, {
          method: \"POST\",
          headers: { \"Content-Type\": \"application/json\" },
          body: JSON.stringify({ message }),
        });

        if (!response.ok || !response.body) {
          trace.textContent = `HTTP ${response.status}: unable to stream`;
          return;
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = \"\";

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          buffer += decoder.decode(value, { stream: true });
          buffer = parseSse(buffer);
        }
      });
    </script>
  </body>
</html>
"""

ADMIN_TEMPLATE = """<!doctype html>
<html><head><meta http-equiv=\"refresh\" content=\"0; url=/admin_dashboard\" /></head><body></body></html>
"""


class UserChatHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802
        backend_stream_url = os.getenv("BACKEND_STREAM_URL", "http://localhost:8080/chat/stream")

        if self.path == "/admin":
            body = ADMIN_TEMPLATE
        elif self.path == "/admin_dashboard":
          from admin_dashboard import render_admin_dashboard_html

            body = render_admin_dashboard_html(os.getenv("BACKEND_API_URL", "http://localhost:8080"))
        else:
            body = HTML_TEMPLATE.replace("__BACKEND_STREAM_URL__", backend_stream_url)

        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(body.encode("utf-8"))

    def log_message(self, format: str, *args: object) -> None:
        _ = (format, args)
        return


def run() -> None:
    port = int(os.getenv("PORT", "8081"))
    server = ThreadingHTTPServer(("0.0.0.0", port), UserChatHandler)
    print(f"Frontend listening on http://0.0.0.0:{port}")
    server.serve_forever()


if __name__ == "__main__":
    run()
