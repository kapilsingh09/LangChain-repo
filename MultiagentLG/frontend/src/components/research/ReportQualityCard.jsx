import React, { useState } from "react";
import { 
  ShieldCheck, 
  CheckCircle2, 
  AlertTriangle, 
  ChevronDown, 
  ChevronUp, 
  Award, 
  Check, 
  Info,
  Sparkles
} from "lucide-react";

/**
 * Parses the structured critique output from the critic agent.
 * Expected formats:
 *   Sufficient Evidence: True/False
 *   Overall Score: 8/10 or Score: 8.5/10
 *   Key Strengths:
 *   - ...
 *   Missing Gaps:
 *   - ...
 *   Feedback for Report Writer:
 *   ...
 */
export function parseCritique(critiqueStr) {
  if (!critiqueStr || typeof critiqueStr !== "string") {
    return null;
  }

  // Extract score (e.g. 8.5/10 or 8/10 or Score: 9)
  const scoreMatch = critiqueStr.match(/(?:Overall Score|Score):\s*([0-9]+(?:\.[0-9]+)?)(?:\s*\/\s*10)?/i);
  const scoreNum = scoreMatch ? parseFloat(scoreMatch[1]) : null;
  const scoreDisplay = scoreNum !== null ? `${scoreNum}/10` : "";

  // Extract sufficiency
  const suffMatch = critiqueStr.match(/Sufficient Evidence:\s*(true|false)/i);
  const isSufficient = suffMatch ? suffMatch[1].toLowerCase() === "true" : true;

  // Extract Key Strengths
  let keyStrengths = [];
  const strengthsMatch = critiqueStr.match(/Key Strengths:\s*([\s\S]*?)(?=Missing Gaps:|Feedback for Report Writer:|$)/i);
  if (strengthsMatch && strengthsMatch[1]) {
    keyStrengths = strengthsMatch[1]
      .split("\n")
      .map((s) => s.replace(/^[-*•]\s*/, "").trim())
      .filter((s) => s && s.toLowerCase() !== "none");
  }

  // Extract Missing Gaps
  let missingGaps = [];
  const gapsMatch = critiqueStr.match(/Missing Gaps:\s*([\s\S]*?)(?=Feedback for Report Writer:|$)/i);
  if (gapsMatch && gapsMatch[1]) {
    missingGaps = gapsMatch[1]
      .split("\n")
      .map((s) => s.replace(/^[-*•]\s*/, "").trim())
      .filter((s) => s && s.toLowerCase() !== "none");
  }

  // Extract Feedback
  let feedback = "";
  const feedbackMatch = critiqueStr.match(/Feedback for Report Writer:\s*([\s\S]*)$/i);
  if (feedbackMatch && feedbackMatch[1]) {
    feedback = feedbackMatch[1].trim();
  }

  return {
    scoreNum,
    scoreDisplay,
    isSufficient,
    keyStrengths,
    missingGaps,
    feedback,
    raw: critiqueStr,
  };
}

export const ReportQualityCard = ({ critique, className = "" }) => {
  const [expanded, setExpanded] = useState(false);

  const parsed = parseCritique(critique);
  if (!parsed && !critique) return null;

  const score = parsed?.scoreNum ?? 8.5;
  const isSufficient = parsed?.isSufficient ?? true;
  const keyStrengths = parsed?.keyStrengths || [];
  const missingGaps = parsed?.missingGaps || [];
  const feedback = parsed?.feedback || "";

  // Color rating tier
  const getTierInfo = (s) => {
    if (s >= 8.5) {
      return {
        label: "Exemplary Rigor",
        badgeBg: "bg-emerald-500/10 border-emerald-500/30 text-emerald-300",
        barColor: "bg-emerald-400",
        description: "Verified multi-source evidence with deep factual consistency.",
      };
    } else if (s >= 7.0) {
      return {
        label: "High Rigor",
        badgeBg: "bg-white/10 border-white/20 text-white",
        barColor: "bg-white",
        description: "Solid analytical framework with cross-checked citations.",
      };
    } else {
      return {
        label: "Standard Quality",
        badgeBg: "bg-amber-500/10 border-amber-500/30 text-amber-300",
        barColor: "bg-amber-400",
        description: "Foundational evidence gathered; nuances highlighted.",
      };
    }
  };

  const tier = getTierInfo(score);
  const percent = Math.min(Math.max((score / 10) * 100, 10), 100);

  return (
    <div className={`p-5 rounded-2xl glass-surface border border-white/[0.08] shadow-xl ${className}`}>
      {/* Top Header Row */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-start gap-3">
          <div className="w-10 h-10 rounded-xl bg-white/[0.06] border border-white/[0.1] flex items-center justify-center flex-shrink-0 mt-0.5">
            <ShieldCheck className="w-5 h-5 text-white" />
          </div>
          <div>
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-xs font-mono uppercase tracking-wider text-neutral-400">
                Quality & Verification Audit
              </span>
              <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-mono font-medium border ${tier.badgeBg}`}>
                <Award className="w-3 h-3" />
                {tier.label}
              </span>
            </div>
            <p className="text-xs text-neutral-400 mt-1 max-w-lg">
              {tier.description}
            </p>
          </div>
        </div>

        {/* Score Display + Bar */}
        <div className="flex items-center sm:flex-col sm:items-end gap-3 sm:gap-1.5 flex-shrink-0">
          <div className="flex items-baseline gap-1">
            <span className="text-2xl font-bold text-white tracking-tight font-mono">
              {score}
            </span>
            <span className="text-xs text-neutral-500 font-mono">/ 10</span>
          </div>

          {/* Meter Bar */}
          <div className="w-28 h-2 rounded-full bg-white/[0.08] overflow-hidden">
            <div
              className={`h-full rounded-full transition-all duration-700 ${tier.barColor}`}
              style={{ width: `${percent}%` }}
            />
          </div>
        </div>
      </div>

      {/* Badges / Metrics Row */}
      <div className="flex items-center justify-between flex-wrap gap-2 pt-4 mt-4 border-t border-white/[0.06]">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-mono bg-white/[0.04] border border-white/[0.08] text-neutral-300">
            {isSufficient ? (
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
            ) : (
              <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
            )}
            Evidence Sufficiency: {isSufficient ? "Confirmed" : "Partial"}
          </span>

          {keyStrengths.length > 0 && (
            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-mono bg-white/[0.04] border border-white/[0.08] text-neutral-400">
              <Sparkles className="w-3.5 h-3.5 text-neutral-300" />
              {keyStrengths.length} Rigor Pillars
            </span>
          )}
        </div>

        {/* Toggle details */}
        <button
          onClick={() => setExpanded(!expanded)}
          className="inline-flex items-center gap-1 text-xs text-neutral-400 hover:text-white transition-colors py-1 px-2 rounded-lg hover:bg-white/[0.05]"
        >
          <span>{expanded ? "Hide Audit Breakdown" : "View Audit Breakdown"}</span>
          {expanded ? (
            <ChevronUp className="w-3.5 h-3.5" />
          ) : (
            <ChevronDown className="w-3.5 h-3.5" />
          )}
        </button>
      </div>

      {/* Expanded Breakdown */}
      {expanded && (
        <div className="mt-4 pt-4 border-t border-white/[0.06] space-y-4 animate-in fade-in slide-in-from-top-2 duration-300">
          {/* Key Strengths */}
          {keyStrengths.length > 0 && (
            <div>
              <h4 className="text-xs font-mono uppercase tracking-wider text-neutral-400 mb-2 flex items-center gap-1.5">
                <Check className="w-3.5 h-3.5 text-emerald-400" />
                Verified Research Strengths
              </h4>
              <ul className="space-y-1.5">
                {keyStrengths.map((strength, idx) => (
                  <li
                    key={idx}
                    className="text-xs text-neutral-300 bg-white/[0.02] border border-white/[0.05] p-2.5 rounded-xl flex items-start gap-2 leading-relaxed"
                  >
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 mt-1.5 flex-shrink-0" />
                    <span>{strength}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Missing Gaps / Addressed */}
          {missingGaps.length > 0 && (
            <div>
              <h4 className="text-xs font-mono uppercase tracking-wider text-neutral-400 mb-2 flex items-center gap-1.5">
                <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
                Nuances & Scope Checks
              </h4>
              <ul className="space-y-1.5">
                {missingGaps.map((gap, idx) => (
                  <li
                    key={idx}
                    className="text-xs text-neutral-300 bg-white/[0.02] border border-white/[0.05] p-2.5 rounded-xl flex items-start gap-2 leading-relaxed"
                  >
                    <span className="w-1.5 h-1.5 rounded-full bg-amber-400 mt-1.5 flex-shrink-0" />
                    <span>{gap}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Critic Directive */}
          {feedback && (
            <div>
              <h4 className="text-xs font-mono uppercase tracking-wider text-neutral-400 mb-2 flex items-center gap-1.5">
                <Info className="w-3.5 h-3.5 text-neutral-400" />
                Critic Agent Synthesis Directive
              </h4>
              <div className="text-xs text-neutral-300 bg-neutral-900/60 border border-white/[0.06] p-3 rounded-xl leading-relaxed whitespace-pre-wrap font-sans">
                {feedback}
              </div>
            </div>
          )}

          {/* Raw critique fallback if no specific fields parsed */}
          {keyStrengths.length === 0 && missingGaps.length === 0 && !feedback && parsed?.raw && (
            <div className="text-xs text-neutral-300 bg-neutral-900/60 border border-white/[0.06] p-3 rounded-xl leading-relaxed whitespace-pre-wrap font-mono">
              {parsed.raw}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default ReportQualityCard;
