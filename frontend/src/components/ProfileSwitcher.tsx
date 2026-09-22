import type { Profile } from "../types/api";

type Props = {
  profile: Profile;
  onChange: (p: Profile) => void;
};

export default function ProfileSwitcher({ profile, onChange }: Props) {
  return (
    <div className="inline-flex rounded-lg border border-slate-200 bg-white overflow-hidden">
      {(["patient", "clinician"] as Profile[]).map((p) => (
        <button
          key={p}
          onClick={() => onChange(p)}
          className={
            "px-4 py-2 text-sm font-medium transition-colors " +
            (profile === p
              ? "bg-blue-600 text-white"
              : "bg-white text-slate-600 hover:bg-slate-50")
          }
        >
          {p === "patient" ? "Patient" : "Clinician"}
        </button>
      ))}
    </div>
  );
}
