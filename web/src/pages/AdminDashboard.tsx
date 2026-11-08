import type { ReactNode } from 'react';
import { useEffect, useState } from 'react';
import { fetchAdminSummary, fetchAdminReservations } from '../services/api';
import { Activity, Calendar, Clock, TrendingUp } from 'lucide-react';

export default function AdminDashboard() {
  const [summary, setSummary] = useState<any>(null);
  const [reservations, setReservations] = useState<any[]>([]);
  const [connection, setConnection] = useState<'loading' | 'connected' | 'error'>('loading');
  const [error, setError] = useState('');

  useEffect(() => {
    let active = true;
    Promise.all([fetchAdminSummary(), fetchAdminReservations()])
      .then(([s, rows]) => {
        if (!active) return;
        setSummary(s);
        setReservations(Array.isArray(rows) ? rows : (rows?.reservations ?? []));
        setConnection('connected');
      })
      .catch((err) => {
        if (!active) return;
        setConnection('error');
        setError(err instanceof Error ? err.message : String(err));
      });
    return () => { active = false; };
  }, []);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-8">
      {/* Header */}
      <div className="flex justify-between items-center mb-8 border-b border-slate-800 pb-5">
        <div>
          <h1 className="text-3xl font-bold bg-gradient-to-r from-green-400 to-emerald-600 bg-clip-text text-transparent">
            SAF Admin Dashboard
          </h1>
          <p className="text-slate-400 text-sm mt-1">Gestió unificada d'ocupació i reserves</p>
        </div>
        <span className="px-3 py-1 bg-green-500/10 text-green-400 border border-green-500/20 rounded-full text-xs font-semibold">
          {connection === 'connected' ? 'Connectat al backend' : connection === 'loading' ? 'Connectant...' : 'Error de connexió'}
        </span>
      </div>

      {connection === 'error' && (
        <div role="alert" className="border border-red-500 bg-red-950/30 text-red-200 p-4 rounded-xl">
          No s'han pogut carregar les dades: {error}
        </div>
      )}

      {/* Grid de KPIs */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <KpiCard icon={<Calendar className="text-green-400" />} title="Total Reserves" value={summary?.total_reservations ?? '0'} />
        <KpiCard icon={<Clock className="text-emerald-400" />} title="Reserves d'Avui" value={summary?.reservations_today ?? '0'} />
        <KpiCard icon={<Activity className="text-teal-400" />} title="Espai Més Sol·licitat" value={summary?.busiest_space?.name ?? 'N/A'} />
        <KpiCard icon={<TrendingUp className="text-cyan-400" />} title="Hora Punta" value={summary?.busiest_hour ?? 'N/A'} />
      </div>

      {/* Taula de Reserves */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl">
        <h2 className="text-xl font-bold mb-4 text-slate-200">Reserves del Sistema (App + Web)</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-slate-300">
            <thead className="bg-slate-800/50 text-slate-400 text-xs uppercase tracking-wider">
              <tr>
                <th className="p-4 rounded-l-lg">ID</th>
                <th className="p-4">Espai</th>
                <th className="p-4">Data</th>
                <th className="p-4">Hora</th>
                <th className="p-4 rounded-r-lg">Estat</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/50 text-sm">
              {reservations.length === 0 && (
                <tr><td colSpan={5} className="p-4 text-center text-slate-400">
                  {connection === 'loading' ? 'Carregant reserves...' : 'No hi ha reserves actives.'}
                </td></tr>
              )}
              {reservations.map((res: any) => (
                <tr key={res.reservation_id} className="hover:bg-slate-800/30 transition">
                  <td className="p-4 font-mono text-slate-400">{res.id}</td>
                  <td className="p-4 font-medium text-slate-200">{res.space_id}</td>
                  <td className="p-4">{res.date}</td>
                  <td className="p-4">{res.start}</td>
                  <td className="p-4">
                    <span className="px-2.5 py-1 bg-emerald-500/10 text-emerald-400 rounded-full text-xs border border-emerald-500/20">
                      {res.status || 'Confirmada'}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

function KpiCard({ icon, title, value }: { icon: ReactNode; title: string; value: string | number }) {
  return (
    <div className="bg-slate-900 border border-slate-800 p-6 rounded-2xl flex items-center gap-4 hover:border-slate-700 transition">
      <div className="p-3 bg-slate-800 rounded-xl">{icon}</div>
      <div>
        <p className="text-slate-400 text-xs font-medium">{title}</p>
        <p className="text-2xl font-bold text-slate-100 mt-1">{value}</p>
      </div>
    </div>
  );
}