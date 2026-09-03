import React, { useState } from "react";
import { createRoot } from "react-dom/client";
import "./style.css";

const API = "http://localhost:8000";

function App() {
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      content:
        "Hello! I’m NOVA. Give me a task and I’ll help you plan and execute it.",
    },
  ]);

  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  const [plan, setPlan] = useState("");

  async function send(e) {
    e?.preventDefault();

    const message = text.trim();

    if (!message || busy) return;

    setMessages((old) => [
      ...old,
      { role: "user", content: message },
    ]);

    setText("");
    setBusy(true);

    try {
      const response = await fetch(`${API}/api/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          message,
        }),
      });

      const data = await response.json();

      setMessages((old) => [
        ...old,
        {
          role: "assistant",
          content: data.answer,
        },
      ]);
    } catch (error) {
      setMessages((old) => [
        ...old,
        {
          role: "assistant",
          content:
            "Backend connection failed. Please start NOVA backend on port 8000.",
        },
      ]);
    }

    setBusy(false);
  }

  async function createPlan() {
    const goal = text.trim();

    if (!goal || busy) return;

    setBusy(true);

    try {
      const response = await fetch(`${API}/api/plan`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          goal,
        }),
      });

      const data = await response.json();

      setPlan(data.plan);
      setText("");
    } catch (error) {
      setPlan("Could not connect to NOVA backend.");
    }

    setBusy(false);
  }

  return (
    <div className="app">
      <aside>
        <div className="brand">
          <div className="orb">N</div>

          <div>
            <b>NOVA</b>
            <span>AI AGENT</span>
          </div>
        </div>

        <div className="sideTitle">
          CAPABILITIES
        </div>

        <div className="caps">
          <div>🧠 Autonomous Planning</div>
          <div>🌐 Research Ready</div>
          <div>💻 Coding Workspace</div>
          <div>🧮 Safe Calculator</div>
          <div>💾 Conversation Memory</div>
        </div>

        <div className="status">
          <i></i>
          System Online
        </div>
      </aside>

      <main>
        <header>
          <div>
            <h1>NOVA AI</h1>
            <p>Advanced Agent Workspace</p>
          </div>

          <div className="pill">
            LOCAL CONTROL
          </div>
        </header>

        <section className="chat">
          {messages.map((message, index) => (
            <div
              key={index}
              className={`msg ${message.role}`}
            >
              <div className="avatar">
                {message.role === "assistant"
                  ? "N"
                  : "You"}
              </div>

              <div className="bubble">
                {message.content}
              </div>
            </div>
          ))}

          {plan && (
            <div className="plan">
              <b>Execution Plan</b>

              <pre>{plan}</pre>
            </div>
          )}

          {busy && (
            <div className="typing">
              NOVA is thinking…
            </div>
          )}
        </section>

        <form onSubmit={send}>
          <textarea
            value={text}
            onChange={(e) =>
              setText(e.target.value)
            }
            placeholder="Tell NOVA what you want to accomplish..."
          />

          <div className="actions">
            <button
              type="button"
              onClick={createPlan}
            >
              Create Plan
            </button>

            <button
              className="send"
              disabled={busy}
            >
              Send ↗
            </button>
          </div>
        </form>

        <div className="hint">
          Tip: try <code>/calc 125*8</code> for the
          built-in calculator.
        </div>
      </main>
    </div>
  );
}

createRoot(
  document.getElementById("root")
).render(<App />);
