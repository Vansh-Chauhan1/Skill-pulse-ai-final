import { useCallback, useRef, useState } from "react";
import axios from "axios";
import { sendAiChat } from "../../services/api";
import type { ChatMessage } from "./types";

export const MAX_QUESTION_LENGTH = 1000;
const MAX_HISTORY = 10;
const MAX_HISTORY_CHARS = 3500;

export const WELCOME_MESSAGE =
  "Hello! I'm SkillPulse Intelligence Assistant. I can help you understand India's labour market, explore state-wise skill gaps, analyse employment sectors and interpret future employment predictions.\n\nWhat would you like to explore today?";

const makeId = () =>
  `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;

function extractErrorMessage(err: unknown): string {
  if (axios.isAxiosError(err)) {
    if (err.code === "ECONNABORTED") {
      return "The request took too long. Please try again.";
    }
    if (!err.response) {
      return "Cannot reach the SkillPulse backend. Check that it is running and that the API URL is correct.";
    }
    const detail = err.response.data?.detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail)) {
      return "Your message could not be processed. Please shorten or rephrase it.";
    }
    if (err.response.status === 429) {
      return "Too many requests. Please wait a moment and try again.";
    }
  }
  return "Something went wrong while generating the answer. Please try again.";
}

export function useChat() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState(false);

  const messagesRef = useRef<ChatMessage[]>([]);
  const loadingRef = useRef(false);
  const requestToken = useRef(0);

  const commit = (next: ChatMessage[]) => {
    messagesRef.current = next;
    setMessages(next);
  };

  const sendMessage = useCallback(async (raw: string) => {
    const question = raw.trim().slice(0, MAX_QUESTION_LENGTH);
    if (!question || loadingRef.current) return;

    const history = messagesRef.current
      .filter((m) => !m.isError)
      .slice(-MAX_HISTORY)
      .map((m) => ({
        role: m.role,
        content: m.content.slice(0, MAX_HISTORY_CHARS),
      }));

    const token = ++requestToken.current;
    commit([
      ...messagesRef.current,
      { id: makeId(), role: "user", content: question, createdAt: Date.now() },
    ]);
    loadingRef.current = true;
    setLoading(true);

    try {
      const data = await sendAiChat(question, history);
      if (token !== requestToken.current) return;
      commit([
        ...messagesRef.current,
        {
          id: makeId(),
          role: "assistant",
          content: data.answer,
          createdAt: Date.now(),
          sources: data.sources,
          dataTimestamp: data.data_timestamp,
        },
      ]);
    } catch (err) {
      if (token !== requestToken.current) return;
      commit([
        ...messagesRef.current,
        {
          id: makeId(),
          role: "assistant",
          content: extractErrorMessage(err),
          createdAt: Date.now(),
          isError: true,
        },
      ]);
    } finally {
      if (token === requestToken.current) {
        loadingRef.current = false;
        setLoading(false);
      }
    }
  }, []);

  const clearConversation = useCallback(() => {
    requestToken.current += 1; // ignore any in-flight response
    loadingRef.current = false;
    setLoading(false);
    commit([]);
  }, []);

  return { messages, loading, sendMessage, clearConversation };
}