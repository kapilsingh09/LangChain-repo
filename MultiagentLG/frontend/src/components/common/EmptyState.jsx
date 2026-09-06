import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Sparkles,
  TrendingUp,
  Eye,
  ArrowUpRight,
  Flame,
  Zap,
  Search,
  Globe,
  Cpu,
  BrainCircuit,
  Heart,
  BarChart3,
  Leaf,
  Loader2,
} from "lucide-react";
import {
  fetchTrendingTopics,
  getCategories,
  filterByCategory,
} from "../../services/trending";

const CATEGORY_ICONS = {
  Trending: Flame,
  "AI & ML": BrainCircuit,
  Science: Zap,
  Technology: Cpu,
  Health: Heart,
  Business: BarChart3,
  Energy: Leaf,
};

export const EmptyState = ({ onSelectPrompt }) => {
  const [topics, setTopics] = useState([]);
  const [categories, setCategories] = useState(["Trending"]);
  const [activeCategory, setActiveCategory] = useState("Trending");
  const [loading, setLoading] = useState(true);
  const [hoveredCard, setHoveredCard] = useState(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);

    fetchTrendingTopics().then((data) => {
      if (cancelled) return;
      setTopics(data);
      setCategories(getCategories(data));
      setLoading(false);
    });

    return () => {
      cancelled = true;
    };
  }, []);

  const filteredTopics = filterByCategory(topics, activeCategory);

  return (
    <div className="flex flex-col items-center w-full max-w-5xl mx-auto">
      {/* ─── Hero Section with Background Glow ─── */}
      <div className="relative w-full flex flex-col items-center pt-6 pb-8 px-4 overflow-hidden">
        {/* Animated background orbs — monochrome */}
        <div className="absolute inset-0 pointer-events-none overflow-hidden">
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] rounded-full bg-gradient-to-br from-white/[0.04] via-white/[0.02] to-transparent blur-3xl hero-glow-orb" />
          <div className="absolute top-1/3 left-1/4 w-[300px] h-[300px] rounded-full bg-gradient-to-tr from-white/[0.03] to-transparent blur-3xl hero-glow-orb" style={{ animationDelay: "2s" }} />
        </div>

        {/* Badge */}
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="relative inline-flex items-center gap-2 px-4 py-1.5 rounded-full glass text-white text-xs font-mono uppercase tracking-widest mb-5"
        >
          <Sparkles className="w-3.5 h-3.5 text-neutral-300" />
          <span>Autonomous Multi-Agent Research</span>
        </motion.div>

        {/* Main Headline */}
        <motion.h1
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.1 }}
          className="relative text-3xl sm:text-4xl md:text-5xl font-bold tracking-tight text-center mb-3 leading-tight"
        >
          Discover, Explore,{" "}
          <span className="animated-gradient-text">Deep Research</span>
        </motion.h1>

        {/* Subtitle */}
        <motion.p
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.2 }}
          className="relative text-neutral-400 text-sm sm:text-base max-w-xl mx-auto text-center leading-relaxed mb-2"
        >
          Pick a trending topic or ask your own question. Our multi-agent team
          plans, searches the web, and delivers exhaustive analytical reports.
        </motion.p>
      </div>

      {/* ─── Category Tabs (Kaggle-style) ─── */}
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.3 }}
        className="w-full mb-5"
      >
        <div className="flex items-center gap-2 overflow-x-auto pb-2 px-1 scrollbar-hide">
          {categories.map((cat) => {
            const Icon = CATEGORY_ICONS[cat] || Globe;
            const isActive = activeCategory === cat;
            return (
              <button
                key={cat}
                onClick={() => setActiveCategory(cat)}
                className={`flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-medium whitespace-nowrap transition-all duration-200 border ${
                  isActive
                    ? "category-pill-active shadow-sm"
                    : "bg-white/[0.03] border-white/[0.06] text-neutral-400 hover:text-white hover:bg-white/[0.06] hover:border-white/[0.12]"
                }`}
              >
                <Icon className="w-3.5 h-3.5" />
                {cat}
              </button>
            );
          })}
        </div>
      </motion.div>

      {/* ─── Trending Topics Grid ─── */}
      <div className="w-full mb-6">
        {loading ? (
          /* Shimmer Loading Skeletons */
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {Array.from({ length: 6 }).map((_, i) => (
              <div
                key={i}
                className="p-4 rounded-xl border border-white/[0.05] bg-white/[0.02] space-y-3"
              >
                <div className="flex items-center gap-2">
                  <div className="w-16 h-5 rounded-full shimmer" />
                  <div className="w-10 h-4 rounded shimmer" />
                </div>
                <div className="w-full h-5 rounded shimmer" />
                <div className="w-3/4 h-4 rounded shimmer" />
              </div>
            ))}
          </div>
        ) : filteredTopics.length === 0 ? (
          <div className="text-center py-10 text-neutral-500 text-sm">
            No trending topics in this category right now.
          </div>
        ) : (
          <motion.div
            layout
            className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3"
          >
            <AnimatePresence mode="popLayout">
              {filteredTopics.map((topic, idx) => {
                const CatIcon = CATEGORY_ICONS[topic.category] || Globe;
                return (
                  <motion.button
                    key={topic.id}
                    layout
                    initial={{ opacity: 0, y: 16 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, scale: 0.95 }}
                    transition={{
                      duration: 0.35,
                      delay: idx * 0.04,
                      layout: { duration: 0.3 },
                    }}
                    onClick={() => onSelectPrompt && onSelectPrompt(topic.prompt)}
                    onMouseEnter={() => setHoveredCard(topic.id)}
                    onMouseLeave={() => setHoveredCard(null)}
                    className="group relative text-left p-4 rounded-xl glass trending-card flex flex-col justify-between min-h-[120px]"
                  >
                    {/* Top row — category + views */}
                    <div className="flex items-center justify-between mb-2.5">
                      <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[10px] font-mono uppercase tracking-wider text-neutral-300 bg-white/[0.06] border border-white/[0.08]">
                        <CatIcon className="w-3 h-3" />
                        {topic.category}
                      </span>

                      <div className="flex items-center gap-1.5">
                        {topic.views > 0 && (
                          <span className="inline-flex items-center gap-1 text-[10px] font-mono text-neutral-500">
                            <Eye className="w-3 h-3" />
                            {topic.viewsFormatted}
                          </span>
                        )}
                        {topic.source === "curated" && (
                          <span className="inline-flex items-center gap-1 text-[10px] font-mono text-neutral-500">
                            <Sparkles className="w-2.5 h-2.5" />
                          </span>
                        )}
                      </div>
                    </div>

                    {/* Title */}
                    <h4 className="text-sm font-semibold text-neutral-200 group-hover:text-white transition-colors leading-snug mb-1.5">
                      {topic.title}
                    </h4>

                    {/* Bottom row */}
                    <div className="flex items-center justify-between mt-auto pt-2">
                      <span className="text-[11px] text-neutral-500 group-hover:text-neutral-400 transition-colors font-mono truncate max-w-[70%]">
                        Click to research
                      </span>
                      <ArrowUpRight
                        className={`w-4 h-4 transition-all duration-300 ${
                          hoveredCard === topic.id
                            ? "text-white translate-x-0.5 -translate-y-0.5"
                            : "text-neutral-600"
                        }`}
                      />
                    </div>

                    {/* Hover overlay */}
                    <div className="absolute inset-0 rounded-xl opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none bg-gradient-to-br from-white/[0.02] via-transparent to-white/[0.01]" />
                  </motion.button>
                );
              })}
            </AnimatePresence>
          </motion.div>
        )}
      </div>

      {/* ─── Bottom attribution ─── */}
      {!loading && topics.length > 0 && topics[0].source !== "curated" && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.8 }}
          className="flex items-center gap-2 text-[10px] text-neutral-600 font-mono mb-4"
        >
          <TrendingUp className="w-3 h-3" />
          <span>
            Trending topics from Wikipedia · Updated daily
          </span>
        </motion.div>
      )}
    </div>
  );
};

export default EmptyState;
