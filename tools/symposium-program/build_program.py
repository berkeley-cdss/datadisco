"""Build foldable (saddle-stitch) symposium programs from the MyST symposium pages.

Each program is read from symposium/<page>.md and written to assets/program-<key>.pdf as
half-letter booklet pages imposed on letter landscape sheets: print double-sided, flipping
on the short edge, then stack and fold.

Setup (once):   pip install reportlab pypdf
Build all:      python tools/symposium-program/build_program.py
Build one:      python tools/symposium-program/build_program.py sp26
Preview:        add --preview to also write program-<key>-reading.pdf (pages in reading
                order, not imposed) next to this script for checking the design.

New semester: add its page to SEMESTERS at the bottom of this file, then link the PDF from
the symposium page the same way SP26symposium.md does. The page needs the same sections as
the existing ones (About Data Discovery, Acknowledgments, Schedule, an Awardees section, and
Posters or Poster Categories), with each entry written as **Title**, a students line and a
"Mentored by ..." line.

Fonts are Inter and Source Serif 4 (SIL Open Font License, see fonts/). The logos are the
CDSS logo from assets/cdss-logo.svg rendered to PNG.
"""
import io
import random
import re
import sys
from pathlib import Path
from xml.sax.saxutils import escape

from pypdf import PageObject, PdfReader, PdfWriter, Transformation
from reportlab.graphics import renderPDF
from reportlab.graphics.barcode.qr import QrCodeWidget
from reportlab.graphics.shapes import Drawing
from reportlab.lib.colors import HexColor, white
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import (BaseDocTemplate, CondPageBreak, Flowable, Frame, KeepTogether,
                                PageBreak, PageTemplate, Paragraph, Spacer)

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
FONTS = HERE / 'fonts'

PAGE_W, PAGE_H = 5.5 * inch, 8.5 * inch          # half-letter booklet page
SHEET_W, SHEET_H = 11 * inch, 8.5 * inch         # letter landscape print sheet
MARGIN_X, MARGIN_TOP, MARGIN_BOTTOM = 0.55 * inch, 0.6 * inch, 0.7 * inch

BLUE = HexColor('#002676')
GOLD = HexColor('#FDB515')
GOLD_DARK = HexColor('#B8860B')
TINT = HexColor('#EEF2FA')
INK = HexColor('#1B1F2A')
MUTED = HexColor('#5B6474')
RULE = HexColor('#D9DEE8')

for name, file in [('Inter', 'Inter-Regular'), ('Inter-SemiBold', 'Inter-SemiBold'),
                   ('Inter-Bold', 'Inter-Bold'), ('Inter-Italic', 'Inter-Italic'),
                   ('Serif', 'SourceSerif-SemiBold'), ('Serif-Bold', 'SourceSerif-Bold'),
                   ('Serif-Italic', 'SourceSerif-Italic')]:
    pdfmetrics.registerFont(TTFont(name, str(FONTS / f'{file}.ttf')))
pdfmetrics.registerFontFamily('Inter', normal='Inter', bold='Inter-Bold',
                              italic='Inter-Italic', boldItalic='Inter-Bold')

S = {
    'h1': ParagraphStyle('h1', fontName='Serif-Bold', fontSize=21, leading=25, textColor=BLUE,
                         spaceAfter=4),
    'kicker': ParagraphStyle('kicker', fontName='Inter-Bold', fontSize=7, leading=9,
                             textColor=GOLD_DARK, spaceAfter=3),
    'body': ParagraphStyle('body', fontName='Inter', fontSize=8.6, leading=13, textColor=INK,
                           spaceAfter=7),
    'small': ParagraphStyle('small', fontName='Inter', fontSize=7.6, leading=11.2, textColor=INK,
                            spaceAfter=6),
    'title': ParagraphStyle('title', fontName='Serif', fontSize=9.6, leading=11.8,
                            textColor=BLUE, spaceAfter=1.5),
    'people': ParagraphStyle('people', fontName='Inter', fontSize=7.4, leading=9.6,
                             textColor=INK),
    'mentor': ParagraphStyle('mentor', fontName='Inter-Italic', fontSize=7, leading=9.2,
                             textColor=MUTED),
    'award_label': ParagraphStyle('award_label', fontName='Inter-Bold', fontSize=6.4,
                                  leading=8, textColor=GOLD_DARK, spaceAfter=2),
    'time': ParagraphStyle('time', fontName='Inter-Bold', fontSize=9, leading=11, textColor=BLUE),
    'event': ParagraphStyle('event', fontName='Inter-SemiBold', fontSize=9, leading=11,
                            textColor=INK),
    'event_detail': ParagraphStyle('event_detail', fontName='Inter', fontSize=7.8, leading=10,
                                   textColor=MUTED),
    'notes': ParagraphStyle('notes', fontName='Serif-Italic', fontSize=13, leading=16,
                            textColor=BLUE, alignment=TA_CENTER),
}


# --------------------------------------------------------------------------- parsing

def clean(text):
    return re.sub(r'\s+', ' ', text.replace('**', '')).strip()


def parse_entries(block):
    """Entries are '**Title**' followed by a people line and a mentor line."""
    entries = []
    for chunk in re.split(r'\n(?=\*\*)', block.strip()):
        lines = [l.strip() for l in chunk.strip().splitlines() if l.strip()]
        if not lines or not lines[0].startswith('**'):
            continue
        title = clean(lines[0])
        entry = {'title': title, 'people': '', 'mentors': '', 'award': ''}
        m = re.match(r'(.*?)\s*\((Awarded for .*|Honorable Mention for .*)\)$', title)
        if m:
            entry['title'], entry['award'] = m.group(1), m.group(2)
        for line in lines[1:]:
            line = clean(line)
            if re.match(r'(Mentored by|Advised by)\s', line):
                entry['mentors'] = line
            elif re.match(r'Mentors?:\s', line):
                entry['mentors'] = 'Mentored by ' + line.split(':', 1)[1].strip()
            elif line.startswith('Awardees:'):
                entry['people'] = line.split(':', 1)[1].strip()
            elif not entry['people']:
                entry['people'] = line
        entries.append(entry)
    return entries


def parse_page(path):
    text = Path(path).read_text(encoding='utf-8')
    text = re.sub(r'<!--.*?-->', '', text, flags=re.S)
    text = re.sub(r'^---\n.*?\n---\n', '', text, flags=re.S)
    sections = re.split(r'^## +(.+)$', text, flags=re.M)
    data = {'awards': [], 'categories': [], 'elsewhere': []}
    mode = None
    for heading, block in zip(sections[1::2], sections[2::2]):
        h = heading.strip()
        block = block.replace('\n---\n', '\n')
        if h == 'About Data Discovery':
            data['about'] = [clean(p) for p in block.strip().split('\n\n') if p.strip()]
        elif h == 'Acknowledgments':
            data['acknowledgments'] = clean(block)
        elif h == 'Schedule':
            sentence = clean(block.strip().split('\n')[0])
            data['date'] = re.search(r'on (\w+day, \w+ \d+, \d{4})', sentence).group(1)
            venue = re.search(r'in the (.*?) at UC Berkeley', sentence).group(1)
            data['venue'] = venue[0].upper() + venue[1:]
            data['schedule'] = [(clean(t), clean(a)) for t, a in
                                re.findall(r'^- \*\*(.+?)\*\*\s*(.+)$', block, flags=re.M)]
        elif 'Awardees' in h:
            mode = 'awards'
            data['awards'] += [dict(e, award=e['award'] or '') for e in parse_entries(block)]
        elif h in ('Research and Storytelling Awards', 'Honorable Mentions'):
            data['awards'] += [dict(e, award=h.rstrip('s') if h.endswith('Mentions') else
                                    'Research & Storytelling Award') for e in parse_entries(block)]
        elif h == 'Poster Categories':
            mode = 'posters'
        elif h == 'Posters':
            mode = 'posters'
            data['categories'].append(('Posters', parse_entries(block)))
        elif h == 'Other Presentations Elsewhere':
            data['elsewhere'] = parse_entries(block)
        elif mode == 'posters':
            data['categories'].append((h, parse_entries(block)))
    # The source occasionally lists the same poster twice; keep the first.
    seen = set()
    for i, (cat, entries) in enumerate(data['categories']):
        unique = []
        for e in entries:
            key = (e['title'].lower(), e['people'].lower())
            if key not in seen:
                seen.add(key)
                unique.append(e)
        data['categories'][i] = (cat, unique)
    return data


# --------------------------------------------------------------------------- flowables

class Rule(Flowable):
    def __init__(self, width, color=RULE, thickness=0.6, space=6):
        super().__init__()
        self.width, self.color, self.thickness, self.space = width, color, thickness, space

    def wrap(self, aw, ah):
        return self.width, self.space * 2

    def draw(self):
        self.canv.setStrokeColor(self.color)
        self.canv.setLineWidth(self.thickness)
        self.canv.line(0, self.space, self.width, self.space)


class GoldBar(Flowable):
    """Short gold accent under page titles."""
    def wrap(self, aw, ah):
        return aw, 12

    def draw(self):
        self.canv.setFillColor(GOLD)
        self.canv.roundRect(0, 6, 34, 3.2, 1.6, stroke=0, fill=1)


class CategoryHeader(Flowable):
    def __init__(self, name, count):
        super().__init__()
        self.name, self.count = name, count

    def wrap(self, aw, ah):
        self.aw = aw
        return aw, 24

    def draw(self):
        c = self.canv
        c.setFillColor(BLUE)
        c.roundRect(0, 3, self.aw, 18, 4, stroke=0, fill=1)
        c.setFillColor(GOLD)
        c.roundRect(0, 3, 5, 18, 2, stroke=0, fill=1)
        c.rect(3, 3, 2, 18, stroke=0, fill=1)
        c.setFillColor(white)
        c.setFont('Inter-Bold', 8.2)
        c.drawString(12, 9.2, self.name.upper())
        c.setFont('Inter', 7)
        label = f'{self.count} poster' + ('' if self.count == 1 else 's')
        c.drawRightString(self.aw - 9, 9.4, label)


class Card(Flowable):
    """Award card: tinted box with a gold side bar around a paragraph stack."""
    def __init__(self, paragraphs, pad=8):
        super().__init__()
        self.paragraphs, self.pad = paragraphs, pad

    def wrap(self, aw, ah):
        self.aw = aw
        inner = aw - self.pad * 2 - 6
        self.sizes = [p.wrap(inner, ah) for p in self.paragraphs]
        self.h = sum(h for _, h in self.sizes) + self.pad * 2
        return aw, self.h + 6

    def draw(self):
        c = self.canv
        c.setFillColor(TINT)
        c.roundRect(0, 6, self.aw, self.h, 5, stroke=0, fill=1)
        c.setFillColor(GOLD)
        c.roundRect(0, 6, 4, self.h, 2, stroke=0, fill=1)
        y = 6 + self.h - self.pad
        for p, (_, h) in zip(self.paragraphs, self.sizes):
            y -= h
            p.drawOn(c, self.pad + 6, y)


class Timeline(Flowable):
    def __init__(self, items):
        super().__init__()
        self.items = items

    def wrap(self, aw, ah):
        self.aw = aw
        self.rows = []
        for time, event, detail in self.items:
            paras = [Paragraph(escape(event), S['event'])]
            if detail:
                paras.append(Paragraph(escape(detail), S['event_detail']))
            h = sum(p.wrap(aw - 92, ah)[1] for p in paras)
            self.rows.append((time, paras, max(h, 14) + 12))
        return aw, sum(r[2] for r in self.rows)

    def draw(self):
        c = self.canv
        total = sum(r[2] for r in self.rows)
        y = total
        c.setStrokeColor(RULE)
        c.setLineWidth(1.4)
        c.line(70, 6, 70, total - 6)
        for time, paras, h in self.rows:
            top = y - 4
            c.setFillColor(BLUE)
            c.setFont('Inter-Bold', 8.6)
            c.drawRightString(60, top - 9, time)
            c.setFillColor(GOLD)
            c.circle(70, top - 6, 4, stroke=0, fill=1)
            c.setFillColor(white)
            c.circle(70, top - 6, 1.6, stroke=0, fill=1)
            py = top
            for p in paras:
                _, ph = p.wrap(self.aw - 92, 1000)
                py -= ph
                p.drawOn(c, 84, py)
            y -= h


class StatTiles(Flowable):
    """'At a glance' row: big serif numbers over small labels."""
    def __init__(self, stats):
        super().__init__()
        self.stats = stats

    def wrap(self, aw, ah):
        self.aw = aw
        return aw, 62

    def draw(self):
        c = self.canv
        gap = 8
        w = (self.aw - gap * (len(self.stats) - 1)) / len(self.stats)
        for i, (num, label) in enumerate(self.stats):
            x = i * (w + gap)
            c.setFillColor(TINT)
            c.roundRect(x, 0, w, 58, 6, stroke=0, fill=1)
            c.setFillColor(GOLD)
            c.roundRect(x + w / 2 - 10, 50, 20, 2.6, 1.3, stroke=0, fill=1)
            c.setFillColor(BLUE)
            c.setFont('Serif-Bold', 22)
            c.drawCentredString(x + w / 2, 24, str(num))
            c.setFillColor(MUTED)
            c.setFont('Inter-SemiBold', 6.6)
            c.drawCentredString(x + w / 2, 11, label.upper())


def entry_block(e):
    parts = [Paragraph(escape(e['title']), S['title'])]
    if e['people']:
        parts.append(Paragraph(escape(e['people']), S['people']))
    if e['mentors']:
        parts.append(Paragraph(escape(e['mentors']), S['mentor']))
    return KeepTogether(parts + [Spacer(1, 7.5)])


def page_title(kicker, title):
    return [Paragraph(kicker.upper(), S['kicker']), Paragraph(escape(title), S['h1']), GoldBar(),
            Spacer(1, 4)]


# --------------------------------------------------------------------------- pages

def interior_story(d, season, pad_notes=0):
    story = []
    # Welcome + schedule
    story += page_title(f'{season} Symposium', 'Welcome')
    for p in d['about']:
        story.append(Paragraph(escape(p), S['body']))
    story += [Spacer(1, 8), Paragraph('SCHEDULE', S['kicker']),
              Paragraph(escape(d['date']), ParagraphStyle('d', parent=S['h1'], fontSize=14,
                                                          leading=17)),
              Paragraph(escape(d['venue']) + ', UC Berkeley', S['small']), Spacer(1, 6)]
    items = []
    for time, act in d['schedule']:
        event, _, detail = act.partition(':')
        items.append((time, event.strip(), detail.strip()))
    total = sum(len(es) for _, es in d['categories'])
    stats = [(total, 'Research posters'), (len(d['awards']), 'Award recipients')]
    if len(d['categories']) > 1:
        stats.append((len(d['categories']), 'Research areas'))
    if d['elsewhere']:
        stats.append((len(d['elsewhere']), 'Other venues'))
    story += [Timeline(items), Spacer(1, 14), Paragraph('AT A GLANCE', S['kicker']), Spacer(1, 3),
              StatTiles(stats), PageBreak()]

    # Awards
    story += page_title('Celebrating excellence', 'Award Recipients')
    for e in d['awards']:
        paras = []
        if e['award']:
            paras.append(Paragraph(escape(e['award']).upper(), S['award_label']))
        paras.append(Paragraph(escape(e['title']), S['title']))
        if e['people']:
            paras.append(Paragraph(escape(e['people']), S['people']))
        if e['mentors']:
            paras.append(Paragraph(escape(e['mentors']), S['mentor']))
        story.append(Card(paras))
    # Start the poster session on the same page when there's room for its opening.
    story += [CondPageBreak(3.2 * inch), Spacer(1, 10)]

    # Posters
    story += page_title(f'{total} research projects', 'Poster Session')
    story.append(Paragraph('Student research teams present their work alongside the mentors and '
                           'organizations who made it possible.', S['small']))
    story.append(Spacer(1, 4))
    grouped = len(d['categories']) > 1
    for cat, entries in d['categories']:
        if grouped:
            story += [CondPageBreak(80), CategoryHeader(cat, len(entries)), Spacer(1, 5)]
        story += [entry_block(e) for e in entries]
    if d['elsewhere']:
        story += [CondPageBreak(80), Spacer(1, 6),
                  Paragraph('ALSO PRESENTING ELSEWHERE', S['kicker']),
                  Paragraph('These Data Discovery teams are sharing their work at other venues.',
                            S['small'])]
        story += [entry_block(e) for e in d['elsewhere']]
    story.append(PageBreak())

    # Acknowledgments
    story += page_title('With gratitude', 'Acknowledgments')
    story.append(Paragraph(escape(d['acknowledgments']), S['body']))
    for _ in range(pad_notes):
        story += [PageBreak(), Spacer(1, 10), Paragraph('Notes', S['notes']), Spacer(1, 14)]
        story += [Rule(PAGE_W - 2 * MARGIN_X, space=11) for _ in range(20)]
    return story


def build_interior(d, season, pad_notes=0):
    buf = io.BytesIO()
    doc = BaseDocTemplate(buf, pagesize=(PAGE_W, PAGE_H), leftMargin=MARGIN_X,
                          rightMargin=MARGIN_X, topMargin=MARGIN_TOP, bottomMargin=MARGIN_BOTTOM,
                          title=f'Data Discovery {season} Symposium Program',
                          author='CDSS Data Discovery')
    frame = Frame(MARGIN_X, MARGIN_BOTTOM, PAGE_W - 2 * MARGIN_X,
                  PAGE_H - MARGIN_TOP - MARGIN_BOTTOM, 0, 0, 0, 0)

    def footer(c, _doc):
        c.saveState()
        page_no = _doc.page + 1  # the cover is page 1
        c.setStrokeColor(GOLD)
        c.setLineWidth(0.8)
        c.line(MARGIN_X, 0.5 * inch, PAGE_W - MARGIN_X, 0.5 * inch)
        c.setFont('Inter', 6.6)
        c.setFillColor(MUTED)
        c.drawString(MARGIN_X, 0.36 * inch, f'Data Discovery Symposium  ·  {season}')
        c.setFont('Inter-Bold', 7)
        c.setFillColor(BLUE)
        c.drawRightString(PAGE_W - MARGIN_X, 0.36 * inch, str(page_no))
        c.restoreState()

    doc.addPageTemplates([PageTemplate('inner', [frame], onPage=footer)])
    doc.build(interior_story(d, season, pad_notes))
    return buf.getvalue()


def scatter_motif(c, seed, x0, y0, w, h):
    """Decorative 'data' scatter: dots along a gently rising trend."""
    rnd = random.Random(seed)
    c.saveState()
    pts = []
    for i in range(70):
        x = x0 + rnd.random() * w
        trend = y0 + h * (0.25 + 0.5 * (x - x0) / w)
        y = trend + rnd.gauss(0, h * 0.16)
        y = min(max(y, y0), y0 + h)
        r = rnd.choice([1.2, 1.6, 2.2, 3, 4.2])
        pts.append((x, y))
        gold = rnd.random() < 0.35
        c.setFillColor(GOLD if gold else white)
        c.setFillAlpha(0.95 if gold else rnd.choice([0.18, 0.28, 0.4]))
        c.circle(x, y, r, stroke=0, fill=1)
    c.setStrokeColor(GOLD)
    c.setStrokeAlpha(0.9)
    c.setLineWidth(1.3)
    path = c.beginPath()
    path.moveTo(x0, y0 + h * 0.22)
    for k in range(1, 9):
        fx = k / 8
        path.lineTo(x0 + fx * w, y0 + h * (0.22 + 0.5 * fx) + rnd.gauss(0, h * 0.05))
    c.drawPath(path, stroke=1, fill=0)
    c.restoreState()


def build_cover(d, season, seed):
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=(PAGE_W, PAGE_H))
    c.setFillColor(BLUE)
    c.rect(0, 0, PAGE_W, PAGE_H, stroke=0, fill=1)
    logo_w = 2.9 * inch
    c.drawImage(str(HERE / 'logo-white.png'), MARGIN_X, PAGE_H - 0.55 * inch - logo_w * 508 / 2400,
                width=logo_w, height=logo_w * 508 / 2400, mask='auto')
    scatter_motif(c, seed, MARGIN_X, 4.55 * inch, PAGE_W - 2 * MARGIN_X, 1.9 * inch)
    c.setFillColor(GOLD)
    c.setFont('Inter-Bold', 8.5)
    c.drawString(MARGIN_X, 3.95 * inch, 'CDSS  DATA  DISCOVERY')
    c.setFillColor(white)
    c.setFont('Serif-Bold', 44)
    c.drawString(MARGIN_X - 2, 3.3 * inch, 'Symposium')
    c.setFillColor(GOLD)
    c.setFont('Serif-Italic', 26)
    c.drawString(MARGIN_X, 2.82 * inch, season)
    c.setStrokeColor(GOLD)
    c.setLineWidth(1)
    c.line(MARGIN_X, 2.45 * inch, MARGIN_X + 0.6 * inch, 2.45 * inch)
    c.setFillColor(white)
    c.setFont('Inter-SemiBold', 10)
    c.drawString(MARGIN_X, 2.12 * inch, d['date'])
    times = [t for t, _ in d['schedule']]
    c.setFont('Inter', 9)
    c.drawString(MARGIN_X, 1.9 * inch, f'{times[0]} – {times[-1]}')
    c.drawString(MARGIN_X, 1.68 * inch, d['venue'])
    c.drawString(MARGIN_X, 1.46 * inch, 'UC Berkeley')
    c.setFillColor(GOLD)
    c.setFont('Inter-Bold', 7.5)
    c.drawString(MARGIN_X, 0.62 * inch, 'PROGRAM')
    c.setFillColor(white)
    c.setFillAlpha(0.7)
    c.setFont('Inter', 7.5)
    c.drawRightString(PAGE_W - MARGIN_X, 0.62 * inch, 'cdss.berkeley.edu/discovery')
    c.showPage()
    c.save()
    return buf.getvalue()


def build_back(season, url):
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=(PAGE_W, PAGE_H))
    c.setFillColor(TINT)
    c.rect(0, 0, PAGE_W, PAGE_H, stroke=0, fill=1)
    c.setFillColor(BLUE)
    c.rect(0, 0, PAGE_W, 0.32 * inch, stroke=0, fill=1)
    c.setFillColor(GOLD)
    c.rect(0, 0.32 * inch, PAGE_W, 0.06 * inch, stroke=0, fill=1)
    c.setFillColor(BLUE)
    c.setFont('Serif-Bold', 26)
    c.drawCentredString(PAGE_W / 2, 6.3 * inch, 'Thank you')
    c.setFont('Inter', 9)
    c.setFillColor(INK)
    c.drawCentredString(PAGE_W / 2, 5.95 * inch, 'for celebrating our student researchers.')
    c.setFillColor(GOLD)
    c.roundRect(PAGE_W / 2 - 17, 5.65 * inch, 34, 3.2, 1.6, stroke=0, fill=1)

    qr = QrCodeWidget(url)
    qr.barFillColor = BLUE
    x1, y1, x2, y2 = qr.getBounds()
    size = 1.45 * inch
    dr = Drawing(size, size, transform=[size / (x2 - x1), 0, 0, size / (y2 - y1), 0, 0])
    dr.add(qr)
    c.setFillColor(white)
    c.roundRect(PAGE_W / 2 - size / 2 - 8, 3.45 * inch - 8, size + 16, size + 16, 8, stroke=0,
                fill=1)
    renderPDF.draw(dr, c, PAGE_W / 2 - size / 2, 3.45 * inch)
    c.setFont('Inter', 7.2)
    c.setFillColor(MUTED)
    c.drawCentredString(PAGE_W / 2, 3.15 * inch, 'Scan to view this program online')

    c.setFont('Inter-SemiBold', 8.6)
    c.setFillColor(BLUE)
    c.drawCentredString(PAGE_W / 2, 2.55 * inch, 'cdss.berkeley.edu/discovery')
    c.setFont('Inter', 8.6)
    c.drawCentredString(PAGE_W / 2, 2.33 * inch, 'cdss-datadiscovery@berkeley.edu')
    logo_w = 2.7 * inch
    c.drawImage(str(HERE / 'logo-color.png'), PAGE_W / 2 - logo_w / 2, 1.0 * inch, width=logo_w,
                height=logo_w * 508 / 2400, mask='auto')
    c.showPage()
    c.save()
    return buf.getvalue()


def impose(pages):
    """Saddle-stitch imposition: pages (multiple of 4) onto double-sided landscape sheets."""
    n = len(pages)
    assert n % 4 == 0
    out = PdfWriter()
    for i in range(n // 4):
        for left, right in [(n - 2 * i, 2 * i + 1), (2 * i + 2, n - 2 * i - 1)]:
            sheet = PageObject.create_blank_page(width=SHEET_W, height=SHEET_H)
            for num, tx in [(left, 0), (right, PAGE_W)]:
                sheet.merge_transformed_page(pages[num - 1], Transformation().translate(tx, 0))
            out.add_page(sheet)
    return out


def build(key, md, season, seed, preview=False):
    d = parse_page(REPO / 'symposium' / md)
    url = f'https://datadisco.cdss.berkeley.edu/{md.lower().replace(".md", "")}/'
    pad = 0
    inner = build_interior(d, season)
    while (len(PdfReader(io.BytesIO(inner)).pages) + 2) % 4:
        pad = (-(len(PdfReader(io.BytesIO(build_interior(d, season))).pages) + 2)) % 4
        inner = build_interior(d, season, pad_notes=pad)
        assert (len(PdfReader(io.BytesIO(inner)).pages) + 2) % 4 == 0, 'notes page overflowed'
    pages = (list(PdfReader(io.BytesIO(build_cover(d, season, seed))).pages)
             + list(PdfReader(io.BytesIO(inner)).pages)
             + list(PdfReader(io.BytesIO(build_back(season, url))).pages))
    if preview:
        reading = PdfWriter()
        for p in pages:
            reading.add_page(p)
        reading.add_metadata({'/Title': f'Data Discovery {season} Symposium Program'})
        with open(HERE / f'program-{key}-reading.pdf', 'wb') as f:
            reading.write(f)
    imposed = impose(pages)
    imposed.add_metadata({'/Title': f'Data Discovery {season} Symposium Program (print & fold)',
                          '/Author': 'CDSS Data Discovery'})
    with open(REPO / 'assets' / f'program-{key}.pdf', 'wb') as f:
        imposed.write(f)
    posters = sum(len(e) for _, e in d['categories'])
    print(f'{key}: {len(pages)} pages ({pad} notes), {len(pages)//4} sheets, '
          f'{len(d["awards"])} awards, {posters} posters, {len(d["elsewhere"])} elsewhere')


# key (used in assets/program-<key>.pdf), page in symposium/, season shown in the program,
# and a seed that varies the cover's dot pattern.
SEMESTERS = [
    ('sp26', 'SP26symposium.md', 'Spring 2026', 2026),
    ('f25', 'F25symposium.md', 'Fall 2025', 2025),
]

if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    for key, md, season, seed in SEMESTERS:
        if not args or key in args:
            build(key, md, season, seed, preview='--preview' in sys.argv)
