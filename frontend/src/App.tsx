import { useState } from "react";
import ChatPane from "./components/ChatPane";
import ProfileSwitcher from "./components/ProfileSwitcher";
import SourceViewer from "./components/SourceViewer";
import type { Citation, Profile } from "./types/api";

export default function App() {
  const [profile, setProfile] = useState<Profile>("patient");
  const [activeCitation, setActiveCitation] = useState<Citation | null>(null);

  return (
    <div className="h-full flex flex-col">
      <header className="bg-white border-b border-slate-200 px-6 py-4 flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-slate-900">MedRAG</h1>
          <p className="text-xs text-slate-500">Citation-grounded health Q&A</p>
        </div>
        <ProfileSwitcher profile={profile} onChange={setProfile} />
      </header>

      <main className="flex-1 flex overflow-hidden">
        <div className="flex-1 overflow-hidden">
          <ChatPane
            profile={profile}
            onCitationClick={setActiveCitation}
            activeCitation={activeCitation}
          />
        </div>
        <aside className="w-96 border-l border-slate-200 bg-white overflow-hidden">
          <SourceViewer
            citation={activeCitation}
            onClose={() => setActiveCitation(null)}
          />
        </aside>
      </main>

      <footer className="border-t border-slate-200 bg-white px-6 py-2 text-xs text-slate-500">
        Research artifact. Not a medical device. Does not provide medical advice.
      </footer>
    </div>
  );
}
