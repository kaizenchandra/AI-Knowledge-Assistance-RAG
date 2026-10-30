"use client";
import { useState, FormEvent } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";

type Member = { id: string; subject: string; role: string };
type Api = <T>(path: string, method?: string, body?: unknown) => Promise<T>;

export function Memberships({
  api,
  workspace,
}: {
  api: Api;
  workspace: string;
}) {
  const queryClient = useQueryClient();
  const [subject, setSubject] = useState(""),
    [role, setRole] = useState("viewer"),
    [error, setError] = useState("");
  const members = useQuery({
    queryKey: ["members"],
    queryFn: () => api<Member[]>("/memberships"),
  });
  async function save(e: FormEvent) {
    e.preventDefault();
    setError("");
    try {
      await api("/memberships", "POST", {
        subject,
        role,
        workspace_ids: workspace ? [workspace] : [],
      });
      setSubject("");
      await queryClient.invalidateQueries({ queryKey: ["members"] });
    } catch (e) {
      setError((e as Error).message);
    }
  }
  return (
    <section className="membership">
      <h3>Organization members</h3>
      <p className="fine">
        Use the identity provider’s exact subject ID. Viewer/editor access is
        limited to the currently selected workspace; administrators can access
        all organization workspaces.
      </p>
      <form onSubmit={save}>
        <label>
          Identity subject
          <input
            value={subject}
            onChange={(e) => setSubject(e.target.value)}
            required
            maxLength={200}
          />
        </label>
        <label>
          Member role
          <select value={role} onChange={(e) => setRole(e.target.value)}>
            <option value="viewer">Viewer</option>
            <option value="editor">Editor</option>
            <option value="admin">Administrator</option>
          </select>
        </label>
        <button disabled={!workspace} className="primary">
          Save membership
        </button>
      </form>
      {(error || members.error) && (
        <p role="alert" className="error">
          {error || members.error?.message}
        </p>
      )}
      {members.data?.map((m) => (
        <div className="activity" key={m.id}>
          <span>
            {m.subject} · {m.role}
          </span>
          <button
            onClick={async () => {
              setError("");
              try {
                await api("/memberships/" + m.id, "DELETE");
                await queryClient.invalidateQueries({ queryKey: ["members"] });
              } catch (e) {
                setError((e as Error).message);
              }
            }}
          >
            Revoke access
          </button>
        </div>
      ))}
    </section>
  );
}
