import { memo } from "react";
import ReactMarkdown from "react-markdown";
import type { Components } from "react-markdown";
import remarkGfm from "remark-gfm";
import type { ChatMessage } from "./types";

const TYPE_LABELS: Record<string, string> = {
  official_plfs: "Official · PLFS",
  official_ncs: "Official · NCS portal vacancies",
  calculated: "Calculated indicator",
  forecast: "Statistical forecast",
  illustrative: "Illustrative sample (not official)",
  mixed: "Consolidated view",
};

const markdownComponents: Components = {
  table: ({ node, ...props }) => {
    void node;
    return (
      <div className="sp-chat__table-wrap">
        <table {...props} />
      </div>
    );
  },
  a: ({ node, ...props }) => {
    void node;
    return <a {...props} target="_blank" rel="noopener noreferrer" />;
  },
};

function formatTime(ts: number): string {
  return new Date(ts).toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
  });
}

interface Props {
  message: ChatMessage;
}

function MessageBubble({ message }: Props) {
  const isUser = message.role === "user";
  const rowClass = `sp-chat__row ${isUser ? "sp-chat__row--user" : ""}`;
  const bubbleClass = [
    "sp-chat__bubble",
    isUser ? "sp-chat__bubble--user" : "sp-chat__bubble--ai",
    message.isError ? "sp-chat__bubble--error" : "",
  ].join(" ");

  return (
    <div className={rowClass}>
      <div className={bubbleClass}>
        {isUser || message.isError ? (
          <p className="sp-chat__plain">{message.content}</p>
        ) : (
          <div className="sp-chat__md">
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              components={markdownComponents}
            >
              {message.content}
            </ReactMarkdown>
          </div>
        )}

        {!isUser && message.sources && message.sources.length > 0 && (
          <details className="sp-chat__sources">
            <summary>Data sources ({message.sources.length})</summary>
            <ul>
              {message.sources.map((s) => (
                <li key={s.endpoint + s.name}>
                  <span className="sp-chat__source-name">{s.name}</span>
                  <span className="sp-chat__source-type">
                    {TYPE_LABELS[s.type] ?? s.type}
                    {s.status !== "ok" ? ` · ${s.status}` : ""}
                  </span>
                </li>
              ))}
            </ul>
            {message.dataTimestamp && (
              <p className="sp-chat__timestamp">
                Data timestamp: {message.dataTimestamp}
              </p>
            )}
          </details>
        )}

        {message.createdAt > 0 && (
          <span className="sp-chat__time">{formatTime(message.createdAt)}</span>
        )}
      </div>
    </div>
  );
}

export default memo(MessageBubble);