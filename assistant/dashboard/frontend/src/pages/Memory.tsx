import { useState, useEffect } from 'react'
import {
  Box,
  Typography,
  Card,
  CardContent,
  Grid,
  CircularProgress,
  Alert,
  Button,
  Chip,
  Divider,
} from '@mui/material'
import { Refresh as RefreshIcon } from '@mui/icons-material'

interface MemoryStats {
  total_memories: number
  total_conversations: number
  total_actions: number
  total_preferences: number
}

interface MemoryItem {
  id: string
  type: string
  content: string
  metadata: any
  timestamp: number
}

export default function MemoryPage() {
  const [stats, setStats] = useState<MemoryStats | null>(null)
  const [memories, setMemories] = useState<MemoryItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchData = async () => {
    try {
      const [statsRes, memoriesRes] = await Promise.all([
        fetch('/api/memory/stats'),
        fetch('/api/memories?limit=50'),
      ])
      
      if (statsRes.ok) {
        const statsData = await statsRes.json()
        setStats(statsData)
      }
      
      if (memoriesRes.ok) {
        const memoriesData = await memoriesRes.json()
        setMemories(memoriesData)
      }
      
      setError(null)
    } catch (err) {
      console.error('Failed to fetch memory data:', err)
      setError('Failed to load memory data')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
    const interval = setInterval(fetchData, 10000) // Update every 10 seconds
    return () => clearInterval(interval)
  }, [])

  const formatTime = (timestamp: number) => {
    const date = new Date(timestamp)
    return date.toLocaleString()
  }

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'conversation': return 'info'
      case 'action': return 'warning'
      case 'preference': return 'success'
      case 'file': return 'secondary'
      default: return 'default'
    }
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
          Memory & Learning
        </Typography>
        <Alert severity="error" sx={{ mt: 2 }}>
          {error}
        </Alert>
        <Button 
          variant="outlined" 
          startIcon={<RefreshIcon />} 
          onClick={fetchData}
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
          Memory & Learning
        </Typography>
        <Button 
          variant="outlined" 
          startIcon={<RefreshIcon />} 
          onClick={fetchData}
          size="small"
        >
          Refresh
        </Button>
      </Box>
      <Typography variant="body1" color="text.secondary" gutterBottom>
        View conversations, actions, and learned preferences
      </Typography>

      <Grid container spacing={3} sx={{ mt: 2 }}>
        {/* Memory Stats */}
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Total Memories
              </Typography>
              <Typography variant="h3" color="primary">
                {stats?.total_memories || 0}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Conversations
              </Typography>
              <Typography variant="h3" color="info.main">
                {stats?.total_conversations || 0}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Actions
              </Typography>
              <Typography variant="h3" color="warning.main">
                {stats?.total_actions || 0}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Preferences
              </Typography>
              <Typography variant="h3" color="success.main">
                {stats?.total_preferences || 0}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        {/* Recent Memories */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Recent Memories
              </Typography>
              {memories.length === 0 ? (
                <Typography color="text.secondary" sx={{ py: 4 }}>
                  No memories recorded yet. Use Aether to start building memory.
                </Typography>
              ) : (
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                  {memories.map((memory) => (
                    <Box key={memory.id}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                        <Chip
                          label={memory.type}
                          color={getTypeColor(memory.type)}
                          size="small"
                        />
                        <Typography variant="caption" color="text.secondary">
                          {formatTime(memory.timestamp)}
                        </Typography>
                      </Box>
                      <Typography variant="body2">
                        {memory.content}
                      </Typography>
                      <Divider sx={{ mt: 1 }} />
                    </Box>
                  ))}
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  )
}
