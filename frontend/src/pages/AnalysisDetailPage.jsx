import { useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import {
  Box, Typography, Card, CardContent, Grid, Chip, LinearProgress,
  Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Paper
} from '@mui/material'
import Highlighter from 'react-highlight-words'
import { analysisAPI } from '../services/api'

const matchTypeConfig = {
  direct: { label: 'Copie directe', color: '#d32f2f' },
  paraphrase: { label: 'Paraphrase', color: '#ed6c02' },
  cross_lingual: { label: 'Cross-lingue', color: '#9c27b0' },
  structural: { label: 'Structurelle', color: '#1976d2' },
}

function ScoreGauge({ label, value, color }) {
  return (
    <Box sx={{ mb: 2 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
        <Typography variant="body2">{label}</Typography>
        <Typography variant="body2" fontWeight={600} color={color}>{value.toFixed(1)}%</Typography>
      </Box>
      <LinearProgress
        variant="determinate"
        value={Math.min(value, 100)}
        sx={{ height: 8, borderRadius: 4, bgcolor: '#eee', '& .MuiLinearProgress-bar': { bgcolor: color, borderRadius: 4 } }}
      />
    </Box>
  )
}

export default function AnalysisDetailPage() {
  const { id } = useParams()

  const { data: analysis, isLoading } = useQuery({
    queryKey: ['analysis', id],
    queryFn: () => analysisAPI.get(id).then(r => r.data),
    refetchInterval: (data) => data?.status === 'running' ? 2000 : false,
  })

  if (isLoading) return <LinearProgress />
  if (!analysis) return <Typography>Analyse introuvable</Typography>

  const getScoreColor = (score) => {
    if (score >= 50) return '#d32f2f'
    if (score >= 25) return '#ed6c02'
    return '#2e7d32'
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>Résultats d'analyse</Typography>
      <Typography variant="body1" color="text.secondary" gutterBottom>
        {analysis.document_title}
      </Typography>

      {analysis.status === 'running' && (
        <Card sx={{ mb: 3, p: 2 }}>
          <Typography gutterBottom>Analyse en cours...</Typography>
          <LinearProgress />
        </Card>
      )}

      {analysis.status === 'completed' && (
        <>
          {/* Scores */}
          <Grid container spacing={3} sx={{ mb: 4 }}>
            <Grid item xs={12} md={4}>
              <Card sx={{ p: 3, textAlign: 'center' }}>
                <Typography variant="h2" fontWeight={700} color={getScoreColor(analysis.overall_score)}>
                  {analysis.overall_score.toFixed(1)}%
                </Typography>
                <Typography variant="h6" color="text.secondary">Score global de plagiat</Typography>
                <Chip
                  label={analysis.overall_score >= 50 ? 'Risque élevé' : analysis.overall_score >= 25 ? 'Risque moyen' : 'Risque faible'}
                  color={analysis.overall_score >= 50 ? 'error' : analysis.overall_score >= 25 ? 'warning' : 'success'}
                  sx={{ mt: 1 }}
                />
              </Card>
            </Grid>
            <Grid item xs={12} md={8}>
              <Card sx={{ p: 3 }}>
                <Typography variant="h6" gutterBottom>Détails des scores</Typography>
                <ScoreGauge label="Copie directe" value={analysis.direct_copy_score} color="#d32f2f" />
                <ScoreGauge label="Paraphrase sémantique" value={analysis.paraphrase_score} color="#ed6c02" />
                <ScoreGauge label="Cross-lingue (traduction)" value={analysis.cross_lingual_score} color="#9c27b0" />
                <ScoreGauge label="Réorganisation structurelle" value={analysis.structural_score} color="#1976d2" />
              </Card>
            </Grid>
          </Grid>

          {/* Infos */}
          <Grid container spacing={3} sx={{ mb: 4 }}>
            <Grid item xs={6} md={3}>
              <Card sx={{ p: 2, textAlign: 'center' }}>
                <Typography variant="h5" fontWeight={600}>{analysis.segments_analyzed}</Typography>
                <Typography variant="body2" color="text.secondary">Segments analysés</Typography>
              </Card>
            </Grid>
            <Grid item xs={6} md={3}>
              <Card sx={{ p: 2, textAlign: 'center' }}>
                <Typography variant="h5" fontWeight={600}>{analysis.matches_found}</Typography>
                <Typography variant="body2" color="text.secondary">Correspondances</Typography>
              </Card>
            </Grid>
            <Grid item xs={6} md={3}>
              <Card sx={{ p: 2, textAlign: 'center' }}>
                <Typography variant="h5" fontWeight={600}>{analysis.processing_time?.toFixed(1)}s</Typography>
                <Typography variant="body2" color="text.secondary">Temps de traitement</Typography>
              </Card>
            </Grid>
            <Grid item xs={6} md={3}>
              <Card sx={{ p: 2, textAlign: 'center' }}>
                <Typography variant="h5" fontWeight={600}>
                  {analysis.completed_at ? new Date(analysis.completed_at).toLocaleDateString('fr-FR') : '-'}
                </Typography>
                <Typography variant="body2" color="text.secondary">Date</Typography>
              </Card>
            </Grid>
          </Grid>

          {/* Passages suspects */}
          {analysis.matches && analysis.matches.length > 0 && (
            <Card sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom>Passages suspects détectés</Typography>
              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>#</TableCell>
                      <TableCell>Type</TableCell>
                      <TableCell>Similarité</TableCell>
                      <TableCell>Passage source</TableCell>
                      <TableCell>Passage trouvé</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {analysis.matches.map((match, idx) => (
                      <TableRow key={match.id || idx}>
                        <TableCell>{idx + 1}</TableCell>
                        <TableCell>
                          <Chip
                            label={matchTypeConfig[match.match_type]?.label || match.match_type}
                            size="small"
                            sx={{ bgcolor: matchTypeConfig[match.match_type]?.color + '20', color: matchTypeConfig[match.match_type]?.color, fontWeight: 500 }}
                          />
                        </TableCell>
                        <TableCell>
                          <Typography fontWeight={600} color={getScoreColor(match.similarity_score * 100)}>
                            {(match.similarity_score * 100).toFixed(0)}%
                          </Typography>
                        </TableCell>
                        <TableCell sx={{ maxWidth: 300 }}>
                          <Typography variant="body2" sx={{ fontSize: 12 }}>
                            {match.source_text?.substring(0, 150)}
                            {match.source_text?.length > 150 && '...'}
                          </Typography>
                        </TableCell>
                        <TableCell sx={{ maxWidth: 300 }}>
                          <Paper variant="outlined" sx={{ p: 1, bgcolor: '#fff3e0' }}>
                            <Typography variant="body2" sx={{ fontSize: 12 }}>
                              {match.target_text?.substring(0, 150)}
                              {match.target_text?.length > 150 && '...'}
                            </Typography>
                          </Paper>
                          {match.target_document_title && (
                            <Typography variant="caption" color="text.secondary">
                              Source: {match.target_document_title}
                            </Typography>
                          )}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </Card>
          )}
        </>
      )}
    </Box>
  )
}
