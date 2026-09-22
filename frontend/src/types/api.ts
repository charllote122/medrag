export type Profile = "patient" | "clinician";

export type TriageClass =
  | "emergency"
  | "urgent"
  | "personal"
  | "out_of_corpus"
  | null;

export type Citation = {
  index: number;
  chunk_id?: number;
  section?: string;
  source_org?: string;
  source_title?: string;
  source_url?: string;
};

export type Verification = {
  supported: boolean;
  coverage: number;
  flagged_count: number;
};

export type QueryResponse = {
  answer: string;
  citations: Citation[];
  triage: TriageClass;
  refused: boolean;
  profile: Profile;
  debug?: {
    latency_ms?: number;
    model?: string;
    verification?: Verification;
  } | null;
};

export type QueryRequest = {
  question: string;
  profile: Profile;
};
