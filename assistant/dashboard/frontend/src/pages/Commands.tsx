import { useState, useEffect } from 'react'
import {
  Box,
  Typography,
  Card,
  CardContent,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  CircularProgress,
  Alert,
  Button,
} from '@mui/material'
import { Refresh as RefreshIcon } from '@mui/icons-material'

interface CommandHistoryItem {
  id: string
  timestamp: string
  command: string
  skill: string
  success: boolean
  risk_level: string
  approval_required: boolean
  approval_given: boolean
  execution_time_ms: number
}

export default function CommandsPage() {
  const [commands, setCommands] = useState<CommandHistoryItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchCommands = async () => {
    try {
      const response = await fetch('/api/commands?limit=50')
      if (!response.ok) throw new Error('Failed to fetch commands')
      const data = await response.json()
      setCommands(data)
      setError(null)
    } catch (err) {
      console.error('Failed to fetch commands:', err)
      setError('Failed to load command history')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchCommands()
    // Poll for updates every 5 seconds
    const interval = setInterval(fetchCommands, 5000)
    return () => clearInterval(interval)
  }, [])

  const getRiskColor = (risk: string) => {
    switch (risk) {
      case 'safe': return 'success'
      case 'low': return 'info'
      case 'medium': return 'warning'
      case 'high': return 'error'
      default: return 'default'
    }
  }

  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp)
    return date.toLocaleTimeString()
  }

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
          Command History
        </Typography>
        <Alert severity="error" sx={{ mt: 2 }}>
          {error}
        </Alert>
        <Button 
          variant="outlined" 
          startIcon={<RefreshIcon />} 
          onClick={fetchCommands}
          sx={{ mt: 2 }}
        >
          Retry
        </Button>
      </Box>
    )
  }

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="h4" gutterBottom>
          Command History
        </Typography>
        <Button 
          variant="outlined" 
          startIcon={<RefreshIcon />} 
          onClick={fetchCommands}
          size="small"
        >
          Refresh
        </Button>
      </Box>
      <Typography variant="body1" color="text.secondary" gutterBottom>
        View and analyze all executed commands
      </Typography>

      <Card sx={{ mt: 2 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Recent Commands
          </Typography>
          {commands.length === 0 ? (
            <Typography color="text.secondary" sx={{ py: 4 }}>
              No commands recorded yet. Start using Aether to see command history here.
            </Typography>
          ) : (
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Time</TableCell>
                    <TableCell>Command</TableCell>
                    <TableCell>Skill</TableCell>
                    <TableCell>Status</TableCell>
                    <TableCell>Risk Level</TableCell>
                    <TableCell>Approval</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {commands.map((cmd) => (
                    <TableRow key={cmd.id}>
                      <TableCell>{formatTime(cmd.timestamp)}</TableCell>
                      <TableCell>{cmd.command}</TableCell>
                      <TableCell>{cmd.skill}</TableCell>
                      <TableCell>
                        <Chip
                          label={cmd.success ? 'Success' : 'Failed'}
                          color={cmd.success ? 'success' : 'error'}
                          size="small"
                        />
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={cmd.risk_level}
                          color={getRiskColor(cmd.risk_level)}
                          size="small"
                        />
                      </TableCell>
                      <TableCell>
                        {cmd.approval_required ? (
                          <Chip
                            label={cmd.approval_given ? 'Approved' : 'Required'}
                            color={cmd.approval_given ? 'success' : 'warning'}
                            size="small"
                          />
                        ) : (
                          <Chip label="Auto" color="default" size="small" />
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          )}
        </CardContent>
      </Card>
    </Box>
  )
}
