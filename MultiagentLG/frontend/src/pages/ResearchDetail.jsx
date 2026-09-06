import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { Header } from "../components/layout/Header";
import { Sidebar } from "../components/layout/Sidebar";
import { ResearchReport } from "../components/research/ResearchReport";
import { LoadingSkeleton } from "../components/common/LoadingSkeleton";
import { useAuth } from "../hooks/useAuth";
import { getResearchById } from "../services/api";
import { ArrowLeft, AlertTriangle } from "lucide-react";

export const ResearchDetail = () => {
  const { id } = useParams();
  const { getIdToken } = useAuth();
  const navigate = useNavigate();

  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [researchData, setResearchData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let isMounted = true;

    const fetchDetail = async () => {
      setLoading(true);
      setError(null);
      try {
        const token = await getIdToken();
        if (!token) throw new Error("Authentication required");
        const data = await getResearchById(id, token);
        if (isMounted) {
          setResearchData(data);
        }
      } catch (err) {
        if (isMounted) {
          setError(err.message || "Failed to load research report");
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    };

    fetchDetail();

    return () => {
      isMounted = false;
    };
  }, [id, getIdToken]);

  return (
    <div className="flex h-screen bg-[#0a0a0a] text-[#f5f5f5] overflow-hidden">
      {/* Sidebar */}
      <Sidebar
        isOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
        onNewResearch={() => navigate("/")}
      />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 h-full overflow-hidden">
        <Header onToggleSidebar={() => setSidebarOpen(!sidebarOpen)} />

        <main className="flex-1 overflow-y-auto px-4 sm:px-8 py-6">
          <div className="max-w-4xl mx-auto space-y-6">
            {/* Back Button */}
            <button
              onClick={() => navigate("/")}
              className="inline-flex items-center gap-1.5 text-xs text-neutral-400 hover:text-white transition-colors"
            >
              <ArrowLeft className="w-4 h-4" />
              <span>Back to Workspace</span>
            </button>

            {loading && (
              <div className="p-8 rounded-2xl bg-[#111111] border border-neutral-800">
                <LoadingSkeleton lines={8} />
              </div>
            )}

            {error && (
              <div className="p-8 rounded-2xl bg-neutral-900/60 border border-neutral-800 text-center space-y-4">
                <div className="w-12 h-12 rounded-full bg-red-500/10 text-red-400 flex items-center justify-center mx-auto">
                  <AlertTriangle className="w-6 h-6" />
                </div>
                <h3 className="text-lg font-medium text-white">Report Not Found</h3>
                <p className="text-sm text-neutral-400 max-w-sm mx-auto">
                  {error || "The requested research document could not be retrieved or is restricted."}
                </p>
                <button
                  onClick={() => navigate("/")}
                  className="px-4 py-2 rounded-xl bg-white hover:bg-neutral-200 text-black text-xs font-semibold shadow-md shadow-white/10 transition-all active:scale-[0.98]"
                >
                  Start New Inquiry
                </button>
              </div>
            )}

            {!loading && !error && researchData && (
              <ResearchReport
                report={researchData.final_report}
                question={researchData.question}
                webSearchPerformed={researchData.web_search_performed}
                critique={researchData.critique}
                createdAt={researchData.created_at}
              />
            )}
          </div>
        </main>
      </div>
    </div>
  );
};

export default ResearchDetail;
