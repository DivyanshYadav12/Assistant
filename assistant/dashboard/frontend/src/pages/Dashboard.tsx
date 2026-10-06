import { useState, useEffect } from 'react'
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  Chip,
  LinearProgress,
  CircularProgress,
} from '@mui/material'
import {
  CheckCircle as CheckIcon,
  Error as ErrorIcon,
} from '@mui/icons-material'

interface SystemStatus {
  planner_running: boolean
  wake_word_running: boolean
  ollama_running: boolean
  hive_running: boolean
  cpu_usage: number
  memory_usage: number
  disk_usage: number
}

export default function DashboardPage() {
  const [status, setStatus] = useState<SystemStatus | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const response = await fetch('/api/status')
        if (!response.ok) throw new Error('Failed to fetch status')
        const data = await response.json()
        setStatus(data)
        setError(null)
      } catch (err) {
        console.error('Failed to fetch status:', err)
        setError('Failed to connect to Aether system')
      } finally {
        setLoading(false)
      }
    }

    fetchStatus()
    const interval = setInterval(fetchStatus, 5000) // Update every 5 seconds
    return () => clearInterval(interval)
  }, [])

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="200px">
        <CircularProgress />
      </Box>
    )
  }

  if (error) {
    return (
      <Box>
        <Typography variant="h4" gutterBottom>
          Dashboard
        </Typography>
        <Typography variant="body1" color="error" gutterBottom>
          {error}
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Make sure the planner is running on port 48100 and the dashboard backend is running on port 8002.
        </Typography>
      </Box>
    )
  }

  if (!status) {
    return <Typography>Loading system status...</Typography>
  }

  const services = [
    { name: 'Planner', running: status.planner_running },
    { name: 'Wake Word', running: status.wake_word_running },
    { name: 'Ollama', running: status.ollama_running },
    { name: 'Hive', running: status.hive_running },
  ]

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Dashboard
      </Typography>
      <Typography variant="body1" color="text.secondary" gutterBottom>
        Real-time system overview and activity feed
      </Typography>

      <Grid container spacing={3} sx={{ mt: 2 }}>
        {/* Service Status */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Service Status
              </Typography>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                {services.map((service) => (
                  <Box
                    key={service.name}
                    sx={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                    }}
                  >
                    <Typography variant="body1">{service.name}</Typography>
                    <Chip
                      icon={service.running ? <CheckIcon /> : <ErrorIcon />}
                      label={service.running ? 'Running' : 'Stopped'}
                      color={service.running ? 'success' : 'error'}
                      size="small"
                    />
                  </Box>
                ))}
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* System Resources */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                System Resources
              </Typography>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                <Box>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                    <Typography variant="body2">CPU Usage</Typography>
                    <Typography variant="body2">{status.cpu_usage.toFixed(1)}%</Typography>
                  </Box>
                  <LinearProgress
                    variant="determinate"
                    value={status.cpu_usage}
                    color={status.cpu_usage > 80 ? 'error' : 'primary'}
                  />
                </Box>
                <Box>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                    <Typography variant="body2">Memory Usage</Typography>
                    <Typography variant="body2">{status.memory_usage.toFixed(1)}%</Typography>
                  </Box>
                  <LinearProgress
                    variant="determinate"
                    value={status.memory_usage}
                    color={status.memory_usage > 80 ? 'error' : 'primary'}
                  />
                </Box>
                <Box>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                    <Typography variant="body2">Disk Usage</Typography>
                    <Typography variant="body2">{status.disk_usage.toFixed(1)}%</Typography>
                  </Box>
                  <LinearProgress
                    variant="determinate"
                    value={status.disk_usage}
                    color={status.disk_usage > 80 ? 'error' : 'primary'}
                  />
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Quick Stats */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                System Status
              </Typography>
              <Typography variant="h3" color={status.planner_running ? 'success.main' : 'error.main'}>
                {status.planner_running ? 'Online' : 'Offline'}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Aether is {status.planner_running ? 'ready' : 'not running'}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Services Active
              </Typography>
              <Typography variant="h3" color="info.main">
                {services.filter(s => s.running).length}/{services.length}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Core services running
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                System Health
              </Typography>
              <Typography variant="h3" color={status.cpu_usage < 80 && status.memory_usage < 80 ? 'success.main' : 'warning.main'}>
                {status.cpu_usage < 80 && status.memory_usage < 80 ? 'Good' : 'Warning'}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Resource utilization
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  )
}
