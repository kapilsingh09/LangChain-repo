import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Sparkles,
  TrendingUp,
  Eye,
  ArrowUpRight,
  Flame,
  Zap,
  Globe,
  Cpu,
  BrainCircuit,
  Heart,
  BarChart3,
  Leaf,
} from "lucide-react";
import {
  fetchTrendingTopics,
  getCategories,
  filterByCategory,
} from "../../services/trending";
import { useAuth } from "../../hooks/useAuth";

const CATEGORY_ICONS = {
  Trending: Flame,
  "AI & ML": BrainCircuit,
  Science: Zap,
  Technology: Cpu,
  Health: Heart,
  Business: BarChart3,
  Energy: Leaf,
};

// Blend of short personal greetings and inspiring simple quotes
const GREETINGS_AND_QUOTES = [
  "Good to see you, {name}.",
  "Turn curiosity into deep clarity.",
  "Welcome back, {name}.",
  "Inquire deeply, discover comprehensively.",
  "Evidence over assumption.",
  "What shall we explore today, {name}?",
  "Where deep inquiry begins.",
  "Seeking truth through research.",
  "Ready when you are, {name}.",
  "Knowledge begins with questions.",
  "Hello, {name}.",
  "Analyze, synthesize, understand.",
];

export const EmptyState = ({ onSelectPrompt, showTopics = false, onCloseTopics }) => {
  const { currentUser } = useAuth();
  const [topics, setTopics] = useState([]);
  const [categories, setCategories] = useState(["Trending"]);
  const [activeCategory, setActiveCategory] = useState("Trending");
  const [loading, setLoading] = useState(true);
  const [hoveredCard, setHoveredCard] = useState(null);

  // Extract ONLY user's first name (e.g. "Harshita" from "Harshita Sharma" or "harshita.sharma@gmail.com")
  const getUserFirstName = () => {
    if (!currentUser) return "Researcher";

    if (currentUser.displayName && currentUser.displayName.trim()) {
      const first = currentUser.displayName.trim().split(/[\s._-]+/)[0];
      if (first) {
        return first.charAt(0).toUpperCase() + first.slice(1).toLowerCase();
      }
    }

    if (currentUser.email && currentUser.email.trim()) {
      const prefix = currentUser.email.split("@")[0].trim();
      const firstPart = prefix.split(/[._\d-]+/)[0] || prefix;
      if (firstPart) {
        return firstPart.charAt(0).toUpperCase() + firstPart.slice(1).toLowerCase();
      }
    }

    return "Researcher";
  };

  const userName = getUserFirstName();

  // Pick random greeting or quote on reload / mount (changes each time page reloads)
  const [greetingIdx] = useState(() => Math.floor(Math.random() * GREETINGS_AND_QUOTES.length));
  const currentGreeting = GREETINGS_AND_QUOTES[greetingIdx].replace("{name}", userName);

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
    <div className={`flex flex-col items-center w-full max-w-5xl mx-auto transition-all duration-300 ${!showTopics ? "min-h-[48vh] justify-center my-auto" : "pt-4"}`}>
      {/* ─── Centered Clean Greeting Section ("beech beech mein") ─── */}
      <div className="relative w-full flex flex-col items-center justify-center text-center px-4 overflow-hidden py-6">
        {/* Subtle background glow */}
        <div className="absolute inset-0 pointer-events-none overflow-hidden">
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[450px] h-[450px] rounded-full bg-gradient-to-br from-white/[0.04] via-white/[0.015] to-transparent blur-3xl hero-glow-orb" />
        </div>

        {/* Short, Clean Personalized Greeting or Thoughtful Quote */}
        <motion.h1
          initial={{ opacity: 0, scale: 0.96 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.45 }}
          className="relative text-3xl sm:text-4xl md:text-5xl font-bold tracking-tight text-center leading-tight"
        >
          {currentGreeting.includes(userName) ? (
            <>
              {currentGreeting.split(userName)[0]}
              <span className="animated-gradient-text">{userName}</span>
              {currentGreeting.split(userName)[1]}
            </>
          ) : (
            currentGreeting
          )}
        </motion.h1>
      </div>

      {/* ─── Collapsible Topic Cards Area ─── */}
      <AnimatePresence>
        {showTopics && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.35, ease: "easeInOut" }}
            className="w-full overflow-hidden"
          >
            {/* ─── Category Tabs (Kaggle-style, compact) ─── */}
            <motion.div
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.25 }}
              className="w-full mb-3 mt-1"
            >
              <div className="flex items-center gap-1.5 overflow-x-auto pb-1.5 px-1 scrollbar-hide">
                {categories.map((cat) => {
                  const Icon = CATEGORY_ICONS[cat] || Globe;
                  const isActive = activeCategory === cat;
                  return (
                    <button
                      key={cat}
                      onClick={() => setActiveCategory(cat)}
                      className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-[11px] font-medium whitespace-nowrap transition-all duration-150 border ${
                        isActive
                          ? "category-pill-active shadow-sm"
                          : "bg-white/[0.03] border-white/[0.06] text-neutral-400 hover:text-white hover:bg-white/[0.06]"
                      }`}
                    >
                      <Icon className="w-3 h-3" />
                      {cat}
                    </button>
                  );
                })}
              </div>
            </motion.div>

            {/* ─── Trending Topics Grid (Compact Cards) ─── */}
            <div className="w-full mb-4">
              {loading ? (
                /* Shimmer Loading Skeletons */
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2 sm:gap-2.5">
                  {Array.from({ length: 6 }).map((_, i) => (
                    <div
                      key={i}
                      className="p-2.5 sm:p-3 rounded-xl border border-white/[0.05] bg-white/[0.02] space-y-2 min-h-[76px]"
                    >
                      <div className="flex items-center justify-between">
                        <div className="w-14 h-3.5 rounded shimmer" />
                        <div className="w-8 h-3 rounded shimmer" />
                      </div>
                      <div className="w-full h-3.5 rounded shimmer" />
                      <div className="w-2/3 h-3 rounded shimmer" />
                    </div>
                  ))}
                </div>
              ) : filteredTopics.length === 0 ? (
                <div className="text-center py-6 text-neutral-500 text-xs font-mono">
                  No trending topics in this category right now.
                </div>
              ) : (
                <motion.div
                  layout
                  className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2 sm:gap-2.5"
                >
                  <AnimatePresence mode="popLayout">
                    {filteredTopics.map((topic, idx) => {
                      const CatIcon = CATEGORY_ICONS[topic.category] || Globe;
                      return (
                        <motion.button
                          key={topic.id}
                          layout
                          initial={{ opacity: 0, y: 10 }}
                          animate={{ opacity: 1, y: 0 }}
                          exit={{ opacity: 0, scale: 0.95 }}
                          transition={{
                            duration: 0.25,
                            delay: idx * 0.03,
                            layout: { duration: 0.2 },
                          }}
                          onClick={() => onSelectPrompt && onSelectPrompt(topic.prompt)}
                          onMouseEnter={() => setHoveredCard(topic.id)}
                          onMouseLeave={() => setHoveredCard(null)}
                          className="group relative text-left p-2.5 sm:p-3 rounded-xl glass trending-card flex flex-col justify-between min-h-[76px] transition-all hover:border-white/[0.12] hover:bg-white/[0.04]"
                        >
                          {/* Top row — category + views */}
                          <div className="flex items-center justify-between mb-1.5">
                            <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded-md text-[9px] font-mono uppercase tracking-wider text-neutral-300 bg-white/[0.05] border border-white/[0.08]">
                              <CatIcon className="w-2.5 h-2.5 text-neutral-400" />
                              {topic.category}
                            </span>

                            {topic.views > 0 && (
                              <span className="inline-flex items-center gap-1 text-[9px] font-mono text-neutral-500">
                                <Eye className="w-2.5 h-2.5" />
                                {topic.viewsFormatted}
                              </span>
                            )}
                          </div>

                          {/* Title & Arrow in single compact layout */}
                          <div className="flex items-start justify-between gap-2 mt-auto">
                            <h4 className="text-xs font-medium text-neutral-300 group-hover:text-white transition-colors leading-snug line-clamp-2">
                              {topic.title}
                            </h4>
                            <ArrowUpRight
                              className={`w-3.5 h-3.5 flex-shrink-0 transition-all duration-200 mt-0.5 ${
                                hoveredCard === topic.id
                                  ? "text-white translate-x-0.5 -translate-y-0.5"
                                  : "text-neutral-600"
                              }`}
                            />
                          </div>

                          {/* Subtle hover sheen */}
                          <div className="absolute inset-0 rounded-xl opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none bg-gradient-to-br from-white/[0.02] to-transparent" />
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
                transition={{ delay: 0.5 }}
                className="flex items-center justify-center gap-2 text-[10px] text-neutral-600 font-mono mb-4"
              >
                <TrendingUp className="w-3 h-3" />
                <span>
                  Trending topics from Wikipedia · Updated daily
                </span>
              </motion.div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default EmptyState;
