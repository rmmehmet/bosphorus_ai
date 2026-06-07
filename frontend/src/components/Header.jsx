import './Header.css'

const SunIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="12" r="5"/>
    <line x1="12" y1="1" x2="12" y2="3"/>
    <line x1="12" y1="21" x2="12" y2="23"/>
    <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/>
    <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/>
    <line x1="1" y1="12" x2="3" y2="12"/>
    <line x1="21" y1="12" x2="23" y2="12"/>
    <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/>
    <line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/>
  </svg>
)

const MoonIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>
  </svg>
)

const BridgeIcon = () => (
  <svg width="28" height="28" viewBox="0 0 28 28" fill="none">
    <path d="M2 20 Q8 10 14 14 Q20 18 26 8" stroke="var(--accent)" strokeWidth="2.5" strokeLinecap="round" fill="none"/>
    <line x1="8" y1="20" x2="8" y2="13" stroke="var(--accent)" strokeWidth="1.8" strokeLinecap="round"/>
    <line x1="14" y1="20" x2="14" y2="14" stroke="var(--accent)" strokeWidth="1.8" strokeLinecap="round"/>
    <line x1="20" y1="20" x2="20" y2="11" stroke="var(--accent)" strokeWidth="1.8" strokeLinecap="round"/>
    <line x1="2" y1="20" x2="26" y2="20" stroke="var(--text)" strokeWidth="2" strokeLinecap="round"/>
  </svg>
)

export default function Header({ theme, onToggleTheme }) {
  return (
    <header className="header">
      <div className="header-brand">
        <BridgeIcon />
        <div>
          <span className="header-title">Bosphorus AI</span>
          <span className="header-sub">İstanbul Veri Asistanı</span>
        </div>
      </div>
      <button className="theme-btn" onClick={onToggleTheme} title="Temayı değiştir">
        {theme === 'dark' ? <SunIcon /> : <MoonIcon />}
      </button>
    </header>
  )
}