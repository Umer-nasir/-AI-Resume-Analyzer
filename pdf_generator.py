import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether
from reportlab.pdfgen import canvas

# Define custom corporate color palette
PRIMARY_COLOR = colors.HexColor("#1E3A8A")    # Deep Navy
SECONDARY_COLOR = colors.HexColor("#3B82F6")  # Vibrant Blue
ACCENT_GREEN = colors.HexColor("#10B981")     # Emerald Green
ACCENT_RED = colors.HexColor("#EF4444")       # Coral Red
BG_LIGHT = colors.HexColor("#F3F4F6")         # Soft Light Grey
TEXT_DARK = colors.HexColor("#1F2937")        # Dark Charcoal
TEXT_MUTED = colors.HexColor("#4B5563")       # Slate Grey

class NumberedCanvas(canvas.Canvas):
    """
    Canvas to calculate total pages dynamically and add professional headers/footers
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        
        # Header
        self.setFont("Helvetica-Bold", 8)
        self.setFillColor(TEXT_MUTED)
        self.drawString(54, letter[1] - 40, "AI RESUME ANALYZER & MATCH REPORT")
        
        # Header divider line
        self.setStrokeColor(BG_LIGHT)
        self.setLineWidth(1)
        self.line(54, letter[1] - 46, letter[0] - 54, letter[1] - 46)
        
        # Footer
        self.setFont("Helvetica", 8)
        self.setFillColor(TEXT_MUTED)
        self.drawString(54, 36, "Confidential - Professional Assessment")
        
        # Page Number: "Page X of Y"
        page_num_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(letter[0] - 54, 36, page_num_str)
        
        # Footer line
        self.line(54, 46, letter[0] - 54, 46)
        
        self.restoreState()


def generate_resume_report_pdf(output_path, data):
    """
    Generates a professionally typeset PDF report for a resume analysis.
    """
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        leftMargin=54, # 0.75 inch margins
        rightMargin=54,
        topMargin=60,
        bottomMargin=60
    )
    
    styles = getSampleStyleSheet()
    
    # Custom Typography Styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=28,
        textColor=PRIMARY_COLOR,
        spaceAfter=6
    )
    
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=12,
        leading=16,
        textColor=TEXT_MUTED,
        spaceAfter=15
    )
    
    h1_style = ParagraphStyle(
        'SectionHeading',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=18,
        textColor=PRIMARY_COLOR,
        spaceBefore=14,
        spaceAfter=6,
        keepWithNext=True
    )
    
    body_style = ParagraphStyle(
        'BodyDark',
        parent=styles['BodyText'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=TEXT_DARK,
        spaceAfter=8
    )
    
    bullet_style = ParagraphStyle(
        'BulletText',
        parent=styles['BodyText'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=TEXT_DARK,
        leftIndent=15,
        firstLineIndent=-10,
        spaceAfter=5
    )

    score_num_style = ParagraphStyle(
        'ScoreNumber',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=36,
        leading=40,
        textColor=PRIMARY_COLOR,
        alignment=1
    )
    
    score_label_style = ParagraphStyle(
        'ScoreLabel',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=14,
        textColor=TEXT_MUTED,
        alignment=1
    )

    story = []
    
    # --- HEADER SECTION ---
    candidate_name = data.get("candidate_name", "Candidate Resume")
    job_title = data.get("job_title", "Python Developer Role")
    story.append(Paragraph(f"Resume Analysis: {candidate_name}", title_style))
    story.append(Paragraph(f"Target Position: {job_title}", subtitle_style))
    
    # --- METRICS & OVERVIEW BOARD (TABLE LAYOUT) ---
    score_val = str(data.get("match_score", "0"))
    try:
        score_int = int(score_val)
    except ValueError:
        score_int = 50
        
    score_color = ACCENT_GREEN if score_int >= 80 else (SECONDARY_COLOR if score_int >= 60 else ACCENT_RED)
    
    # Overwrite score text style color dynamically
    score_num_style.textColor = score_color
    
    # Description block
    overview_html = (
        f"<b>Executive Summary:</b><br/>"
        f"This report presents an AI-driven matching assessment comparing the candidate's resume "
        f"against the requirements of the <b>{job_title}</b> position. "
        f"Using RAG (Retrieval-Augmented Generation) and multi-agent AI execution, we have analyzed the profile, "
        f"assessed core competency alignments, identified potential experience/skill gaps, and formulated "
        f"actionable resume enhancement recommendations and mock interview questions."
    )
    
    metric_table_data = [
        [
            Paragraph(f"{score_val}<font size=18>/100</font>", score_num_style), 
            Paragraph(overview_html, body_style)
        ],
        [
            Paragraph("COMPATIBILITY SCORE", score_label_style),
            Paragraph("", body_style)
        ]
    ]
    
    metric_table = Table(metric_table_data, colWidths=[2.0*inch, 5.0*inch])
    metric_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (0,1), BG_LIGHT),
        ('ALIGN', (0,0), (0,1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOX', (0,0), (-1,-1), 1, BG_LIGHT),
        ('TOPPADDING', (0,0), (-1,-1), 12),
        ('BOTTOMPADDING', (0,0), (-1,-1), 12),
        ('LEFTPADDING', (0,0), (-1,-1), 12),
        ('RIGHTPADDING', (0,0), (-1,-1), 12),
    ]))
    
    story.append(metric_table)
    story.append(Spacer(1, 15))
    
    # Helper to parse string of bullet points or text blocks into Paragraph flowables
    def parse_section_text(text_content):
        elements = []
        if not text_content:
            return [Paragraph("No details extracted.", body_style)]
            
        lines = text_content.strip().split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                continue
            # Format bullets
            if line.startswith('-') or line.startswith('*') or line.startswith('•'):
                cleaned = line.lstrip('-*• ').strip()
                elements.append(Paragraph(f"&bull; {cleaned}", bullet_style))
            elif line[0].isdigit() and (line[1] == '.' or (line[2] == '.' if len(line) > 2 else False)):
                elements.append(Paragraph(line, bullet_style))
            else:
                elements.append(Paragraph(line, body_style))
        return elements

    # --- SECTION 1: EXTRACTED INFO ---
    story.append(Paragraph("1. Extracted Resume Profile", h1_style))
    story.append(Paragraph("A clean structured profile containing all identified technical skills, employment experience, credentials, and achievements:", body_style))
    story.extend(parse_section_text(data.get("extracted_info", "")))
    story.append(Spacer(1, 12))
    
    # --- SECTION 2: MATCH ANALYSIS & GAPS ---
    story.append(Paragraph("2. Requirements Gap Analysis", h1_style))
    story.append(Paragraph("A direct comparison of qualifications against target job requirements, highlighting matching attributes and critical capability gaps:", body_style))
    story.extend(parse_section_text(data.get("match_analysis", "")))
    story.append(Spacer(1, 12))
    
    # --- SECTION 3: IMPROVEMENTS & COACHING ---
    story.append(Paragraph("3. Career Coaching & Improvements", h1_style))
    story.append(Paragraph("Targeted, specific recommendations from our Career Coach to bridge experience gaps and optimize your resume:", body_style))
    story.extend(parse_section_text(data.get("improvements", "")))
    story.append(Spacer(1, 12))
    
    # --- SECTION 4: INTERVIEW PREPARATION ---
    interview_section = []
    interview_section.append(Paragraph("4. Targeted Interview Questions", h1_style))
    interview_section.append(Paragraph("Tailored, technical, and situational interview questions designed specifically for your candidate profile to help prepare for interviews:", body_style))
    interview_section.extend(parse_section_text(data.get("interview_questions", "")))
    
    story.append(KeepTogether(interview_section))
    
    # Build Document using NumberedCanvas
    doc.build(story, canvasmaker=NumberedCanvas)
