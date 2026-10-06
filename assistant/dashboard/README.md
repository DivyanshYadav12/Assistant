# Aether Web Dashboard

A professional, user-friendly web dashboard for Aether voice assistant with real-time monitoring, configuration, and personalization features.

## Features

- **Real-time Dashboard**: System status, resource monitoring, activity feed
- **Command History**: View and analyze all executed commands
- **Memory & Learning**: Visualize memory usage and learning patterns
- **Skills Management**: Configure and test Aether's skills
- **User Preferences**: Customize theme, notifications, language, and layout
- **Responsive Design**: Works on desktop, tablet, and mobile devices
- **Real-time Updates**: WebSocket for live system updates

## Architecture

- **Backend**: FastAPI (Python) on port 8001
- **Frontend**: React + TypeScript + Material-UI
- **Database**: SQLite (shared with planner)
- **Real-time**: WebSocket for live updates

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- Aether planner running (port 48100)

### Backend Setup

1. **Install Python dependencies** (already included in planner):
```bash
cd assistant/planner
.\.venv\Scripts\pip.exe install fastapi uvicorn websockets psutil
```

2. **Start the backend server**:
```powershell
cd assistant/planner
.\.venv\Scripts\python.exe -m assistant.dashboard.main
```

The backend will start on `http://localhost:8002`

### Frontend Setup

1. **Install Node dependencies**:
```bash
cd assistant/dashboard/frontend
npm install
```

2. **Start the development server**:
```bash
npm run dev
```

The frontend will start on `http://localhost:5173`

### Access the Dashboard

Open your browser and navigate to: `http://localhost:5173`

## Development

### Backend Development

The backend is a FastAPI application with the following structure:

```
assistant/planner/src/assistant/dashboard/
└── main.py              # FastAPI application entry point
```

### Frontend Development

The frontend is a React application with TypeScript:

```
frontend/
├── src/
│   ├── components/      # Reusable components
│   ├── pages/          # Page components
│   ├── hooks/          # Custom React hooks
│   ├── services/       # API client
│   └── types/          # TypeScript types
├── package.json
└── vite.config.ts
```

### Building for Production

**Frontend**:
```bash
cd frontend
npm run build
```

**Backend**:
```bash
cd backend
# TODO: Add production build script
```

## API Endpoints

### System Status
- `GET /api/status` - Get current system status

### User Preferences
- `GET /api/preferences` - Get user preferences
- `PUT /api/preferences` - Update user preferences

### Configuration
- `GET /api/config` - Get system configuration
- `PUT /api/config` - Update system configuration

### Command History
- `GET /api/commands` - Get command history

### WebSocket
- `WS /ws` - Real-time updates

## User Personalization Features

The dashboard provides extensive personalization options:

### Appearance
- **Theme**: Light, Dark, or Auto (system preference)
- **UI Density**: Compact, Comfortable, or Spacious
- **Accent Colors**: Customizable color schemes

### Notifications
- **Desktop Notifications**: Enable/disable desktop alerts
- **Sound Alerts**: Enable/disable sound notifications
- **Notification Types**: Configure which events trigger notifications

### Language & Region
- **Language**: Multiple language options (English, Spanish, French, German, Chinese, Japanese)
- **Date/Time Format**: Regional formatting options

### Layout
- **Sidebar**: Collapsible sidebar with navigation
- **Dashboard Widgets**: Customizable widget arrangement (coming soon)
- **Quick Actions**: Customizable quick action buttons (coming soon)

### Privacy Settings
- **Data Retention**: Configure how long to keep command history
- **Anonymization**: Options to anonymize sensitive data
- **Export**: Export all data for backup or migration

## Integration with Aether

The dashboard integrates with the existing Aether planner system:

1. **Status Monitoring**: Connects to planner to check service status
2. **Command History**: Reads from the audit log database
3. **Configuration**: Updates environment variables and settings
4. **Real-time Updates**: Receives live updates via WebSocket

## Security

- **Local Only**: Dashboard runs on localhost by default
- **No External APIs**: All data stays on your local machine
- **CORS Protected**: Configured for local development only
- **Authentication**: Simple token-based auth (optional for remote access)

## Troubleshooting

### Backend won't start
- Check if port 8001 is already in use
- Ensure Python dependencies are installed
- Check the console for error messages

### Frontend won't connect to backend
- Ensure backend is running on port 8001
- Check browser console for CORS errors
- Verify API proxy configuration in vite.config.ts

### Real-time updates not working
- Check WebSocket connection in browser network tab
- Ensure WebSocket endpoint is accessible
- Check firewall settings

## Future Enhancements

- [ ] Complete command history integration with audit log
- [ ] Memory visualization with charts and graphs
- [ ] Skills management with testing interface
- [ ] Advanced user preferences (custom themes, widget arrangement)
- [ ] Mobile app (PWA)
- [ ] Authentication for remote access
- [ ] Data export and import
- [ ] Performance monitoring and analytics

## Contributing

See main project [CONTRIBUTING.md](../../CONTRIBUTING.md) for guidelines.

## License

MIT License - see main project [LICENSE](../../LICENSE) file.
