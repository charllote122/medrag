import type { Citation as CitationType } from "../types/api";

type Props = {
  citation: CitationType;
  onClick: (c: CitationType) => void;
  active?: boolean;
};

export default function Citation({ citation, onClick, active }: Props) {
  return (
    <button
      onClick={() => onClick(citation)}
      className={
        "inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-xs font-medium border transition-colors " +
        (active
          ? "bg-blue-100 border-blue-400 text-blue-900"
          : "bg-slate-50 border-slate-200 text-slate-700 hover:bg-blue-50 hover:border-blue-300")
      }
      title={citation.source_title}
    >
      <span>[{citation.index}]</span>
      <span className="text-slate-500">{citation.source_org}</span>
    </button>
  );
}
