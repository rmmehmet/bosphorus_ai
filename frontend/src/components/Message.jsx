const SOURCE_LABELS = {
  get_holidays: '📅 Tatiller',
  get_vehicles: '🚗 Araçlar',
  get_weather_from_excel: '📊 İklim Verileri',
  get_current_weather_api: '🌤 Anlık Hava',
  get_current_date_info: '🗓 Tarih',
}

export default function Message({ message }) {
  const isUser = message.role === 'user'
  return (
    <div className={`message ${isUser ? 'user' : 'ai'}`}>
      <div className="msg-bubble">
        <div style={{ whiteSpace: 'pre-wrap' }}>{message.content}</div>
        {!isUser && message.sources && message.sources.length > 0 && (
          <div className="msg-sources">
            {message.sources.map(s => (
              <span key={s} className="source-tag">
                {SOURCE_LABELS[s] || s}
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}