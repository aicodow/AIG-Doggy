import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import '@arco-design/web-react/dist/css/arco.css';

import Dashboard from './pages/Dashboard';
import Policies from './pages/Policies';
import AuditLogs from './pages/AuditLogs';
import Apps from './pages/Apps';
import Users from './pages/Users';
import Layout from './components/Layout';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { refetchInterval: 10000, staleTime: 5000 },
  },
});

const App: React.FC = () => (
  <QueryClientProvider client={queryClient}>
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/policies" element={<Policies />} />
          <Route path="/audit" element={<AuditLogs />} />
          <Route path="/apps" element={<Apps />} />
          <Route path="/users" element={<Users />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  </QueryClientProvider>
);

ReactDOM.createRoot(document.getElementById('root')!).render(<App />);