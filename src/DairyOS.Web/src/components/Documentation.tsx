import { useEffect, useMemo, useState } from "react";
import {
    MANUALS,
    searchManuals,
    type ManualAudience,
    type ManualSection,
} from "../documentation/manualContent";
import "./Documentation.css";

type DocumentationProps = {
    compact?: boolean;
    initialManual?: ManualAudience;
    initialSectionId?: string;
    onClose?: () => void;
};

type SearchOverlayProps = {
    onClose: () => void;
    onOpenDocumentation?: (manualId: ManualAudience, sectionId: string) => void;
};

function manualById(id: ManualAudience) {
    return MANUALS.find((manual) => manual.id === id) ?? MANUALS[0];
}

function sectionLines(content: string) {
    return content.split("\n").filter((line) => line.trim().length > 0);
}

function renderLine(line: string, index: number) {
    if (line.startsWith("### ")) return <h4 key={`${index}-${line}`}>{line.slice(4)}</h4>;
    if (line.startsWith("## ")) return <h3 key={`${index}-${line}`}>{line.slice(3)}</h3>;
    if (/^\d+\. /.test(line)) return <div className="documentation-list-item ordered" key={`${index}-${line}`}>{line}</div>;
    if (line.startsWith("- ")) return <div className="documentation-list-item" key={`${index}-${line}`}>{line.slice(2)}</div>;
    return <p key={`${index}-${line}`}>{line}</p>;
}

function DocumentReader({ manual, section }: { manual: ReturnType<typeof manualById>; section: ManualSection }) {
    return (
        <article className="documentation-reader">
            <div className="documentation-reader-meta"><span>{manual.audience}</span><span>{section.id}</span></div>
            <h2>{section.title}</h2>
            <p className="documentation-summary">{section.summary}</p>
            <div className="documentation-body">{sectionLines(section.content).map(renderLine)}</div>
            {manual.id === "technical" && section.id === "technical-architecture" && (
                <div className="documentation-diagram" aria-label="DairyOS architecture overview">
                    <div className="diagram-layer"><strong>Operator UI</strong><span>React / Vite / bundled Help</span></div>
                    <div className="diagram-arrow">↓</div>
                    <div className="diagram-layer"><strong>FastAPI API</strong><span>routers / contracts / authentication</span></div>
                    <div className="diagram-arrow">↓</div>
                    <div className="diagram-layer"><strong>Domain &amp; Application Services</strong><span>authoritative rules / intelligence / workflows</span></div>
                    <div className="diagram-arrow">↓</div>
                    <div className="diagram-layer"><strong>PostgreSQL</strong><span>persisted domain facts / operational state</span></div>
                </div>
            )}
        </article>
    );
}

export function DocumentationView({ compact = false, initialManual = "operator", initialSectionId, onClose }: DocumentationProps) {
    const [manualId, setManualId] = useState<ManualAudience>(initialManual);
    const [sectionId, setSectionId] = useState<string | undefined>(initialSectionId);
    const [query, setQuery] = useState("");
    const manual = useMemo(() => manualById(manualId), [manualId]);
    const section = useMemo(() => manual.sections.find((item) => item.id === sectionId) ?? manual.sections[0], [manual, sectionId]);
    const results = useMemo(() => searchManuals(query), [query]);

    useEffect(() => {
        if (!manual.sections.some((item) => item.id === sectionId)) setSectionId(manual.sections[0]?.id);
    }, [manual, sectionId]);

    return (
        <div className={compact ? "documentation documentation-compact" : "documentation"}>
            <div className="documentation-header">
                <div><div className="documentation-kicker">HELP &amp; DOCUMENTATION</div><h1>{manual.title}</h1><p>{manual.purpose}</p></div>
                {onClose && <button type="button" className="documentation-close" onClick={onClose}>Close</button>}
            </div>
            <div className="documentation-search-row">
                <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search all manual topics, headings and keywords…" aria-label="Search DairyOS documentation" />
                <span>{query ? `${results.length} matches` : "Full-text local search"}</span>
            </div>
            {query && (
                <div className="documentation-results">
                    {results.map((result) => (
                        <button key={`${result.manualId}-${result.sectionId}`} type="button" className="documentation-result" onClick={() => { setManualId(result.manualId); setSectionId(result.sectionId); setQuery(""); }}>
                            <strong>{result.sectionTitle}</strong><span>{result.manualTitle}</span><small>{result.summary}</small>
                        </button>
                    ))}
                    {results.length === 0 && <div className="documentation-empty">No manual topic matched that search.</div>}
                </div>
            )}
            <div className="documentation-layout">
                <aside className="documentation-nav" aria-label="Documentation table of contents">
                    <div className="documentation-tabs">
                        {MANUALS.map((item) => (
                            <button key={item.id} type="button" className={manualId === item.id ? "selected" : ""} onClick={() => { setManualId(item.id); setSectionId(undefined); }}>
                                {item.id === "operator" ? "Operator Manual" : "Technical Manual"}
                            </button>
                        ))}
                    </div>
                    <div className="documentation-toc">
                        {manual.sections.map((item) => (
                            <button key={item.id} type="button" className={section.id === item.id ? "selected" : ""} onClick={() => setSectionId(item.id)}>
                                <strong>{item.title}</strong><span>{item.summary}</span>
                            </button>
                        ))}
                    </div>
                </aside>
                <DocumentReader manual={manual} section={section} />
            </div>
        </div>
    );
}

export function DocumentationSearchOverlay({ onClose, onOpenDocumentation: _onOpenDocumentation }: SearchOverlayProps) {
    const [query, setQuery] = useState("");
    const [selected, setSelected] = useState<{ manualId: ManualAudience; sectionId: string } | null>(null);
    const results = useMemo(() => searchManuals(query), [query]);

    useEffect(() => {
        const onKeyDown = (event: KeyboardEvent) => { if (event.key === "Escape") onClose(); };
        window.addEventListener("keydown", onKeyDown);
        return () => window.removeEventListener("keydown", onKeyDown);
    }, [onClose]);

    if (selected) {
        return (
            <div className="documentation-overlay" role="dialog" aria-modal="true" aria-label="DairyOS Help topic">
                <div className="documentation-search-dialog documentation-topic-dialog">
                    <DocumentationView compact initialManual={selected.manualId} initialSectionId={selected.sectionId} onClose={onClose} />
                </div>
            </div>
        );
    }

    return (
        <div className="documentation-overlay" role="dialog" aria-modal="true" aria-label="DairyOS Help search">
            <div className="documentation-search-dialog">
                <div className="documentation-search-dialog-header">
                    <div><div className="documentation-kicker">DAIRYOS HELP</div><h2>Search Operator &amp; Technical Manuals</h2></div>
                    <button type="button" className="documentation-close" onClick={onClose}>Esc</button>
                </div>
                <input autoFocus value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Try: milk reconciliation, PostgreSQL, reset protection, breeding…" aria-label="Global manual search" />
                <div className="documentation-search-results">
                    {query.trim() ? results.map((result) => (
                        <button key={`${result.manualId}-${result.sectionId}`} type="button" className="documentation-result" onClick={() => setSelected({ manualId: result.manualId, sectionId: result.sectionId })}>
                            <strong>{result.sectionTitle}</strong><span>{result.manualTitle}</span><small>{result.summary}</small>
                        </button>
                    )) : <div className="documentation-search-hint">Search is local and works offline. Use keywords, field names, workflow names or API terms.</div>}
                    {query.trim() && results.length === 0 && <div className="documentation-empty">No matching manual topic.</div>}
                </div>
            </div>
        </div>
    );
}

export default DocumentationView;
