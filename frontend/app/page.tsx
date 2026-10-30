"use client";
import { Memberships } from "./memberships";
import { useState, useRef, useEffect, FormEvent } from "react";
import {
  QueryClient,
  QueryClientProvider,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";

type Item = { id: string; name: string; title?: string };
type Doc = {
  id: string;
  filename: string;
  status: string;
  version: number;
  error?: string;
};
type Citation = {
  id: string;
  filename: string;
  text: string;
  page: number | null;
  number: number;
};
type Message = {
  id: string;
  role: string;
  text: string;
  citations: Citation[];
};
type Approval = {
  id: string;
  document_id: string;
  state: string;
  expires: number;
};
type Analytics = {
  documents: Record<string, number>;
  answers: number;
  estimated_cost: number | null;
  provider: string;
  events: { id: string; kind: string; created: number }[];
};
const base = "/api/v1";
const client = new QueryClient({
  defaultOptions: { queries: { retry: false, staleTime: 1000 } },
});

export default function Page() {
  return (
    <QueryClientProvider client={client}>
      <Application />
    </QueryClientProvider>
  );
}

function Application() {
  const queryClient = useQueryClient();
  const [token, setToken] = useState(""),
    [tenant, setTenant] = useState("local"),
    [signedIn, setSignedIn] = useState(false);
  const [role, setRole] = useState("viewer"),
    [provider, setProvider] = useState("offline");
  const [tab, setTab] = useState("Chat"),
    [ws, setWs] = useState(""),
    [kb, setKb] = useState(""),
    [conv, setConv] = useState("");
  const [error, setError] = useState(""),
    [notice, setNotice] = useState(""),
    [question, setQuestion] = useState("");
  const [draft, setDraft] = useState(""),
    [stage, setStage] = useState(""),
    [running, setRunning] = useState(false),
    [uploading, setUploading] = useState(false);
  const [source, setSource] = useState<Citation | null>(null),
    [newWs, setNewWs] = useState(""),
    [newKb, setNewKb] = useState("");
  const abort = useRef<AbortController | null>(null),
    end = useRef<HTMLDivElement | null>(null);
  const headers = () => ({
    Authorization: `Bearer ${token}`,
    "X-Tenant-ID": tenant,
  });
  async function api<T>(
    path: string,
    method = "GET",
    body?: unknown,
  ): Promise<T> {
    const form = body instanceof FormData;
    const response = await fetch(base + path, {
      method,
      headers: {
        ...headers(),
        ...(!form && body ? { "Content-Type": "application/json" } : {}),
      },
      body: body ? (form ? body : JSON.stringify(body)) : undefined,
    });
    if (!response.ok) {
      const data = await response
        .json()
        .catch(() => ({ detail: "Request failed" }));
      throw new Error(
        typeof data.detail === "string"
          ? data.detail
          : `Request failed (${response.status})`,
      );
    }
    return response.status === 204 ? (undefined as T) : response.json();
  }
  async function act(fn: () => Promise<unknown>) {
    setError("");
    try {
      await fn();
      await queryClient.invalidateQueries();
    } catch (e) {
      setError((e as Error).message);
    }
  }
  const workspaces = useQuery({
    queryKey: ["workspaces", tenant],
    queryFn: () => api<Item[]>("/workspaces"),
    enabled: signedIn,
  });
  const kbs = useQuery({
    queryKey: ["kbs", ws],
    queryFn: () => api<Item[]>(`/knowledge-bases?workspace_id=${ws}`),
    enabled: signedIn && !!ws,
  });
  const docs = useQuery({
    queryKey: ["docs", kb],
    queryFn: () => api<Doc[]>(`/documents?kb_id=${kb}`),
    enabled: signedIn && !!kb,
    refetchInterval: signedIn && kb ? 3000 : false,
  });
  const conversations = useQuery({
    queryKey: ["conversations", kb],
    queryFn: () => api<Item[]>(`/conversations?kb_id=${kb}`),
    enabled: signedIn && !!kb,
  });
  const messages = useQuery({
    queryKey: ["messages", conv],
    queryFn: () => api<Message[]>(`/conversations/${conv}/messages`),
    enabled: signedIn && !!conv,
  });
  const approvals = useQuery({
    queryKey: ["approvals", ws],
    queryFn: () => api<Approval[]>(`/approvals?workspace_id=${ws}`),
    enabled: signedIn && !!ws,
    refetchInterval: tab === "Approvals" ? 5000 : false,
  });
  const analytics = useQuery({
    queryKey: ["analytics", tenant],
    queryFn: () => api<Analytics>("/analytics"),
    enabled: signedIn && role === "admin" && tab === "Overview",
    refetchInterval: tab === "Overview" ? 5000 : false,
  });
  useEffect(() => {
    if (!ws && workspaces.data?.length) setWs(workspaces.data[0].id);
  }, [ws, workspaces.data]);
  useEffect(() => {
    if (!kb && kbs.data?.length) setKb(kbs.data[0].id);
  }, [kb, kbs.data]);
  useEffect(() => {
    end.current?.scrollIntoView({ behavior: "smooth" });
  }, [draft, messages.data]);
  useEffect(() => () => abort.current?.abort(), []);
  const queryError = [
    workspaces,
    kbs,
    docs,
    conversations,
    messages,
    approvals,
    analytics,
  ].find((q) => q.error)?.error;
  async function login(e: FormEvent) {
    e.preventDefault();
    await act(async () => {
      const session = await api<{ role: string; provider: string }>("/session");
      setRole(session.role);
      setProvider(session.provider);
      setSignedIn(true);
    });
  }
  function resetConversation() {
    abort.current?.abort();
    setConv("");
    setDraft("");
    setStage("");
    setSource(null);
  }
  async function upload(files: FileList | null) {
    if (!files || !kb) return;
    setUploading(true);
    await act(async () => {
      for (const file of Array.from(files)) {
        if (file.size > 20 * 1024 * 1024)
          throw new Error("Maximum file size is 20 MB");
        const form = new FormData();
        form.append("file", file);
        await api(`/documents?kb_id=${kb}`, "POST", form);
      }
      setNotice("Upload accepted. Indexing runs in the background.");
    });
    setUploading(false);
  }
  async function send(e: FormEvent, retryQuestion?: string) {
    e.preventDefault();
    const nextQuestion = retryQuestion ?? question;
    if (!kb || !nextQuestion.trim() || running) return;
    setError("");
    setRunning(true);
    setDraft("");
    setStage("Starting");
    const text = nextQuestion;
    setQuestion("");
    abort.current = new AbortController();
    try {
      let id = conv;
      if (!id) {
        const row = await api<Item>("/conversations", "POST", { kb_id: kb });
        id = row.id;
        setConv(id);
      }
      const response = await fetch(base + `/conversations/${id}/messages`, {
        method: "POST",
        headers: { ...headers(), "Content-Type": "application/json" },
        body: JSON.stringify({ question: text }),
        signal: abort.current.signal,
      });
      if (!response.ok)
        throw new Error(
          (await response.json()).detail || "Unable to start run",
        );
      await queryClient.invalidateQueries({ queryKey: ["messages", id] });
      const reader = response.body!.getReader(),
        decoder = new TextDecoder();
      let buffer = "",
        completed = false;
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        let split;
        while ((split = buffer.indexOf("\n\n")) >= 0) {
          const frame = buffer.slice(0, split);
          buffer = buffer.slice(split + 2);
          for (const line of frame.split("\n")) {
            if (!line.startsWith("data: ")) continue;
            const event = JSON.parse(line.slice(6));
            if (event.type === "token") setDraft((x) => x + event.text);
            if (event.type === "stage") setStage(event.stage);
            if (event.type === "error") throw new Error(event.message);
            if (event.type === "final") {
              completed = true;
              setDraft("");
              setStage("Complete");
              await queryClient.invalidateQueries({
                queryKey: ["messages", id],
              });
            }
          }
        }
      }
      if (!completed)
        throw new Error("Stream ended before completion. Please retry.");
    } catch (e) {
      if ((e as Error).name === "AbortError") {
        setStage("Stopped");
        setDraft("");
      } else {
        setError((e as Error).message);
        setQuestion(text);
      }
    } finally {
      setRunning(false);
      await queryClient.invalidateQueries();
    }
  }
  if (!signedIn)
    return (
      <main className="login">
        <div className="brandMark">K</div>
        <p className="eyebrow">KNOWLEDGE INTELLIGENCE</p>
        <h1>
          Your knowledge.
          <br />
          Connected.
        </h1>
        <p className="muted">
          A workspace for grounded answers and verifiable evidence.
        </p>
        <form onSubmit={login} className="loginForm">
          <label>
            Organization ID
            <input
              value={tenant}
              onChange={(e) => setTenant(e.target.value)}
              required
            />
          </label>
          <label>
            Access token
            <input
              type="password"
              autoComplete="off"
              value={token}
              onChange={(e) => setToken(e.target.value)}
              required
            />
          </label>
          <button className="primary">
            Enter workspace <span>→</span>
          </button>
        </form>
        <p className="fine">
          Local development: use your configured DEV_TOKEN and organization
          “local”. OIDC deployments accept a valid access token. Tokens stay in
          memory.
        </p>
        {error && (
          <p role="alert" className="error">
            {error}
          </p>
        )}
      </main>
    );
  return (
    <div className="shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brandMark small">K</div>
          <strong>
            Knowledge
            <br />
            <span>Intelligence</span>
          </strong>
        </div>
        <p className="eyebrow">WORKSPACE</p>
        <select
          aria-label="Workspace"
          disabled={running}
          value={ws}
          onChange={(e) => {
            setWs(e.target.value);
            setKb("");
            resetConversation();
          }}
        >
          <option value="">Select workspace</option>
          {workspaces.data?.map((w) => (
            <option key={w.id} value={w.id}>
              {w.name}
            </option>
          ))}
        </select>
        <nav>
          {["Chat", "Knowledge", "Approvals", "Overview", "Settings"].map(
            (name) => (
              <button
                className={tab === name ? "nav active" : "nav"}
                key={name}
                onClick={() => setTab(name)}
              >
                <span>
                  {
                    (
                      {
                        Chat: "◈",
                        Knowledge: "▤",
                        Approvals: "✓",
                        Overview: "▥",
                        Settings: "⚙",
                      } as Record<string, string>
                    )[name]
                  }
                </span>
                {name}
              </button>
            ),
          )}
        </nav>
        <div className="history">
          <div className="sectionLabel">
            CONVERSATIONS
            <button
              aria-label="New conversation"
              disabled={running}
              onClick={() => {
                resetConversation();
                setTab("Chat");
              }}
            >
              ＋
            </button>
          </div>
          {conversations.data?.map((c) => (
            <button
              disabled={running}
              className={
                conv === c.id ? "conversation selected" : "conversation"
              }
              key={c.id}
              onClick={() => {
                setConv(c.id);
                setDraft("");
                setTab("Chat");
              }}
            >
              {c.title}
            </button>
          ))}
          {conv && !running && (
            <details className="conversationTools">
              <summary>Manage conversation</summary>
              <form
                key={conv}
                onSubmit={(e) => {
                  e.preventDefault();
                  const name = new FormData(e.currentTarget).get("title");
                  void act(() =>
                    api(`/conversations/${conv}`, "PATCH", { name }),
                  );
                }}
              >
                <label>
                  Conversation title
                  <input
                    name="title"
                    defaultValue={
                      conversations.data?.find((c) => c.id === conv)?.title
                    }
                    maxLength={120}
                    required
                  />
                </label>
                <button>Rename</button>
              </form>
              <button
                className="danger"
                onClick={() =>
                  void act(async () => {
                    await api(`/conversations/${conv}`, "DELETE");
                    resetConversation();
                  })
                }
              >
                Delete conversation
              </button>
            </details>
          )}
        </div>
        <div className="account">
          <span className="avatar">{role.slice(0, 1).toUpperCase()}</span>
          <div>
            <strong>{tenant}</strong>
            <small>
              {role} · {provider}
            </small>
          </div>
          <button
            aria-label="Sign out"
            onClick={() => {
              resetConversation();
              setSignedIn(false);
              setToken("");
              setWs("");
              setKb("");
              queryClient.clear();
            }}
          >
            ↗
          </button>
        </div>
      </aside>
      <main className="main">
        <header>
          <div>
            <p className="eyebrow">YOUR ORGANIZATION / {tab.toUpperCase()}</p>
            <h2>
              {tab === "Chat"
                ? "Ask with confidence"
                : tab === "Knowledge"
                  ? "Your knowledge library"
                  : tab === "Approvals"
                    ? "Human oversight"
                    : tab === "Overview"
                      ? "Workspace overview"
                      : "Workspace settings"}
            </h2>
          </div>
          <span className="mode">
            <i />
            {provider === "offline"
              ? "Offline evidence mode"
              : "Live providers"}
          </span>
        </header>
        {(error || queryError) && (
          <div role="alert" className="error">
            {error || queryError?.message}
            <button
              onClick={() => {
                setError("");
                void queryClient.invalidateQueries();
              }}
            >
              Retry
            </button>
          </div>
        )}
        {notice && (
          <div role="status" className="notice">
            {notice}
            <button
              aria-label="Dismiss notification"
              onClick={() => setNotice("")}
            >
              ×
            </button>
          </div>
        )}
        <div className="toolbar">
          <label>
            Knowledge base
            <select
              aria-label="Knowledge base"
              disabled={running}
              value={kb}
              onChange={(e) => {
                setKb(e.target.value);
                resetConversation();
              }}
            >
              <option value="">Select a knowledge base</option>
              {kbs.data?.map((k) => (
                <option key={k.id} value={k.id}>
                  {k.name}
                </option>
              ))}
            </select>
          </label>
          <span className="muted">
            {docs.data?.filter((d) => d.status === "ready").length || 0}{" "}
            searchable documents
          </span>
        </div>
        {tab === "Chat" && (
          <div className="chat">
            <div className="messages">
              {!messages.data?.length && !running && (
                <div className="empty">
                  <div className="spark">✦</div>
                  <p className="eyebrow">FROM INFORMATION TO UNDERSTANDING</p>
                  <h1>
                    What would you like
                    <br />
                    to know?
                  </h1>
                  <p>
                    Explore your team’s knowledge.
                    <br />
                    Every answer starts with evidence.
                  </p>
                  <div className="suggestions">
                    {[
                      "What are our key policies?",
                      "Summarize the available guidance",
                      "What evidence supports this decision?",
                    ].map((q) => (
                      <button key={q} onClick={() => setQuestion(q)}>
                        {q}
                        <span>↗</span>
                      </button>
                    ))}
                  </div>
                  {!kb && (
                    <p className="fine">
                      Create a workspace and knowledge base in Settings to
                      begin.
                    </p>
                  )}
                </div>
              )}
              {messages.data?.map((m, messageIndex) => (
                <article key={m.id} className={"message " + m.role}>
                  <div className="messageLabel">
                    {m.role === "user" ? "YOU" : "KNOWLEDGE INTELLIGENCE"}
                  </div>
                  <div className="messageText">{m.text}</div>
                  {m.citations?.length > 0 && (
                    <div className="citations">
                      {m.citations.map((c) => (
                        <button
                          key={c.id}
                          onClick={() =>
                            void act(async () =>
                              setSource(
                                await api<Citation>(`/citations/${c.id}`),
                              ),
                            )
                          }
                        >
                          [{c.number}] {c.filename}
                          {c.page ? ` · p. ${c.page}` : ""}
                        </button>
                      ))}
                    </div>
                  )}
                  {m.role === "assistant" && (
                    <div className="messageActions">
                      <button
                        disabled={running}
                        onClick={(e) => {
                          const original = messages.data
                            ?.slice(0, messageIndex)
                            .reverse()
                            .find((prior) => prior.role === "user");
                          if (original) void send(e, original.text);
                        }}
                      >
                        Regenerate
                      </button>
                      <button
                        onClick={() =>
                          void act(async () => {
                            await navigator.clipboard.writeText(m.text);
                            setNotice("Answer copied.");
                          })
                        }
                      >
                        Copy
                      </button>
                      <button
                        aria-label="Helpful answer"
                        onClick={() =>
                          void act(async () => {
                            await api("/feedback", "POST", {
                              message_id: m.id,
                              score: 1,
                            });
                            setNotice("Feedback saved.");
                          })
                        }
                      >
                        Helpful
                      </button>
                      <button
                        aria-label="Unhelpful answer"
                        onClick={() =>
                          void act(async () => {
                            await api("/feedback", "POST", {
                              message_id: m.id,
                              score: -1,
                            });
                            setNotice("Feedback saved.");
                          })
                        }
                      >
                        Needs work
                      </button>
                    </div>
                  )}
                </article>
              ))}
              {running && (
                <article className="message assistant">
                  <div role="status" className="stage">
                    <i />
                    {stage}
                  </div>
                  <div className="messageText">{draft}</div>
                </article>
              )}
              <div ref={end} />
            </div>
            <form className="composer" onSubmit={send}>
              <textarea
                aria-label="Question"
                placeholder={
                  kb
                    ? "Ask a question about your knowledge…"
                    : "Select a knowledge base to begin"
                }
                value={question}
                maxLength={4000}
                onChange={(e) => setQuestion(e.target.value)}
                disabled={!kb}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    void send(e);
                  }
                }}
              />
              <div>
                <span>Grounded in your authorized sources</span>
                {running ? (
                  <button type="button" onClick={() => abort.current?.abort()}>
                    ■ Stop
                  </button>
                ) : (
                  <button
                    className="primary"
                    disabled={!kb || !question.trim()}
                  >
                    Ask ↗
                  </button>
                )}
              </div>
            </form>
            <p className="disclaimer">
              Verify important decisions against the cited sources.
            </p>
          </div>
        )}
        {tab === "Knowledge" && (
          <section className="content">
            <div className="sectionHeading">
              <div>
                <h3>Documents</h3>
                <p className="muted">
                  Upload, index, and manage the sources behind your answers.
                </p>
              </div>
              <span className="pill">{docs.data?.length || 0} sources</span>
            </div>
            {role !== "viewer" && (
              <label
                className="dropzone"
                onDragOver={(e) => e.preventDefault()}
                onDrop={(e) => {
                  e.preventDefault();
                  void upload(e.dataTransfer.files);
                }}
              >
                <span className="uploadIcon">↑</span>
                <strong>
                  {uploading
                    ? "Uploading…"
                    : "Drop documents here, or choose files"}
                </strong>
                <span>PDF, DOCX, TXT, Markdown, HTML · up to 20 MB each</span>
                <input
                  aria-label="Upload documents"
                  type="file"
                  multiple
                  accept=".pdf,.docx,.txt,.md,.html"
                  disabled={!kb || uploading}
                  onChange={(e) => void upload(e.target.files)}
                />
              </label>
            )}
            <div className="documentList">
              {docs.data?.map((d) => (
                <div className="document" key={d.id}>
                  <div className="fileIcon">▤</div>
                  <div className="documentName">
                    <strong>{d.filename}</strong>
                    <small>
                      Version {d.version}
                      {d.error ? " · " + d.error : ""}
                    </small>
                  </div>
                  <span className={"status " + d.status}>{d.status}</span>
                  {role !== "viewer" && (
                    <>
                      <button
                        onClick={() =>
                          void act(async () => {
                            await api("/approvals", "POST", {
                              document_id: d.id,
                            });
                            setNotice(
                              "Reprocessing requested. Review it in Approvals.",
                            );
                          })
                        }
                      >
                        Reprocess
                      </button>
                      <button
                        className="danger"
                        onClick={() =>
                          void act(async () => {
                            await api(`/documents/${d.id}`, "DELETE");
                            setNotice(
                              "Document access removed; cleanup queued.",
                            );
                          })
                        }
                      >
                        Delete
                      </button>
                    </>
                  )}
                </div>
              ))}
              {!docs.data?.length && (
                <p className="emptySmall">
                  Your library is empty. Add your first source above.
                </p>
              )}
            </div>
          </section>
        )}
        {tab === "Approvals" && (
          <section className="content">
            <h3>Controlled actions</h3>
            <p className="muted">
              Reprocessing pauses in a durable workflow until an administrator
              decides.
            </p>
            {approvals.data?.map((a) => (
              <div className="approval" key={a.id}>
                <div>
                  <strong>Reprocess document</strong>
                  <p className="fine">
                    {docs.data?.find((d) => d.id === a.document_id)?.filename ||
                      a.document_id}
                  </p>
                  <small>
                    Expires {new Date(a.expires * 1000).toLocaleString()}
                  </small>
                </div>
                <span className="status">{a.state}</span>
                {role === "admin" &&
                  ["pending", "approved", "denied"].includes(a.state) && (
                    <>
                      <button
                        className="primary"
                        onClick={() =>
                          void act(() =>
                            api(`/approvals/${a.id}/decision`, "POST", {
                              approve: true,
                            }),
                          )
                        }
                      >
                        Approve
                      </button>
                      <button
                        onClick={() =>
                          void act(() =>
                            api(`/approvals/${a.id}/decision`, "POST", {
                              approve: false,
                            }),
                          )
                        }
                      >
                        Reject
                      </button>
                    </>
                  )}
              </div>
            ))}
            {!approvals.data?.length && (
              <p className="emptySmall">No actions awaiting review.</p>
            )}
          </section>
        )}
        {tab === "Overview" && (
          <section className="content">
            {role !== "admin" ? (
              <p>
                Administrator access is required for organization analytics.
              </p>
            ) : (
              <>
                <div className="metrics">
                  <div>
                    <span>Searchable sources</span>
                    <strong>{analytics.data?.documents.ready || 0}</strong>
                  </div>
                  <div>
                    <span>Completed answers</span>
                    <strong>{analytics.data?.answers || 0}</strong>
                  </div>
                  <div>
                    <span>Failed documents</span>
                    <strong>{analytics.data?.documents.failed || 0}</strong>
                  </div>
                  <div>
                    <span>Estimated cost</span>
                    <strong>—</strong>
                    <small>Usage accounting not configured</small>
                  </div>
                </div>
                <h3>Recent activity</h3>
                {analytics.data?.events.map((e) => (
                  <div className="activity" key={e.id}>
                    <span>{e.kind.replaceAll(".", " / ")}</span>
                    <time>{new Date(e.created * 1000).toLocaleString()}</time>
                  </div>
                ))}
              </>
            )}
          </section>
        )}
        {tab === "Settings" && (
          <section className="content settings">
            <h3>Build your workspace</h3>
            <p className="muted">
              Organize knowledge into workspaces and focused knowledge bases.
            </p>
            {role === "admin" && (
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  void act(async () => {
                    const w = await api<Item>("/workspaces", "POST", {
                      name: newWs,
                    });
                    setWs(w.id);
                    setKb("");
                    setNewWs("");
                  });
                }}
              >
                <label>
                  New workspace
                  <input
                    value={newWs}
                    onChange={(e) => setNewWs(e.target.value)}
                    maxLength={120}
                    required
                    placeholder="e.g. People Operations"
                  />
                </label>
                <button className="primary">Create workspace</button>
              </form>
            )}
            {role !== "viewer" && (
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  void act(async () => {
                    const k = await api<Item>("/knowledge-bases", "POST", {
                      name: newKb,
                      workspace_id: ws,
                    });
                    setKb(k.id);
                    setNewKb("");
                  });
                }}
              >
                <label>
                  New knowledge base
                  <input
                    value={newKb}
                    onChange={(e) => setNewKb(e.target.value)}
                    maxLength={120}
                    required
                    placeholder="e.g. Employee handbook"
                  />
                </label>
                <button className="primary" disabled={!ws}>
                  Create knowledge base
                </button>
              </form>
            )}
            {role === "admin" && <Memberships api={api} workspace={ws} />}
            <div className="info">
              <strong>Current access</strong>
              <p>
                Organization: {tenant}
                <br />
                Role: {role}
                <br />
                Provider: {provider}
              </p>
              <p className="fine">
                OIDC sign-in redirects require operator configuration. This
                interface accepts an already-issued access token.
              </p>
            </div>
          </section>
        )}
      </main>
      {source && (
        <aside className="sourcePanel">
          <button
            className="close"
            onClick={() => setSource(null)}
            aria-label="Close source"
          >
            ×
          </button>
          <p className="eyebrow">VERIFIED SOURCE</p>
          <h3>{source.filename}</h3>
          {source.page && <p>Page {source.page}</p>}
          <p className="sourceText">{source.text}</p>
        </aside>
      )}
    </div>
  );
}
