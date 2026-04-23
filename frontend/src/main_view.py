from __future__ import annotations

import os
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


HTML_TEMPLATE = """<!doctype html>
<html lang=\"en\">
  <head>
    <meta charset=\"utf-8\" />
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
    <title>Hackathon Agent Console</title>
    <style>
      :root {
        --bg: #f5f7fb;
        --surface: #ffffff;
        --text: #101828;
        --muted: #667085;
        --accent: #0b7285;
        --border: #d0d5dd;
      }
      body {
        margin: 0;
        background: radial-gradient(circle at top right, #def7ec 0%, var(--bg) 45%);
        color: var(--text);
        font-family: "IBM Plex Sans", "Segoe UI", sans-serif;
      }
      main {
        max-width: 920px;
        margin: 32px auto;
        padding: 24px;
      }
      .panel {
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: 16px;
        padding: 20px;
        box-shadow: 0 10px 40px rgba(16, 24, 40, 0.08);
      }
      h1 {
        margin-top: 0;
        font-size: 1.8rem;
      }
      textarea {
        width: 100%;
        min-height: 130px;
        border-radius: 10px;
        border: 1px solid var(--border);
        padding: 12px;
        font: inherit;
        resize: vertical;
      }
      button {
        margin-top: 12px;
        background: var(--accent);
        color: #ffffff;
        border: none;
        border-radius: 10px;
        padding: 10px 18px;
        font: inherit;
        cursor: pointer;
      }
      pre {
        margin-top: 16px;
        background: #0f172a;
        color: #e2e8f0;
        padding: 14px;
        border-radius: 10px;
        white-space: pre-wrap;
        word-break: break-word;
        min-height: 150px;
      }
      .muted {
        color: var(--muted);
      }
    </style>
  </head>
  <body>
    <main>
      <section class=\"panel\">
        <h1>Hackathon Agent Streaming Console</h1>
        <p class=\"muted\">POST SSE target: __BACKEND_STREAM_URL__</p>
        <form id=\"chat-form\">
          <textarea id=\"prompt\" placeholder=\"Ask for research or code execution\"></textarea>
          <button type=\"submit\">Stream Response</button>
        </form>
        <pre id=\"trace\">Waiting for input...</pre>
      </section>
    </main>
    <script>
      const streamUrl = "__BACKEND_STREAM_URL__";
      const form = document.getElementById("chat-form");
      const promptInput = document.getElementById("prompt");
      const trace = document.getElementById("trace");

      function append(text) {
        trace.textContent += "\n" + text;
      }

      function parseSseChunk(chunk) {
        const blocks = chunk.split("\n\n");
        const complete = blocks.slice(0, -1);
        const remainder = blocks[blocks.length - 1] || "";

        for (const block of complete) {
          if (!block.trim()) {
            continue;
          }
          const lines = block.split("\n");
          let eventName = "message";
          let data = "";
          for (const line of lines) {
            if (line.startsWith("event:")) {
              eventName = line.replace("event:", "").trim();
            } else if (line.startsWith("data:")) {
              data += line.replace("data:", "").trim();
            }
          }
          append(`[${eventName}] ${data}`);
        }

        return remainder;
      }

      form.addEventListener("submit", async (event) => {
        event.preventDefault();
        const prompt = promptInput.value.trim();
        if (!prompt) {
          return;
        }

        trace.textContent = "Streaming...";

        const response = await fetch(streamUrl, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ message: prompt }),
        });

        if (!response.ok || !response.body) {
          trace.textContent = `HTTP ${response.status}: failed to start stream`;
          return;
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";

        while (true) {
          const { value, done } = await reader.read();
          if (done) {
            break;
          }
          buffer += decoder.decode(value, { stream: true });
          buffer = parseSseChunk(buffer);
        }
      });
    </script>
  </body>
</html>
"""


class MainViewHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802
        backend_stream_url = os.getenv(
            "BACKEND_STREAM_URL",
            "http://localhost:8080/chat/stream",
        )
        html = HTML_TEMPLATE.replace("__BACKEND_STREAM_URL__", backend_stream_url)

        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html.encode("utf-8"))

    def log_message(self, format: str, *args: object) -> None:
        return


def run() -> None:
    port = int(os.getenv("PORT", "8081"))
    server = ThreadingHTTPServer(("0.0.0.0", port), MainViewHandler)
    print(f"Frontend listening on http://0.0.0.0:{port}")
    server.serve_forever()


if __name__ == "__main__":
    run()
