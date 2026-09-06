import React from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { ReportActions } from "./ReportActions";
import { ReportQualityCard } from "./ReportQualityCard";

export const ResearchReport = ({ 
  report, 
  question, 
  webSearchPerformed, 
  critique, 
  createdAt 
}) => {
  if (!report) return null;

  // Extract score from critique text if available
  let critiqueScore = "";
  if (critique) {
    const scoreMatch = critique.match(/(?:Overall Score|Score):\s*([0-9/.\s]+)/i);
    if (scoreMatch) {
      critiqueScore = scoreMatch[1].trim();
    }
  }

  return (
    <div className="w-full max-w-4xl mx-auto space-y-6 animate-in fade-in slide-in-from-bottom-3 duration-500">
      {/* Header card with metadata & actions */}
      <div className="p-6 rounded-2xl glass-surface shadow-2xl">
        <div className="flex flex-col gap-3">
          <div className="flex items-center gap-2 text-xs font-mono text-neutral-400">
            <span>Research Synthesis</span>
            {createdAt && (
              <>
                <span>•</span>
                <span>{new Date(createdAt).toLocaleString()}</span>
              </>
            )}
          </div>

          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-white leading-tight">
            {question}
          </h1>

          <ReportActions
            reportText={report}
            question={question}
            webSearchPerformed={webSearchPerformed}
            critiqueScore={critiqueScore}
            className="mt-3"
          />
        </div>
      </div>

      {/* Research Quality & Rigor Audit */}
      {critique && (
        <ReportQualityCard critique={critique} />
      )}

      {/* Rendered Markdown Body */}
      <article className="p-6 sm:p-10 rounded-2xl glass-surface shadow-2xl overflow-hidden prose prose-invert max-w-none font-reading">
        <ReactMarkdown
          remarkPlugins={[remarkGfm]}
          components={{
            h1: ({ node, ...props }) => (
              <h1 className="text-2xl sm:text-3xl font-bold text-white tracking-tight mt-8 mb-4 border-b border-neutral-800 pb-3" {...props} />
            ),
            h2: ({ node, ...props }) => (
              <h2 className="text-xl sm:text-2xl font-bold text-white tracking-tight mt-7 mb-3" {...props} />
            ),
            h3: ({ node, ...props }) => (
              <h3 className="text-lg sm:text-xl font-semibold text-neutral-200 mt-6 mb-2" {...props} />
            ),
            p: ({ node, ...props }) => (
              <p className="text-sm sm:text-base text-neutral-300 leading-relaxed my-3" {...props} />
            ),
            ul: ({ node, ...props }) => (
              <ul className="list-disc list-outside pl-5 space-y-1 text-neutral-300 my-3 text-sm sm:text-base" {...props} />
            ),
            ol: ({ node, ...props }) => (
              <ol className="list-decimal list-outside pl-5 space-y-1 text-neutral-300 my-3 text-sm sm:text-base" {...props} />
            ),
            li: ({ node, ...props }) => (
              <li className="leading-relaxed" {...props} />
            ),
            blockquote: ({ node, ...props }) => (
              <blockquote className="border-l-2 border-white/60 bg-neutral-900/50 px-4 py-2 my-4 rounded-r-lg text-neutral-300 italic text-sm" {...props} />
            ),
            code: ({ node, inline, className, children, ...props }) => {
              if (inline) {
                return (
                  <code className="px-1.5 py-0.5 rounded bg-white/10 text-white font-mono text-xs border border-white/15" {...props}>
                    {children}
                  </code>
                );
              }
              return (
                <div className="my-4 rounded-xl overflow-x-auto bg-[#0a0a0a] border border-neutral-800 p-4 font-mono text-xs sm:text-sm text-neutral-200">
                  <pre {...props}>
                    <code>{children}</code>
                  </pre>
                </div>
              );
            },
            table: ({ node, ...props }) => (
              <div className="my-6 w-full overflow-x-auto rounded-xl border border-neutral-800">
                <table className="w-full text-left border-collapse text-xs sm:text-sm" {...props} />
              </div>
            ),
            th: ({ node, ...props }) => (
              <th className="bg-neutral-800/80 p-3 font-semibold text-neutral-200 border-b border-neutral-700 font-mono text-xs uppercase tracking-wider" {...props} />
            ),
            td: ({ node, ...props }) => (
              <td className="p-3 border-b border-neutral-800 text-neutral-300 hover:bg-white/[0.02]" {...props} />
            ),
            a: ({ href, children, ...props }) => {
              const isSafe = /^https?:\/\//i.test(href || "");
              if (!isSafe) {
                return <span>{children}</span>;
              }
              return (
                <a
                  href={href}
                  className="text-white underline underline-offset-4 decoration-white/40 hover:decoration-white transition-colors"
                  target="_blank"
                  rel="noopener noreferrer"
                  {...props}
                >
                  {children}
                </a>
              );
            },
            img: ({ src, alt, ...props }) => {
              const apiBase = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";
              const resolvedSrc = src?.startsWith("/images/")
                ? `${apiBase.replace(/\/+$/, "")}${src}`
                : src?.startsWith("images/")
                ? `${apiBase.replace(/\/+$/, "")}/${src}`
                : src;

              return (
                <div className="my-6 rounded-xl overflow-hidden border border-neutral-800 bg-neutral-950 p-2">
                  <img
                    className="max-w-full rounded-lg mx-auto"
                    src={resolvedSrc}
                    alt={alt || "Research visual"}
                    loading="lazy"
                    {...props}
                  />
                  {alt && (
                    <p className="text-center text-xs text-neutral-400 mt-2 font-mono italic">
                      {alt}
                    </p>
                  )}
                </div>
              );
            },
            hr: ({ node, ...props }) => (
              <hr className="my-8 border-neutral-800" {...props} />
            ),
          }}
        >
          {report}
        </ReactMarkdown>
      </article>
    </div>
  );
};

export default ResearchReport;
