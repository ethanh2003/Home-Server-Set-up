import React, { useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import {
  Activity,
  CheckCircle2,
  ClipboardList,
  HeartPulse,
  Loader2,
  Play,
  RefreshCcw,
  Search,
  Send,
  ShieldCheck,
  TerminalSquare,
} from "lucide-react";
import "./styles.css";

type Job = {
  id: string;
  capture_id: string;
  job_type: string;
  status: string;
  created_at: string;
  updated_at: string;
  last_error?: string | null;
  commit_sha?: string | null;
  superseded?: boolean;
};

type Command = {
  id: string;
  label: string;
  description: string;
};

type SearchResult = {
  path: string;
  title: string;
  preview: string;
};

async function api<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json", ...(options?.headers ?? {}) },
    ...options,
  });
  if (!response.ok) {
    throw new Error(`${response.status} ${response.statusText}`);
  }
  return response.json() as Promise<T>;
}

function useSharedText() {
  const params = new URLSearchParams(window.location.search);
  return {
    title: params.get("title") ?? "",
    text: params.get("text") ?? "",
    url: params.get("url") ?? "",
  };
}

function App() {
  const shared = useSharedText();
  const [content, setContent] = useState([shared.title, shared.text, shared.url].filter(Boolean).join("\n"));
  const [hint, setHint] = useState("");
  const [contentType, setContentType] = useState<"text" | "url" | "markdown_batch">(
    shared.url ? "url" : "text",
  );
  const [jobs, setJobs] = useState<Job[]>([]);
  const [commands, setCommands] = useState<Command[]>([]);
  const [health, setHealth] = useState<Record<string, unknown> | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [busy, setBusy] = useState<string | null>(null);
  const [message, setMessage] = useState("");

  const sourceUrl = useMemo(() => {
    if (contentType !== "url") return null;
    const match = content.match(/https?:\/\/\S+/);
    return match?.[0] ?? shared.url ?? null;
  }, [content, contentType, shared.url]);

  async function refresh() {
    const [jobData, commandData, healthData] = await Promise.all([
      api<{ jobs: Job[] }>("/api/jobs"),
      api<{ actions: Command[] }>("/api/commands"),
      api<Record<string, unknown>>("/api/health"),
    ]);
    setJobs(jobData.jobs);
    setCommands(commandData.actions);
    setHealth(healthData);
  }

  useEffect(() => {
    refresh().catch((error) => setMessage(error.message));
  }, []);

  async function submitCapture() {
    setBusy("capture");
    setMessage("");
    try {
      await api("/api/captures", {
        method: "POST",
        body: JSON.stringify({
          content,
          hint: hint || null,
          content_type: contentType,
          source_url: sourceUrl,
        }),
      });
      setContent("");
      setHint("");
      await refresh();
      setMessage("Captured. Job queued.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Capture failed");
    } finally {
      setBusy(null);
    }
  }

  async function runCommand(id: string) {
    setBusy(id);
    setMessage("");
    try {
      const result = await api<Record<string, unknown>>(`/api/commands/${id}`, { method: "POST" });
      await refresh();
      setMessage(`${id}: ${JSON.stringify(result).slice(0, 240)}`);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Command failed");
    } finally {
      setBusy(null);
    }
  }

  async function rerun(job: Job) {
    setBusy(job.id);
    try {
      await api(`/api/jobs/${job.id}/rerun`, { method: "POST" });
      await refresh();
      setMessage("Rerun queued.");
    } finally {
      setBusy(null);
    }
  }

  async function runSearch() {
    if (!searchQuery.trim()) return;
    setBusy("search");
    try {
      const data = await api<{ results: SearchResult[] }>(`/api/search?q=${encodeURIComponent(searchQuery)}`);
      setSearchResults(data.results);
    } finally {
      setBusy(null);
    }
  }

  return (
    <main className="app">
      <header className="topbar">
        <div>
          <h1>vault-inbox</h1>
          <p>Capture, organize, audit, and search your Obsidian second brain.</p>
        </div>
        <button className="iconButton" onClick={refresh} aria-label="Refresh">
          <RefreshCcw size={19} />
        </button>
      </header>

      <section className="panel capturePanel">
        <div className="sectionTitle">
          <Send size={18} />
          <h2>Capture</h2>
        </div>
        <div className="segmented">
          {(["text", "url", "markdown_batch"] as const).map((type) => (
            <button
              key={type}
              className={contentType === type ? "selected" : ""}
              onClick={() => setContentType(type)}
            >
              {type === "markdown_batch" ? "Markdown" : type.toUpperCase()}
            </button>
          ))}
        </div>
        <textarea
          value={content}
          onChange={(event) => setContent(event.target.value)}
          placeholder="Drop a thought, link, project note, task, or Markdown batch..."
          rows={8}
        />
        <input
          value={hint}
          onChange={(event) => setHint(event.target.value)}
          placeholder="Optional hint"
        />
        <button className="primary" disabled={!content.trim() || busy === "capture"} onClick={submitCapture}>
          {busy === "capture" ? <Loader2 className="spin" size={18} /> : <Send size={18} />}
          Capture
        </button>
      </section>

      {message && <div className="notice">{message}</div>}

      <section className="grid">
        <div className="panel">
          <div className="sectionTitle">
            <Activity size={18} />
            <h2>Activity</h2>
          </div>
          <div className="list">
            {jobs.slice(0, 12).map((job) => (
              <article className="row" key={job.id}>
                <div>
                  <div className="jobHeader">
                    <strong>{job.status}</strong>
                    {job.superseded && <span className="badge">historical</span>}
                  </div>
                  <span>{job.job_type} · {new Date(job.created_at).toLocaleString()}</span>
                  {job.last_error && <small>{job.last_error}</small>}
                </div>
                <button
                  className="iconButton"
                  onClick={() => rerun(job)}
                  aria-label="Rerun job"
                  disabled={job.superseded}
                  title={job.superseded ? "Historical attempt" : "Rerun job"}
                >
                  {busy === job.id ? <Loader2 className="spin" size={17} /> : <Play size={17} />}
                </button>
              </article>
            ))}
          </div>
        </div>

        <div className="panel">
          <div className="sectionTitle">
            <TerminalSquare size={18} />
            <h2>Command Center</h2>
          </div>
          <div className="commandGrid">
            {commands.map((command) => (
              <button key={command.id} onClick={() => runCommand(command.id)}>
                {busy === command.id ? <Loader2 className="spin" size={16} /> : <ShieldCheck size={16} />}
                <span>{command.label}</span>
              </button>
            ))}
          </div>
        </div>
      </section>

      <section className="panel">
        <div className="sectionTitle">
          <Search size={18} />
          <h2>Search Notes</h2>
        </div>
        <div className="searchLine">
          <input value={searchQuery} onChange={(event) => setSearchQuery(event.target.value)} placeholder="Search titles, body text, paths..." />
          <button onClick={runSearch}>
            {busy === "search" ? <Loader2 className="spin" size={18} /> : <Search size={18} />}
          </button>
        </div>
        <div className="list">
          {searchResults.map((result) => (
            <article className="row result" key={result.path}>
              <div>
                <strong>{result.title}</strong>
                <span>{result.path}</span>
                <small>{result.preview}</small>
              </div>
            </article>
          ))}
        </div>
      </section>

      <section className="panel health">
        <div className="sectionTitle">
          <HeartPulse size={18} />
          <h2>Health</h2>
        </div>
        <pre>{health ? JSON.stringify(health, null, 2) : "Loading..."}</pre>
        <div className="sectionTitle statusOk">
          <CheckCircle2 size={17} />
          <span>LAN trusted v1 · Cloudflare Access expected off-LAN</span>
        </div>
      </section>
    </main>
  );
}

createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
