import ReactMarkdown from 'react-markdown';
import { Copy, Download } from 'lucide-react';

export function ResearchReport({ markdown }) {
  
  const handleCopy = () => {
    navigator.clipboard.writeText(markdown);
  };

  const handleDownload = () => {
    const blob = new Blob([markdown], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'deep_research_report.md';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="w-full max-w-4xl mx-auto">
      <div className="flex justify-end gap-2 mb-6">
        <button onClick={handleCopy} className="btn-secondary text-xs py-1.5 px-3">
          <Copy className="w-3 h-3" /> Copy
        </button>
        <button onClick={handleDownload} className="btn-secondary text-xs py-1.5 px-3">
          <Download className="w-3 h-3" /> Export MD
        </button>
      </div>

      <div className="prose prose-invert prose-indigo max-w-none 
          prose-headings:text-text-main prose-headings:font-bold 
          prose-p:text-text-main/90 prose-p:leading-relaxed
          prose-a:text-primary prose-a:no-underline hover:prose-a:underline
          prose-strong:text-text-main prose-strong:font-semibold
          prose-code:text-primary prose-code:bg-primary/10 prose-code:px-1 prose-code:rounded
          prose-pre:bg-surface-hover prose-pre:border prose-pre:border-border
          prose-blockquote:border-primary prose-blockquote:bg-surface-hover/50 prose-blockquote:py-1 prose-blockquote:px-4 prose-blockquote:rounded-r-lg prose-blockquote:text-text-muted
          prose-li:text-text-main/90"
      >
        <ReactMarkdown>{markdown}</ReactMarkdown>
      </div>
    </div>
  );
}
