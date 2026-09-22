import type { TriageClass } from "../types/api";

type Props = { triage: TriageClass };

export default function TriageBanner({ triage }: Props) {
  if (!triage) return null;

  const styles: Record<string, { bg: string; border: string; text: string; label: string }> = {
    emergency:    { bg: "bg-red-50",   border: "border-red-300",   text: "text-red-900",   label: "Emergency — call services now" },
    urgent:       { bg: "bg-amber-50", border: "border-amber-300", text: "text-amber-900", label: "Urgent — see a doctor within 24h" },
    personal:     { bg: "bg-slate-50", border: "border-slate-300", text: "text-slate-800", label: "Personal question — refused" },
    out_of_corpus:{ bg: "bg-slate-50", border: "border-slate-300", text: "text-slate-800", label: "Out of scope" },
  };

  const s = styles[triage];
  if (!s) return null;

  return (
    <div className={`${s.bg} ${s.border} ${s.text} border rounded-lg px-4 py-2 text-sm font-medium`}>
      {s.label}
    </div>
  );
}
