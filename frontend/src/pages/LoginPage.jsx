import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { Box, Card, TextField, Button, Typography, CircularProgress } from '@mui/material'
import useAuthStore from '../hooks/useAuth'

export default function LoginPage() {
  const navigate = useNavigate()
  const { login, loading } = useAuthStore()
  const [form, setForm] = useState({ username: '', password: '' })

  const handleSubmit = async (e) => {
    e.preventDefault()
    const success = await login(form)
    if (success) navigate('/')
  }

  return (
    <Box sx={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', bgcolor: 'background.default' }}>
      <Card sx={{ p: 4, width: '100%', maxWidth: 420 }}>
        <Typography variant="h4" textAlign="center" color="primary" gutterBottom>
          PlagiatDetect
        </Typography>
        <Typography variant="body2" textAlign="center" color="text.secondary" sx={{ mb: 3 }}>
          Connectez-vous pour accéder à la plateforme
        </Typography>
        <form onSubmit={handleSubmit}>
          <TextField
            fullWidth label="Nom d'utilisateur" margin="normal"
            value={form.username} onChange={(e) => setForm({ ...form, username: e.target.value })}
            required
          />
          <TextField
            fullWidth label="Mot de passe" type="password" margin="normal"
            value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })}
            required
          />
          <Button
            type="submit" variant="contained" fullWidth size="large"
            disabled={loading} sx={{ mt: 2, py: 1.5 }}
          >
            {loading ? <CircularProgress size={24} /> : 'Se connecter'}
          </Button>
        </form>
        <Typography variant="body2" textAlign="center" sx={{ mt: 2 }}>
          Pas encore de compte ?{' '}
          <Link to="/register" style={{ color: '#1976d2' }}>S'inscrire</Link>
        </Typography>
      </Card>
    </Box>
  )
}
