# Aether Web Dashboard - Architecture Plan

## Overview
A professional, user-friendly web dashboard for Aether voice assistant with real-time monitoring, configuration, and personalization features.

## Architecture

### Backend (FastAPI)
- **API Server**: FastAPI on port 8001 (separate from planner on 48100)
- **Location**: `assistant/planner/src/assistant/dashboard/`
- **Database**: SQLite (shares with existing planner data)
- **Real-time**: WebSocket for live updates
- **Authentication**: Simple token-based (local use only)

### Frontend (React + TypeScript)
- **Framework**: React 18 with TypeScript
- **UI Library**: Material-UI (MUI) for professional look
- **Charts**: Recharts for data visualization
- **Real-time**: Socket.io client for WebSocket
- **Build**: Vite for fast development

## Features

### 1. Dashboard Home
- **Status Overview**: System health, active services, recent activity
- **Quick Stats**: Commands today, success rate, memory usage
- **Live Feed**: Real-time command execution feed
- **Quick Actions**: Start/stop services, trigger commands

### 2. Command History
- **Timeline View**: Chronological list of all commands
- **Filter/Search**: By date, skill, success/failure, risk level
- **Details Modal**: Full command details, approval status, execution time
- **Export**: Export history to CSV/JSON

### 3. Memory & Learning
- **Memory Overview**: Memory usage, retention statistics
- **Learning Visualization**: Approval rates, rejection rates, undo rates
- **Rule Management**: View, edit, delete explicit rules
- **Memory Search**: Search stored memories and conversations

### 4. Skills Management
- **Skills Status**: Active/inactive skills, success rates
- **Skill Configuration**: Per-skill settings and parameters
- **Skill Testing**: Test individual skills with custom input
- **Custom Skills**: (Future) Upload/manage custom skill plugins

### 5. System Configuration
- **Voice Settings**: Wake word, hotkey, microphone selection
- **Model Settings**: Ollama URL, model selection, parameters
- **Safety Settings**: Risk thresholds, approval requirements
- **Data Management**: Clear history, export data, reset learning

### 6. User Preferences (Personalization)
- **Theme**: Light/Dark mode, accent colors
- **UI Density**: Compact/Comfortable/Spacious
- **Notifications**: Desktop notifications, sound alerts
- **Language**: UI language selection
- **Dashboard Layout**: Customizable widget arrangement
- **Privacy Settings**: Data retention, anonymization options

### 7. Real-time Monitoring
- **Live Audio**: Visualizer for current audio input
- **System Resources**: CPU, memory, disk usage
- **Service Status**: Planner, wake word, Ollama, Hive status
- **Error Logs**: Real-time error display and filtering

## User Experience Priorities

### 1. User-Friendly Design
- **Intuitive Navigation**: Clear sidebar with icons and labels
- **Progressive Disclosure**: Advanced options hidden by default
- **Help Tooltips**: Context-sensitive help for all settings
- **Error Messages**: Clear, actionable error messages
- **Loading States**: Visual feedback during operations

### 2. Personalization
- **Persistent Preferences**: Save user preferences across sessions
- **Customizable Dashboard**: Drag-and-drop widget arrangement
- **Theme Selection**: Multiple theme options with preview
- **Quick Actions**: Customizable quick action buttons
- **Keyboard Shortcuts**: Power user shortcuts

### 3. Mobile-Friendly
- **Responsive Design**: Works on phones, tablets, desktops
- **Touch-Optimized**: Large touch targets, swipe gestures
- **Mobile-Specific Features**: Push notifications, haptic feedback
- **Progressive Web App**: Install as mobile app

## Data Flow

```
User Dashboard → FastAPI Backend → Planner System
     ↓              ↓                    ↓
  WebSocket    SQLite Database    Skills & Agents
     ↓              ↓                    ↓
Real-time UI   Persistence & Config   Execution
```

## API Endpoints

### Configuration
- `GET /api/config` - Get current configuration
- `PUT /api/config` - Update configuration
- `GET /api/preferences` - Get user preferences
- `PUT /api/preferences` - Update user preferences

### Command History
- `GET /api/commands` - Get command history (paginated)
- `GET /api/commands/{id}` - Get specific command details
- `DELETE /api/commands` - Clear command history

### Memory & Learning
- `GET /api/memory/stats` - Get memory statistics
- `GET /api/rules` - Get all rules
- `POST /api/rules` - Create new rule
- `PUT /api/rules/{id}` - Update rule
- `DELETE /api/rules/{id}` - Delete rule

### Skills
- `GET /api/skills` - Get all skills and status
- `PUT /api/skills/{id}/toggle` - Enable/disable skill
- `POST /api/skills/{id}/test` - Test skill with input

### System
- `GET /api/system/status` - Get system status
- `POST /api/system/restart` - Restart services
- `GET /api/system/logs` - Get system logs

### WebSocket
- `WS /ws` - Real-time updates for commands, status, errors

## File Structure

```
assistant/
├── planner/
│   ├── src/assistant/
│   │   └── dashboard/
│   │       └── main.py              # FastAPI application
│   └── pyproject.toml               # Includes FastAPI dependencies
└── dashboard/
    ├── frontend/
    │   ├── src/
    │   │   ├── components/
    │   │   │   ├── Dashboard/   # Dashboard components
    │   │   │   ├── Commands/    # Command history components
    │   │   │   ├── Memory/      # Memory & learning components
    │   │   │   ├── Skills/      # Skills management components
    │   │   │   ├── Settings/    # Configuration components
    │   │   │   └── Common/      # Shared components
    │   │   ├── pages/
    │   │   │   ├── Dashboard.tsx
    │   │   │   ├── Commands.tsx
    │   │   │   ├── Memory.tsx
    │   │   │   ├── Skills.tsx
    │   │   │   └── Settings.tsx
    │   │   ├── hooks/
    │   │   │   ├── useWebSocket.ts
    │   │   │   └── usePreferences.ts
    │   │   ├── services/
    │   │   │   └── api.ts       # API client
    │   │   ├── types/
    │   │   │   └── index.ts     # TypeScript types
    │   │   ├── App.tsx
    │   │   └── main.tsx
    │   ├── package.json
    │   └── vite.config.ts
    ├── DASHBOARD_PLAN.md
    └── README.md
```

## Implementation Priority

1. **Phase 1** (Core Dashboard):
   - FastAPI backend setup
   - React frontend structure
   - Basic dashboard with system status
   - Command history viewer

2. **Phase 2** (Configuration):
   - Configuration API
   - Settings pages
   - User preferences system

3. **Phase 3** (Advanced Features):
   - Memory & learning visualization
   - Skills management
   - Real-time WebSocket updates

4. **Phase 4** (Polish):
   - Responsive design
   - Theme system
   - Performance optimization
   - Error handling

## Security Considerations

- **Local Only**: Dashboard runs on localhost by default
- **Optional Remote**: Can be enabled with authentication
- **Data Privacy**: No data sent to external servers
- **CORS**: Configured for local development
- **Rate Limiting**: Prevent API abuse

## Success Metrics

- **User Engagement**: Time spent in dashboard, feature usage
- **Performance**: Page load time < 2s, real-time updates < 100ms
- **Reliability**: 99.9% uptime for local dashboard
- **User Satisfaction**: Easy to use, intuitive navigation
