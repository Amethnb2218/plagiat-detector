import { useState } from 'react'
import { Box, Typography, Card, CardContent, TextField, Button, Grid, Avatar } from '@mui/material'
import { useMutation } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import useAuthStore from '../hooks/useAuth'
import { authAPI } from '../services/api'

export default function ProfilePage() {
  const { user, loadProfile } = useAuthStore()
  const [form, setForm] = useState({
    first_name: user?.first_name || '',
    last_name: user?.last_name || '',
    email: user?.email || '',
    institution: user?.institution || '',
    department: user?.department || '',
  })

  const updateMutation = useMutation({
    mutationFn: (data) => authAPI.updateProfile(data),
    onSuccess: () => {
      loadProfile()
      toast.success('Profil mis à jour')
    },
    onError: () => toast.error('Erreur lors de la mise à jour'),
  })

  const handleSubmit = (e) => {
    e.preventDefault()
    updateMutation.mutate(form)
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>Mon profil</Typography>
      <Card sx={{ maxWidth: 600 }}>
        <CardContent sx={{ p: 4 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
            <Avatar sx={{ width: 64, height: 64, bgcolor: 'primary.main', fontSize: 24 }}>
              {user?.first_name?.[0]}{user?.last_name?.[0]}
            </Avatar>
            <Box>
              <Typography variant="h6">{user?.first_name} {user?.last_name}</Typography>
              <Typography variant="body2" color="text.secondary">@{user?.username} - {user?.role === 'admin' ? 'Administrateur' : 'Enseignant'}</Typography>
            </Box>
          </Box>
          <form onSubmit={handleSubmit}>
            <Grid container spacing={2}>
              <Grid item xs={6}>
                <TextField fullWidth label="Prénom" value={form.first_name} onChange={(e) => setForm({ ...form, first_name: e.target.value })} />
              </Grid>
              <Grid item xs={6}>
                <TextField fullWidth label="Nom" value={form.last_name} onChange={(e) => setForm({ ...form, last_name: e.target.value })} />
              </Grid>
              <Grid item xs={12}>
                <TextField fullWidth label="Email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
              </Grid>
              <Grid item xs={12}>
                <TextField fullWidth label="Institution" value={form.institution} onChange={(e) => setForm({ ...form, institution: e.target.value })} />
              </Grid>
              <Grid item xs={12}>
                <TextField fullWidth label="Département" value={form.department} onChange={(e) => setForm({ ...form, department: e.target.value })} />
              </Grid>
            </Grid>
            <Button type="submit" variant="contained" sx={{ mt: 3 }}>
              Enregistrer
            </Button>
          </form>
        </CardContent>
      </Card>
    </Box>
  )
}
