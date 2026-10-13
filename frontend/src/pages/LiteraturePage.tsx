import { useState } from "react";
import { api, ApiError } from "../api/client";
import { Card } from "../components/Card";
import { Badge } from "../components/Badge";
import { EmptyState, SkeletonRows } from "../components/EmptyState";
import { useToast } from "../components/Toast";
import { IconFileText, IconSearch } from "../components/icons";
import type { Paper } from "../types";

type Source = "arxiv" | "semantic_scholar" | "crossref";

const SOURCE_LABEL: Record<Source, string> = {
  arxiv: "arXiv",
  semantic_scholar: "Semantic Scholar",
  crossref: "Crossref",
};

/** Section 9: real bibliographic retrieval, deterministic dedup, no
 * fabricated fields - every search hits a live external API and ingests
 * the response as-is into the paper registry. */
export default function LiteraturePage() {
  const toast = useToast();
  const [query, setQuery] = useState("");
  const [source, setSource] = useState<Source>("arxiv");
  const [maxResults, setMaxResults] = useState(10);
  const [papers, setPapers] = useState<Paper[]>([]);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function search(e: React.FormEvent) {
    e.preventDefault();
    if (!query.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const results = await api.post<Paper[]>("/literature/search", {
        query,
        max_results: maxResults,
        source,
      });
      setPapers(results);
      setSearched(true);
      toast.success(`Found ${results.length} paper${results.length === 1 ? "" : "s"} via ${SOURCE_LABEL[source]}.`);
    } catch (err) {
      if (err instanceof ApiError && err.status === 503) {
        setError(`${SOURCE_LABEL[source]} is unreachable right now. This platform fails loudly rather than fabricating results.`);
      } else {
        setError(err instanceof ApiError ? err.message : "Search failed.");
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <div className="page-header">
        <div>
          <h2>Literature</h2>
          <div className="subtitle">
            Real-time search across arXiv, Semantic Scholar, and Crossref. Every result is ingested
            verbatim into the paper registry — no field is ever guessed or invented.
          </div>
        </div>
      </div>

      <Card>
        <form onSubmit={search}>
          <div className="field-row">
            <div style={{ flex: 3 }}>
              <label>Search query</label>
              <input
                placeholder="e.g. graph neural networks intrusion detection"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                autoFocus
              />
            </div>
            <div>
              <label>Source</label>
              <select value={source} onChange={(e) => setSource(e.target.value as Source)}>
                <option value="arxiv">arXiv</option>
                <option value="semantic_scholar">Semantic Scholar</option>
                <option value="crossref">Crossref</option>
              </select>
            </div>
            <div style={{ maxWidth: 100 }}>
              <label>Results</label>
              <input type="number" min={1} max={50} value={maxResults} onChange={(e) => setMaxResults(parseInt(e.target.value, 10) || 10)} />
            </div>
          </div>
          <button type="submit" disabled={loading || !query.trim()} style={{ marginTop: 14 }}>
            {loading ? <span className="spinner" /> : <IconSearch size={14} />}
            Search &amp; ingest
          </button>
        </form>
      </Card>

      {error && <div className="error-banner">{error}</div>}

      {loading && (
        <Card>
          <SkeletonRows rows={4} height={44} />
        </Card>
      )}

      {!loading && searched && papers.length === 0 && !error && (
        <Card>
          <EmptyState
            icon={<IconFileText size={30} />}
            title="No papers found"
            description="Try a broader query or switch to a different source."
          />
        </Card>
      )}

      {!loading &&
        papers.map((p) => (
          <Card key={p.id}>
            <div style={{ display: "flex", justifyContent: "space-between", gap: 16 }}>
              <div style={{ minWidth: 0 }}>
                <div style={{ fontWeight: 650, fontSize: 14, marginBottom: 4 }}>
                  {p.url ? (
                    <a href={p.url} target="_blank" rel="noreferrer">{p.title}</a>
                  ) : (
                    p.title
                  )}
                </div>
                <div className="muted tiny">
                  {(p.authors ?? []).slice(0, 4).join(", ")}
                  {(p.authors?.length ?? 0) > 4 ? " et al." : ""}
                  {p.year ? ` · ${p.year}` : ""}
                  {p.venue ? ` · ${p.venue}` : ""}
                </div>
                {p.abstract && (
                  <p className="tiny muted" style={{ marginTop: 8, lineHeight: 1.55 }}>
                    {p.abstract.length > 320 ? p.abstract.slice(0, 320) + "…" : p.abstract}
                  </p>
                )}
              </div>
              <div style={{ flexShrink: 0, display: "flex", flexDirection: "column", gap: 6, alignItems: "flex-end" }}>
                <Badge tone="muted">{p.source}</Badge>
                {p.doi && <span className="tiny faint mono">{p.doi}</span>}
              </div>
            </div>
          </Card>
        ))}

      {!searched && !loading && (
        <Card>
          <EmptyState
            icon={<IconSearch size={30} />}
            title="Search the literature"
            description="Query arXiv, Semantic Scholar, or Crossref directly. Results are stored in the paper registry, ready for claim extraction and the knowledge graph."
          />
        </Card>
      )}
    </div>
  );
}
