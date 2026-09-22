import type { Citation } from "../types/api";

type Props = {
  citation: Citation | null;
  onClose: () => void;
};

export default function SourceViewer({ citation, onClose }: Props) {
  if (!citation) {
    return (
      <div className="h-full flex items-center justify-center text-slate-400 text-sm p-6 text-center">
        Click a citation to view its source.
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col">
      <div className="p-4 border-b border-slate-200 flex items-start justify-between gap-3">
        <div className="flex-1">
          <div className="text-xs uppercase tracking-wider text-slate-500 mb-1">
            {citation.source_org}
          </div>
          <div className="font-semibold text-slate-900 leading-tight">
            {citation.source_title}
          </div>
          {citation.section && (
            <div className="text-sm text-slate-600 mt-1">{citation.section}</div>
          )}
        </div>
        <button
          onClick={onClose}
          className="text-slate-400 hover:text-slate-700 text-xl leading-none"
          aria-label="Close"
        >
          ×
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-4">
        <p className="text-sm text-slate-700 leading-relaxed mb-3">
          Citation [#{citation.index}] from this source.
        </p>
        {citation.chunk_id && (
          <p className="text-xs text-slate-500">
            Chunk ID: <span className="font-mono">{citation.chunk_id}</span>
          </p>
        )}
      </div>

      {citation.source_url && (
        <div className="p-4 border-t border-slate-200">
          <a
            href={citation.source_url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-sm text-blue-600 hover:text-blue-800 hover:underline"
          >
            Open original source →
          </a>
        </div>
      )}
    </div>
  );
}
