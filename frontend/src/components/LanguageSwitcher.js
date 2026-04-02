import React from 'react';
import { useLanguage } from '../i18n/LanguageContext';

const FLAGS = { de: 'DE', nl: 'NL', en: 'EN' };
const LABELS = { de: 'Deutsch', nl: 'Nederlands', en: 'English' };

export default function LanguageSwitcher({ mobile = false }) {
  const { lang, setLang } = useLanguage();

  return (
    <div className={`lang-switcher ${mobile ? 'lang-mobile' : ''}`} data-testid="language-switcher" role="group" aria-label="Language selection">
      {Object.entries(FLAGS).map(([code, flag]) => (
        <button
          key={code}
          className={`lang-btn ${lang === code ? 'active' : ''}`}
          onClick={() => setLang(code)}
          aria-label={LABELS[code]}
          aria-pressed={lang === code}
          data-testid={`lang-btn-${code}`}
        >
          {flag}
        </button>
      ))}
    </div>
  );
}
