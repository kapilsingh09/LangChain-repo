import React, { useEffect, useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { Zap, ShieldCheck, Globe, Cpu, Sparkles, Layers } from "lucide-react";
import { useAuth } from "../hooks/useAuth";
import { GoogleSignInButton } from "../components/auth/GoogleSignInButton";

export const Login = () => {
  const { currentUser, loading, authError } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [localError, setLocalError] = useState(null);

  const from = location.state?.from?.pathname || "/";

  useEffect(() => {
    if (!loading && currentUser) {
      navigate(from, { replace: true });
    }
  }, [currentUser, loading, navigate, from]);

  const features = [
    {
      icon: Cpu,
      title: "Multi-Agent Orchestration",
      description: "Planner, 3 parallel investigators, evidence synthesizer, and critic running in lockstep.",
    },
    {
      icon: Globe,
      title: "Real-Time Web Intelligence",
      description: "Live web search & citation verification via Tavily to ground findings with facts.",
    },
    {
      icon: Layers,
      title: "Automated Report Synthesis",
      description: "Long-form structured analytical Markdown reports with critique scoring and figures.",
    },
  ];

  return (
    <div className="min-h-screen bg-[#0a0a0a] text-white flex flex-col justify-between relative overflow-hidden selection:bg-white/20 selection:text-white">
      {/* Background ambient lighting */}
      <div className="absolute top-[-20%] left-[20%] w-[600px] h-[600px] bg-white/[0.03] rounded-full blur-[140px] pointer-events-none" />
      <div className="absolute bottom-[-10%] right-[10%] w-[500px] h-[500px] bg-white/[0.02] rounded-full blur-[120px] pointer-events-none" />

      {/* Top navbar bar */}
      <header className="px-6 py-6 flex items-center justify-between max-w-6xl mx-auto w-full z-10">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-xl bg-gradient-to-b from-white to-neutral-300 flex items-center justify-center text-black font-bold shadow-lg shadow-white/10 ring-1 ring-white/20">
            <Zap className="w-4 h-4 fill-black text-black" />
          </div>
          <span className="font-bold text-base tracking-tight text-white">
            Deep Researcher <span className="text-white font-mono text-xs ml-1 px-2 py-0.5 rounded bg-white/10 border border-white/20">AI</span>
          </span>
        </div>

        <div className="flex items-center gap-2 text-xs font-mono text-neutral-400">
          <span className="w-2 h-2 rounded-full bg-white shadow-[0_0_8px_rgba(255,255,255,0.8)]" />
          <span>v2.0 Production</span>
        </div>
      </header>

      {/* Main hero & auth card */}
      <main className="flex-1 flex flex-col items-center justify-center px-4 py-8 z-10 max-w-4xl mx-auto w-full text-center">
        <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-white/10 border border-white/15 text-white text-xs font-mono mb-6">
          <Sparkles className="w-3.5 h-3.5 text-white" />
          <span>LangGraph Autonomous Intelligence</span>
        </div>

        <h1 className="text-4xl sm:text-6xl font-bold tracking-tight max-w-2xl leading-[1.1] mb-5">
          Deep research, <br />
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-white via-neutral-200 to-neutral-400">
            synthesized by agents.
          </span>
        </h1>

        <p className="text-neutral-400 text-sm sm:text-base max-w-lg mb-8 leading-relaxed">
          Sign in to trigger autonomous parallel investigators, gather verifiable web evidence, and receive rigorous research reports.
        </p>

        {/* Auth Box */}
        <div className="w-full max-w-sm p-6 rounded-2xl bg-[#111111]/90 border border-neutral-800 shadow-2xl backdrop-blur-xl">
          <GoogleSignInButton
            className="w-full"
            onSuccess={() => navigate(from, { replace: true })}
            onError={(err) => setLocalError(err.message)}
          />

          {(localError || authError) && (
            <div className="mt-4 p-3 rounded-xl bg-red-500/10 border border-red-500/20 text-xs text-red-400 text-left">
              {localError || authError}
            </div>
          )}

          <p className="text-[11px] text-neutral-500 mt-4 leading-normal">
            Secure authentication via Google Firebase. Each inquiry is encrypted and mapped to your private user ID.
          </p>
        </div>

        {/* Feature Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-16 text-left w-full">
          {features.map((item, idx) => {
            const Icon = item.icon;
            return (
              <div
                key={idx}
                className="p-5 rounded-2xl bg-neutral-900/40 border border-neutral-800/80 hover:border-neutral-700/80 transition-all"
              >
                <div className="w-8 h-8 rounded-lg bg-neutral-800 flex items-center justify-center text-white mb-3 border border-white/5">
                  <Icon className="w-4 h-4" />
                </div>
                <h4 className="text-sm font-semibold text-white mb-1">{item.title}</h4>
                <p className="text-xs text-neutral-400 leading-relaxed">{item.description}</p>
              </div>
            );
          })}
        </div>
      </main>

      {/* Footer */}
      <footer className="px-6 py-6 border-t border-neutral-900 max-w-6xl mx-auto w-full flex flex-col sm:flex-row items-center justify-between gap-2 text-xs text-neutral-500 font-mono">
        <div>LangGraph • Google Gemini • Groq Llama 3 • Tavily Search</div>
        <div>Private & Secure Autonomous Deep Research</div>
      </footer>
    </div>
  );
};

export default Login;
