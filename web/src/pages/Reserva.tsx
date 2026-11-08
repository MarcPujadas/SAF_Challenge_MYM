import React, { useEffect, useState } from 'react';
import { getServices, getAvailability, getRecommendation, sendRecommendationAction, createReservation } from '../services/api';
import type { Service } from '../services/api';

export default function Reserva() {
  const [services, setServices] = useState<Service[]>([]);
  const [selectedParentCategory, setSelectedParentCategory] = useState<string | null>(null);
  const [selectedService, setSelectedService] = useState<Service | null>(null);
  const [date, setDate] = useState<string>('');
  const [slots, setSlots] = useState<any[]>([]);
  const [selectedSlot, setSelectedSlot] = useState<string | null>(null);
  
  // Per a la recomanació de SAFi
  const [recommendation, setRecommendation] = useState<any>(null);
  const [loadingRec, setLoadingRec] = useState<boolean>(false);
  
  // Missatges d'estat
  const [message, setMessage] = useState<string>('');
  const [error, setError] = useState<string>('');

  // Carregar serveis en iniciar
  useEffect(() => {
    getServices()
      .then((data) => {
        if (Array.isArray(data)) {
          setServices(data);
        } else if (data && Array.isArray((data as any).services)) {
          setServices((data as any).services);
        } else {
          setServices([]);
        }
      })
      .catch((err) => {
        console.error("Error carregant serveis:", err);
        setError('Error al carregar els serveis del backend');
      });
  }, []);

  // Helper per agrupar la llista plana en categories d'Espais Pares
  const getParentCategory = (name: string) => {
    if (name.includes('Poliesportiu')) return 'Poliesportiu';
    if (name.includes('Piscina 25m')) return 'Piscina 25 metres';
    if (name.includes('Pàdel')) return 'Pistes de pàdel';
    if (name.includes('Futbol 7')) return 'Futbol 7';
    if (name.includes('Activitats dirigides')) return 'Sales activitats dirigides';
    if (name.includes('Tennis')) return 'Tennis';
    return name.split(' - ')[0]; // Retorna l'espai pare per defecte
  };

  const safeServices = Array.isArray(services) ? services : [];
  
  // Llista d'espais pares únics
  const parentCategories = Array.from(new Set(safeServices.map((s) => getParentCategory(s.name))));

  // Subespais/pistes de la categoria seleccionada
  const filteredSubspaces = selectedParentCategory
    ? safeServices.filter((s) => getParentCategory(s.name) === selectedParentCategory)
    : [];

  // Quan canvia el servei o la data, consultar disponibilitat
  const handleFetchAvailability = async (srv: Service, dt: string) => {
    if (!dt) return;
    try {
      setError('');
      const data = await getAvailability(srv.space_id, dt);
      setSlots(data.slots || []);
    } catch (err: any) {
      setError(err.message || 'Error al carregar disponibilitat');
    }
  };

  // Demanar recomanació a SAFi quan es tria una franja
  const handleSelectSlot = async (slotTime: string) => {
    setSelectedSlot(slotTime);
    setRecommendation(null);
    if (!selectedService || !date) return;

    try {
      setLoadingRec(true);
      const rec = await getRecommendation({
        user_id: 'demo-user',
        basis: {
          space_id: selectedService.space_id,
          weekday: new Date(date).toLocaleDateString('en-US', { weekday: 'long' }),
        },
        requested_start: slotTime,
      });
      setRecommendation(rec);
    } catch (err) {
      console.error('Error al obtenir recomanació SAFi', err);
    } finally {
      setLoadingRec(false);
    }
  };

  // Confirmar la reserva realment contra el backend
  const handleMakeReservation = async (useRecommended: boolean = false) => {
    if (!selectedService || !date) return;

    const startTime = useRecommended && recommendation ? recommendation.recommended_start : selectedSlot;
    if (!startTime) return;

    const [hours, minutes] = startTime.split(':').map(Number);
    const startDate = new Date();
    startDate.setHours(hours, minutes + 75);
    const endTime = `${String(startDate.getHours()).padStart(2, '0')}:${String(startDate.getMinutes()).padStart(2, '0')}`;

    try {
      setError('');
      setMessage('');

      // 1. Registrar l'acció de la recomanació si s'escau
      if (recommendation) {
        try {
          const actionType = useRecommended ? 'accepted' : 'ignored';
          const recId = recommendation.recommendation_id || recommendation.id || recommendation._id || 'rec-1';
          await sendRecommendationAction(recId, actionType);
        } catch (errRec) {
          console.warn("Avís en registrar l'acció de recomanació:", errRec);
        }
      }

      // 2. Crear la reserva real a la base de dades
      await createReservation({
        space_id: selectedService.space_id,
        user_id: 'demo-user',
        date: date,
        start_time: startTime,
        end_time: endTime,
      });

      setMessage('¡Reserva creada amb èxit i guardada a la base de dades!');
      setSelectedSlot(null);
      setRecommendation(null);
    } catch (err: any) {
      setError(err.message || 'Error al crear la reserva');
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-8">
      <div className="max-w-4xl mx-auto space-y-8">
        <div>
          <h1 className="text-3xl font-bold bg-gradient-to-r from-emerald-400 to-cyan-400 bg-clip-text text-transparent">
            Reserva el teu Espai - SAF
          </h1>
          <p className="text-slate-400">Selecciona un espai principal i tria la pista o carrer disponible.</p>
        </div>

        {error && <div className="bg-red-900/50 border border-red-500 text-red-200 p-4 rounded-xl">{error}</div>}
        {message && <div className="bg-emerald-900/50 border border-emerald-500 text-emerald-200 p-4 rounded-xl">{message}</div>}

        {/* 1. Seleccionar Categoria d'Espai Pare */}
        <div className="bg-slate-900 border border-slate-800 p-6 rounded-2xl shadow-xl space-y-4">
          <h2 className="text-xl font-semibold text-emerald-400">1. Tria un Espai Principal</h2>
          {safeServices.length === 0 ? (
            <p className="text-sm text-slate-400">Carregant serveis del backend...</p>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              {parentCategories.map((cat) => (
                <button
                  key={cat}
                  onClick={() => {
                    setSelectedParentCategory(cat);
                    setSelectedService(null);
                    setSlots([]);
                    setSelectedSlot(null);
                  }}
                  className={`p-4 rounded-xl border text-left transition-all ${
                    selectedParentCategory === cat
                      ? 'border-emerald-500 bg-emerald-950/30 text-emerald-300 shadow-lg'
                      : 'border-slate-800 bg-slate-800/50 hover:border-slate-700'
                  }`}
                >
                  <div className="font-bold text-lg">{cat}</div>
                  <div className="text-xs text-slate-400 mt-1">
                    {safeServices.filter((s) => getParentCategory(s.name) === cat).length} opcions disponibles
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* 2. Seleccionar Subespai / Pista corresponent */}
        {selectedParentCategory && (
          <div className="bg-slate-900 border border-slate-800 p-6 rounded-2xl shadow-xl space-y-4">
            <h2 className="text-xl font-semibold text-emerald-400">
              2. Selecciona Pista / Subespai de "{selectedParentCategory}"
            </h2>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              {filteredSubspaces.map((srv) => (
                <button
                  key={srv.id}
                  onClick={() => {
                    setSelectedService(srv);
                    if (date) handleFetchAvailability(srv, date);
                  }}
                  className={`p-4 rounded-xl border text-left transition-all ${
                    selectedService?.id === srv.id
                      ? 'border-cyan-500 bg-cyan-950/30 text-cyan-300 shadow-md'
                      : 'border-slate-800 bg-slate-800/50 hover:border-slate-700'
                  }`}
                >
                  <div className="font-bold">{srv.name}</div>
                  <div className="text-xs text-slate-400 mt-1">{srv.description || `Espai: ${srv.space_id}`}</div>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* 3. Seleccionar Data */}
        {selectedService && (
          <div className="bg-slate-900 border border-slate-800 p-6 rounded-2xl shadow-xl space-y-4">
            <h2 className="text-xl font-semibold">3. Tria una Data</h2>
            <input
              type="date"
              value={date}
              onChange={(e) => {
                setDate(e.target.value);
                handleFetchAvailability(selectedService, e.target.value);
              }}
              className="bg-slate-800 border border-slate-700 rounded-xl px-4 py-2 text-slate-100 focus:outline-none focus:border-emerald-500"
            />
          </div>
        )}

        {/* 4. Seleccionar Franja Horària */}
        {slots.length > 0 && (
          <div className="bg-slate-900 border border-slate-800 p-6 rounded-2xl shadow-xl space-y-4">
            <h2 className="text-xl font-semibold">4. Tria una Franja Horària</h2>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              {slots.map((slot, idx) => {
                const timeText = slot.start_time || slot.time || slot.hour || `Franja ${idx + 1}`;
                const scoreVal = slot.occupancy_score ?? slot.score ?? slot.points ?? '15';

                return (
                  <button
                    key={idx}
                    onClick={() => handleSelectSlot(timeText)}
                    className={`p-3 rounded-xl border text-center transition-all ${
                      selectedSlot === timeText
                        ? 'border-cyan-500 bg-cyan-950/30 text-cyan-300'
                        : 'border-slate-800 bg-slate-800/50 hover:border-slate-700'
                    }`}
                  >
                    <div className="font-mono font-bold">{timeText}</div>
                    <div className="text-xs text-slate-400 mt-1">Score: {scoreVal}</div>
                  </button>
                );
              })}
            </div>
          </div>
        )}

        {/* 5. Recomanació SAFi i Confirmació */}
        {(selectedSlot || loadingRec) && (
          <div className="bg-slate-900 border border-emerald-500/40 p-6 rounded-2xl shadow-xl space-y-4">
            <h2 className="text-xl font-semibold text-emerald-400">🤖 Recomanació intel·ligent SAFi</h2>
            {loadingRec ? (
              <p className="text-slate-400">Analitzant hores òptimes...</p>
            ) : recommendation ? (
              <div className="bg-emerald-950/20 border border-emerald-900/50 p-4 rounded-xl space-y-2">
                <p className="text-sm">{recommendation.reason}</p>
                <p className="text-xs text-slate-400">
                  Franja recomanada per evitar aglomeracions: <strong className="text-emerald-300">{recommendation.recommended_start}</strong>
                </p>
                <div className="flex gap-4 pt-2">
                  <button
                    onClick={() => handleMakeReservation(true)}
                    className="bg-emerald-600 hover:bg-emerald-500 text-white px-4 py-2 rounded-xl font-medium transition-colors"
                  >
                    Acceptar recomanació ({recommendation.recommended_start || 'Òptima'})
                  </button>
                  <button
                    onClick={() => handleMakeReservation(false)}
                    className="bg-slate-800 hover:bg-slate-700 text-slate-300 px-4 py-2 rounded-xl font-medium transition-colors"
                  >
                    Mantenir la meva hora ({selectedSlot})
                  </button>
                </div>
              </div>
            ) : (
              <div className="space-y-4">
                <p className="text-slate-400">Hora seleccionada: <strong className="text-white">{selectedSlot}</strong></p>
                <button
                  onClick={() => handleMakeReservation(false)}
                  className="bg-emerald-600 hover:bg-emerald-500 text-white px-6 py-2.5 rounded-xl font-medium transition-colors"
                >
                  Confirmar Reserva ({selectedService?.name})
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}