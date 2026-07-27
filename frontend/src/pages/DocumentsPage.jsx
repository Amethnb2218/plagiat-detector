import { useState, useCallback } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  Box, Typography, Card, Button, Table, TableBody, TableCell, TableContainer,
  TableHead, TableRow, Chip, IconButton, LinearProgress, Dialog, DialogTitle,
  DialogContent, DialogActions
} from '@mui/material'
import { CloudUpload, Delete, Visibility } from '@mui/icons-material'
import { useDropzone } from 'react-dropzone'
import toast from 'react-hot-toast'
import { documentsAPI } from '../services/api'

const statusColors = {
  uploaded: 'default',
  processing: 'warning',
  processed: 'success',
  error: 'error',
}

const statusLabels = {
  uploaded: 'Téléversé',
  processing: 'En cours',
  processed: 'Traité',
  error: 'Erreur',
}

export default function DocumentsPage() {
  const queryClient = useQueryClient()
  const [uploadProgress, setUploadProgress] = useState(0)
  const [uploading, setUploading] = useState(false)
  const [dialogOpen, setDialogOpen] = useState(false)

  const { data: documents, isLoading } = useQuery({
    queryKey: ['documents'],
    queryFn: () => documentsAPI.list().then(r => r.data.results || r.data),
    refetchInterval: 5000,
  })

  const uploadMutation = useMutation({
    mutationFn: (file) => {
      const formData = new FormData()
      formData.append('file', file)
      formData.append('title', file.name.replace(/\.[^/.]+$/, ''))
      return documentsAPI.upload(formData, (e) => {
        setUploadProgress(Math.round((e.loaded / e.total) * 100))
      })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] })
      toast.success('Document téléversé avec succès')
      setUploading(false)
      setUploadProgress(0)
    },
    onError: (error) => {
      toast.error(error.response?.data?.file?.[0] || 'Erreur lors du téléversement')
      setUploading(false)
      setUploadProgress(0)
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id) => documentsAPI.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] })
      toast.success('Document supprimé')
    },
  })

  const onDrop = useCallback((acceptedFiles) => {
    if (acceptedFiles.length > 0) {
      setUploading(true)
      uploadMutation.mutate(acceptedFiles[0])
    }
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx']
    },
    maxSize: 52428800,
    multiple: false,
  })

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">Documents</Typography>
      </Box>

      {/* Zone de dépôt */}
      <Card
        {...getRootProps()}
        sx={{
          p: 4, mb: 3, textAlign: 'center', cursor: 'pointer',
          border: '2px dashed', borderColor: isDragActive ? 'primary.main' : 'divider',
          bgcolor: isDragActive ? 'primary.50' : 'background.paper',
          transition: 'all 0.2s',
        }}
      >
        <input {...getInputProps()} />
        <CloudUpload sx={{ fontSize: 48, color: 'primary.main', mb: 1 }} />
        <Typography variant="h6" color="text.secondary">
          {isDragActive ? 'Déposez le fichier ici...' : 'Glissez-déposez un fichier PDF ou DOCX'}
        </Typography>
        <Typography variant="body2" color="text.secondary">
          ou cliquez pour sélectionner (max 50 Mo)
        </Typography>
        {uploading && (
          <Box sx={{ mt: 2, width: '50%', mx: 'auto' }}>
            <LinearProgress variant="determinate" value={uploadProgress} />
            <Typography variant="caption">{uploadProgress}%</Typography>
          </Box>
        )}
      </Card>

      {/* Liste des documents */}
      <Card>
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Titre</TableCell>
                <TableCell>Type</TableCell>
                <TableCell>Pages</TableCell>
                <TableCell>Statut</TableCell>
                <TableCell>Date</TableCell>
                <TableCell align="right">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {documents?.map((doc) => (
                <TableRow key={doc.id} hover>
                  <TableCell>{doc.title}</TableCell>
                  <TableCell>
                    <Chip label={doc.file_type.toUpperCase()} size="small" variant="outlined" />
                  </TableCell>
                  <TableCell>{doc.page_count}</TableCell>
                  <TableCell>
                    <Chip label={statusLabels[doc.status]} color={statusColors[doc.status]} size="small" />
                  </TableCell>
                  <TableCell>{new Date(doc.uploaded_at).toLocaleDateString('fr-FR')}</TableCell>
                  <TableCell align="right">
                    <IconButton size="small" color="error" onClick={() => deleteMutation.mutate(doc.id)}>
                      <Delete fontSize="small" />
                    </IconButton>
                  </TableCell>
                </TableRow>
              ))}
              {(!documents || documents.length === 0) && (
                <TableRow>
                  <TableCell colSpan={6} align="center" sx={{ py: 4 }}>
                    <Typography color="text.secondary">Aucun document. Téléversez votre premier fichier.</Typography>
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </TableContainer>
      </Card>
    </Box>
  )
}
