/**
 * Trending Topics Service
 * Fetches trending topics from Wikipedia's free "Most Read" API.
 * Falls back to curated topics if the API is unreachable.
 */

const CATEGORIES = {
  "AI & ML": ["artificial intelligence", "machine learning", "neural", "deep learning", "chatbot", "openai", "language model", "robot", "automation", "algorithm", "compute", "gpu", "nvidia", "transformer"],
  "Science": ["physics", "chemistry", "biology", "space", "nasa", "quantum", "genome", "evolution", "particle", "telescope", "astronomy", "mars", "planet", "atom", "molecule", "climate", "fossil"],
  "Technology": ["software", "hardware", "internet", "crypto", "blockchain", "cybersecurity", "programming", "computer", "silicon", "semiconductor", "apple", "google", "microsoft", "meta", "tesla", "startup", "app"],
  "Health": ["health", "medicine", "vaccine", "disease", "cancer", "virus", "pandemic", "drug", "therapy", "brain", "mental", "surgery", "hospital", "dna", "clinical", "pharma"],
  "Business": ["economy", "market", "stock", "finance", "trade", "company", "billion", "investment", "gdp", "inflation", "bank", "revenue", "ceo", "merger", "ipo"],
  "Energy": ["energy", "solar", "wind", "battery", "nuclear", "oil", "renewable", "electric", "hydrogen", "fusion", "grid", "power", "carbon"],
};

const ALL_CATEGORY = "Trending";

/**
 * Categorize a topic based on its title and description keywords
 */
function categorize(title, extract = "") {
  const text = `${title} ${extract}`.toLowerCase();
  for (const [category, keywords] of Object.entries(CATEGORIES)) {
    if (keywords.some((kw) => text.includes(kw))) {
      return category;
    }
  }
  return "Science"; // default bucket
}

/**
 * Generate a research prompt from a topic
 */
function toResearchPrompt(title, extract) {
  if (extract && extract.length > 40) {
    return `Provide an in-depth analysis of "${title}": ${extract.slice(0, 120)}...`;
  }
  return `Conduct comprehensive research on "${title}" — cover latest developments, key facts, and future implications.`;
}

/**
 * Fetch trending topics from Wikipedia's Most Read API
 * @returns {Promise<Array>} Array of topic objects
 */
export async function fetchTrendingTopics() {
  try {
    // Get yesterday's date for the API
    const yesterday = new Date();
    yesterday.setDate(yesterday.getDate() - 1);
    const year = yesterday.getFullYear();
    const month = String(yesterday.getMonth() + 1).padStart(2, "0");
    const day = String(yesterday.getDate()).padStart(2, "0");

    const url = `https://wikimedia.org/api/rest_v1/metrics/pageviews/top/en.wikipedia/all-access/${year}/${month}/${day}`;
    const res = await fetch(url, {
      headers: { "Api-User-Agent": "DeepResearcher/1.0" },
    });

    if (!res.ok) throw new Error(`Wikipedia API returned ${res.status}`);

    const data = await res.json();
    const articles = data?.items?.[0]?.articles || [];

    // Filter out Wikipedia internal pages and boring entries
    const SKIP_PREFIXES = ["Main_Page", "Special:", "Wikipedia:", "Portal:", "Help:", "File:", "Category:", "Template:", "Talk:"];
    const SKIP_EXACT = ["Main_Page", "Search", "404.php", "undefined", "-"];

    const filtered = articles.filter((a) => {
      const title = a.article || "";
      if (SKIP_EXACT.includes(title)) return false;
      if (SKIP_PREFIXES.some((p) => title.startsWith(p))) return false;
      if (title.length < 3) return false;
      return true;
    });

    // Take top 18 articles and transform
    const topics = filtered.slice(0, 18).map((article) => {
      const title = (article.article || "").replace(/_/g, " ");
      const views = article.views || 0;
      const category = categorize(title);

      return {
        id: article.article,
        title,
        category,
        views,
        viewsFormatted: views > 1_000_000 ? `${(views / 1_000_000).toFixed(1)}M` : views > 1_000 ? `${(views / 1_000).toFixed(0)}K` : String(views),
        prompt: toResearchPrompt(title, ""),
        source: "wikipedia",
      };
    });

    return topics;
  } catch (err) {
    console.warn("Failed to fetch trending topics from Wikipedia:", err);
    return getFallbackTopics();
  }
}

/**
 * Curated fallback topics in case the API fails
 */
export function getFallbackTopics() {
  return [
    {
      id: "quantum-computing",
      title: "Quantum Error Correction Breakthroughs",
      category: "Science",
      views: 0,
      viewsFormatted: "Curated",
      prompt: "Analyze the current state of quantum error correction codes (surface codes vs LDPC) and timeline to fault-tolerant quantum advantage.",
      source: "curated",
    },
    {
      id: "moe-architectures",
      title: "Mixture-of-Experts vs Dense LLMs",
      category: "AI & ML",
      views: 0,
      viewsFormatted: "Curated",
      prompt: "Compare inference economics, routing mechanisms, and performance tradeoffs between sparse Mixture-of-Experts (MoE) and dense LLMs.",
      source: "curated",
    },
    {
      id: "solid-state-batteries",
      title: "Solid State Battery Chemistry",
      category: "Energy",
      views: 0,
      viewsFormatted: "Curated",
      prompt: "Evaluate the commercial readiness and energy density bottlenecks of lithium-metal vs silicon-anode solid state batteries.",
      source: "curated",
    },
    {
      id: "crispr-2025",
      title: "CRISPR Gene Editing Applications",
      category: "Health",
      views: 0,
      viewsFormatted: "Curated",
      prompt: "Survey the latest CRISPR-Cas9 clinical trial results and emerging therapeutic applications in oncology and genetic diseases.",
      source: "curated",
    },
    {
      id: "ai-agents",
      title: "Autonomous AI Agent Architectures",
      category: "AI & ML",
      views: 0,
      viewsFormatted: "Curated",
      prompt: "Analyze the latest architectures for autonomous AI agents — tool use, planning, memory systems, and multi-agent coordination.",
      source: "curated",
    },
    {
      id: "neuromorphic-computing",
      title: "Neuromorphic Computing Chips",
      category: "Technology",
      views: 0,
      viewsFormatted: "Curated",
      prompt: "Investigate neuromorphic computing chip designs (Intel Loihi, IBM TrueNorth) and their potential for edge AI inference.",
      source: "curated",
    },
    {
      id: "fusion-energy",
      title: "Nuclear Fusion Progress",
      category: "Energy",
      views: 0,
      viewsFormatted: "Curated",
      prompt: "Assess the latest progress in nuclear fusion — ITER, NIF, and private startups — and the realistic timeline to commercial power.",
      source: "curated",
    },
    {
      id: "longevity-science",
      title: "Anti-Aging & Longevity Research",
      category: "Health",
      views: 0,
      viewsFormatted: "Curated",
      prompt: "Review the most promising longevity interventions — senolytics, epigenetic reprogramming, and caloric restriction mimetics.",
      source: "curated",
    },
    {
      id: "space-economy",
      title: "Commercial Space Economy",
      category: "Business",
      views: 0,
      viewsFormatted: "Curated",
      prompt: "Analyze the growth of the commercial space economy — satellite constellations, space tourism, and orbital manufacturing.",
      source: "curated",
    },
  ];
}

/**
 * Get all unique categories from a list of topics
 */
export function getCategories(topics) {
  const cats = new Set(topics.map((t) => t.category));
  return [ALL_CATEGORY, ...Array.from(cats)];
}

/**
 * Filter topics by category
 */
export function filterByCategory(topics, category) {
  if (category === ALL_CATEGORY) return topics;
  return topics.filter((t) => t.category === category);
}
