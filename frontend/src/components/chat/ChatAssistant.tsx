import { useEffect, useRef, useState } from "react";
import type { ChangeEvent, KeyboardEvent } from "react";
import MessageBubble from "./MessageBubble";
import { MAX_QUESTION_LENGTH, WELCOME_MESSAGE, useChat } from "./useChat";
import type { ChatMessage } from "./types";
import "./chat.css";

const SUGGESTED_QUESTIONS = [
  "Which Indian states have the highest skill gaps?",
  "Explain the employment situation in Maharashtra.",
  "Which sectors have increasing vacancy demand?",
  "What are the future employment trends in India?",
  "What are the major skill-development challenges?",
  "Explain the latest available PLFS employment indicators.",
  "What does the NCS vacancy data indicate?",
  "Which sectors should policymakers prioritise?",
];

const WELCOME: ChatMessage = {
  id: "welcome",
  role: "assistant",
  content: WELCOME_MESSAGE,
  createdAt: 0,
};

const SparkIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" aria-hidden="true">
    <path
      d="M12 3l1.9 5.1L19 10l-5.1 1.9L12 17l-1.9-5.1L5 10l5.1-1.9L12 3z"
      fill="currentColor"
    />
    <path
      d="M19 15l.9 2.1L22 18l-2.1.9L19 21l-.9-2.1L16 18l2.1-.9L19 15z"
      fill="currentColor"
      opacity="0.7"
    />
  </svg>
);

const SendIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden="true">
    <path d="M3 11.5L21 3l-8.5 18-2.2-7.3L3 11.5z" fill="currentColor" />
  </svg>
);

export default function ChatAssistant() {
  const [open, setOpen] = useState(false);
  const [input, setInput] = useState("");
  const { messages, loading, sendMessage, clearConversation } = useChat();

  const bottomRef = useRef<HTMLDivElement | null>(null);
  const inputRef = useRef<HTMLTextAreaElement | null>(null);

  useEffect(() => {
    if (open) bottomRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages, loading, open]);

  useEffect(() => {
    if (open) inputRef.current?.focus();
  }, [open]);

  useEffect(() => {
    const el = inputRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, 120)}px`;
  }, [input, open]);

  const submit = () => {
    if (loading || !input.trim()) return;
    void sendMessage(input);
    setInput("");
  };

  const onKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey && !e.nativeEvent.isComposing) {
      e.preventDefault();
      submit();
    }
  };

  const onChange = (e: ChangeEvent<HTMLTextAreaElement>) =>
    setInput(e.target.value.slice(0, MAX_QUESTION_LENGTH));

  return (
    <div className="sp-chat">
      {!open && (
        <button
          type="button"
          className="sp-chat__launcher"
          onClick={() => setOpen(true)}
          aria-label="Open SkillPulse Intelligence Assistant"
        >
          <SparkIcon />
          <span>AI Assistant</span>
        </button>
      )}

      {open && (
        <section
          className="sp-chat__panel"
          role="dialog"
          aria-label="SkillPulse Intelligence Assistant"
          onKeyDown={(e) => e.key === "Escape" && setOpen(false)}
        >
          <header className="sp-chat__header">
            <div className="sp-chat__title">
              <span className="sp-chat__avatar">
                <SparkIcon />
              </span>
              <div>
                <h2>SkillPulse Intelligence Assistant</h2>
                <p>Grounded in PLFS and NCS data</p>
              </div>
            </div>
            <div className="sp-chat__header-actions">
              <button
                type="button"
                onClick={clearConversation}
                disabled={messages.length === 0}
                title="Clear conversation"
              >
                Clear
              </button>
              <button
                type="button"
                onClick={() => setOpen(false)}
                aria-label="Close assistant"
                title="Close"
              >
                ✕
              </button>
            </div>
          </header>

          <div className="sp-chat__body" role="log" aria-live="polite">
            <MessageBubble message={WELCOME} />

            {messages.length === 0 && (
              <div className="sp-chat__suggestions">
                {SUGGESTED_QUESTIONS.map((q) => (
                  <button
                    key={q}
                    type="button"
                    className="sp-chat__suggestion"
                    onClick={() => void sendMessage(q)}
                  >
                    {q}
                  </button>
                ))}
              </div>
            )}

            {messages.map((m) => (
              <MessageBubble key={m.id} message={m} />
            ))}

            {loading && (
              <div className="sp-chat__row">
                <div className="sp-chat__bubble sp-chat__bubble--ai sp-chat__typing">
                  <span />
                  <span />
                  <span />
                  <em>Analysing labour-market data…</em>
                </div>
              </div>
            )}
            <div ref={bottomRef} />
          </div>

          <footer className="sp-chat__footer">
            <div className="sp-chat__composer">
              <textarea
                ref={inputRef}
                value={input}
                onChange={onChange}
                onKeyDown={onKeyDown}
                placeholder="Ask about employment, sectors, skills or forecasts…"
                rows={1}
                aria-label="Message"
              />
              <button
                type="button"
                className="sp-chat__send"
                onClick={submit}
                disabled={loading || !input.trim()}
                aria-label="Send message"
              >
                <SendIcon />
              </button>
            </div>
            <p className="sp-chat__disclaimer">
              AI-generated analysis. Verify important figures against the source data.
            </p>
          </footer>
        </section>
      )}
    </div>
  );
}