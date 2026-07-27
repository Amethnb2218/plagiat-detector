import io
from django.http import FileResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.units import cm

from apps.detection.models import PlagiarismAnalysis, PlagiarismMatch


class GenerateReportPDFView(APIView):
    """Génère un rapport PDF détaillé de l'analyse de plagiat."""

    def get(self, request, analysis_id):
        try:
            analysis = PlagiarismAnalysis.objects.get(id=analysis_id)
        except PlagiarismAnalysis.DoesNotExist:
            return Response({"error": "Analyse introuvable."}, status=status.HTTP_404_NOT_FOUND)

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=2*cm, bottomMargin=2*cm)
        styles = getSampleStyleSheet()
        elements = []

        title_style = ParagraphStyle('Title', parent=styles['Title'], fontSize=16, spaceAfter=20)
        heading_style = ParagraphStyle('Heading', parent=styles['Heading2'], fontSize=13, spaceAfter=10)
        body_style = ParagraphStyle('Body', parent=styles['Normal'], fontSize=10, spaceAfter=6)

        # Titre
        elements.append(Paragraph("Rapport d'Analyse de Plagiat", title_style))
        elements.append(Spacer(1, 12))

        # Informations document
        elements.append(Paragraph("Informations du document", heading_style))
        info_data = [
            ['Document:', analysis.document.title],
            ['Auteur:', analysis.document.author_name or 'Non spécifié'],
            ['Date d\'analyse:', analysis.created_at.strftime('%d/%m/%Y %H:%M')],
            ['Durée de traitement:', f"{analysis.processing_time:.1f} secondes"],
            ['Segments analysés:', str(analysis.segments_analyzed)],
        ]
        info_table = Table(info_data, colWidths=[5*cm, 12*cm])
        info_table.setStyle(TableStyle([
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        elements.append(info_table)
        elements.append(Spacer(1, 20))

        # Scores
        elements.append(Paragraph("Scores de similarité", heading_style))
        score_data = [
            ['Type de détection', 'Score'],
            ['Score global', f"{analysis.overall_score:.1f}%"],
            ['Copie directe', f"{analysis.direct_copy_score:.1f}%"],
            ['Paraphrase', f"{analysis.paraphrase_score:.1f}%"],
            ['Cross-lingue', f"{analysis.cross_lingual_score:.1f}%"],
            ['Structurel', f"{analysis.structural_score:.1f}%"],
        ]
        score_table = Table(score_data, colWidths=[10*cm, 5*cm])
        score_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1976d2')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(score_table)
        elements.append(Spacer(1, 20))

        # Correspondances trouvées
        matches = analysis.matches.all()[:20]
        if matches:
            elements.append(Paragraph("Passages suspects détectés", heading_style))
            for i, match in enumerate(matches, 1):
                elements.append(Paragraph(
                    f"<b>#{i} - {match.get_match_type_display()} "
                    f"(Similarité: {match.similarity_score:.0%})</b>",
                    body_style
                ))
                source_preview = match.source_text[:150] + '...' if len(match.source_text) > 150 else match.source_text
                target_preview = match.target_text[:150] + '...' if len(match.target_text) > 150 else match.target_text
                elements.append(Paragraph(f"<i>Source:</i> {source_preview}", body_style))
                elements.append(Paragraph(f"<i>Cible:</i> {target_preview}", body_style))
                elements.append(Spacer(1, 8))

        # Conclusion
        elements.append(Spacer(1, 20))
        elements.append(Paragraph("Conclusion", heading_style))
        if analysis.overall_score >= 50:
            conclusion = "Le document présente un taux de similarité élevé. Une vérification manuelle approfondie est fortement recommandée."
        elif analysis.overall_score >= 25:
            conclusion = "Le document présente des passages similaires à des sources existantes. Une vérification est conseillée."
        else:
            conclusion = "Le document ne présente pas de similarité significative avec les sources du corpus."
        elements.append(Paragraph(conclusion, body_style))

        doc.build(elements)
        buffer.seek(0)

        filename = f"rapport_plagiat_{analysis.document.title[:30]}_{analysis.created_at.strftime('%Y%m%d')}.pdf"
        return FileResponse(buffer, as_attachment=True, filename=filename, content_type='application/pdf')
