import { useState } from "react";
import { askQuestion } from "../api/client";
import type { Citation as CitationType, Profile, QueryResponse } from "../types/api";
import Citation from "./Citation";
import TriageBanner from "./TriageBanner";

type Props = {
  profile: Profile;
  onCitationClick: (c: CitationType) => void;
  activeCitation: CitationType | null;
};

export default function ChatPane({ profile, onCitationClick, activeCitation }: Props) {
  const [question, setQuestion] = useState("");
  const [response, setResponse] = useState<QueryResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!question.trim() || loading) return;

    setLoading(true);
    setError(null);
    setResponse(null);

    try {
      const res = await askQuestion({ question: question.trim(), profile });
      setResponse(res);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="h-full flex flex-col">
      <div className="flex-1 overflow-y-auto p-6">
        {!response && !loading && !error && (
          <div className="text-center text-slate-400 mt-24">
            <div className="text-lg font-medium text-slate-600 mb-2">
              Ask a health question
            </div>
            <div className="text-sm">
              Answers are grounded in NICE guidelines and MedlinePlus.
            </div>
          </div>
        )}

        {loading && (
          <div className="text-center text-slate-500 mt-24">
            <div className="animate-pulse">Thinking…</div>
            <div className="text-xs mt-2 text-slate-400">
              triage → retrieve → rerank → generate → verify
            </div>
          </div>
        )}

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-800">
            <div className="font-medium mb-1">Error</div>
            <div className="text-sm">{error}</div>
          </div>
        )}

        {response && (
          <div className="space-y-4 max-w-3xl">
            <TriageBanner triage={response.triage} />
            <div className="text-slate-800 whitespace-pre-wrap leading-relaxed">
              {response.answer}
            </div>

            {response.citations.length > 0 && (
              <div className="pt-4 border-t border-slate-200">
                <div className="text-xs uppercase tracking-wider text-slate-500 mb-2">
                  Sources
                </div>
                <div className="flex flex-wrap gap-2">
                  {response.citations.map((c) => (
                    <Citation
                      key={c.index}
                      citation={c}
                      onClick={onCitationClick}
                      active={activeCitation?.index === c.index}
                    />
                  ))}
                </div>
              </div>
            )}

            {response.debug?.latency_ms && (
              <div className="text-xs text-slate-400 pt-2">
                {response.debug.model} · {response.debug.latency_ms}ms
                {response.debug.verification && (
                  <>
                    {" "}· verification{" "}
                    {response.debug.verification.supported ? "passed" : "flagged"}
                    {" "}({Math.round(response.debug.verification.coverage * 100)}% coverage)
                  </>
                )}
              </div>
            )}
          </div>
        )}
      </div>

      <form onSubmit={submit} className="border-t border-slate-200 p-4 bg-white">
        <div className="flex gap-2">
          <input
            type="text"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Ask about type 2 diabetes or high blood pressure…"
            disabled={loading}
            className="flex-1 px-4 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-slate-50"
          />
          <button
            type="submit"
            disabled={loading || !question.trim()}
            className="px-5 py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 disabled:bg-slate-300 disabled:cursor-not-allowed transition-colors"
          >
            Ask
          </button>
        </div>
      </form>
    </div>
  );
}
