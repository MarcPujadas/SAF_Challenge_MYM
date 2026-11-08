// web/src/App.tsx
import { useState } from 'react';
import AdminDashboard from './pages/AdminDashboard';
import Reserva from './pages/Reserva';

export default function App() {
  const [currentView, setCurrentView] = useState<'admin' | 'reserva'>('reserva');

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <nav className="bg-slate-900 border-b border-slate-800 px-6 py-4 flex justify-between items-center">
        <div className="font-bold text-lg bg-gradient-to-r from-emerald-400 to-cyan-400 bg-clip-text text-transparent">
          SAF Portal Web
        </div>
        <div className="flex gap-4">
          <button
            onClick={() => setCurrentView('reserva')}
            className={`px-4 py-2 rounded-xl text-sm font-medium transition-colors ${
              currentView === 'reserva'
                ? 'bg-emerald-600 text-white'
                : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
            }`}
          >
            Fes una Reserva
          </button>
          <button
            onClick={() => setCurrentView('admin')}
            className={`px-4 py-2 rounded-xl text-sm font-medium transition-colors ${
              currentView === 'admin'
                ? 'bg-emerald-600 text-white'
                : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
            }`}
          >
            Admin Dashboard
          </button>
        </div>
      </nav>

      <main>
        {currentView === 'admin' ? <AdminDashboard /> : <Reserva />}
      </main>
    </div>
  );
}