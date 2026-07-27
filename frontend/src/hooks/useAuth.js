import { create } from 'zustand'
import { authAPI } from '../services/api'
import toast from 'react-hot-toast'

const useAuthStore = create((set) => ({
  user: null,
  isAuthenticated: !!localStorage.getItem('access_token'),
  loading: false,

  login: async (credentials) => {
    set({ loading: true })
    try {
      const res = await authAPI.login(credentials)
      localStorage.setItem('access_token', res.data.access)
      localStorage.setItem('refresh_token', res.data.refresh)
      const profileRes = await authAPI.profile()
      set({ user: profileRes.data, isAuthenticated: true, loading: false })
      toast.success('Connexion réussie')
      return true
    } catch (error) {
      set({ loading: false })
      toast.error(error.response?.data?.detail || 'Identifiants incorrects')
      return false
    }
  },

  register: async (data) => {
    set({ loading: true })
    try {
      await authAPI.register(data)
      set({ loading: false })
      toast.success('Inscription réussie. Veuillez vous connecter.')
      return true
    } catch (error) {
      set({ loading: false })
      const errors = error.response?.data
      const message = errors ? Object.values(errors).flat().join(', ') : 'Erreur lors de l\'inscription'
      toast.error(message)
      return false
    }
  },

  loadProfile: async () => {
    try {
      const res = await authAPI.profile()
      set({ user: res.data, isAuthenticated: true })
    } catch {
      set({ user: null, isAuthenticated: false })
    }
  },

  logout: () => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    set({ user: null, isAuthenticated: false })
    toast.success('Déconnexion réussie')
  },
}))

export default useAuthStore
