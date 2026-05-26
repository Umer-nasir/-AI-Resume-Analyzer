import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

def create_mock_resume(pdf_path):
    """
    Generates a beautiful mock resume in PDF format for testing.
    """
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )
    
    styles = getSampleStyleSheet()
    
    # Define custom corporate colors
    PRIMARY = colors.HexColor("#0F172A") # Slate 900
    SECONDARY = colors.HexColor("#475569") # Slate 600
    TEXT_DARK = colors.HexColor("#334155") # Slate 700
    ACCENT = colors.HexColor("#2563EB") # Royal Blue
    
    # Custom Typography Styles
    title_style = ParagraphStyle(
        'ResumeTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=22,
        leading=26,
        textColor=PRIMARY,
        spaceAfter=4
    )
    
    subtitle_style = ParagraphStyle(
        'ResumeSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=SECONDARY,
        spaceAfter=15
    )
    
    section_title_style = ParagraphStyle(
        'ResumeSection',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=ACCENT,
        spaceBefore=10,
        spaceAfter=6,
        keepWithNext=True
    )
    
    body_style = ParagraphStyle(
        'ResumeBody',
        parent=styles['BodyText'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=13.5,
        textColor=TEXT_DARK,
        spaceAfter=6
    )
    
    bullet_style = ParagraphStyle(
        'ResumeBullet',
        parent=styles['BodyText'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=13.5,
        textColor=TEXT_DARK,
        leftIndent=15,
        firstLineIndent=-10,
        spaceAfter=4
    )
    
    story = []
    
    # 1. Header (Name & Contact)
    story.append(Paragraph("JOHN DOE", title_style))
    contact_text = (
        "Email: john.doe@email.com | Phone: +1 (555) 0199 | "
        "GitHub: github.com/johndoe | Seattle, WA"
    )
    story.append(Paragraph(contact_text, subtitle_style))
    
    # Divider line
    divider = Table([[""]], colWidths=[7.0*inch])
    divider.setStyle(TableStyle([
        ('LINEBELOW', (0,0), (-1,-1), 1.5, PRIMARY),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
        ('TOPPADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(divider)
    story.append(Spacer(1, 10))
    
    # 2. Summary
    story.append(Paragraph("PROFESSIONAL SUMMARY", section_title_style))
    summary_text = (
        "Results-driven Junior Software Engineer with 1.5 years of hands-on experience building "
        "web applications and API services using Python. Skilled in developing clean, maintainable "
        "code, collaborating in Agile teams, and implementing backend logic. Eager to expand skills "
        "in database design and advanced web frameworks like Django or Flask."
    )
    story.append(Paragraph(summary_text, body_style))
    story.append(Spacer(1, 8))
    
    # 3. Skills
    story.append(Paragraph("TECHNICAL SKILLS", section_title_style))
    skills_text = (
        "<b>Languages:</b> Python, SQL, JavaScript, HTML5, CSS3<br/>"
        "<b>Frameworks & Tools:</b> Flask, Git, Docker, RESTful APIs, SQLite, Postman<br/>"
        "<b>Methodologies:</b> Agile, Scrum, Unit Testing (unittest, pytest), CI/CD basics"
    )
    story.append(Paragraph(skills_text, body_style))
    story.append(Spacer(1, 8))
    
    # 4. Experience
    story.append(Paragraph("PROFESSIONAL EXPERIENCE", section_title_style))
    
    # Job 1
    job_title = "<b>Junior Software Engineer</b> — TechSolutions Inc., Seattle, WA"
    job_dates = "<i>January 2024 – Present</i>"
    
    job_header = Table([[Paragraph(job_title, body_style), Paragraph(job_dates, ParagraphStyle('RightText', parent=body_style, alignment=2))]], colWidths=[5.0*inch, 2.0*inch])
    job_header.setStyle(TableStyle([
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
        ('TOPPADDING', (0,0), (-1,-1), 0),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(job_header)
    story.append(Spacer(1, 4))
    
    story.append(Paragraph("&bull; Designed, developed, and maintained 10+ scalable backend REST API endpoints using Python and Flask.", bullet_style))
    story.append(Paragraph("&bull; Optimized legacy SQL database queries in SQLite, reducing server response times by 15%.", bullet_style))
    story.append(Paragraph("&bull; Wrote comprehensive unit tests using PyTest, raising codebase test coverage from 65% to 88%.", bullet_style))
    story.append(Paragraph("&bull; Participated in daily standups and weekly sprint reviews in an Agile/Scrum environment of 8 developers.", bullet_style))
    story.append(Spacer(1, 6))
    
    # Internship
    internship_title = "<b>Software Engineer Intern</b> — InnovateWeb Corp, Bellevue, WA"
    internship_dates = "<i>June 2023 – Dec 2023</i>"
    internship_header = Table([[Paragraph(internship_title, body_style), Paragraph(internship_dates, ParagraphStyle('RightText2', parent=body_style, alignment=2))]], colWidths=[5.0*inch, 2.0*inch])
    internship_header.setStyle(TableStyle([
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
        ('TOPPADDING', (0,0), (-1,-1), 0),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(internship_header)
    story.append(Spacer(1, 4))
    
    story.append(Paragraph("&bull; Built frontend features using JavaScript and CSS, improving user interaction metrics by 10%.", bullet_style))
    story.append(Paragraph("&bull; Managed code repositories and version control workflows utilizing Git and GitHub.", bullet_style))
    story.append(Paragraph("&bull; Collaborated with QA analysts to troubleshoot and fix 25+ software bugs during release cycles.", bullet_style))
    story.append(Spacer(1, 8))
    
    # 5. Education
    story.append(Paragraph("EDUCATION", section_title_style))
    edu_text = "<b>Bachelor of Science in Computer Science</b> — University of Washington, Seattle, WA"
    edu_dates = "<i>Graduated: December 2023</i>"
    edu_header = Table([[Paragraph(edu_text, body_style), Paragraph(edu_dates, ParagraphStyle('RightText3', parent=body_style, alignment=2))]], colWidths=[5.2*inch, 1.8*inch])
    edu_header.setStyle(TableStyle([
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
        ('TOPPADDING', (0,0), (-1,-1), 0),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(edu_header)
    
    doc.build(story)
    print("Mock resume PDF generated successfully!")

if __name__ == "__main__":
    create_mock_resume("my_resume.pdf")
