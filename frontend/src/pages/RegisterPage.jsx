import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { Box, Card, TextField, Button, Typography, CircularProgress, Grid } from '@mui/material'
import useAuthStore from '../hooks/useAuth'

export default function RegisterPage() {
  const navigate = useNavigate()
  const { register, loading } = useAuthStore()
  const [form, setForm] = useState({
    username: '', email: '', first_name: '', last_name: '',
    password: '', password_confirm: '', institution: '', department: ''
  })

  const handleSubmit = async (e) => {
    e.preventDefault()
    const success = await register(form)
    if (success) navigate('/login')
  }

  const updateField = (field) => (e) => setForm({ ...form, [field]: e.target.value })

  return (
    <Box sx={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', bgcolor: 'background.default', py: 4 }}>
      <Card sx={{ p: 4, width: '100%', maxWidth: 520 }}>
        <Typography variant="h4" textAlign="center" color="primary" gutterBottom>
          Inscription
        </Typography>
        <form onSubmit={handleSubmit}>
          <Grid container spacing={2}>
            <Grid item xs={6}>
              <TextField fullWidth label="Prénom" value={form.first_name} onChange={updateField('first_name')} required />
            </Grid>
            <Grid item xs={6}>
              <TextField fullWidth label="Nom" value={form.last_name} onChange={updateField('last_name')} required />
            </Grid>
            <Grid item xs={12}>
              <TextField fullWidth label="Nom d'utilisateur" value={form.username} onChange={updateField('username')} required />
            </Grid>
            <Grid item xs={12}>
              <TextField fullWidth label="Email" type="email" value={form.email} onChange={updateField('email')} required />
            </Grid>
            <Grid item xs={12}>
              <TextField fullWidth label="Institution" value={form.institution} onChange={updateField('institution')} />
            </Grid>
            <Grid item xs={12}>
              <TextField fullWidth label="Département" value={form.department} onChange={updateField('department')} />
            </Grid>
            <Grid item xs={6}>
              <TextField fullWidth label="Mot de passe" type="password" value={form.password} onChange={updateField('password')} required />
            </Grid>
            <Grid item xs={6}>
              <TextField fullWidth label="Confirmer" type="password" value={form.password_confirm} onChange={updateField('password_confirm')} required />
            </Grid>
          </Grid>
          <Button type="submit" variant="contained" fullWidth size="large" disabled={loading} sx={{ mt: 3, py: 1.5 }}>
            {loading ? <CircularProgress size={24} /> : "S'inscrire"}
          </Button>
        </form>
        <Typography variant="body2" textAlign="center" sx={{ mt: 2 }}>
          Déjà inscrit ? <Link to="/login" style={{ color: '#1976d2' }}>Se connecter</Link>
        </Typography>
      </Card>
    </Box>
  )
}
