import re
import spacy
from typing import List, Dict


class HierarchicalSegmenter:
    """Segmentation hiérarchique du texte académique (chapitres > sections > paragraphes > phrases)."""

    CHAPTER_PATTERNS = [
        r'^(?:chapitre|chapter)\s+[\dIVXivx]+',
        r'^(?:CHAPITRE|CHAPTER)\s+[\dIVXivx]+',
        r'^\d+\.\s+[A-Z]',
    ]

    SECTION_PATTERNS = [
        r'^\d+\.\d+\.?\s+',
        r'^(?:section|partie)\s+\d+',
        r'^[A-Z][a-z]+\s*:\s*$',
    ]

    def __init__(self, language='fr'):
        model_name = 'fr_core_news_lg' if language == 'fr' else 'en_core_web_sm'
        try:
            self.nlp = spacy.load(model_name)
        except OSError:
            self.nlp = spacy.load('fr_core_news_sm')
        self.nlp.max_length = 2_000_000

    def segment(self, text: str) -> List[Dict]:
        segments = []
        chapters = self._split_chapters(text)

        position = 0
        for ch_idx, chapter in enumerate(chapters):
            chapter_start = text.find(chapter)
            segments.append({
                'level': 'chapter',
                'position': ch_idx,
                'text': chapter[:200],
                'char_start': chapter_start,
                'char_end': chapter_start + len(chapter),
                'children': [],
            })

            paragraphs = self._split_paragraphs(chapter)
            for p_idx, paragraph in enumerate(paragraphs):
                if len(paragraph.strip()) < 20:
                    continue

                para_start = chapter_start + chapter.find(paragraph)
                para_segment = {
                    'level': 'paragraph',
                    'position': position,
                    'text': paragraph,
                    'char_start': para_start,
                    'char_end': para_start + len(paragraph),
                    'children': [],
                }

                sentences = self._split_sentences(paragraph)
                for s_idx, sentence in enumerate(sentences):
                    if len(sentence.strip()) < 10:
                        continue
                    sent_start = para_start + paragraph.find(sentence)
                    para_segment['children'].append({
                        'level': 'sentence',
                        'position': position,
                        'text': sentence.strip(),
                        'char_start': sent_start,
                        'char_end': sent_start + len(sentence),
                    })
                    position += 1

                segments[-1]['children'].append(para_segment)

        return segments

    def get_flat_sentences(self, text: str) -> List[Dict]:
        """Retourne toutes les phrases à plat pour l'embedding."""
        sentences = []
        doc = self.nlp(text)
        position = 0
        for sent in doc.sents:
            sent_text = sent.text.strip()
            if len(sent_text) >= 15:
                sentences.append({
                    'position': position,
                    'text': sent_text,
                    'char_start': sent.start_char,
                    'char_end': sent.end_char,
                })
                position += 1
        return sentences

    def _split_chapters(self, text: str) -> List[str]:
        pattern = '|'.join(self.CHAPTER_PATTERNS)
        splits = re.split(f'({pattern})', text, flags=re.MULTILINE)
        if len(splits) <= 1:
            return [text]

        chapters = []
        i = 1
        while i < len(splits):
            if i + 1 < len(splits):
                chapters.append(splits[i] + splits[i + 1])
                i += 2
            else:
                chapters.append(splits[i])
                i += 1
        return chapters if chapters else [text]

    def _split_paragraphs(self, text: str) -> List[str]:
        paragraphs = re.split(r'\n\s*\n', text)
        return [p.strip() for p in paragraphs if p.strip()]

    def _split_sentences(self, text: str) -> List[str]:
        doc = self.nlp(text)
        return [sent.text.strip() for sent in doc.sents if len(sent.text.strip()) >= 10]
