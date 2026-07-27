import { useQuery } from '@tanstack/react-query'
import { Box, Grid, Card, CardContent, Typography, Skeleton } from '@mui/material'
import { Description, Analytics, Warning, CheckCircle } from '@mui/icons-material'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts'
import { dashboardAPI } from '../services/api'

const COLORS = ['#2e7d32', '#ed6c02', '#d32f2f']

function StatCard({ title, value, icon, color }) {
  return (
    <Card>
      <CardContent sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
        <Box sx={{ p: 1.5, borderRadius: 2, bgcolor: `${color}15` }}>
          {icon}
        </Box>
        <Box>
          <Typography variant="body2" color="text.secondary">{title}</Typography>
          <Typography variant="h5" fontWeight={600}>{value}</Typography>
        </Box>
      </CardContent>
    </Card>
  )
}

export default function DashboardPage() {
  const { data: stats, isLoading } = useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: () => dashboardAPI.stats().then(r => r.data),
  })

  const { data: distribution } = useQuery({
    queryKey: ['score-distribution'],
    queryFn: () => dashboardAPI.distribution().then(r => r.data),
  })

  if (isLoading) {
    return (
      <Grid container spacing={3}>
        {[1, 2, 3, 4].map((i) => (
          <Grid item xs={12} sm={6} md={3} key={i}>
            <Skeleton variant="rounded" height={100} />
          </Grid>
        ))}
      </Grid>
    )
  }

  const riskData = [
    { name: 'Faible risque', value: stats?.low_risk_count || 0 },
    { name: 'Risque moyen', value: stats?.medium_risk_count || 0 },
    { name: 'Risque élevé', value: stats?.high_risk_count || 0 },
  ]

  return (
    <Box>
      <Typography variant="h4" gutterBottom>Tableau de bord</Typography>

      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard title="Documents" value={stats?.total_documents || 0} icon={<Description sx={{ color: '#1976d2' }} />} color="#1976d2" />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard title="Analyses" value={stats?.total_analyses || 0} icon={<Analytics sx={{ color: '#9c27b0' }} />} color="#9c27b0" />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard title="Score moyen" value={`${stats?.average_score || 0}%`} icon={<Warning sx={{ color: '#ed6c02' }} />} color="#ed6c02" />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard title="Risque élevé" value={stats?.high_risk_count || 0} icon={<CheckCircle sx={{ color: '#d32f2f' }} />} color="#d32f2f" />
        </Grid>
      </Grid>

      <Grid container spacing={3}>
        <Grid item xs={12} md={8}>
          <Card sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>Distribution des scores</Typography>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={distribution || []}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="range" fontSize={11} />
                <YAxis />
                <Tooltip />
                <Bar dataKey="count" fill="#1976d2" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </Card>
        </Grid>
        <Grid item xs={12} md={4}>
          <Card sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>Répartition des risques</Typography>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie data={riskData} cx="50%" cy="50%" outerRadius={100} dataKey="value" label={({ name, value }) => `${name}: ${value}`}>
                  {riskData.map((_, index) => (
                    <Cell key={index} fill={COLORS[index]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </Card>
        </Grid>
      </Grid>
    </Box>
  )
}
