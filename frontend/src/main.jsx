import React,{useState} from "react";
import {createRoot} from "react-dom/client";
import "./style.css";

const API="http://localhost:8000";
function App(){
  const [messages,setMessages]=useState([{role:"assistant",content:"Hello! I’m NOVA. Give me a task and I’ll help plan and execute it."}]);
  const [text,setText]=useState(""); const [busy,setBusy]=useState(false); const [plan,setPlan]=useState("");
  async function send(e){
    e?.preventDefault(); const m=text.trim(); if(!m||busy)return;
    setMessages(x=>[...x,{role:"user",content:m}]); setText(""); setBusy(true);
    try{const r=await fetch(API+"/api/chat",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({message:m})});
      const d=await r.json(); setMessages(x=>[...x,{role:"assistant",content:d.answer}]);
    }catch(err){setMessages(x=>[...x,{role:"assistant",content:"Backend connection failed. Start FastAPI on port 8000."}])}
    setBusy(false);
  }
  async function makePlan(){
    const goal=text.trim(); if(!goal||busy)return; setBusy(true);
    try{const r=await fetch(API+"/api/plan",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({goal})});
      setPlan((await r.json()).plan); setText("");
    }catch{setPlan("Could not connect to backend.")}
    setBusy(false);
  }
  return <div className="app">
    <aside><div className="brand"><div className="orb">N</div><div><b>NOVA</b><span>AI AGENT</span></div></div>
      <div className="sideTitle">CAPABILITIES</div><div className="caps"><div>🧠 Autonomous planning</div><div>🌐 Research-ready</div><div>💻 Coding workspace</div><div>🧮 Safe calculator</div><div>💾 Conversation memory</div></div>
      <div className="status"><i/> System online</div>
    </aside>
    <main><header><div><h1>NOVA AI</h1><p>Advanced Agent Workspace</p></div><div className="pill">LOCAL CONTROL</div></header>
      <section className="chat">{messages.map((m,i)=><div key={i} className={"msg "+m.role}><div className="avatar">{m.role==="assistant"?"N":"You"}</div><div className="bubble">{m.content}</div></div>)}
      {plan&&<div className="plan"><b>Execution Plan</b><pre>{plan}</pre></div>}{busy&&<div className="typing">NOVA is thinking…</div>}</section>
      <form onSubmit={send}><textarea value={text} onChange={e=>setText(e.target.value)} placeholder="Tell NOVA what you want to accomplish…" />
      <div className="actions"><button type="button" onClick={makePlan}>Create Plan</button><button className="send" disabled={busy}>Send ↗</button></div></form>
      <div className="hint">Tip: try <code>/calc 125*8</code> for the built-in safe calculator.</div>
    </main>
  </div>
}
createRoot(document.getElementById("root")).render(<App/>);