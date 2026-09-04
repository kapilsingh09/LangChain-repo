import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Layout } from './components/layout/Layout';
import { HomePage } from './pages/HomePage';
import { ResearchPage } from './pages/ResearchPage';

function MockPage({ title }) {
  return (
    <div className="flex flex-col items-center justify-center h-full p-8 text-center animate-in fade-in duration-500">
      <div className="w-16 h-16 bg-surface border border-border rounded-2xl flex items-center justify-center mb-4">
         <span className="text-2xl text-text-muted">🚧</span>
      </div>
      <h2 className="text-2xl font-semibold text-text-main mb-2">{title}</h2>
      <p className="text-text-muted max-w-md">
        This feature is part of the premium workspace experience but requires additional backend endpoints to be fully functional.
      </p>
    </div>
  );
}

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<HomePage />} />
          <Route path="research" element={<ResearchPage />} />
          <Route path="history" element={<MockPage title="Research History" />} />
          <Route path="saved" element={<MockPage title="Saved Reports" />} />
          <Route path="sources" element={<MockPage title="Sources Library" />} />
          <Route path="settings" element={<MockPage title="Workspace Settings" />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </Router>
  );
}

export default App;
