import { useEffect, useMemo, useState } from 'react';
import {
  createReservation, getRecommendation, getServiceAvailabilityWeek,
  getServiceSpaces, getServices, sendRecommendationAction
} from '../services/api';
import type { Recommendation, Service, ServiceSpace, Slot } from '../services/api';

function categoryOf(name: string): string {
  if (name.toLowerCase().includes('piscina')) return 'Piscines';
  if (/pàdel|padel|tennis|esquaix|futbol/i.test(name)) return 'Pistes i camps';
  if (/dirigid/i.test(name)) return 'Activitats dirigides';
  return 'Fitness i altres serveis';
}
function localISO(d: Date): string {
  return [d.getFullYear(), String(d.getMonth() + 1).padStart(2, '0'), String(d.getDate()).padStart(2, '0')].join('-');
}
function tomorrow(): string { const d = new Date(); d.setDate(d.getDate() + 1); return localISO(d); }
const DEMO_USER = 'demo-user';

export default function Reserva() {
  const [services, setServices] = useState<Service[]>([]);
  const [category, setCategory] = useState<string | null>(null);
  const [serviceId, setServiceId] = useState('');
  const [resources, setResources] = useState<ServiceSpace[]>([]);
  const [date, setDate] = useState(tomorrow);
  const [slots, setSlots] = useState<Slot[]>([]);
  const [selectedSlot, setSelectedSlot] = useState<Slot | null>(null);
  const [recommendation, setRecommendation] = useState<Recommendation | null>(null);
  const [recommendationLoading, setRecommendationLoading] = useState(false);
  const [recommendationNote, setRecommendationNote] = useState('');
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [refresh, setRefresh] = useState(0);

  const categories = useMemo(() => Array.from(new Set(services.map(s => categoryOf(s.name)))), [services]);
  const categoryServices = services.filter(s => s.reservable && categoryOf(s.name) === category);
  const currentService = services.find(s => s.id === serviceId);
  const alternative = recommendation?.recommended_slot
    ? slots.find(s => s.start === recommendation.recommended_slot?.start && s.available) ?? null
    : null;

  useEffect(() => {
    getServices().then(setServices).catch(err => setError(err instanceof Error ? err.message : String(err)));
  }, []);

  useEffect(() => {
    setResources([]);
    if (!serviceId) return;
    let cancelled = false;
    getServiceSpaces(serviceId).then(result => { if (!cancelled) setResources(result); }).catch(console.error);
    return () => { cancelled = true; };
  }, [serviceId]);

  useEffect(() => {
    setSelectedSlot(null);
    setRecommendation(null);
    setSlots([]);
    if (!serviceId || !date) return;
    let cancelled = false;
    setLoading(true);
    setError('');
    getServiceAvailabilityWeek(serviceId, date)
      .then(result => {
        if (!cancelled) setSlots(result.days.find(day => day.date === date)?.slots || []);
      })
      .catch(err => { if (!cancelled) setError(err instanceof Error ? err.message : String(err)); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [serviceId, date, refresh]);

  async function selectSlot(slot: Slot) {
    setSelectedSlot(slot);
    setRecommendation(null);
    setRecommendationNote('');
    setError('');
    setRecommendationLoading(true);
    try {
      const result = await getRecommendation({
        service_id: serviceId, date, preferred_start: slot.start, preferred_end: slot.end
      });
      setRecommendation(result);
    } catch (err) {
      setRecommendationNote(err instanceof Error ? err.message : 'No hi ha previsió disponible.');
    } finally {
      setRecommendationLoading(false);
    }
  }

  async function confirm(useAlternative: boolean) {
    const chosen = useAlternative ? alternative : selectedSlot;
    if (!chosen || !serviceId) return;
    setSubmitting(true);
    setError('');
    setMessage('');
    try {
      await createReservation({
        user_id: DEMO_USER, service_id: serviceId, date, start: chosen.start, end: chosen.end
      });
      if (recommendation?.recommendation_id) {
        await sendRecommendationAction(
          recommendation.recommendation_id,
          useAlternative ? 'accepted' : 'ignored'
        ).catch(console.warn);
      }
      setMessage('Reserva confirmada: ' + currentService?.name + ' · ' + date + ' · ' + chosen.start + '–' + chosen.end);
      setSelectedSlot(null);
      setRecommendation(null);
      setRefresh(n => n + 1);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally { setSubmitting(false); }
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-4 sm:p-8">
      <div className="max-w-5xl mx-auto space-y-8">
        <header>
          <h1 className="text-3xl font-bold bg-gradient-to-r from-emerald-400 to-cyan-400 bg-clip-text text-transparent">
            Reserva el teu Espai - SAF
          </h1>
          <p className="text-slate-400 mt-2">Selecciona l'activitat i troba una franja disponible. SAFi et pot suggerir una alternativa més tranquil·la.</p>
        </header>
        {error && <div role="alert" className="bg-red-900/40 border border-red-500 text-red-100 p-4 rounded-xl">{error}</div>}
        {message && <div role="status" className="bg-emerald-950/50 border border-emerald-500 text-emerald-200 p-4 rounded-xl">{message}</div>}

        <section className="bg-slate-900 border border-slate-800 p-6 rounded-2xl shadow-xl space-y-4">
          <h2 className="text-xl font-semibold text-emerald-400">1. Tria un Espai Principal</h2>
          {services.length === 0 && <p className="text-slate-400">Carregant els serveis del backend...</p>}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
            {categories.map(cat => (
              <button type="button" key={cat} onClick={() => { setCategory(cat); setServiceId(''); setMessage(''); }}
                className={'rounded-xl border p-4 text-left font-semibold transition-colors ' +
                  (category === cat ? 'border-emerald-500 bg-emerald-950/40 text-emerald-300' : 'border-slate-700 bg-slate-800/50 hover:border-slate-500')}>
                {cat}
              </button>
            ))}
          </div>
        </section>

        {category && <section className="bg-slate-900 border border-slate-800 p-6 rounded-2xl shadow-xl space-y-4">
          <h2 className="text-xl font-semibold text-emerald-400">2. Selecciona el Servei</h2>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            {categoryServices.map(srv => (
              <button type="button" key={srv.id} onClick={() => { setServiceId(srv.id); setMessage(''); }}
                className={'rounded-xl border p-4 text-left transition-colors ' +
                  (serviceId === srv.id ? 'border-cyan-500 bg-cyan-950/30 text-cyan-200' : 'border-slate-700 bg-slate-800/50 hover:border-slate-500')}>
                <strong>{srv.name}</strong>
                <p className="text-xs text-slate-400 mt-1">{srv.description}</p>
              </button>
            ))}
          </div>
          {currentService && <div className="pt-2">
            <p className="text-sm text-slate-300 font-semibold mb-2">Recursos inclosos en aquest servei</p>
            <div className="flex flex-wrap gap-2">
              {resources.filter(r => r.is_active).map(r => (
                <span key={r.space_id} className="rounded-lg border border-slate-700 bg-slate-800 text-slate-300 px-3 py-2 text-sm">
                  {r.resource_label}
                </span>
              ))}
            </div>
            <p className="text-xs text-slate-400 mt-3">El backend assigna automàticament un recurs lliure quan confirmes la reserva.</p>
          </div>}
        </section>}

        {currentService && <section className="bg-slate-900 border border-slate-800 p-6 rounded-2xl shadow-xl space-y-4">
          <h2 className="text-xl font-semibold text-emerald-400">3. Tria una Data</h2>
          <input aria-label="Data de reserva" type="date" value={date} min={localISO(new Date())}
            onChange={e => { setDate(e.target.value); setMessage(''); }}
            className="bg-slate-800 border border-slate-700 rounded-xl px-4 py-3 text-slate-100 focus:border-emerald-500"/>
        </section>}

        {currentService && date && <section className="bg-slate-900 border border-slate-800 p-6 rounded-2xl shadow-xl space-y-4">
          <h2 className="text-xl font-semibold text-emerald-400">4. Tria una Franja Horària</h2>
          {loading ? <p className="text-slate-400">Consultant disponibilitat...</p> :
           slots.length === 0 ? <p className="text-slate-400">No hi ha franges per a aquest dia.</p> :
           <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
             {slots.map(slot => <button type="button" key={slot.start + slot.end} disabled={!slot.available}
               onClick={() => selectSlot(slot)}
               className={'p-3 rounded-xl border text-center transition-colors ' +
                 (!slot.available ? 'border-slate-800 bg-slate-950/40 text-slate-500 cursor-not-allowed' :
                  selectedSlot?.start === slot.start ? 'border-cyan-500 bg-cyan-950/30 text-cyan-200' :
                  'border-slate-700 bg-slate-800/50 hover:border-emerald-500')}>
               <strong>{slot.start}–{slot.end}</strong>
               <span className="block text-xs mt-1">{slot.available ? 'Disponible' : 'Complet'}</span>
               {slot.available_units != null &&
                 <span className="block text-xs text-slate-400">{slot.available_units} unitats lliures</span>}
               {slot.remaining_people_capacity != null &&
                 <span className="block text-xs text-slate-400">{slot.remaining_people_capacity} places lliures</span>}
             </button>)}
           </div>}
          <p className="text-xs text-slate-400">Això és disponibilitat actual segons les reserves, no una previsió d'ocupació.</p>
        </section>}

        {selectedSlot && <section className="border border-emerald-500/40 bg-slate-900 p-6 rounded-2xl shadow-xl space-y-4">
          <h2 className="text-xl font-semibold text-emerald-400">5. Recomanació intel·ligent SAFi</h2>
          {recommendationLoading ? <p className="text-slate-400">Consultant la previsió...</p> :
           <p>{recommendation?.message || recommendationNote || 'No hi ha una previsió validada per a aquesta franja.'}</p>}
          {alternative &&
            <p className="rounded-xl bg-emerald-950/20 border border-emerald-900/50 p-4 text-emerald-300">
              Alternativa disponible: {alternative.start}–{alternative.end}
            </p>}
          {recommendation?.recommended_slot && !alternative &&
            <p className="text-sm text-slate-400">L'alternativa prevista no està disponible actualment.</p>}
          <div className="flex flex-wrap gap-3">
            <button type="button" disabled={submitting} onClick={() => confirm(false)}
              className="bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 px-5 py-3 rounded-xl font-semibold">
              Confirmar {selectedSlot.start}
            </button>
            {alternative && <button type="button" disabled={submitting} onClick={() => confirm(true)}
              className="bg-slate-700 hover:bg-slate-600 disabled:opacity-50 px-5 py-3 rounded-xl font-semibold">
              Acceptar SAFi: {alternative.start}
            </button>}
          </div>
        </section>}
      </div>
    </div>
  );
}
