import { useState, useEffect } from 'react'
import {
  Box,
  CssBaseline,
  AppBar,
  Toolbar,
  Typography,
  Drawer,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Container,
  CircularProgress,
  Alert,
} from '@mui/material'
import {
  Dashboard as DashboardIcon,
  History as HistoryIcon,
  Memory as MemoryIcon,
  Extension as SkillsIcon,
  Settings as SettingsIcon,
  Menu as MenuIcon,
} from '@mui/icons-material'
import { BrowserRouter as Router, Routes, Route, useLocation } from 'react-router-dom'

// Pages
import DashboardPage from './pages/Dashboard.tsx'
import CommandsPage from './pages/Commands.tsx'
import MemoryPage from './pages/Memory.tsx'
import SkillsPage from './pages/Skills.tsx'
import SettingsPage from './pages/Settings.tsx'

const drawerWidth = 280

const menuItems = [
  { text: 'Dashboard', icon: <DashboardIcon />, path: '/' },
  { text: 'Command History', icon: <HistoryIcon />, path: '/commands' },
  { text: 'Memory & Learning', icon: <MemoryIcon />, path: '/memory' },
  { text: 'Skills', icon: <SkillsIcon />, path: '/skills' },
  { text: 'Settings', icon: <SettingsIcon />, path: '/settings' },
]

function AppContent() {
  const [mobileOpen, setMobileOpen] = useState(false)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const location = useLocation()

  useEffect(() => {
    // Check API connection
    fetch('/api/status')
      .then(res => {
        if (!res.ok) throw new Error('API not responding')
        return res.json()
      })
      .then(() => setLoading(false))
      .catch(err => {
        setError(err.message)
        setLoading(false)
      })
  }, [])

  const handleDrawerToggle = () => {
    setMobileOpen(!mobileOpen)
  }

  const drawer = (
    <div>
      <Toolbar>
        <Typography variant="h6" noWrap component="div" sx={{ fontWeight: 'bold' }}>
          Aether Dashboard
        </Typography>
      </Toolbar>
      <List>
        {menuItems.map((item) => (
          <ListItem key={item.text} disablePadding>
            <ListItemButton
              selected={location.pathname === item.path}
              onClick={() => {
                if (location.pathname !== item.path) {
                  window.location.href = item.path
                }
                setMobileOpen(false)
              }}
            >
              <ListItemIcon>{item.icon}</ListItemIcon>
              <ListItemText primary={item.text} />
            </ListItemButton>
          </ListItem>
        ))}
      </List>
    </div>
  )

  if (loading) {
    return (
      <Box
        display="flex"
        justifyContent="center"
        alignItems="center"
        minHeight="100vh"
      >
        <CircularProgress />
      </Box>
    )
  }

  if (error) {
    return (
      <Container maxWidth="md" sx={{ mt: 4 }}>
        <Alert severity="error">
          Failed to connect to Aether Dashboard API: {error}
          <br />
          Make sure the dashboard backend is running on port 8001
        </Alert>
      </Container>
    )
  }

  return (
    <Box sx={{ display: 'flex' }}>
      <AppBar
        position="fixed"
        sx={{
          width: { sm: `calc(100% - ${drawerWidth}px)` },
          ml: { sm: `${drawerWidth}px` },
        }}
      >
        <Toolbar>
          <Box
            sx={{ flexGrow: 1, display: { xs: 'flex', sm: 'none' } }}
          >
            <MenuIcon onClick={handleDrawerToggle} sx={{ cursor: 'pointer' }} />
          </Box>
          <Typography variant="h6" noWrap component="div">
            {menuItems.find(item => item.path === location.pathname)?.text || 'Aether'}
          </Typography>
        </Toolbar>
      </AppBar>
      <Box
        component="nav"
        sx={{ width: { sm: drawerWidth }, flexShrink: { sm: 0 } }}
      >
        <Drawer
          variant="temporary"
          open={mobileOpen}
          onClose={handleDrawerToggle}
          ModalProps={{
            keepMounted: true,
          }}
          sx={{
            display: { xs: 'block', sm: 'none' },
            '& .MuiDrawer-paper': { boxSizing: 'border-box', width: drawerWidth },
          }}
        >
          {drawer}
        </Drawer>
        <Drawer
          variant="permanent"
          sx={{
            display: { xs: 'none', sm: 'block' },
            '& .MuiDrawer-paper': { boxSizing: 'border-box', width: drawerWidth },
          }}
          open
        >
          {drawer}
        </Drawer>
      </Box>
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          p: 3,
          width: { sm: `calc(100% - ${drawerWidth}px)` },
          mt: 8,
        }}
      >
        <Routes>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/commands" element={<CommandsPage />} />
          <Route path="/memory" element={<MemoryPage />} />
          <Route path="/skills" element={<SkillsPage />} />
          <Route path="/settings" element={<SettingsPage />} />
        </Routes>
      </Box>
    </Box>
  )
}

function App() {
  return (
    <Router>
      <CssBaseline />
      <AppContent />
    </Router>
  )
}

export default App
