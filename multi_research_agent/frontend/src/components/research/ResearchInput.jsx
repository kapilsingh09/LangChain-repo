import { useState } from 'react';
import { Sparkles, ArrowRight, Settings2 } from 'lucide-react';
import { cn } from '../layout/Sidebar';

export function ResearchInput({ onSubmit }) {
  const [question, setQuestion] = useState('');
  const [isDeep, setIsDeep] = useState(false);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (question.trim()) {
      onSubmit(question.trim());
    }
  };

  return (
    <div className="w-full max-w-3xl mx-auto mt-12 animate-in fade-in slide-in-from-bottom-4 duration-700">
      <div className="text-center mb-8 space-y-4">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-primary/10 text-primary border border-primary/20 text-sm font-medium mb-2">
          <Sparkles className="w-4 h-4" />
          <span>Research Intelligence Engine</span>
        </div>
        <h1 className="text-4xl md:text-5xl font-bold text-text-main tracking-tight">
          What do you want to understand deeply?
        </h1>
        <p className="text-text-muted text-lg max-w-2xl mx-auto">
          Ask a complex question and watch multiple AI research stages investigate, verify and synthesize the answer.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="relative group">
        <div className="absolute -inset-1 bg-gradient-to-r from-primary/50 to-purple-500/50 rounded-2xl blur opacity-20 group-hover:opacity-40 transition duration-500"></div>
        <div className="relative glass-panel p-2 flex flex-col md:flex-row gap-2">
          <textarea
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Research the current state of generative AI, major developments, limitations, market adoption and likely direction over the next 2–3 years..."
            className="flex-1 bg-transparent border-0 focus:ring-0 text-text-main placeholder:text-text-muted/50 p-4 min-h-[120px] md:min-h-[60px] resize-none outline-none"
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSubmit(e);
              }
            }}
          />
          <div className="flex flex-row md:flex-col justify-between md:justify-end gap-2 p-2">
            <button 
              type="button"
              onClick={() => setIsDeep(!isDeep)}
              className={cn(
                "p-3 rounded-xl border transition-colors flex items-center justify-center",
                isDeep 
                  ? "bg-primary/20 border-primary/50 text-primary" 
                  : "bg-surface border-border text-text-muted hover:bg-surface-hover hover:text-text-main"
              )}
              title="Toggle Deep Research Mode"
            >
              <Settings2 className="w-5 h-5" />
            </button>
            <button 
              type="submit"
              disabled={!question.trim()}
              className="btn-primary py-3 px-6 rounded-xl flex-1 md:flex-none"
            >
              <span>Start</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </form>
      
      <div className="mt-8 flex flex-wrap justify-center gap-3">
        {["RAG vs Fine-tuning", "Future of AI Agents", "Edge AI architectures"].map((suggestion) => (
          <button 
            key={suggestion}
            onClick={() => setQuestion(suggestion)}
            className="px-4 py-2 rounded-full glass-card text-sm text-text-muted hover:text-text-main"
          >
            {suggestion}
          </button>
        ))}
      </div>
    </div>
  );
}
