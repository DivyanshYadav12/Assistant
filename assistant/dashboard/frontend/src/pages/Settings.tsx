import { useState, useEffect } from 'react'
import {
  Box,
  Typography,
  Card,
  CardContent,
  Grid,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Switch,
  FormControlLabel,
  Alert,
  Snackbar,
} from '@mui/material'
import {
  LightMode as LightIcon,
  DarkMode as DarkIcon,
  SettingsBrightness as AutoIcon,
} from '@mui/icons-material'

interface UserPreferences {
  theme: string
  ui_density: string
  notifications_enabled: boolean
  sound_enabled: boolean
  language: string
  sidebar_collapsed: boolean
  conversation_timeout: number
}

interface SettingsPageProps {
  preferences?: UserPreferences
  updatePreferences?: (prefs: UserPreferences) => void
}

export default function SettingsPage({ preferences, updatePreferences }: SettingsPageProps) {
  const [localPrefs, setLocalPrefs] = useState(preferences || {
    theme: 'light',
    ui_density: 'comfortable',
    notifications_enabled: true,
    sound_enabled: true,
    language: 'en',
    sidebar_collapsed: false,
    conversation_timeout: 10.0,
  })
  const [showSuccess, setShowSuccess] = useState(false)

  useEffect(() => {
    if (preferences) {
      setLocalPrefs(preferences)
    }
  }, [preferences])

  const handleChange = (field: keyof UserPreferences, value: any) => {
    const newPrefs = { ...localPrefs, [field]: value }
    setLocalPrefs(newPrefs)
    if (updatePreferences) {
      updatePreferences(newPrefs)
    }
    setShowSuccess(true)
    setTimeout(() => setShowSuccess(false), 2000)
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Settings
      </Typography>
      <Typography variant="body1" color="text.secondary" gutterBottom>
        Customize your Aether experience
      </Typography>

      <Grid container spacing={3} sx={{ mt: 2 }}>
        {/* Appearance Settings */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Appearance
              </Typography>

              <Box sx={{ mt: 2 }}>
                <FormControl fullWidth sx={{ mb: 2 }}>
                  <InputLabel>Theme</InputLabel>
                  <Select
                    value={localPrefs.theme}
                    label="Theme"
                    onChange={(e) => handleChange('theme', e.target.value)}
                  >
                    <MenuItem value="light">
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <LightIcon fontSize="small" />
                        Light
                      </Box>
                    </MenuItem>
                    <MenuItem value="dark">
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <DarkIcon fontSize="small" />
                        Dark
                      </Box>
                    </MenuItem>
                    <MenuItem value="auto">
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <AutoIcon fontSize="small" />
                        Auto (System)
                      </Box>
                    </MenuItem>
                  </Select>
                </FormControl>

                <FormControl fullWidth>
                  <InputLabel>UI Density</InputLabel>
                  <Select
                    value={localPrefs.ui_density}
                    label="UI Density"
                    onChange={(e) => handleChange('ui_density', e.target.value)}
                  >
                    <MenuItem value="compact">Compact</MenuItem>
                    <MenuItem value="comfortable">Comfortable</MenuItem>
                    <MenuItem value="spacious">Spacious</MenuItem>
                  </Select>
                </FormControl>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Notifications Settings */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Notifications
              </Typography>

              <Box sx={{ mt: 2 }}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={localPrefs.notifications_enabled}
                      onChange={(e) => handleChange('notifications_enabled', e.target.checked)}
                    />
                  }
                  label="Enable desktop notifications"
                  sx={{ mb: 2, display: 'block' }}
                />

                <FormControlLabel
                  control={
                    <Switch
                      checked={localPrefs.sound_enabled}
                      onChange={(e) => handleChange('sound_enabled', e.target.checked)}
                    />
                  }
                  label="Enable sound alerts"
                  sx={{ display: 'block' }}
                />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Language Settings */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Language & Region
              </Typography>

              <Box sx={{ mt: 2 }}>
                <FormControl fullWidth>
                  <InputLabel>Language</InputLabel>
                  <Select
                    value={localPrefs.language}
                    label="Language"
                    onChange={(e) => handleChange('language', e.target.value)}
                  >
                    <MenuItem value="en">English</MenuItem>
                    <MenuItem value="es">Español</MenuItem>
                    <MenuItem value="fr">Français</MenuItem>
                    <MenuItem value="de">Deutsch</MenuItem>
                    <MenuItem value="zh">中文</MenuItem>
                    <MenuItem value="ja">日本語</MenuItem>
                  </Select>
                </FormControl>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Layout Settings */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Layout
              </Typography>

              <Box sx={{ mt: 2 }}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={localPrefs.sidebar_collapsed}
                      onChange={(e) => handleChange('sidebar_collapsed', e.target.checked)}
                    />
                  }
                  label="Collapse sidebar by default"
                  sx={{ display: 'block' }}
                />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Conversation Settings */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Conversation Mode
              </Typography>

              <Box sx={{ mt: 2 }}>
                <FormControl fullWidth>
                  <InputLabel>Follow-up Timeout</InputLabel>
                  <Select
                    value={localPrefs.conversation_timeout}
                    label="Follow-up Timeout"
                    onChange={(e) => handleChange('conversation_timeout', e.target.value)}
                  >
                    <MenuItem value={5.0}>5 seconds</MenuItem>
                    <MenuItem value={10.0}>10 seconds</MenuItem>
                    <MenuItem value={15.0}>15 seconds</MenuItem>
                    <MenuItem value={20.0}>20 seconds</MenuItem>
                    <MenuItem value={30.0}>30 seconds</MenuItem>
                  </Select>
                </FormControl>
                <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                  How long to wait for follow-up questions after each response
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Snackbar
          open={showSuccess}
          autoHideDuration={3000}
          onClose={() => setShowSuccess(false)}
        >
          <Alert severity="success" onClose={() => setShowSuccess(false)}>
            Preferences saved successfully!
          </Alert>
        </Snackbar>
      </Grid>
    </Box>
  )
}
