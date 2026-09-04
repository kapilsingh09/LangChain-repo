import { useNavigate } from 'react-router-dom';
import { ResearchInput } from '../components/research/ResearchInput';

export function HomePage() {
  const navigate = useNavigate();

  const handleStartResearch = (question) => {
    // Navigate to the research page with the question in state
    navigate('/research', { state: { question } });
  };

  return (
    <div className="w-full h-full flex flex-col items-center justify-center p-6 bg-[url('/grid-pattern.svg')] bg-center">
      <ResearchInput onSubmit={handleStartResearch} />
    </div>
  );
}
