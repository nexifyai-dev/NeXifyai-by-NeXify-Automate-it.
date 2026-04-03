import React, { useState, useEffect, useRef } from 'react';
import { motion } from 'framer-motion';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { API, I, genSid, track, BrandName } from '../shared';

const LiveChat = ({ isOpen, onClose, initialQ, t, lang }) => {
  const [msgs, setMsgs] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [sid] = useState(() => genSid());
  const [qual, setQual] = useState({});
  const endRef = useRef(null);
  const inputRef = useRef(null);
  const sentInitial = useRef(false);

  useEffect(() => {
    setMsgs([]);
    sentInitial.current = false;
  }, [lang]);

  useEffect(() => {
    if (isOpen && msgs.length === 0) {
      setMsgs([{ role: 'assistant', content: t.chat.welcome, ts: Date.now() }]);
      track('chat_started');
    }
  }, [isOpen, msgs.length, t.chat.welcome]);

  useEffect(() => {
    if (initialQ && isOpen && !sentInitial.current) {
      sentInitial.current = true;
      setTimeout(() => send(initialQ), 300);
    }
  }, [initialQ, isOpen]);

  useEffect(() => { endRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [msgs]);
  useEffect(() => {
    if (isOpen) { inputRef.current?.focus(); document.body.style.overflow = 'hidden'; }
    return () => { document.body.style.overflow = ''; };
  }, [isOpen]);

  const send = async (text = input) => {
    const txt = (typeof text === 'string' ? text : input).trim();
    if (!txt || loading) return;
    setMsgs(prev => [...prev, { role: 'user', content: txt, ts: Date.now() }]);
    setInput('');
    setLoading(true);
    try {
      const r = await fetch(`${API}/api/chat/message`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sid, message: txt, language: lang })
      });
      const d = await r.json();
      if (!r.ok) throw new Error(d.detail || 'Error');
      setMsgs(prev => [...prev, { role: 'assistant', content: d.message, ts: Date.now(), actions: d.actions }]);
      setQual(d.qualification || {});
      if (d.should_escalate) track('chat_escalation', { qual: d.qualification });
    } catch (_) {
      setMsgs(prev => [...prev, { role: 'assistant', content: t.contact.form.error, ts: Date.now() }]);
    } finally { setLoading(false); }
  };

  const onKey = (e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(); } };

  if (!isOpen) return null;
  return (
    <div className="chat-overlay" onClick={e => e.target === e.currentTarget && onClose()} role="dialog" aria-modal="true" aria-labelledby="chat-t" data-testid="chat-modal">
      <motion.div className="chat-modal" initial={{ opacity: 0, scale: 0.95, y: 20 }} animate={{ opacity: 1, scale: 1, y: 0 }} transition={{ duration: 0.3 }}>
        <button className="chat-close" onClick={onClose} aria-label="Close" data-testid="chat-close"><I n="close" /></button>
        <div className="chat-layout">
          <div className="chat-sidebar">
            <h2 id="chat-t" className="chat-sidebar-title"><BrandName /> {t.chat.sidebarRole}</h2>
            <p className="chat-sidebar-desc">{t.chat.sidebarDesc}</p>
            <div className="chat-presets">
              {t.chat.presets.map((q, i) => (
                <button key={i} className="chat-preset" onClick={() => { track('preset_click', { q }); send(q); }} data-testid={`chat-preset-${i}`}><svg className="chat-preset-arrow" width="14" height="14" viewBox="0 0 14 14" fill="none"><path d="M1 7h10M8 3.5L11.5 7 8 10.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/></svg><span>{q}</span></button>
              ))}
            </div>
            <div className="chat-sidebar-cta"><button className="btn btn-primary btn-glow" onClick={() => { track('chat_booking_click'); send(t.chat.presets[3] || 'Book a meeting'); }} style={{ width: '100%' }} data-testid="chat-sidebar-book-btn">{t.chat.bookBtn}</button></div>
          </div>
          <div className="chat-main">
            <div className="chat-header"><div className="chat-status"><span className="status-dot on"></span>{t.chat.status}</div><span className="chat-topic">{t.chat.topicLabel}</span></div>
            <div className="chat-msgs" data-testid="chat-messages">
              {msgs.map((m, i) => (
                <motion.div key={i} className={`chat-msg ${m.role}`} data-testid={`chat-msg-${i}`} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.25 }}>
                  {m.role === 'assistant' ? (
                    <div className="chat-md">
                      <ReactMarkdown remarkPlugins={[remarkGfm]}>{m.content}</ReactMarkdown>
                    </div>
                  ) : (
                    <div>{m.content}</div>
                  )}
                  {m.actions && m.actions.length > 0 && <div className="chat-msg-actions">{m.actions.map((a, ai) => {
                    if (a.type === 'offer_generated') return <a key={ai} href={`${API}${a.pdf_url}`} target="_blank" rel="noreferrer" className="btn btn-sm btn-primary" data-testid="offer-pdf-download">PDF-Angebot herunterladen</a>;
                    return <button key={ai} className="btn btn-sm btn-primary" onClick={() => send(t.booking.title)}>{a.label}</button>;
                  })}</div>}
                </motion.div>
              ))}
              {loading && <div className="chat-msg assistant"><div className="chat-typing"><span></span><span></span><span></span></div></div>}
              <div ref={endRef} />
            </div>
            <div className="chat-input-area">
              <input ref={inputRef} type="text" className="chat-input" placeholder={t.chat.placeholder} value={input} onChange={e => setInput(e.target.value)} onKeyDown={onKey} disabled={loading} aria-label="Message" data-testid="chat-input" />
              <button className="chat-send" onClick={() => send()} disabled={!input.trim() || loading} aria-label="Send" data-testid="chat-send"><I n="send" /></button>
            </div>
          </div>
        </div>
      </motion.div>
    </div>
  );
};

export default LiveChat;
