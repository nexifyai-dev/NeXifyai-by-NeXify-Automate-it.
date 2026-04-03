import React, { useState, useEffect, useMemo } from 'react';
import { motion } from 'framer-motion';
import { API, LOCALE_MAP, I, track } from '../shared';

const Booking = ({ isOpen, onClose, t, lang }) => {
  const locale = LOCALE_MAP[lang] || 'de-DE';
  const fmtDate = (d) => new Date(d).toLocaleDateString(locale, { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' });
  const fmtDateShort = (d) => new Date(d).toLocaleDateString(locale, { weekday: 'short', day: 'numeric', month: 'short' });

  const [step, setStep] = useState(1);
  const [date, setDate] = useState('');
  const [time, setTime] = useState('');
  const [slots, setSlots] = useState([]);
  const [form, setForm] = useState({ vorname: '', nachname: '', email: '', telefon: '', unternehmen: '', thema: '' });
  const [errors, setErrors] = useState({});
  const [busy, setBusy] = useState(false);
  const [ok, setOk] = useState(null);
  const dates = useMemo(() => { const d = []; const now = new Date(); for (let i = 1; i <= 14; i++) { const x = new Date(now); x.setDate(now.getDate() + i); if (x.getDay() !== 0 && x.getDay() !== 6) d.push(x.toISOString().split('T')[0]); } return d; }, []);
  useEffect(() => { if (date) { fetch(`${API}/api/booking/slots?date=${date}`).then(r => r.json()).then(d => setSlots(d.slots || [])).catch(() => setSlots(['09:00','10:00','11:00','14:00','15:00','16:00'])); } }, [date]);
  useEffect(() => { if (isOpen) { document.body.style.overflow = 'hidden'; track('booking_modal_opened'); } return () => { document.body.style.overflow = ''; }; }, [isOpen]);
  const v = () => { const e = {}; if (form.vorname.trim().length < 2) e.vorname = t.booking.validation.firstName; if (form.nachname.trim().length < 2) e.nachname = t.booking.validation.lastName; if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)) e.email = t.booking.validation.email; setErrors(e); return !Object.keys(e).length; };
  const submit = async () => {
    if (!v()) return; setBusy(true); track('booking_submit', { date, time });
    try {
      const r = await fetch(`${API}/api/booking`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ ...form, date, time }) });
      const d = await r.json();
      if (r.ok) { setOk(d); track('calendar_booked', { id: d.booking_id }); } else throw new Error(d.detail);
    } catch (e) { setErrors({ submit: e.message || 'Booking failed' }); } finally { setBusy(false); }
  };
  if (!isOpen) return null;
  return (
    <div className="booking-overlay" onClick={e => e.target === e.currentTarget && onClose()} role="dialog" aria-modal="true" aria-labelledby="book-t" data-testid="booking-modal">
      <motion.div className="booking-modal" initial={{ opacity: 0, scale: 0.95, y: 20 }} animate={{ opacity: 1, scale: 1, y: 0 }} transition={{ duration: 0.3 }}>
        <button className="booking-close" onClick={onClose} aria-label="Close" data-testid="booking-close"><I n="close" /></button>
        {ok ? (
          <div className="booking-success" data-testid="booking-success"><I n="check_circle" c="booking-success-icon" /><h2>{t.booking.successTitle}</h2><p>{fmtDate(date)} — {time}</p><p>{t.booking.successText.replace('{email}', form.email)}</p><button className="btn btn-primary btn-glow" onClick={onClose}>{t.booking.close}</button></div>
        ) : (
          <>
            <h2 id="book-t" className="booking-title">{t.booking.title}</h2>
            <div className="booking-steps">{t.booking.steps.map((s, i) => <div key={i} className={`booking-step-ind ${step >= i + 1 ? 'active' : ''}`}>{i + 1}. {s}</div>)}</div>
            {step === 1 && (
              <div className="booking-step" data-testid="booking-step-1">
                <h3>{t.booking.selectDate}</h3>
                <div className="booking-dates">{dates.map(d => <button key={d} className={`booking-date ${date === d ? 'sel' : ''}`} onClick={() => setDate(d)} data-testid={`booking-date-${d}`}>{fmtDateShort(d)}</button>)}</div>
                {date && <><h3>{t.booking.selectTime}</h3><div className="booking-times">{slots.length > 0 ? slots.map(s => <button key={s} className={`booking-time ${time === s ? 'sel' : ''}`} onClick={() => setTime(s)} data-testid={`booking-time-${s}`}>{s}</button>) : <p style={{ color: 'var(--nx-muted)' }}>{t.booking.noTimes}</p>}</div></>}
                <button className="btn btn-primary btn-glow booking-next" disabled={!date || !time} onClick={() => setStep(2)} data-testid="booking-next">{t.booking.next} <I n="arrow_forward" /></button>
              </div>
            )}
            {step === 2 && (
              <div className="booking-step" data-testid="booking-step-2">
                <button className="booking-back" onClick={() => setStep(1)}><I n="arrow_back" /> {t.booking.back}</button>
                <div className="booking-selected"><I n="event" /><span>{fmtDate(date)} — {time}</span></div>
                <div className="booking-form">
                  <div className="form-row">
                    <div className="form-group"><label htmlFor="b-vn" className="form-label">{t.booking.firstName} *</label><input type="text" id="b-vn" className={`form-input ${errors.vorname ? 'error' : ''}`} value={form.vorname} onChange={e => setForm({ ...form, vorname: e.target.value })} data-testid="booking-vorname" /></div>
                    <div className="form-group"><label htmlFor="b-nn" className="form-label">{t.booking.lastName} *</label><input type="text" id="b-nn" className={`form-input ${errors.nachname ? 'error' : ''}`} value={form.nachname} onChange={e => setForm({ ...form, nachname: e.target.value })} data-testid="booking-nachname" /></div>
                  </div>
                  <div className="form-group"><label htmlFor="b-em" className="form-label">{t.booking.email} *</label><input type="email" id="b-em" className={`form-input ${errors.email ? 'error' : ''}`} value={form.email} onChange={e => setForm({ ...form, email: e.target.value })} data-testid="booking-email" /></div>
                  <div className="form-row">
                    <div className="form-group"><label htmlFor="b-tel" className="form-label">{t.booking.phone}</label><input type="tel" id="b-tel" className="form-input" value={form.telefon} onChange={e => setForm({ ...form, telefon: e.target.value })} /></div>
                    <div className="form-group"><label htmlFor="b-co" className="form-label">{t.booking.company}</label><input type="text" id="b-co" className="form-input" value={form.unternehmen} onChange={e => setForm({ ...form, unternehmen: e.target.value })} /></div>
                  </div>
                  <div className="form-group"><label htmlFor="b-th" className="form-label">{t.booking.message}</label><input type="text" id="b-th" className="form-input" value={form.thema} onChange={e => setForm({ ...form, thema: e.target.value })} /></div>
                  {errors.submit && <div className="form-error">{errors.submit}</div>}
                  <button className="btn btn-primary btn-glow booking-submit" onClick={submit} disabled={busy} data-testid="booking-submit">{busy ? <><span className="spinner"></span></> : t.booking.submit}</button>
                </div>
              </div>
            )}
          </>
        )}
      </motion.div>
    </div>
  );
};

export default Booking;
