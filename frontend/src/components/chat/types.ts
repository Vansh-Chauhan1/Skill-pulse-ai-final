export type ChatRole = "user" | "assistant";

export interface ChatTurn {
  role: ChatRole;
  content: string;
}

export interface ChatSource {
  name: string;
  type: string;
  endpoint: string;
  status: string;
}

export interface ChatMessage {
  id: string;
  role: ChatRole;
  content: string;
  createdAt: number;
  sources?: ChatSource[];
  dataTimestamp?: string | null;
  isError?: boolean;
}

export interface ChatApiResponse {
  success: boolean;
  answer: string;
  sources: ChatSource[];
  data_timestamp: string | null;
  data_retrieved_at: string;
  focus_states: string[];
  topics: string[];
}