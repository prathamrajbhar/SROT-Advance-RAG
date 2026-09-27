export type Role = "owner" | "editor" | "viewer";

export interface User {
  id: string;
  email: string;
  full_name?: string;
  created_at?: string;
}

export interface Project {
  id: string;
  name: string;
  description?: string;
  role?: Role;
  document_count: number;
  indexed_count?: number;
  failed_count?: number;
  total_chunks?: number;
  last_indexed_at?: string;
  updated_at?: string;
}

export interface ProjectMember {
  user: User;
  role: Role;
  joined_at: string;
}

export type IngestStatus =
  | "queued"
  | "parsing"
  | "chunking"
  | "embedding"
  | "indexing"
  | "indexed"
  | "failed";

export interface DocumentItem {
  id: string;
  filename: string;
  mime_type: string;
  size_bytes: number;
  status: IngestStatus;
  stats?: {
    pages?: number;
    chunk_count?: number;
    token_count?: number;
  };
  pii_flags?: {
    density?: "none" | "low" | "medium" | "high";
    kinds?: string[];
    match_count?: number;
  };
  error_code?: string;
  error_human?: string;
  created_at: string;
  indexed_at?: string;
}

export interface ChunkItem {
  id: string;
  chunk_index: number;
  parent_id?: string | null;
  kind: string;
  token_count: number;
  content: string;
  locator?: Record<string, unknown> | null;
  content_hash: string;
  embedding_id?: string | null;
}

export interface DocumentChunksResponse {
  document: DocumentItem;
  total_chunks: number;
  chunks: ChunkItem[];
}

export type Verdict = "answered" | "insufficient_evidence" | "unverified" | "error";

export interface Citation {
  index: number;
  chunk_id: string;
  document_id: string;
  document_name: string;
  locator?: {
    page_number?: number;
    start_s?: number;
    end_s?: number;
    row_range?: [number, number];
    sheet?: string;
  };
  snippet: string;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant" | "system";
  content_md: string;
  created_at: string;
  verdict?: Verdict;
  confidence?: number;
  faithfulness?: number;
  latency_ms?: number;
  cost_usd?: number;
  model_provider?: string;
  model_name?: string;
  citations?: Citation[];
  searched_documents?: { document_id: string; filename: string }[];
  error_detail?: string;
}

export interface Conversation {
  id: string;
  project_id: string;
  title?: string;
  created_at: string;
}

export interface ProjectMetrics {
  chat_volume: number;
  avg_latency_ms: number;
  avg_faithfulness: number;
  total_cost_usd: number;
  verdict_distribution: Record<string, number>;
  total_documents: number;
  failed_documents: number;
}
