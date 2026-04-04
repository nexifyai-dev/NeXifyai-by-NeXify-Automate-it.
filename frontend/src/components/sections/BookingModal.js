import React, { useState, useEffect, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
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

  const dates = useMemo(() => {
    const d = [];
    const now = new Date();
    for (let i = 1; i <= 14; i++) {
      const x = new Date(now);
      x.setDate(now.getDate() + i);
      if (x.getDay() !== 0 && x.getDay() !== 6) d.push(x.toISOString().split('T')[0]);
    }
    return d;
  }, []);

  useEffect(() => {
    if (date) {
      fetch(`${API}/api/booking/slots?date=${date}`)
        .then(r => r.json())
        .then(d => setSlots(d.slots || []))
        .catch(() => setSlots(['09:00', '10:00', '11:00', '14:00', '15:00', '16:00']));
    }
  }, [date]);

  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
      track('booking_modal_opened');
    }
    return () => { document.body.style.overflow = ''; };
  }, [isOpen]);

  const validate = () => {
    const e = {};
    if (form.vorname.trim().length < 2) e.vorname = t.booking.validation.firstName;
    if (form.nachname.trim().length < 2) e.nachname = t.booking.validation.lastName;
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)) e.email = t.booking.validation.email;
    setErrors(e);
    return !Object.keys(e).length;
  };

  const submit = async () => {
    if (!validate()) return;
    setBusy(true);
    track('booking_submit', { date, time });
    try {
      const r = await fetch(`${API}/api/booking`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...form, date, time })
      });
      const d = await r.json();
      if (r.ok) { setOk(d); track('calendar_booked', { id: d.booking_id }); }
      else throw new Error(d.detail);
    } catch (e) {
      setErrors({ submit: e.message || 'Booking failed' });
    } finally { setBusy(false); }
  };

  const reset = () => {
    setStep(1); setDate(''); setTime(''); setOk(null);
    setForm({ vorname: '', nachname: '', email: '', telefon: '', unternehmen: '', thema: '' });
    setErrors({});
  };

  if (!isOpen) return null;

  const stepLabels = t.booking.steps || ['Datum', 'Details'];
  const durationLabel = { de: '30 Min. Strategiegespräch', nl: '30 min. Strategiegesprek', en: '30 min. Strategy Call' };
  const freeLabel = { de: 'Kostenfrei & unverbindlich', nl: 'Gratis & vrijblijvend', en: 'Free & no obligation' };

  return (
    <div className="bk-overlay" onClick={e => e.target === e.currentTarget && onClose()} role="dialog" aria-modal="true" aria-labelledby="bk-title" data-testid="booking-modal">
      <motion.div className="bk-modal" initial={{ opacity: 0, scale: 0.96, y: 16 }} animate={{ opacity: 1, scale: 1, y: 0 }} transition={{ duration: 0.35, ease: [0.25, 0.4, 0, 1] }}>

        {/* Header */}
        <div className="bk-header" data-testid="booking-header">
          <div>
            <h2 id="bk-title" className="bk-title">{t.booking.title}</h2>
            <div className="bk-meta">
              <span className="bk-meta-item"><I n="timer" /> {durationLabel[lang] || durationLabel.de}</span>
              <span className="bk-meta-divider" />
              <span className="bk-meta-item bk-meta-free"><I n="verified" /> {freeLabel[lang] || freeLabel.de}</span>
            </div>
          </div>
          <button className="bk-close" onClick={onClose} aria-label="Close" data-testid="booking-close"><I n="close" /></button>
        </div>

        {/* Progress */}
        {!ok && (
          <div className="bk-progress" data-testid="booking-progress">
            {stepLabels.map((s, i) => (
              <div key={i} className={`bk-step-ind ${step >= i + 1 ? 'active' : ''} ${step === i + 1 ? 'current' : ''}`}>
                <span className="bk-step-num">{i + 1}</span>
                <span className="bk-step-label">{s}</span>
              </div>
            ))}
            <div className="bk-progress-bar">
              <div className="bk-progress-fill" style={{ width: ok ? '100%' : step === 2 ? '100%' : '50%' }} />
            </div>
          </div>
        )}

        {/* Content */}
        <div className="bk-body">
          <AnimatePresence mode="wait">
            {ok ? (
              <motion.div className="bk-success" key="success" data-testid="booking-success" initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} transition={{ duration: 0.4 }}>
                <div className="bk-success-icon"><I n="check_circle" /></div>
                <h3>{t.booking.successTitle}</h3>
                <div className="bk-success-detail">
                  <div className="bk-success-row"><I n="event" /> <span>{fmtDate(date)}</span></div>
                  <div className="bk-success-row"><I n="schedule" /> <span>{time} Uhr</span></div>
                  <div className="bk-success-row"><I n="mail" /> <span>{form.email}</span></div>
                </div>
                <p className="bk-success-text">{t.booking.successText.replace('{email}', form.email)}</p>
                <button className="bk-btn bk-btn-primary" onClick={() => { reset(); onClose(); }} data-testid="booking-done">{t.booking.close}</button>
              </motion.div>
            ) : step === 1 ? (
              <motion.div className="bk-step-content" key="step1" data-testid="booking-step-1" initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: 10 }} transition={{ duration: 0.25 }}>
                <h3 className="bk-section-title">{t.booking.selectDate}</h3>
                <div className="bk-dates" data-testid="booking-dates">
                  {dates.map(d => (
                    <button key={d} className={`bk-date ${date === d ? 'sel' : ''}`} onClick={() => setDate(d)} data-testid={`booking-date-${d}`}>
                      <span className="bk-date-day">{new Date(d).toLocaleDateString(locale, { weekday: 'short' })}</span>
                      <span className="bk-date-num">{new Date(d).getDate()}</span>
                      <span className="bk-date-month">{new Date(d).toLocaleDateString(locale, { month: 'short' })}</span>
                    </button>
                  ))}
                </div>
                {date && (
                  <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}>
                    <h3 className="bk-section-title">{t.booking.selectTime}</h3>
                    <div className="bk-times" data-testid="booking-times">
                      {slots.length > 0 ? slots.map(s => (
                        <button key={s} className={`bk-time ${time === s ? 'sel' : ''}`} onClick={() => setTime(s)} data-testid={`booking-time-${s}`}>
                          {s}
                        </button>
                      )) : <p className="bk-no-slots">{t.booking.noTimes}</p>}
                    </div>
                  </motion.div>
                )}
                <button className="bk-btn bk-btn-primary" disabled={!date || !time} onClick={() => { setStep(2); track('booking_step_2'); }} data-testid="booking-next">
                  {t.booking.next} <I n="arrow_forward" />
                </button>
              </motion.div>
            ) : (
              <motion.div className="bk-step-content" key="step2" data-testid="booking-step-2" initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: 10 }} transition={{ duration: 0.25 }}>
                <button className="bk-back" onClick={() => setStep(1)} data-testid="booking-back"><I n="arrow_back" /> {t.booking.back}</button>
                <div className="bk-selected-summary">
                  <I n="event" />
                  <div>
                    <span className="bk-selected-date">{fmtDate(date)}</span>
                    <span className="bk-selected-time">{time} Uhr</span>
                  </div>
                </div>
                <div className="bk-form">
                  <div className="bk-form-row">
                    <div className="bk-field">
                      <label>{t.booking.firstName} *</label>
                      <input type="text" className={errors.vorname ? 'error' : ''} value={form.vorname} onChange={e => setForm({...form, vorname: e.target.value})} data-testid="booking-vorname" />
                      {errors.vorname && <span className="bk-field-error">{errors.vorname}</span>}
                    </div>
                    <div className="bk-field">
                      <label>{t.booking.lastName} *</label>
                      <input type="text" className={errors.nachname ? 'error' : ''} value={form.nachname} onChange={e => setForm({...form, nachname: e.target.value})} data-testid="booking-nachname" />
                      {errors.nachname && <span className="bk-field-error">{errors.nachname}</span>}
                    </div>
                  </div>
                  <div className="bk-field">
                    <label>{t.booking.email} *</label>
                    <input type="email" className={errors.email ? 'error' : ''} value={form.email} onChange={e => setForm({...form, email: e.target.value})} data-testid="booking-email" />
                    {errors.email && <span className="bk-field-error">{errors.email}</span>}
                  </div>
                  <div className="bk-form-row">
                    <div className="bk-field">
                      <label>{t.booking.phone}</label>
                      <input type="tel" value={form.telefon} onChange={e => setForm({...form, telefon: e.target.value})} placeholder="+49 ..." data-testid="booking-telefon" />
                    </div>
                    <div className="bk-field">
                      <label>{t.booking.company}</label>
                      <input type="text" value={form.unternehmen} onChange={e => setForm({...form, unternehmen: e.target.value})} data-testid="booking-company" />
                    </div>
                  </div>
                  <div className="bk-field">
                    <label>{t.booking.message}</label>
                    <textarea value={form.thema} onChange={e => setForm({...form, thema: e.target.value})} rows={2} placeholder={lang === 'en' ? 'Brief description of your project...' : lang === 'nl' ? 'Korte beschrijving van uw project...' : 'Kurze Beschreibung Ihres Vorhabens...'} data-testid="booking-thema" />
                  </div>
                  {errors.submit && <div className="bk-error"><I n="error" /> {errors.submit}</div>}
                  <button className="bk-btn bk-btn-primary" onClick={submit} disabled={busy} data-testid="booking-submit">
                    {busy ? <><div className="bk-spinner" /> {lang === 'en' ? 'Submitting...' : lang === 'nl' ? 'Bezig...' : 'Wird gebucht...'}</> : <>{t.booking.submit} <I n="check" /></>}
                  </button>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </motion.div>
    </div>
  );
};

export default Booking;
