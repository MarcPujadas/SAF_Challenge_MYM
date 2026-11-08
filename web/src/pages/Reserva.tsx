import {useEffect,useState} from 'react';
import {createReservation,getRecommendation,getServiceAvailabilityWeek,getServices,sendRecommendationAction} from '../services/api';
import type {Recommendation,Service,Slot} from '../services/api';
export default function Reserva(){
 const [services,setServices]=useState<Service[]>([]),[service,setService]=useState(''),[date,setDate]=useState(() => new Date(Date.now()+86400000).toLocaleDateString('en-CA'));
 const [slots,setSlots]=useState<Slot[]>([]),[selected,setSelected]=useState<Slot|null>(null),[rec,setRec]=useState<Recommendation|null>(null);
 const [error,setError]=useState(''),[message,setMessage]=useState(''),[busy,setBusy]=useState(false),[loading,setLoading]=useState(false);
 useEffect(()=>{getServices().then(setServices).catch(e=>setError(String(e)));},[]);
 useEffect(()=>{setSlots([]);setSelected(null);setRec(null);if(!service||!date)return;setLoading(true);getServiceAvailabilityWeek(service,date).then(v=>setSlots(v.days.find(x=>x.date===date)?.slots||[])).catch(e=>setError(e.message)).finally(()=>setLoading(false));},[service,date]);
 async function choose(slot:Slot){setSelected(slot);setRec(null);setError('');try{setRec(await getRecommendation({service_id:service,date,preferred_start:slot.start,preferred_end:slot.end}));}catch(e){setError((e as Error).message);}}
 async function reserve(useRec:boolean){if(!selected)return;setBusy(true);setError('');setMessage('');const start=useRec&&rec?.recommended_slot?.start?rec.recommended_slot.start:selected.start;
 // Keep the duration of the original available slot; the backend validates the final slot.
 const minutes=(t:string)=>Number(t.split(':')[0])*60+Number(t.split(':')[1]);
 const len=minutes(selected.end)-minutes(selected.start);const endMin=minutes(start)+len;
 const end=String(Math.floor(endMin/60)).padStart(2,'0')+':'+String(endMin%60).padStart(2,'0');
 try{await createReservation({user_id:'demo-user',service_id:service,date,start,end});if(rec?.recommendation_id)await sendRecommendationAction(rec.recommendation_id,useRec?'accepted':'ignored').catch(console.warn);
 setMessage('Reserva confirmada correctament: '+date+' '+start);setRec(null);setSelected(null);
 const fresh=await getServiceAvailabilityWeek(service,date);setSlots(fresh.days.find(x=>x.date===date)?.slots||[]);
 }catch(e){setError((e as Error).message);}finally{setBusy(false);}
 }
 return <div className="min-h-screen bg-slate-950 text-slate-100 p-6"><div className="max-w-5xl mx-auto space-y-6">
 <h1 className="text-3xl font-bold text-emerald-400">Reserva el teu espai</h1>
 <p className="text-slate-400">Tria un servei, consulta la disponibilitat real i deixa't orientar per SAFi.</p>
 {error&&<div className="p-4 rounded-xl bg-red-900/40 border border-red-700" role="alert">{error}</div>}
 {message&&<div className="p-4 rounded-xl bg-emerald-900/40 border border-emerald-700">{message}</div>}
 <div className="grid md:grid-cols-2 gap-4"><label className="bg-slate-900 rounded-2xl p-5">Servei
 <select className="block bg-slate-800 w-full mt-3 p-3 rounded-lg" value={service} onChange={e=>setService(e.target.value)}>
 <option value="">Selecciona un servei</option>{services.filter(s=>s.reservable).map(s=><option key={s.id} value={s.id}>{s.name}</option>)}</select></label>
 <label className="bg-slate-900 rounded-2xl p-5">Data
 <input type="date" className="block bg-slate-800 w-full mt-3 p-3 rounded-lg" value={date} onChange={e=>setDate(e.target.value)}/></label></div>
 {loading&&<p>Consultant disponibilitat...</p>}
 {service&&!loading&&<section className="bg-slate-900 rounded-2xl p-5"><h2 className="font-bold text-xl mb-4">Franges disponibles</h2>
 {slots.length===0?<p className="text-slate-400">No hi ha franges per aquest dia.</p>:
 <div className="grid grid-cols-2 md:grid-cols-5 gap-3">{slots.map(s=><button disabled={!s.available} key={s.start+s.end} onClick={()=>choose(s)}
 className={'rounded-xl border p-3 text-left '+(!s.available?'opacity-35 border-slate-700':selected?.start===s.start?'bg-emerald-700 border-emerald-400':'bg-slate-800 border-slate-700 hover:border-emerald-400')}>
 <strong>{s.start}–{s.end}</strong><div className="text-xs mt-1">{s.available?'Disponible':'Completa'}</div></button>)}</div>}
 <p className="text-xs text-slate-400 mt-4">Disponibilitat operativa actual. No és una predicció d'ocupació.</p></section>}
 {selected&&<section className="border border-emerald-700 bg-slate-900 rounded-2xl p-5 space-y-3">
 <h2 className="text-xl text-emerald-400 font-bold">SAFi recomana</h2><p>{rec?.message||'Preparant recomanació...'}</p>
 {rec?.recommended_slot&&<p className="text-emerald-300">Alternativa: {rec.recommended_slot.start}</p>}
 <div className="flex gap-3 flex-wrap"><button disabled={busy} onClick={()=>reserve(false)} className="bg-emerald-600 px-5 py-3 rounded-xl disabled:opacity-50">Reservar {selected.start}</button>
 {rec?.recommended_slot&&<button disabled={busy} onClick={()=>reserve(true)} className="bg-slate-700 px-5 py-3 rounded-xl disabled:opacity-50">Reservar {rec.recommended_slot.start}</button>}</div>
 </section>}</div></div>;
}
