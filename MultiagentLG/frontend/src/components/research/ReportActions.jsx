import React, { useState } from "react";
import { Copy, Check, Download, Share2, Globe, Shield } from "lucide-react";

export const ReportActions = ({ 
  reportText, 
  question, 
  webSearchPerformed, 
  critiqueScore,
  className = "" 
}) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    if (!reportText) return;
    try {
      await navigator.clipboard.writeText(reportText);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error("Failed to copy:", err);
    }
  };

  const handleDownload = () => {
    if (!reportText) return;
    const blob = new Blob([reportText], { type: "text/markdown;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    const sanitizedTitle = (question || "deep_research")
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "_")
      .slice(0, 40);
    link.href = url;
    link.download = `${sanitizedTitle}_report.md`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  return (
    <div className={`flex flex-wrap items-center justify-between gap-3 p-3 bg-neutral-900/60 rounded-xl border border-neutral-800 ${className}`}>
      <div className="flex items-center gap-2">
        {webSearchPerformed && (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-mono font-medium bg-white/10 text-neutral-300 border border-white/15">
            <Globe className="w-3.5 h-3.5" />
            Live Web Verified
          </span>
        )}

        {critiqueScore && (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-mono font-medium bg-white/10 text-white border border-white/20">
            <Shield className="w-3.5 h-3.5" />
            Rigor: {critiqueScore}
          </span>
        )}
      </div>

      <div className="flex items-center gap-2">
        <button
          onClick={handleCopy}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-neutral-800 hover:bg-neutral-700 text-neutral-300 hover:text-white text-xs font-medium border border-neutral-700 transition-colors active:scale-95"
          title="Copy markdown to clipboard"
        >
          {copied ? (
            <>
              <Check className="w-3.5 h-3.5 text-white" />
              <span className="text-white">Copied</span>
            </>
          ) : (
            <>
              <Copy className="w-3.5 h-3.5" />
              <span>Copy</span>
            </>
          )}
        </button>

        <button
          onClick={handleDownload}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white hover:bg-neutral-200 text-black text-xs font-semibold shadow-sm transition-colors active:scale-95"
          title="Download as Markdown file"
        >
          <Download className="w-3.5 h-3.5 stroke-[2.2]" />
          <span>Download .md</span>
        </button>
      </div>
    </div>
  );
};

export default ReportActions;
