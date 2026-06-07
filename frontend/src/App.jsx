import { useState, useEffect } from 'react'
import Chat from './components/Chat'
import Header from './components/Header'
import './App.css'

export default function App() {
  const [theme, setTheme] = useState(() => {
    return localStorage.getItem('bai-theme') || 'dark'
  })

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme)
    localStorage.setItem('bai-theme', theme)
  }, [theme])

  const toggleTheme = () => setTheme(t => t === 'dark' ? 'light' : 'dark')

  return (
    <div className="app">
      <Header theme={theme} onToggleTheme={toggleTheme} />
      <Chat />
    </div>
  )
}