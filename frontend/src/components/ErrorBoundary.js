import React from 'react';

/**
 * NeXifyAI Global Error Boundary
 * Verhindert White Screen of Death bei unhandled JS Errors.
 */
class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('[NeXifyAI Error Boundary]', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div data-testid="error-boundary-fallback" style={{
          minHeight: '100vh',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          background: '#0c1117',
          color: '#c8d1dc',
          fontFamily: "'DM Sans', sans-serif",
          padding: 24,
        }}>
          <div style={{ textAlign: 'center', maxWidth: 480 }}>
            <div style={{
              width: 64, height: 64, borderRadius: '50%',
              background: 'rgba(239,68,68,0.1)', border: '2px solid rgba(239,68,68,0.3)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              margin: '0 auto 24px',
            }}>
              <span className="material-symbols-outlined" style={{ fontSize: 32, color: '#ef4444' }}>error</span>
            </div>
            <h1 style={{ fontSize: '1.5rem', fontWeight: 700, color: '#fff', marginBottom: 12 }}>
              Etwas ist schiefgelaufen
            </h1>
            <p style={{ fontSize: '.875rem', color: '#6b7b8d', marginBottom: 24, lineHeight: 1.6 }}>
              Ein unerwarteter Fehler ist aufgetreten. Bitte laden Sie die Seite neu. Falls das Problem bestehen bleibt, kontaktieren Sie den Support.
            </p>
            <button
              data-testid="error-boundary-reload"
              onClick={() => window.location.reload()}
              style={{
                background: '#ff9b7a', color: '#0c1117', border: 'none',
                padding: '12px 32px', borderRadius: 8, fontSize: '.875rem',
                fontWeight: 700, cursor: 'pointer', transition: 'all 0.2s',
              }}
              onMouseOver={e => e.currentTarget.style.background = '#ffb599'}
              onMouseOut={e => e.currentTarget.style.background = '#ff9b7a'}
            >
              Seite neu laden
            </button>
            {process.env.NODE_ENV === 'development' && this.state.error && (
              <pre style={{
                marginTop: 24, padding: 16, background: 'rgba(239,68,68,0.05)',
                border: '1px solid rgba(239,68,68,0.15)', borderRadius: 8,
                fontSize: '.6875rem', color: '#ef4444', textAlign: 'left',
                overflow: 'auto', maxHeight: 200,
              }}>
                {this.state.error.toString()}
              </pre>
            )}
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}

export default ErrorBoundary;
