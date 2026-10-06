
import {
  Box,
  Typography,
  Card,
  CardContent,
} from '@mui/material'

export default function SkillsPage() {
  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Skills Management
      </Typography>
      <Typography variant="body1" color="text.secondary" gutterBottom>
        View, configure, and test Aether's skills
      </Typography>

      <Card sx={{ mt: 2 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Available Skills
          </Typography>
          <Typography color="text.secondary">
            Skills management coming soon. This will show all available skills,
            their status, success rates, and allow configuration.
          </Typography>
        </CardContent>
      </Card>
    </Box>
  )
}
