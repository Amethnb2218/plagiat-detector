import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  Box, Typography, Card, Button, Table, TableBody, TableCell, TableContainer,
  TableHead, TableRow, Chip, IconButton, Dialog, DialogTitle, DialogContent,
  DialogActions, FormControl, InputLabel, Select, MenuItem, LinearProgress
} from '@mui/material'
import { PlayArrow, Visibility, Download } from '@mui/icons-material'
import toast from 'react-hot-toast'
import { analysisAPI, documentsAPI, reportsAPI } from '../services/api'

const statusConfig = {
  pending: { label: 'En attente', color: 'default' },
  running: { label: 'En cours', color: 'warning' },
  completed: { label: 'Terminée', color: 'success' },
  failed: { label: 'Échouée', color: 'error' },
}

function getScoreColor(score) {
  if (score >= 50) return '#d32f2f'
  if (score >= 25) return '#ed6c02'
  return '#2e7d32'
}

export default function AnalysisPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [dialogOpen, setDialogOpen] = useState(false)
  const [selectedDoc, setSelectedDoc] = useState('')
  const [compareDoc, setCompareDoc] = useState('')

  const { data: analyses, isLoading } = useQuery({
    queryKey: ['analyses'],
    queryFn: () => analysisAPI.list().then(r => r.data.results || r.data),
    refetchInterval: 3000,
  })

  const { data: documents } = useQuery({
    queryKey: ['documents-processed'],
    queryFn: () => documentsAPI.list({ status: 'processed' }).then(r => r.data.results || r.data),
  })

  const startMutation = useMutation({
    mutationFn: (data) => analysisAPI.start(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['analyses'] })
      toast.success('Analyse lancée')
      setDialogOpen(false)
    },
    onError: (error) => {
      toast.error(error.response?.data?.error || "Erreur lors du lancement")
    },
  })

  const handleStart = () => {
    const data = { document_id: selectedDoc }
    if (compareDoc) data.compare_with = compareDoc
    startMutation.mutate(data)
  }

  const handleDownloadPDF = async (analysisId) => {
    try {
      const response = await reportsAPI.downloadPDF(analysisId)
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', `rapport_plagiat_${analysisId}.pdf`)
      document.body.appendChild(link)
      link.click()
      link.remove()
    } catch {
      toast.error('Erreur lors du téléchargement')
    }
  }

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">Analyses de plagiat</Typography>
        <Button variant="contained" startIcon={<PlayArrow />} onClick={() => setDialogOpen(true)}>
          Nouvelle analyse
        </Button>
      </Box>

      <Card>
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Document</TableCell>
                <TableCell>Statut</TableCell>
                <TableCell>Score global</TableCell>
                <TableCell>Copie directe</TableCell>
                <TableCell>Paraphrase</TableCell>
                <TableCell>Cross-lingue</TableCell>
                <TableCell>Date</TableCell>
                <TableCell align="right">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {analyses?.map((analysis) => (
                <TableRow key={analysis.id} hover>
                  <TableCell>{analysis.document_title}</TableCell>
                  <TableCell>
                    <Chip
                      label={statusConfig[analysis.status]?.label}
                      color={statusConfig[analysis.status]?.color}
                      size="small"
                    />
                  </TableCell>
                  <TableCell>
                    <Typography fontWeight={600} color={getScoreColor(analysis.overall_score)}>
                      {analysis.overall_score?.toFixed(1)}%
                    </Typography>
                  </TableCell>
                  <TableCell>{analysis.direct_copy_score?.toFixed(1)}%</TableCell>
                  <TableCell>{analysis.paraphrase_score?.toFixed(1)}%</TableCell>
                  <TableCell>{analysis.cross_lingual_score?.toFixed(1)}%</TableCell>
                  <TableCell>{new Date(analysis.created_at).toLocaleDateString('fr-FR')}</TableCell>
                  <TableCell align="right">
                    <IconButton size="small" onClick={() => navigate(`/analysis/${analysis.id}`)}>
                      <Visibility fontSize="small" />
                    </IconButton>
                    {analysis.status === 'completed' && (
                      <IconButton size="small" onClick={() => handleDownloadPDF(analysis.id)}>
                        <Download fontSize="small" />
                      </IconButton>
                    )}
                  </TableCell>
                </TableRow>
              ))}
              {(!analyses || analyses.length === 0) && (
                <TableRow>
                  <TableCell colSpan={8} align="center" sx={{ py: 4 }}>
                    <Typography color="text.secondary">Aucune analyse. Lancez votre première détection.</Typography>
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </TableContainer>
      </Card>

      {/* Dialog nouvelle analyse */}
      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Lancer une analyse de plagiat</DialogTitle>
        <DialogContent>
          <FormControl fullWidth sx={{ mt: 2 }}>
            <InputLabel>Document à analyser</InputLabel>
            <Select value={selectedDoc} onChange={(e) => setSelectedDoc(e.target.value)} label="Document à analyser">
              {documents?.map((doc) => (
                <MenuItem key={doc.id} value={doc.id}>{doc.title}</MenuItem>
              ))}
            </Select>
          </FormControl>
          <FormControl fullWidth sx={{ mt: 2 }}>
            <InputLabel>Comparer avec (optionnel)</InputLabel>
            <Select value={compareDoc} onChange={(e) => setCompareDoc(e.target.value)} label="Comparer avec (optionnel)">
              <MenuItem value="">Tout le corpus</MenuItem>
              {documents?.filter(d => d.id !== selectedDoc).map((doc) => (
                <MenuItem key={doc.id} value={doc.id}>{doc.title}</MenuItem>
              ))}
            </Select>
          </FormControl>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen(false)}>Annuler</Button>
          <Button variant="contained" onClick={handleStart} disabled={!selectedDoc}>
            Lancer l'analyse
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}
