"""
Script to generate a recruiter-approved, ATS-optimized 1-page PDF resume for Shravani Raut.
"""
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable

def generate_resume(output_pdf: str):
    doc = SimpleDocTemplate(
        output_pdf,
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=32,
        bottomMargin=32
    )

    styles = getSampleStyleSheet()
    
    # Custom styles
    primary_color = colors.HexColor("#0F2942")  # Deep Navy
    text_color = colors.HexColor("#222222")     # Dark Charcoal
    subtext_color = colors.HexColor("#4B5563")  # Slate Gray
    link_color = colors.HexColor("#1D4ED8")     # Professional Blue

    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=17,
        leading=20,
        alignment=1, # Center
        textColor=primary_color
    )

    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=13,
        alignment=1,
        textColor=primary_color
    )

    contact_style = ParagraphStyle(
        'ContactInfo',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11,
        alignment=1,
        textColor=subtext_color
    )

    project_link_style = ParagraphStyle(
        'ProjectLink',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.0,
        leading=10,
        alignment=0, # Left-aligned
        textColor=subtext_color,
        spaceBefore=0.5,
        spaceAfter=1.5
    )

    section_heading_style = ParagraphStyle(
        'SectionHeading',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10.5,
        leading=13,
        textColor=primary_color,
        spaceBefore=5,
        spaceAfter=2
    )

    body_style = ParagraphStyle(
        'BodyTextCustom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11.5,
        textColor=text_color
    )

    bullet_style = ParagraphStyle(
        'BulletCustom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.2,
        leading=11,
        leftIndent=12,
        firstLineIndent=-8,
        textColor=text_color,
        spaceBefore=1,
        spaceAfter=1
    )

    story = []

    # 1. Header
    story.append(Paragraph("SHRAVANI RAUT", title_style))
    story.append(Paragraph("Data Analyst &amp; Machine Learning Engineer", subtitle_style))
    story.append(Spacer(1, 2))
    
    contact_text = (
        "Bengaluru, Karnataka, India &nbsp;|&nbsp; +91 9405398279 &nbsp;|&nbsp; "
        "<a href='mailto:shravaniraut1708@gmail.com'><font color='#1D4ED8'>shravaniraut1708@gmail.com</font></a> &nbsp;|&nbsp; "
        "<a href='https://linkedin.com/in/shravani-raut-80739326a'><font color='#1D4ED8'>linkedin.com/in/shravani-raut-80739326a</font></a> &nbsp;|&nbsp; "
        "<a href='https://github.com/ShravaniDRaut'><font color='#1D4ED8'>github.com/ShravaniDRaut</font></a>"
    )
    story.append(Paragraph(contact_text, contact_style))
    story.append(Spacer(1, 4))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#CBD5E1"), spaceAfter=5, spaceBefore=2))

    # 2. Summary
    story.append(Paragraph("PROFESSIONAL SUMMARY", section_heading_style))
    summary_text = (
        "Analytical and detail-oriented Engineering graduate with practical project experience across "
        "<b>Python, SQL, Computer Vision, and Power BI</b>. Skilled in data cleaning, relational data modeling, "
        "deep learning object detection pipelines, and executive dashboard development. Proven ability to translate "
        "complex datasets into actionable business insights and production-grade software solutions."
    )
    story.append(Paragraph(summary_text, body_style))
    story.append(Spacer(1, 3))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#E2E8F0"), spaceAfter=4, spaceBefore=2))

    # 3. Technical Skills
    story.append(Paragraph("TECHNICAL SKILLS", section_heading_style))
    skills_data = [
        [
            Paragraph("<b>Programming &amp; Tools:</b>", body_style),
            Paragraph("Python (OOP, File Handling), Java, SQL, Git, Microsoft Excel, Power BI, VS Code", body_style)
        ],
        [
            Paragraph("<b>Data Analytics &amp; ML:</b>", body_style),
            Paragraph("Exploratory Data Analysis (EDA), Computer Vision, Object Detection &amp; Tracking, Machine Learning, Deep Learning, Statistics", body_style)
        ],
        [
            Paragraph("<b>Libraries &amp; Frameworks:</b>", body_style),
            Paragraph("Pandas, NumPy, Matplotlib, Seaborn, Scikit-learn, OpenCV, Ultralytics (YOLOv8), PyTorch", body_style)
        ],
        [
            Paragraph("<b>Databases:</b>", body_style),
            Paragraph("MySQL, SQLite, SQLAlchemy", body_style)
        ]
    ]
    skills_table = Table(skills_data, colWidths=[130, 410])
    skills_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 1.5),
        ('TOPPADDING', (0,0), (-1,-1), 1.5),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(skills_table)
    story.append(Spacer(1, 3))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#E2E8F0"), spaceAfter=4, spaceBefore=2))

    # 4. Projects
    story.append(Paragraph("TECHNICAL PROJECTS", section_heading_style))
    
    # Project 1: Object Counting System
    p1_header = [
        Paragraph("<b>AI-Powered Real-Time Object Counting &amp; Tracking System</b>", body_style),
        Paragraph("<font color='#4B5563'><i>Python, YOLOv8, OpenCV, ByteTrack, SQLite</i></font>", ParagraphStyle('R', parent=body_style, alignment=2))
    ]
    t1 = Table([p1_header], colWidths=[310, 230])
    t1.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP'), ('LEFTPADDING', (0,0), (-1,-1), 0), ('RIGHTPADDING', (0,0), (-1,-1), 0), ('BOTTOMPADDING', (0,0), (-1,-1), 1), ('TOPPADDING', (0,0), (-1,-1), 1)]))
    story.append(t1)
    story.append(Paragraph("GitHub: <a href='https://github.com/ShravaniDRaut/object_counting'><font color='#1D4ED8'><u>github.com/ShravaniDRaut/object_counting</u></font></a>", project_link_style))
    story.append(Paragraph("• Built an end-to-end computer vision application using <b>YOLOv8</b> and <b>ByteTrack</b> to detect, classify, and track 6 distinct object classes (pedestrians, cars, buses, trucks, motorcycles, bicycles) across video streams at <b>30+ FPS</b>.", bullet_style))
    story.append(Paragraph("• Implemented a 2D vector geometry line-crossing algorithm utilizing counter-clockwise (CCW) segment straddle tests and ground-contact centroid tracking, eliminating parallax errors and preventing duplicate counts via a 60-frame cooldown filter.", bullet_style))
    story.append(Paragraph("• Developed a resolution-adaptive OpenCV HUD overlay showing live in-frame counts, unique detections, and directional (IN/OUT) traffic flow, with automated transactional logging into an <b>SQLite database</b> using <b>SQLAlchemy ORM</b>.", bullet_style))
    story.append(Spacer(1, 3))

    # Project 2: Uber Analytics
    p2_header = [
        Paragraph("<b>Uber Data Analytics Project</b>", body_style),
        Paragraph("<font color='#4B5563'><i>Python, SQL, Power BI, Pandas</i></font>", ParagraphStyle('R', parent=body_style, alignment=2))
    ]
    t2 = Table([p2_header], colWidths=[310, 230])
    t2.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP'), ('LEFTPADDING', (0,0), (-1,-1), 0), ('RIGHTPADDING', (0,0), (-1,-1), 0), ('BOTTOMPADDING', (0,0), (-1,-1), 1), ('TOPPADDING', (0,0), (-1,-1), 1)]))
    story.append(t2)
    story.append(Paragraph("GitHub: <a href='https://github.com/ShravaniDRaut/my_da_project-'><font color='#1D4ED8'><u>github.com/ShravaniDRaut/my_da_project-</u></font></a>", project_link_style))
    story.append(Paragraph("• Processed and analyzed <b>5,000+ NYC taxi/Uber trip records</b> end-to-end; cleaned raw records in Python (Pandas) by handling missing values, standardizing schemas, and engineering time-based features.", bullet_style))
    story.append(Paragraph("• Authored complex analytical SQL queries using aggregate functions, subqueries, and window functions to evaluate trip distance distributions, peak-hour demand, revenue contributions, and payment method behavior.", bullet_style))
    story.append(Paragraph("• Designed a multi-page interactive Power BI dashboard (Demand, Route, Revenue, Customer Analysis) with dynamic slicers and DAX measures to surface key driver availability and fare optimization insights.", bullet_style))
    story.append(Spacer(1, 3))

    # Project 3: Netflix Data Analysis
    p3_header = [
        Paragraph("<b>Netflix Content &amp; Viewership Analysis</b>", body_style),
        Paragraph("<font color='#4B5563'><i>Python, Pandas, MySQL, Power BI</i></font>", ParagraphStyle('R', parent=body_style, alignment=2))
    ]
    t3 = Table([p3_header], colWidths=[310, 230])
    t3.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP'), ('LEFTPADDING', (0,0), (-1,-1), 0), ('RIGHTPADDING', (0,0), (-1,-1), 0), ('BOTTOMPADDING', (0,0), (-1,-1), 1), ('TOPPADDING', (0,0), (-1,-1), 1)]))
    story.append(t3)
    story.append(Paragraph("GitHub: <a href='https://github.com/ShravaniDRaut/da_netflix_project'><font color='#1D4ED8'><u>github.com/ShravaniDRaut/da_netflix_project</u></font></a>", project_link_style))
    story.append(Paragraph("• Conducted exploratory data analysis (EDA) on Netflix catalog records using Python to identify release trends, runtime distributions, and regional content generation patterns.", bullet_style))
    story.append(Paragraph("• Integrated Python with a <b>MySQL database</b> for structured querying and data extraction, creating dynamic Power BI visuals to track content catalog evolution across countries and ratings.", bullet_style))
    story.append(Spacer(1, 3))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#E2E8F0"), spaceAfter=4, spaceBefore=2))

    # 5. Experience
    story.append(Paragraph("EXPERIENCE &amp; SIMULATIONS", section_heading_style))
    exp_header = [
        Paragraph("<b>Data Analytics Job Simulation</b> — Deloitte Australia (Forage)", body_style),
        Paragraph("<font color='#4B5563'><i>Completed</i></font>", ParagraphStyle('R', parent=body_style, alignment=2))
    ]
    te = Table([exp_header], colWidths=[380, 160])
    te.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP'), ('LEFTPADDING', (0,0), (-1,-1), 0), ('RIGHTPADDING', (0,0), (-1,-1), 0), ('BOTTOMPADDING', (0,0), (-1,-1), 1), ('TOPPADDING', (0,0), (-1,-1), 1)]))
    story.append(te)
    story.append(Paragraph("• Completed practical simulation covering forensic data analytics, data reconciliation, and executive dashboard reporting.", bullet_style))
    story.append(Paragraph("• Built analytical dashboards in Tableau and Excel to classify unstructured records and communicate business conclusions to non-technical stakeholders.", bullet_style))
    story.append(Spacer(1, 3))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#E2E8F0"), spaceAfter=4, spaceBefore=2))

    # 6. Education
    story.append(Paragraph("EDUCATION", section_heading_style))
    edu_data = [
        [
            Paragraph("<b>B.E., Electronics &amp; Telecommunication Engineering</b> — Sinhgad College of Engineering, Pune (SPPU)", body_style),
            Paragraph("<b>2025</b> | CGPA: <b>7.26</b>", ParagraphStyle('R', parent=body_style, alignment=2))
        ],
        [
            Paragraph("<b>HSC</b> — Dayanand Science College, Latur (MSBSHSE)", body_style),
            Paragraph("<b>2021</b> | <b>95.17%</b>", ParagraphStyle('R', parent=body_style, alignment=2))
        ],
        [
            Paragraph("<b>SSC</b> — Yogeshwari Girls School, Ambajogai (MSBSHSE)", body_style),
            Paragraph("<b>2019</b> | <b>90.00%</b>", ParagraphStyle('R', parent=body_style, alignment=2))
        ]
    ]
    edu_table = Table(edu_data, colWidths=[400, 140])
    edu_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 1),
        ('TOPPADDING', (0,0), (-1,-1), 1),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(edu_table)
    story.append(Spacer(1, 3))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#E2E8F0"), spaceAfter=4, spaceBefore=2))

    # 7. Certifications
    story.append(Paragraph("CERTIFICATIONS", section_heading_style))
    certs = "• <b>Data Science Course Certificate</b> (8-Month Intensive Program) &nbsp;&nbsp;&nbsp; • <b>Python Programming Certificate</b> &nbsp;&nbsp;&nbsp; • <b>Java Certificate</b>"
    story.append(Paragraph(certs, body_style))

    doc.build(story)
    print(f"Resume generated successfully at: {output_pdf}")

if __name__ == "__main__":
    generate_resume("data/outputs/Shravani_Raut_Resume.pdf")
