import { useState } from 'react';
import AdminDashboard from './pages/AdminDashboard';
import AdminInsights from './pages/AdminInsights';
import Reserva from './pages/Reserva';

type View = 'admin' | 'reserva' | 'insights';
export default function App() {
  const [currentView, setCurrentView] = useState<View>('admin');
  const tabs: Array<{ id: View; title: string }> = [
    { id: 'admin', title: 'Dashboard SAF' },
    { id: 'insights', title: 'SAFi Insights' },
    { id: 'reserva', title: 'Fes una reserva' },
  ];
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <nav aria-label="Navegació SAFi" className="bg-slate-900 border-b border-slate-800 px-4 md:px-6 py-4 flex flex-col sm:flex-row gap-4 justify-between items-start sm:items-center">
        <div className="font-bold text-lg bg-gradient-to-r from-emerald-400 to-cyan-400 bg-clip-text text-transparent">
          SAFi · Portal del SAF
        </div>
        <div className="flex flex-wrap gap-2">
          {tabs.map(tab => (
            <button key={tab.id} type="button" onClick={() => setCurrentView(tab.id)}
              aria-current={currentView === tab.id ? 'page' : undefined}
              className={`px-4 py-2 rounded-xl text-sm font-medium transition-colors ${currentView === tab.id ? 'bg-emerald-600 text-white' : 'bg-slate-800 text-slate-300 hover:bg-slate-700'}`}>
              {tab.title}
            </button>
          ))}
        </div>
      </nav>
      <main>
        {currentView === 'admin' ? <AdminDashboard /> : currentView === 'insights' ? <AdminInsights /> : <Reserva />}
      </main>
    </div>
  );
}
