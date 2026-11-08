import type { ReactNode } from 'react';
import { useEffect, useState } from 'react';
import { 
  fetchAdminSummary, 
  fetchAdminStats, 
  fetchAdminRecommendationsByService, 
  fetchAdminReservations, 
  fetchServices 
} from '../services/api';
import { Activity, Calendar, Clock, TrendingUp, ShieldCheck } from 'lucide-react';

export default function AdminDashboard() {
  const [summary, setSummary] = useState<any>(null);
  const [stats, setStats] = useState<any>(null);
  const [recStats, setRecStats] = useState<any>(null);
  const [reservations, setReservations] = useState<any[]>([]);
  const [services, setServices] = useState<any[]>([]);
  const [selectedSpace, setSelectedSpace] = useState<string>('');
  const [connection, setConnection] = useState<'loading' | 'connected' | 'error'>('loading');
  const [error, setError] = useState('');

  useEffect(() => {
    let cancelled = false;
    // La connexió es considera establerta només quan arriben dades reals del backend.
    Promise.all([fetchAdminSummary(), fetchAdminReservations(), fetchServices()])
      .then(([s, rows, catalog]) => {
        if (cancelled) return;
        setSummary(s);
        setReservations(Array.isArray(rows) ? rows : rows?.reservations || []);
        setServices(catalog);
        setConnection('connected');
      })
      .catch((err) => {
        if (cancelled) return;
        setConnection('error');
        setError(err instanceof Error ? err.message : String(err));
      });
    fetchAdminStats().then(value => { if (!cancelled) setStats(value); }).catch(console.error);
    fetchAdminRecommendationsByService().then(value => { if (!cancelled) setRecStats(value); }).catch(console.error);
    return () => { cancelled = true; };
  }, []);

  // Gestionar filtre per espai a les estadístiques de SAFi si cal
  const handleSpaceChange = async (spaceId: string) => {
    setSelectedSpace(spaceId);
    try {
      const data = await fetchAdminRecommendationsByService(spaceId || undefined);
      setRecStats(data);
    } catch (err) {
      console.error("Error al filtrar recomanacions:", err);
    }
  };

  const safeReservations = Array.isArray(reservations) ? reservations : [];
  const safeServices = Array.isArray(services) ? services : [];

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-8 space-y-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center border-b border-slate-800 pb-5 gap-4">
        <div>
          <h1 className="text-3xl font-bold bg-gradient-to-r from-green-400 to-emerald-600 bg-clip-text text-transparent">
            SAF Admin Dashboard
          </h1>
          <p className="text-slate-400 text-sm mt-1">Gestió unificada d'ocupació, reserves i impacte intel·ligent</p>
        </div>
        <div className="flex items-center gap-3">
          {/* Selector de serveis per filtrar */}
          <select 
            value={selectedSpace}
            onChange={(e) => handleSpaceChange(e.target.value)}
            className="bg-slate-900 border border-slate-700 text-slate-200 text-sm rounded-xl px-3 py-2 focus:outline-none focus:border-emerald-500"
          >
            <option value="">Tots els espais</option>
            {safeServices.map((srv) => (
              <option key={srv.id || srv.space_id} value={srv.id}>
                {srv.name}
              </option>
            ))}
          </select>
          <span className="px-3.5 py-1.5 bg-green-500/10 text-green-400 border border-green-500/20 rounded-full text-xs font-semibold">
            {connection === 'connected' ? 'Connectat al backend' : connection === 'loading' ? 'Connectant...' : 'Sense connexió'}
          </span>
        </div>
      </div>

      {connection === 'error' && (
        <p role="alert" className="rounded-xl border border-red-500 bg-red-950/30 p-4 text-red-200">
          No s'han pogut carregar les dades del backend: {error}
        </p>
      )}
      {/* Grid de KPIs Principals */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        <KpiCard 
          icon={<Calendar className="text-green-400" />} 
          title="Total Reserves" 
          value={summary?.total_reservations ?? stats?.total_reservations ?? '—'} 
        />
        <KpiCard 
          icon={<Clock className="text-emerald-400" />} 
          title="Reserves d'Avui" 
          value={summary?.reservations_today ?? '—'} 
        />
        <KpiCard 
          icon={<Activity className="text-teal-400" />} 
          title="Espai Més Sol·licitat" 
          value={summary?.busiest_space?.name ?? stats?.most_used_spaces?.[0]?.name ?? '—'} 
        />
        <KpiCard 
          icon={<TrendingUp className="text-cyan-400" />} 
          title="Hora Punta (Històrica)" 
          value={summary?.busiest_hour ?? stats?.busiest_hour ?? '—'} 
        />
      </div>

      {/* Secció d'Impacte de Recomanacions SAFi amb valors segurs */}
      <div className="bg-slate-900 border border-emerald-500/30 rounded-2xl p-6 shadow-xl space-y-6">
        <div className="flex items-center gap-3">
          <ShieldCheck className="text-emerald-400 w-6 h-6" />
          <h2 className="text-xl font-bold text-slate-100">Impacte de les Recomanacions Intel·ligents (SAFi)</h2>
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
          <StatBox label="Total Recomanacions" value={recStats?.total_recommendations ?? '—'} />
          <StatBox label="Acceptades" value={recStats?.accepted ?? '—'} color="text-emerald-400" />
          <StatBox label="Ignorades" value={recStats?.ignored ?? '—'} color="text-amber-400" />
          <StatBox label="% Acceptació" value={recStats ? `${recStats.acceptance_rate}%` : '—'} color="text-green-400" />
          <StatBox label="% Usuaris decideixen" value={recStats ? `${recStats.decision_rate}%` : '—'} color="text-cyan-400" />
          <StatBox label="Millora mitjana de score" value={recStats?.average_score_improvement != null ? `${recStats.average_score_improvement} pts` : '—'} color="text-teal-400" />
        </div>
      </div>

      {/* Taula de Reserves Actives */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl">
        <h2 className="text-xl font-bold mb-4 text-slate-200">Reserves Actives del Sistema</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-slate-300">
            <thead className="bg-slate-800/50 text-slate-400 text-xs uppercase tracking-wider">
              <tr>
                <th className="p-4 rounded-l-lg">ID Reserva</th>
                <th className="p-4">Espai</th>
                <th className="p-4">Data</th>
                <th className="p-4">Hora</th>
                <th className="p-4 rounded-r-lg">Estat</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/50 text-sm">
              {safeReservations.length === 0 ? (
                <tr>
                  <td colSpan={5} className="p-4 text-center text-slate-500">
                    No hi ha reserves actives registrades al sistema.
                  </td>
                </tr>
              ) : (
                safeReservations.map((res: any, idx: number) => (
                  <tr key={res.reservation_id || res.id || idx} className="hover:bg-slate-800/30 transition">
                    <td className="p-4 font-mono text-slate-400">{res.reservation_id || res.id}</td>
                    <td className="p-4 font-medium text-slate-200">{res.space_id}</td>
                    <td className="p-4">{res.date}</td>
                    <td className="p-4">{res.start || res.start_time}</td>
                    <td className="p-4">
                      <span className="px-2.5 py-1 bg-emerald-500/10 text-emerald-400 rounded-full text-xs border border-emerald-500/20">
                        {res.status || 'Confirmada'}
                      </span>
                    </td>
                  </tr>
                ))
              )}
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

function StatBox({ label, value, color = "text-white" }: { label: string; value: any; color?: string }) {
  return (
    <div className="bg-slate-950/50 border border-slate-800 p-4 rounded-xl">
      <p className="text-xs text-slate-400">{label}</p>
      <p className={`text-xl font-bold mt-1 ${color}`}>{value ?? 0}</p>
    </div>
  );
}