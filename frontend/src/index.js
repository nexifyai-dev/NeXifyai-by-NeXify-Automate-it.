import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { HelmetProvider } from 'react-helmet-async';
import { LanguageProvider } from './i18n/LanguageContext';
import ErrorBoundary from './components/ErrorBoundary';
import './index.css';
import App from './App';
import Admin from './pages/Admin';
import LegalPage from './pages/LegalPages';
import QuotePortal from './pages/QuotePortal';
import CustomerPortal from './pages/CustomerPortal';
import IntegrationDetail from './pages/IntegrationDetail';
import UnifiedLogin from './pages/UnifiedLogin';
import BookingPage from './pages/BookingPage';

/* Language-aware redirect: / → /<detected lang> */
function LangRedirect() {
  const stored = localStorage.getItem('nx_lang');
  const lang = stored && ['de', 'nl', 'en'].includes(stored) ? stored : 'de';
  return <Navigate to={`/${lang}`} replace />;
}

/* Backward compat: /impressum → /de/impressum etc */
function LegacyRedirect({ slug }) {
  const stored = localStorage.getItem('nx_lang');
  const lang = stored && ['de', 'nl', 'en'].includes(stored) ? stored : 'de';
  return <Navigate to={`/${lang}/${slug}`} replace />;
}

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <ErrorBoundary>
      <HelmetProvider>
        <BrowserRouter>
          <LanguageProvider>
            <Routes>
            {/* Root redirect */}
            <Route path="/" element={<LangRedirect />} />

            {/* Language-prefixed landing page */}
            <Route path="/de" element={<App />} />
            <Route path="/nl" element={<App />} />
            <Route path="/en" element={<App />} />

            {/* Language-prefixed legal pages (all slug variants) */}
            <Route path="/:lang/:page" element={<LegalPage />} />

            {/* Unified Login (Admin + Customer) */}
            <Route path="/login" element={<UnifiedLogin />} />
            <Route path="/login/verify" element={<UnifiedLogin />} />

            {/* Standalone Booking Page (Pre-Login) */}
            <Route path="/termin" element={<BookingPage />} />
            <Route path="/booking" element={<BookingPage />} />

            {/* Admin (no language prefix) */}
            <Route path="/admin" element={<Admin />} />

            {/* Integration SEO Pages */}
            <Route path="/integrationen/:slug" element={<IntegrationDetail />} />

            {/* Customer Offer Portal */}
            <Route path="/angebot" element={<QuotePortal />} />

            {/* Customer Portal (JWT-authenticated) */}
            <Route path="/portal" element={<CustomerPortal />} />
            <Route path="/portal/:token" element={<CustomerPortal />} />

            {/* Backward compatibility: old routes without lang prefix */}
            <Route path="/impressum" element={<LegacyRedirect slug="impressum" />} />
            <Route path="/datenschutz" element={<LegacyRedirect slug="datenschutz" />} />
            <Route path="/agb" element={<LegacyRedirect slug="agb" />} />
            <Route path="/ki-hinweise" element={<LegacyRedirect slug="ki-hinweise" />} />

            {/* Fallback */}
            <Route path="*" element={<LangRedirect />} />
          </Routes>
        </LanguageProvider>
      </BrowserRouter>
    </HelmetProvider>
    </ErrorBoundary>
  </React.StrictMode>
);
