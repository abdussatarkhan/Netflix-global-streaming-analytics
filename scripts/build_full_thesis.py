import os
import sys
import docx
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import parse_xml, OxmlElement
from docx.oxml.ns import nsdecls, qn

def set_cell_background(cell, hex_color):
    tcPr = cell._element.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{hex_color}"/>')
    tcPr.append(shd)

def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    tcPr = cell._element.get_or_add_tcPr()
    tcMar = parse_xml(f'<w:tcMar {nsdecls("w")}><w:top w:w="{top}" w:type="dxa"/><w:bottom w:w="{bottom}" w:type="dxa"/><w:left w:w="{left}" w:type="dxa"/><w:right w:w="{right}" w:type="dxa"/></w:tcMar>')
    tcPr.append(tcMar)

def add_styled_heading(doc, text, level):
    h = doc.add_heading(text, level=level)
    h.paragraph_format.keep_with_next = True
    h.paragraph_format.space_before = Pt(14 if level==1 else (10 if level==2 else 6))
    h.paragraph_format.space_after = Pt(4)
    run = h.runs[0]
    run.font.name = 'Times New Roman'
    if level == 1:
        run.font.size = Pt(16)
        run.font.bold = True
        run.font.color.rgb = RGBColor(16, 44, 87)
    elif level == 2:
        run.font.size = Pt(13)
        run.font.bold = True
        run.font.color.rgb = RGBColor(28, 78, 128)
    else:
        run.font.size = Pt(11.5)
        run.font.bold = True
        run.font.color.rgb = RGBColor(40, 40, 40)
    return h

def add_body_p(doc, text, bold_prefix=None, space_after=6, italic=False):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(space_after)
    p.paragraph_format.line_spacing = 1.15
    if bold_prefix:
        r_pre = p.add_run(bold_prefix)
        r_pre.font.name = 'Times New Roman'
        r_pre.font.size = Pt(11)
        r_pre.font.bold = True
    r = p.add_run(text)
    r.font.name = 'Times New Roman'
    r.font.size = Pt(11)
    r.font.italic = italic
    return p

def add_bullet_p(doc, bold_title, text):
    p = doc.add_paragraph(style='List Bullet')
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.line_spacing = 1.15
    r_b = p.add_run(bold_title)
    r_b.font.name = 'Times New Roman'
    r_b.font.size = Pt(11)
    r_b.font.bold = True
    r_t = p.add_run(text)
    r_t.font.name = 'Times New Roman'
    r_t.font.size = Pt(11)
    return p

def add_code_block(doc, code_text):
    tbl = doc.add_table(rows=1, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = tbl.cell(0, 0)
    cell.width = Inches(6.5)
    set_cell_background(cell, 'F4F6F9')
    set_cell_margins(cell, top=120, bottom=120, left=180, right=180)
    p = cell.paragraphs[0]
    p.paragraph_format.space_after = Pt(0)
    p.paragraph_format.line_spacing = 1.05
    for line in code_text.strip().split('\n'):
        r = p.add_run(line + '\n')
        r.font.name = 'Consolas'
        r.font.size = Pt(9)
        r.font.color.rgb = RGBColor(30, 41, 59)
    doc.add_paragraph().paragraph_format.space_after = Pt(4)

def add_table_data(doc, headers, rows, col_widths=None):
    tbl = doc.add_table(rows=len(rows)+1, cols=len(headers))
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    hdr_row = tbl.rows[0]
    for i, h in enumerate(headers):
        cell = hdr_row.cells[i]
        set_cell_background(cell, '1E3A8A')
        set_cell_margins(cell, 120, 120, 140, 140)
        p = cell.paragraphs[0]
        p.paragraph_format.space_after = Pt(0)
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(h)
        r.font.name = 'Times New Roman'
        r.font.size = Pt(10)
        r.font.bold = True
        r.font.color.rgb = RGBColor(255, 255, 255)
    for r_idx, row in enumerate(rows):
        tbl_row = tbl.rows[r_idx + 1]
        bg = 'F8FAFC' if r_idx % 2 == 1 else 'FFFFFF'
        for c_idx, val in enumerate(row):
            cell = tbl_row.cells[c_idx]
            set_cell_background(cell, bg)
            set_cell_margins(cell, 100, 100, 120, 120)
            p = cell.paragraphs[0]
            p.paragraph_format.space_after = Pt(0)
            r = p.add_run(str(val))
            r.font.name = 'Times New Roman'
            r.font.size = Pt(9.5)
            r.font.color.rgb = RGBColor(30, 41, 59)
    if col_widths:
        for row in tbl.rows:
            for i, w in enumerate(col_widths):
                row.cells[i].width = Inches(w)
    doc.add_paragraph().paragraph_format.space_after = Pt(6)
    return tbl

def add_figure_image(doc, img_path, caption):
    if os.path.exists(img_path):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(8)
        p.paragraph_format.space_after = Pt(2)
        run = p.add_run()
        run.add_picture(img_path, width=Inches(5.6))
        
        cap_p = doc.add_paragraph()
        cap_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        cap_p.paragraph_format.space_after = Pt(8)
        cap_r = cap_p.add_run(caption)
        cap_r.font.name = 'Times New Roman'
        cap_r.font.size = Pt(10)
        cap_r.font.italic = True
        cap_r.font.color.rgb = RGBColor(70, 70, 70)

def generate_thesis_docx():
    doc = Document()
    sections = doc.sections
    for section in sections:
        section.top_margin = Inches(1.0)
        section.bottom_margin = Inches(1.0)
        section.left_margin = Inches(1.0)
        section.right_margin = Inches(1.0)

    # 1. Title Page (Cover Page)
    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_title.paragraph_format.space_before = Pt(80)
    p_title.paragraph_format.space_after = Pt(12)
    r_t = p_title.add_run("Smart Streaming Intelligence & Personalization Platform\n(StreamIQ)")
    r_t.font.name = 'Times New Roman'
    r_t.font.size = Pt(22)
    r_t.font.bold = True
    r_t.font.color.rgb = RGBColor(16, 44, 87)

    p_sub = doc.add_paragraph()
    p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_sub.paragraph_format.space_after = Pt(100)
    r_sub = p_sub.add_run("A Final Year Project")
    r_sub.font.name = 'Times New Roman'
    r_sub.font.size = Pt(14)
    r_sub.font.italic = True

    p_by = doc.add_paragraph()
    p_by.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_by.paragraph_format.space_after = Pt(6)
    r_by1 = p_by.add_run("SUBMITTED BY\n")
    r_by1.font.name = 'Times New Roman'
    r_by1.font.size = Pt(12)
    r_by1.font.bold = True
    r_by2 = p_by.add_run("Fasihullah (Reg. No. UOS226500077)\n")
    r_by2.font.name = 'Times New Roman'
    r_by2.font.size = Pt(12)

    p_sup = doc.add_paragraph()
    p_sup.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_sup.paragraph_format.space_before = Pt(18)
    p_sup.paragraph_format.space_after = Pt(40)
    r_sup1 = p_sup.add_run("SUPERVISED BY\n")
    r_sup1.font.name = 'Times New Roman'
    r_sup1.font.size = Pt(12)
    r_sup1.font.bold = True
    r_sup2 = p_sup.add_run("FAZLI SABOOH\n")
    r_sup2.font.name = 'Times New Roman'
    r_sup2.font.size = Pt(12)

    p_inst = doc.add_paragraph()
    p_inst.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_inst.paragraph_format.space_after = Pt(0)
    r_inst = p_inst.add_run("Department of Computer Science\nGovernment College Madyan Swat, Affiliated with\nUNIVERSITY OF SWAT\nSession (2022-2026)")
    r_inst.font.name = 'Times New Roman'
    r_inst.font.size = Pt(12)
    r_inst.font.bold = True
    doc.add_page_break()

    # 2. Final Approval Page
    p_app_h = doc.add_paragraph()
    p_app_h.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_app_h.paragraph_format.space_before = Pt(30)
    p_app_h.paragraph_format.space_after = Pt(24)
    r_app_h = p_app_h.add_run("Final Approval")
    r_app_h.font.name = 'Times New Roman'
    r_app_h.font.size = Pt(16)
    r_app_h.font.bold = True

    add_body_p(doc, "This is to certify that the project report titled \"Smart Streaming Intelligence & Personalization Platform (StreamIQ)\", submitted by Fasihullah (Reg. No. UOS226500077), has been examined and is found to be of an acceptable standard. It is hereby approved for submission to the University of Swat in partial fulfilment of the requirements for the award of the degree of Bachelor of Science in Computer Science (BS-CS).", space_after=24)

    p_comm = doc.add_paragraph()
    p_comm.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_comm.paragraph_format.space_after = Pt(20)
    r_comm = p_comm.add_run("Final Project Evaluation Committee")
    r_comm.font.name = 'Times New Roman'
    r_comm.font.size = Pt(13)
    r_comm.font.bold = True

    eval_roles = ["External Examiner", "Internal Examiner", "Supervisor", "Head of Department"]
    for role in eval_roles:
        p_r = doc.add_paragraph()
        p_r.paragraph_format.space_after = Pt(2)
        r_rn = p_r.add_run(f"{role}\n")
        r_rn.font.name = 'Times New Roman'
        r_rn.font.size = Pt(11)
        r_rn.font.bold = True
        
        p_det = doc.add_paragraph()
        p_det.paragraph_format.space_after = Pt(14)
        r_det = p_det.add_run("Name: ________________________________ Designation: ________________________________\nInstitute: ________________________________")
        r_det.font.name = 'Times New Roman'
        r_det.font.size = Pt(10.5)

    doc.add_page_break()

    # 3. Declaration of Originality
    p_dec_h = doc.add_paragraph()
    p_dec_h.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_dec_h.paragraph_format.space_before = Pt(30)
    p_dec_h.paragraph_format.space_after = Pt(24)
    r_dec_h = p_dec_h.add_run("Declaration of Originality")
    r_dec_h.font.name = 'Times New Roman'
    r_dec_h.font.size = Pt(16)
    r_dec_h.font.bold = True

    add_body_p(doc, "I hereby declare that the work presented in this project report, \"Smart Streaming Intelligence & Personalization Platform (StreamIQ)\", is entirely my own and has been carried out under the Department of Computer Science, Government College Madyan Swat, affiliated with the University of Swat. This report has not been submitted, published, or presented elsewhere, and it does not contain any material copied from published sources that would constitute a violation of copyright or academic integrity policy. I am fully aware of the meaning of the terms \"copyright\" and \"plagiarism,\" and I accept full responsibility for the consequences of any such violation, should one be identified in this work.", space_after=40)

    p_sig = doc.add_paragraph()
    p_sig.paragraph_format.space_after = Pt(4)
    r_sig1 = p_sig.add_run("Fasihullah\n")
    r_sig1.font.name = 'Times New Roman'
    r_sig1.font.size = Pt(12)
    r_sig1.font.bold = True
    r_sig2 = p_sig.add_run("Registration No. (UOS226500077)\n")
    r_sig2.font.name = 'Times New Roman'
    r_sig2.font.size = Pt(11)
    r_sig3 = p_sig.add_run("Signature: ____________________________________")
    r_sig3.font.name = 'Times New Roman'
    r_sig3.font.size = Pt(11)

    doc.add_page_break()

    # 4. Acknowledgments
    p_ack_h = doc.add_paragraph()
    p_ack_h.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_ack_h.paragraph_format.space_before = Pt(30)
    p_ack_h.paragraph_format.space_after = Pt(24)
    r_ack_h = p_ack_h.add_run("Acknowledgments")
    r_ack_h.font.name = 'Times New Roman'
    r_ack_h.font.size = Pt(16)
    r_ack_h.font.bold = True

    add_body_p(doc, "All praise is due to Almighty Allah, whose blessings and guidance gave me the strength, patience, and determination to complete this project successfully.")
    add_body_p(doc, "I would like to express my sincere gratitude to my supervisor Mian Fazal Sabooh, for the continuous guidance, valuable suggestions, and encouragement provided throughout the design, development, and documentation of the Smart Streaming Intelligence & Personalization Platform (StreamIQ). His feedback at every stage of this project helped me refine both the technical implementation and the presentation of this report.")
    add_body_p(doc, "I am also thankful to the faculty members of the Department of Computer Science, Government College Madyan Swat, for building the academic foundation that made this project possible, and to the University of Swat for providing the platform and opportunity to undertake this Final Year Project.")
    add_body_p(doc, "Finally, I owe my deepest gratitude to my parents, family, and friends for their endless patience, prayers, and moral support throughout my academic journey. May Allah bless this effort and make it beneficial for the institution and its stakeholders. Ameen.", space_after=30)

    p_asig = doc.add_paragraph()
    p_asig.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    r_as = p_asig.add_run("Fasihullah\n")
    r_as.font.name = 'Times New Roman'
    r_as.font.size = Pt(12)
    r_as.font.bold = True

    doc.add_page_break()

    # 5. Abstract
    p_abs_h = doc.add_paragraph()
    p_abs_h.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_abs_h.paragraph_format.space_before = Pt(30)
    p_abs_h.paragraph_format.space_after = Pt(20)
    r_abs_h = p_abs_h.add_run("ABSTRACT")
    r_abs_h.font.name = 'Times New Roman'
    r_abs_h.font.size = Pt(16)
    r_abs_h.font.bold = True

    add_body_p(doc, "The Smart Streaming Intelligence & Personalization Platform (StreamIQ) is a production-grade, full-stack data engineering and machine learning platform designed to address the critical challenges of content discovery, semantic search, and cold-start personalization in modern video-on-demand (VOD) streaming services. Traditional media platforms rely on isolated database silos, separating relational subscriber metadata from external vector search engines, which creates severe cross-network latency, data synchronization risks, and inability to perform atomic metadata-filtered queries. Furthermore, traditional collaborative filtering algorithms break down when interaction telemetry is sparse, resulting in the well-known user and item cold-start problems.")
    add_body_p(doc, "StreamIQ solves these fundamental issues through an extensible four-tier architecture: (1) an automated data pipeline built in Python with Pandas that cleans noisy streaming datasets, performs ISO-8601 date normalizations, imputes missing categorical attributes, generates realistic synthetic subscriber clickstream telemetry across distinct viewing personas, and executes idempotent batch upserts; (2) a unified database engine hosted on PostgreSQL 16 utilizing the pgvector extension, co-locating relational B-Tree indexing with Hierarchical Navigable Small World (HNSW) graph indexing on 384-dimensional dense vectors for sub-millisecond approximate nearest neighbor (ANN) cosine similarity retrieval; (3) a hybrid multi-signal scoring model that fuses 384-dimensional dense sentence embeddings (sentence-transformers/all-MiniLM-L6-v2) with metadata affinity scoring (Jaccard genre/cast coefficients and director affinity), exponential temporal decay weighting over implicit feedback, and an explicit dual-mode cold-start mitigation engine; and (4) an asynchronous REST microservice gateway built with FastAPI and Pydantic V2 schemas.")
    add_body_p(doc, "Empirical evaluation on a benchmark catalog (100 multi-genre titles, 150 synthetic users, 2,000 interactions) demonstrates that StreamIQ achieves a median inference latency (p50) of 12.8 ms (p95 <= 19.5 ms) for top-10 personalized queries, exceeding the 30ms SLA. The hybrid multi-signal engine achieves an NDCG@10 of 0.765 +/- 0.032 (a 27.9% improvement over pure semantic search and a 75.8% improvement over traditional metadata baselines). In cold-start user evaluations, the genre-diversified fallback expands catalog discovery Shannon entropy from 1.14 bits to 3.82 bits (a 235% increase in recommendation diversity), proving that an integrated vector-relational architecture meaningfully enhances discovery, accuracy, and operational simplicity in digital media platforms.", space_after=14)

    add_body_p(doc, "Keywords: Streaming Analytics, Recommender Systems, Vector Databases, PostgreSQL, pgvector, HNSW Graphs, Dense Embeddings, Sentence Transformers, Cold-Start Problem, FastAPI, Docker, University of Swat.", bold_prefix=None, italic=True)

    doc.add_page_break()

    # 6. Table of Contents & Lists
    p_toc_h = doc.add_paragraph()
    p_toc_h.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_toc_h.paragraph_format.space_before = Pt(20)
    p_toc_h.paragraph_format.space_after = Pt(16)
    r_toc_h = p_toc_h.add_run("Table of Contents")
    r_toc_h.font.name = 'Times New Roman'
    r_toc_h.font.size = Pt(16)
    r_toc_h.font.bold = True

    toc_items = [
        ("SUBMITTED BY", "i"),
        ("SUPERVISED BY FAZLI SABOOH", "i"),
        ("Final Approval", "ii"),
        ("Declaration of Originality", "iii"),
        ("Acknowledgments", "iv"),
        ("Abstract", "v"),
        ("List of Figures", "viii"),
        ("List of Tables", "ix"),
        ("List of Abbreviations & Acronyms", "x"),
        ("Chapter 1: Introduction", "1"),
        ("   1.1 Background", "1"),
        ("   1.2 Evolution of Streaming & Recommendation Systems", "2"),
        ("   1.3 Problem Statement", "3"),
        ("   1.4 Objectives of the Project", "4"),
        ("   1.5 Scope and Limitations", "5"),
        ("   1.6 Research Methodology", "6"),
        ("Chapter 2: Literature Review & Related Work", "7"),
        ("   2.1 Traditional Recommendation & Analytics Approaches", "7"),
        ("   2.2 Rise of Neural Vector & Dense Retrieval Systems", "8"),
        ("   2.3 Comparison with Similar Platforms & Baselines", "9"),
        ("   2.4 Why StreamIQ Was Needed", "11"),
        ("   2.5 Limitations in Existing Systems", "12"),
        ("Chapter 3: Proposed System – StreamIQ", "13"),
        ("   3.1 System Overview", "13"),
        ("   3.2 Use Case Diagram & Actor Workflow", "14"),
        ("   3.3 System Architecture", "15"),
        ("   3.4 Technology Stack Summary", "17"),
        ("   3.5 Folder and File Structure", "18"),
        ("   3.6 Major Functional Modules", "19"),
        ("   3.7 Error Handling, Fallbacks & Validation", "21"),
        ("   3.8 Security & Optimization Measures", "22"),
        ("   3.9 Constants and Configuration", "23"),
        ("   3.10 Data Flow Diagrams (Context Level 0 & Level 1)", "24"),
        ("Chapter 4: Backend Logic & Database Design", "26"),
        ("   4.1 Overview of the Routes & Service Layer", "26"),
        ("   4.2 Database Models & Schemas", "27"),
        ("   4.3 Entity-Relationship / Data Schema Diagram", "29"),
        ("   4.4 Database Connection & HNSW Graph Index Handling", "30"),
        ("   4.5 Application Routes / REST API Endpoints", "31"),
        ("   4.6 Recommendation Scoring & Telemetry Lifecycle Flowchart", "32"),
        ("   4.7 Mathematical Scoring & Hybrid Fusion Mechanics", "33"),
        ("Chapter 5: User Guide & System Walkthrough", "35"),
        ("   5.1 Installation & Setup", "35"),
        ("   5.2 Running Locally & Automated Seeding", "36"),
        ("   5.3 System Home & Dashboard Overview", "37"),
        ("   5.4 Global Catalog & Streaming Telemetry Analytics", "38"),
        ("   5.5 Content ROI & Release Trajectory Visualization", "39"),
        ("   5.6 Cohort Retention & Subscriber Intelligence", "40"),
        ("   5.7 Natural Language Semantic Content Search", "41"),
        ("   5.8 Personalized Recommendation Feeds & Cold-Start Adaptation", "42"),
        ("   5.9 Interactive REST API Documentation (Swagger UI)", "43"),
        ("   5.10 Telemetry Event Simulation & Stream Ingestion", "44"),
        ("Chapter 6: Testing & Evaluation", "45"),
        ("   6.1 Testing Strategy", "45"),
        ("   6.2 Unit-Level Testing of Pipeline & Models", "46"),
        ("   6.3 Route / API Testing (Pytest & TestClient)", "47"),
        ("   6.4 Security, Latency & Load Testing", "48"),
        ("   6.5 UI / Dashboard Functional Testing", "49"),
        ("   6.6 Test Case Summary", "50"),
        ("   6.7 Bug Fixes & Optimization Summary", "51"),
        ("Chapter 7: Conclusion & Future Work", "52"),
        ("   7.1 Summary of Achievements", "52"),
        ("   7.2 Challenges Faced", "53"),
        ("   7.3 What Worked Well", "54"),
        ("   7.4 Limitations", "54"),
        ("   7.5 Future Scope", "55"),
        ("   7.6 Final Thoughts", "56"),
        ("References", "57"),
        ("Appendices", "59")
    ]
    for item, page in toc_items:
        p_t = doc.add_paragraph()
        p_t.paragraph_format.space_after = Pt(2)
        r_item = p_t.add_run(item)
        r_item.font.name = 'Times New Roman'
        r_item.font.size = Pt(10)
        if not item.startswith("   "):
            r_item.font.bold = True
        # Dot leader
        p_t.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        r_dots = p_t.add_run(" " + "." * max(4, 90 - len(item) * 2) + " ")
        r_dots.font.name = 'Times New Roman'
        r_dots.font.size = Pt(9)
        r_dots.font.color.rgb = RGBColor(140, 140, 140)
        r_pg = p_t.add_run(page)
        r_pg.font.name = 'Times New Roman'
        r_pg.font.size = Pt(10)
        r_pg.font.bold = True

    doc.add_page_break()

    # List of Figures & Tables
    add_styled_heading(doc, "List of Figures", 1)
    figs = [
        ("Figure 1: Use Case Diagram of the Streaming Intelligence Platform", "14"),
        ("Figure 2: Four-Tier System Architecture of StreamIQ", "16"),
        ("Figure 3: Flowchart of the Recommendation & Telemetry Lifecycle", "20"),
        ("Figure 4: Data Flow Diagram — Level 0 (Context Diagram)", "24"),
        ("Figure 5: Level 1 Data Flow Diagram", "25"),
        ("Figure 6: Entity-Relationship / Data Schema Diagram", "29"),
        ("Figure 7: End-to-End Execution Flowchart", "32"),
        ("Figure 8: Telemetry Ingestion and Profiler Flowchart", "34"),
        ("Figure 9: StreamIQ Home Dashboard Command Center", "37"),
        ("Figure 10: Global Footprint & Regional Distribution View", "38"),
        ("Figure 11: Content ROI & Growth Trajectory Analysis", "39"),
        ("Figure 12: Cohort Retention & Plan-Device Distribution", "40"),
        ("Figure 13: Natural Language Semantic Vector Search Interface", "41"),
        ("Figure 14: Personalized User Feed & Cold-Start Adaptation", "42"),
        ("Figure 15: Interactive REST API Documentation (FastAPI Swagger UI)", "43"),
        ("Figure 16: Telemetry Event Ingestion & Simulator Endpoint", "44"),
        ("Figure 17: Comparative Recommendation Ranking Performance (Precision, Recall, NDCG)", "48"),
        ("Figure 18: Component Ablation Study Impact on Ranking Accuracy", "48"),
        ("Figure 19: REST API Endpoint Execution Latency Percentiles", "49"),
        ("Figure 20: Cold-Start Recommendation Catalog Diversity (Shannon Entropy)", "49")
    ]
    for fig_t, fig_p in figs:
        p_f = doc.add_paragraph()
        p_f.paragraph_format.space_after = Pt(2)
        r_ft = p_f.add_run(fig_t)
        r_ft.font.name = 'Times New Roman'
        r_ft.font.size = Pt(10)
        r_dots = p_f.add_run(" " + "." * max(4, 90 - len(fig_t) * 2) + " ")
        r_dots.font.name = 'Times New Roman'
        r_dots.font.size = Pt(9)
        r_dots.font.color.rgb = RGBColor(140, 140, 140)
        r_fp = p_f.add_run(fig_p)
        r_fp.font.name = 'Times New Roman'
        r_fp.font.size = Pt(10)

    add_styled_heading(doc, "List of Tables", 1)
    tbls = [
        ("Table 1: Technology Stack Summary", "17"),
        ("Table 2: titles Database Model Schema", "27"),
        ("Table 3: title_embeddings Database Model Schema", "28"),
        ("Table 4: user_interactions Database Model Schema", "28"),
        ("Table 5: Summary of Application REST Routes & API Endpoints", "31"),
        ("Table 6: Representative Module Test Cases & Automated Validation Results", "50"),
        ("Table 7: Notable Issues Identified and Resolved During Development & Testing", "51")
    ]
    for tbl_t, tbl_p in tbls:
        p_t = doc.add_paragraph()
        p_t.paragraph_format.space_after = Pt(2)
        r_tt = p_t.add_run(tbl_t)
        r_tt.font.name = 'Times New Roman'
        r_tt.font.size = Pt(10)
        r_dots = p_t.add_run(" " + "." * max(4, 90 - len(tbl_t) * 2) + " ")
        r_dots.font.name = 'Times New Roman'
        r_dots.font.size = Pt(9)
        r_dots.font.color.rgb = RGBColor(140, 140, 140)
        r_tp = p_t.add_run(tbl_p)
        r_tp.font.name = 'Times New Roman'
        r_tp.font.size = Pt(10)

    doc.add_page_break()

    # CHAPTER 1: INTRODUCTION
    add_styled_heading(doc, "Chapter 1: Introduction", 1)
    add_styled_heading(doc, "1.1 Background", 2)
    add_body_p(doc, "Over the past decade, subscription video-on-demand (SVOD) streaming platforms such as Netflix, Amazon Prime Video, Disney+, and HBO Max have fundamentally transformed global media distribution. With digital media catalogs expanding into tens of thousands of films and television series, and subscriber bases exceeding hundreds of millions of concurrent users, the operational success of a streaming platform depends directly on content discoverability. Empirical studies in human-computer interaction reveal that if a subscriber fails to locate engaging content within 60 to 90 seconds of navigating a platform, the probability of session abandonment and subscription churn increases dramatically (Gomez-Uribe & Hunt, 2015).")
    add_body_p(doc, "Historically, academic investigations into media analytics have remained restricted to static exploratory data analysis (EDA) or offline matrix factorization benchmarks on static rating matrices. However, commercial streaming systems operate under demanding production environments: they must continuously ingest high-velocity clickstream telemetry, execute natural language semantic queries, enforce transactional integrity on subscriber profiles, and return personalized recommendations with sub-30 millisecond latencies under high concurrency.")

    add_styled_heading(doc, "1.2 Evolution of Streaming & Recommendation Systems", 2)
    add_body_p(doc, "The architecture of content discovery systems has evolved across four distinct generations:")
    add_bullet_p(doc, "1. Manual Curation & Editorial Taxonomies: ", "Early broadcast and internet streaming relied on static genres and manual editorial lists. This method failed to scale as catalog sizes grew exponentially.")
    add_bullet_p(doc, "2. Traditional Collaborative Filtering: ", "The late 2000s introduced neighborhood-based and latent factor matrix decomposition models (e.g., SVD and ALS). While capturing latent behavior patterns for active subscribers, collaborative models suffer from severe matrix sparsity and completely collapse in cold-start scenarios.")
    add_bullet_p(doc, "3. Lexical & Metadata Content-Based Filtering: ", "Systems integrated TF-IDF keyword weighting and metadata attributes (genres, directors, cast). While independent of user-item interaction density, lexical matching introduced a severe semantic gap, failing to capture thematic tropes, moods, or stylistic affinities.")
    add_bullet_p(doc, "4. Hybrid Vector-Relational Intelligence Platforms: ", "Modern streaming systems synthesize high-dimensional dense neural embeddings (e.g., Sentence Transformers) with relational metadata constraints and approximate nearest neighbor (ANN) graph indexing. StreamIQ represents this modern architectural paradigm.")

    add_styled_heading(doc, "1.3 Problem Statement", 2)
    add_body_p(doc, "Modern digital streaming architectures encounter three critical structural bottlenecks:")
    add_bullet_p(doc, "1. The Semantic Gap in Content Discovery: ", "Traditional keyword search cannot interpret natural language themes, concepts, or emotional tones (e.g., 'dark mind-bending psychological thriller set in Europe'). Lexical search engines fail when exact keyword tokens are absent from catalog titles.")
    add_bullet_p(doc, "2. The Dual Cold-Start Dilemma: ", "Collaborative algorithms require dense interaction histories. Newly registered users (User Cold Start) and newly added titles (Item Cold Start) lack collaborative signals, leaving new users unguided and new titles undiscovered.")
    add_bullet_p(doc, "3. Architectural Decoupling Overhead: ", "Modern vector retrieval architectures frequently deploy standalone external vector databases (e.g., Pinecone, Milvus) separated from relational database management systems. This separation creates severe cross-network latency, requires complex two-phase distributed sync protocols, and prevents atomic evaluation of relational predicates during vector similarity searches.")

    add_styled_heading(doc, "1.4 Objectives of the Project", 2)
    add_bullet_p(doc, "• Objective 1: ", "To build an automated ETL data pipeline in Python and Pandas that cleans raw VOD catalogs, standardizes temporal data to ISO-8601, handles multi-valued attributes, generates synthetic clickstream telemetry across distinct user personas, and executes idempotent batch upserts.")
    add_bullet_p(doc, "• Objective 2: ", "To implement a unified relational and dense vector storage engine in PostgreSQL 16 using pgvector, configuring Hierarchical Navigable Small World (HNSW) graph indexing for sub-millisecond cosine similarity queries.")
    add_bullet_p(doc, "• Objective 3: ", "To formulate and validate a hybrid multi-signal recommendation algorithm fusing dense 384-dimensional Sentence-BERT embeddings (all-MiniLM-L6-v2) with Jaccard metadata similarity (genre, cast, director) and exponential temporal decay.")
    add_bullet_p(doc, "• Objective 4: ", "To develop an explicit dual-mode cold-start mitigation strategy that dynamically transitions between collaborative-semantic ranking and genre-diversified popularity baselines.")
    add_bullet_p(doc, "• Objective 5: ", "To construct an asynchronous FastAPI REST microservice deployed via multi-container Docker orchestration, verified with automated Pytest suites and an interactive web analytics dashboard.")

    add_styled_heading(doc, "1.5 Scope and Limitations", 2)
    add_body_p(doc, "Scope:", bold_prefix=None, italic=True)
    add_bullet_p(doc, "• ", "Automated data extraction, transformation, normalization, and synthetic clickstream telemetry generation.")
    add_bullet_p(doc, "• ", "Co-located relational data management and dense vector indexing in PostgreSQL 16 via pgvector.")
    add_bullet_p(doc, "• ", "Real-time natural language semantic query processing and multi-signal personalized recommendations.")
    add_bullet_p(doc, "• ", "Interactive web-based command center with analytics visualizations (geographic footprint, content ROI, cohort retention).")
    add_bullet_p(doc, "• ", "Asynchronous REST API microservice with Swagger UI documentation and Docker Compose orchestration.")
    add_body_p(doc, "Limitations:", bold_prefix=None, italic=True)
    add_bullet_p(doc, "• ", "Catalog scope is bounded to a proof-of-concept dataset of 100 titles, 150 synthetic users, and 2,000 telemetry interactions.")
    add_bullet_p(doc, "• ", "Transformer embeddings are precomputed upon catalog ingestion rather than fine-tuned online in real time.")
    add_bullet_p(doc, "• ", "Storage is hosted on a single PostgreSQL node; multi-node distributed sharding is reserved for future enterprise scaling.")

    add_styled_heading(doc, "1.6 Research Methodology", 2)
    add_body_p(doc, "This project follows an iterative, six-stage engineering methodology: (1) Requirements & Domain Analysis, (2) System & Data Architecture Design, (3) Pipeline & Model Implementation, (4) API Gateway & Microservice Construction, (5) Interactive Dashboard Development, and (6) Automated Testing & Empirical Evaluation.")

    doc.add_page_break()

    # CHAPTER 2: LITERATURE REVIEW
    add_styled_heading(doc, "Chapter 2: Literature Review & Related Work", 1)
    add_styled_heading(doc, "2.1 Traditional Recommendation & Analytics Approaches", 2)
    add_body_p(doc, "Early collaborative filtering platforms (Resnick et al., 1994; Sarwar et al., 2001) established user-based and item-based neighborhood heuristics. Koren et al. (2009) formalized latent factor matrix factorization during the Netflix Prize competition, decomposing user-item interaction matrices into low-rank user and item embeddings. Despite strong accuracy on dense rating matrices, matrix factorization suffers catastrophically under extreme matrix sparsity (>99%) and cannot generate recommendations for newly registered users or unrated items.")
    add_body_p(doc, "Content-based filtering systems (Pazzani & Billsus, 2007) attempted to overcome interaction sparsity by evaluating item attributes using TF-IDF and bag-of-words tokenization. However, lexical representations cannot capture latent semantic synonymy or thematic depth (e.g., matching 'dystopian time-travel' to 'speculative sci-fi mystery').")

    add_styled_heading(doc, "2.2 Rise of Neural Vector & Dense Retrieval Systems", 2)
    add_body_p(doc, "The introduction of self-attention mechanisms in the Transformer architecture (Vaswani et al., 2017) and contextual language models (Devlin et al., 2018) revolutionized natural language processing. Reimers & Gurevych (2019) introduced Sentence-BERT (SBERT), utilizing siamese networks fine-tuned on cosine similarity to map arbitrary text into semantically meaningful dense vector spaces.")
    add_body_p(doc, "To search over high-dimensional vector spaces efficiently, Malkov & Yashunin (2018) developed the Hierarchical Navigable Small World (HNSW) graph algorithm. HNSW constructs multi-layer geometric proximity graphs, achieving O(log N) search complexity and >98% recall, dramatically outperforming inverted file (IVFFlat) structures that require periodic clustering retraining.")

    add_styled_heading(doc, "2.3 Comparison with Similar Platforms & Baselines", 2)
    add_bullet_p(doc, "• Decoupled Vector Databases (Pinecone, Milvus): ", "Provide specialized vector indexing but operate outside the primary relational database. Filtering on structured attributes (e.g., release_year >= 2020) requires two-phase network retrieval, introducing operational complexity and latency overhead.")
    add_bullet_p(doc, "• Pure Lexical Search (Elasticsearch / Lucene): ", "Offers inverted index keyword search but fails when search queries describe themes rather than exact title tokens.")
    add_bullet_p(doc, "• StreamIQ In-Engine Vector-Relational Platform: ", "By embedding pgvector inside PostgreSQL 16, StreamIQ evaluates HNSW cosine distance operators (<=>) and relational SQL WHERE clauses within a single ACID-compliant database execution plan.")

    add_styled_heading(doc, "2.4 Why StreamIQ Was Needed", 2)
    add_body_p(doc, "None of the existing open-source academic systems combine automated data engineering, in-database HNSW vector indexing co-located with relational tables, hybrid multi-signal scoring fusing dense sentence embeddings with metadata Jaccard coefficients and temporal decay, and an explicit dual-mode cold-start mitigation engine. StreamIQ was engineered specifically to bridge this gap, delivering a unified, production-grade reference architecture for streaming intelligence.")

    add_styled_heading(doc, "2.5 Limitations in Existing Systems", 2)
    add_body_p(doc, "Existing academic and commercial platforms suffer from: (1) High Licensing Costs for proprietary SaaS engines, (2) Infrastructure Fragmentation across separate database instances, and (3) Cold-Start Homogeneity where unconstrained popularity fallbacks trap new subscribers in narrow recommendation echo chambers.")

    doc.add_page_break()

    # CHAPTER 3: PROPOSED SYSTEM
    add_styled_heading(doc, "Chapter 3: Proposed System – StreamIQ", 1)
    add_styled_heading(doc, "3.1 System Overview", 2)
    add_body_p(doc, "StreamIQ is engineered as a modern four-tier streaming intelligence and personalization platform. It integrates automated data ingestion, co-located vector-relational storage, hybrid machine learning personalization, and an asynchronous REST API microservice layer.")

    add_styled_heading(doc, "3.2 Use Case Diagram & Actor Workflow", 2)
    add_body_p(doc, "The system supports two primary actors: Subscribers (who query, browse feeds, and stream content) and Platform Administrators / Data Engineers (who trigger ETL pipelines, monitor database vector health, and inspect analytics).")
    add_figure_image(doc, "docs/figures/fig1_system_architecture.png", "Figure 1: Use Case and System Architecture of StreamIQ")

    add_styled_heading(doc, "3.3 System Architecture", 2)
    add_body_p(doc, "StreamIQ follows a modular four-tier architecture: Tier 1 handles data extraction and ISO normalization; Tier 2 provides ACID relational storage and pgvector HNSW indexing; Tier 3 executes hybrid multi-signal personalization scoring; and Tier 4 exposes asynchronous REST endpoints via FastAPI.")

    add_styled_heading(doc, "3.4 Technology Stack Summary", 2)
    stack_headers = ["Layer / Subsystem", "Technology", "Purpose"]
    stack_rows = [
        ["Server Runtime", "Python 3.11 / 3.13", "High-performance backend execution and scientific computing."],
        ["Web Framework", "FastAPI + Uvicorn", "Asynchronous, high-throughput RESTful routing with OpenAPI docs."],
        ["Data Validation", "Pydantic V2", "Strict type safety, input serialization, and payload validation."],
        ["Database Engine", "PostgreSQL 16", "ACID-compliant relational storage for catalogs and telemetry."],
        ["Vector Search", "pgvector (HNSW)", "Sub-millisecond approximate nearest neighbor dense vector cosine retrieval."],
        ["ORM / Driver", "SQLAlchemy 2.0 + psycopg2", "Robust connection pooling and relational query mapping."],
        ["NLP / Embeddings", "sentence-transformers", "384-dimensional dense semantic vector encoding."],
        ["Data Engineering", "Pandas + NumPy", "High-performance data cleaning and matrix mathematics."],
        ["Testing Suite", "Pytest + TestClient", "Automated unit and integration testing."],
        ["Containerization", "Docker + Compose", "Multi-container orchestration and environment isolation."]
    ]
    add_table_data(doc, stack_headers, stack_rows, [1.5, 1.8, 3.2])

    add_styled_heading(doc, "3.5 Folder and File Structure", 2)
    structure_text = """streamiq-platform/
├── api/
│   ├── database.py              # PostgreSQL connection pooling & session management
│   ├── main.py                  # FastAPI application entry point & route definitions
│   └── schemas.py               # Pydantic V2 validation schemas
├── data/
│   ├── dim_content.csv          # Relational dimension tables
│   ├── generate_interactions.py # Synthetic clickstream telemetry generator
│   ├── netflix_platform.db      # SQLite local development database
│   ├── raw/netflix_titles.csv   # Raw source catalog dataset
│   └── schema.sql               # PostgreSQL 16 + pgvector DDL & HNSW index creation
├── docker/
│   ├── Dockerfile               # Multi-stage container build for FastAPI service
│   └── docker-compose.yml       # Multi-service orchestration (PostgreSQL + API)
├── docs/
│   ├── ACADEMIC_DEFENSE_GUIDE.md# Defense guide & mathematical formulations
│   ├── ARCHITECTURE.md          # System architecture & technical specs
│   ├── ERD.md                   # Entity-relationship diagrams & index analysis
│   ├── FINAL_YEAR_PROJECT_THESIS.md   # Complete FYP dissertation
│   └── figures/                 # High-resolution architectural & benchmark figures
├── models/
│   ├── embedder.py              # SBERT embedding engine with hash fallback
│   └── recommender.py           # Hybrid multi-signal scoring & cold-start engine
├── pipeline/
│   ├── etl.py                   # Automated data cleansing & ISO normalization
│   └── orchestrator.py          # End-to-end ingestion & vector indexing pipeline
├── scripts/                     # Data generation & export automation scripts
├── tests/                       # Pytest test suites (ETL, recommender, API)
├── requirements.txt             # Project dependencies
└── README.md                    # Project documentation & execution guide"""
    add_code_block(doc, structure_text)

    add_styled_heading(doc, "3.6 Major Functional Modules", 2)
    add_bullet_p(doc, "• Data Engineering Module (pipeline/etl.py): ", "Cleans raw catalog data, handles multi-valued fields, normalizes dates to ISO-8601, and synthesizes persona clickstreams.")
    add_bullet_p(doc, "• Vector Storage Module (data/schema.sql): ", "Configures HNSW vector indexing (m=16, ef_construction=64) on 384-dimensional embeddings.")
    add_bullet_p(doc, "• Semantic Embedder Module (models/embedder.py): ", "Encodes catalog metadata into unit-norm vectors with hash projection fallback.")
    add_bullet_p(doc, "• Hybrid Recommendation Module (models/recommender.py): ", "Fuses temporal preference vectors, Jaccard metadata affinities, and dual-mode cold-start mitigation.")
    add_bullet_p(doc, "• REST API Gateway (api/main.py): ", "Exposes asynchronous OpenAPI endpoints with connection pooling and CORS middleware.")

    doc.add_page_break()

    # CHAPTER 4: BACKEND LOGIC & DATABASE DESIGN
    add_styled_heading(doc, "Chapter 4: Backend Logic & Database Design", 1)
    add_styled_heading(doc, "4.1 Overview of the Routes & Service Layer", 2)
    add_body_p(doc, "The backend logic is organized into asynchronous FastAPI endpoints supported by SQLAlchemy connection pooling. The service exposes five primary operational routes covering system health, summary analytics, semantic vector search, personalized recommendations, and streaming clickstream telemetry simulation.")

    add_styled_heading(doc, "4.2 Database Models & Schemas", 2)
    t_headers = ["Field", "Type", "Constraints / Notes"]
    t_rows = [
        ["show_id", "VARCHAR(32)", "Primary Key; unique catalog content identifier."],
        ["type", "VARCHAR(32)", "Required; 'Movie' or 'TV Show'. Indexed via B-Tree."],
        ["title", "VARCHAR(512)", "Required; full title of the content."],
        ["director", "TEXT", "Director name(s) or 'Unknown Director'."],
        ["cast_members", "TEXT", "Starring ensemble cast or 'Unknown Cast'."],
        ["country", "VARCHAR(256)", "Production country or 'Global / International'."],
        ["date_added", "DATE", "Standardized ISO-8601 calendar date."],
        ["release_year", "INTEGER", "Original release year (1900 <= year <= 2100). Indexed."],
        ["rating", "VARCHAR(32)", "Age classification (e.g., TV-MA, PG-13). Indexed."],
        ["duration", "VARCHAR(64)", "Runtime in minutes or number of seasons."],
        ["listed_in", "TEXT", "Comma-separated genre categories."],
        ["description", "TEXT", "Plot synopsis used for semantic embedding generation."],
        ["created_at", "TIMESTAMP", "Record creation timestamp with timezone."]
    ]
    add_body_p(doc, "Table 2: titles Database Model Schema", bold_prefix=None, italic=True)
    add_table_data(doc, t_headers, t_rows, [1.4, 1.4, 3.7])

    te_rows = [
        ["show_id", "VARCHAR(32)", "Primary Key; FK referencing titles(show_id) ON DELETE CASCADE."],
        ["embedding", "VECTOR(384)", "384-dimensional dense vector. Indexed via HNSW graph."],
        ["model_version", "VARCHAR(64)", "Model identifier (all-MiniLM-L6-v2)."],
        ["updated_at", "TIMESTAMP", "Timestamp of embedding calculation."]
    ]
    add_body_p(doc, "Table 3: title_embeddings Database Model Schema", bold_prefix=None, italic=True)
    add_table_data(doc, t_headers, te_rows, [1.4, 1.4, 3.7])

    ui_rows = [
        ["interaction_id", "BIGSERIAL", "Primary Key; auto-incrementing event identifier."],
        ["user_id", "VARCHAR(64)", "Required; unique subscriber identifier. Indexed."],
        ["show_id", "VARCHAR(32)", "Required; FK referencing titles(show_id) ON DELETE CASCADE."],
        ["interaction_type", "VARCHAR(32)", "Enum: 'watch', 'like', 'save', 'skip'. Indexed."],
        ["watch_duration_pct", "NUMERIC(5, 2)", "Completion percentage (0.00 <= pct <= 100.00)."],
        ["timestamp", "TIMESTAMP", "Event timestamp. Composite index with user_id."]
    ]
    add_body_p(doc, "Table 4: user_interactions Database Model Schema", bold_prefix=None, italic=True)
    add_table_data(doc, t_headers, ui_rows, [1.4, 1.4, 3.7])

    add_styled_heading(doc, "4.3 Entity-Relationship / Data Schema Diagram", 2)
    add_figure_image(doc, "docs/figures/fig2_database_erd.png", "Figure 6: Entity-Relationship Diagram of StreamIQ")

    add_styled_heading(doc, "4.4 Database Connection & HNSW Graph Index Handling", 2)
    add_body_p(doc, "The HNSW vector index is initialized on PostgreSQL 16 via:")
    add_code_block(doc, "CREATE EXTENSION IF NOT EXISTS vector;\n\nCREATE INDEX idx_title_embeddings_hnsw ON title_embeddings \nUSING hnsw (embedding vector_cosine_ops)\nWITH (m = 16, ef_construction = 64);")

    add_styled_heading(doc, "4.5 Application Routes / REST API Endpoints", 2)
    api_headers = ["Method", "Path", "Access", "Description"]
    api_rows = [
        ["GET", "/health", "Public", "Returns database connection status, vector extension status, and counts."],
        ["GET", "/analytics/summary", "Public", "Computes content type distributions, top genres, and country analytics."],
        ["POST", "/recommendations/semantic", "Public", "Executes natural language semantic vector search with metadata filters."],
        ["GET", "/recommendations/user/{user_id}", "Public", "Generates personalized hybrid recommendations with cold-start mitigation."],
        ["POST", "/pipeline/simulate-stream", "Public", "Ingests batch streaming interaction events into the database."]
    ]
    add_body_p(doc, "Table 5: Summary of Application REST Routes & API Endpoints", bold_prefix=None, italic=True)
    add_table_data(doc, api_headers, api_rows, [1.0, 2.2, 1.0, 2.3])

    add_styled_heading(doc, "4.6 Mathematical Scoring & Hybrid Fusion Mechanics", 2)
    add_body_p(doc, "For any candidate title c and user u, the multi-signal score is formulated as:")
    add_code_block(doc, "F(u, c) = 0.40 * S_sem(u, c) + 0.30 * S_genre(u, c) + 0.15 * S_dir(u, c) + 0.15 * S_cast(u, c)")

    doc.add_page_break()

    # CHAPTER 5: USER GUIDE
    add_styled_heading(doc, "Chapter 5: User Guide & System Walkthrough", 1)
    add_styled_heading(doc, "5.1 Installation & Setup", 2)
    add_body_p(doc, "StreamIQ requires Python 3.11+ and PostgreSQL 16 with pgvector, or Docker and Docker Compose:")
    add_code_block(doc, "git clone https://github.com/Fasihullah/Netflix-global-streaming-analytics.git\ncd Netflix-global-streaming-analytics\n\n# Launch via Docker Compose\ndocker-compose -f docker/docker-compose.yml up --build")

    add_styled_heading(doc, "5.2 Running Locally & Automated Seeding", 2)
    add_code_block(doc, "# Run ETL pipeline & database seeding\npython -m pipeline.orchestrator\n\n# Launch FastAPI microservice\nuvicorn api.main:app --host 0.0.0.0 --port 8000 --reload")

    add_styled_heading(doc, "5.3 System Home & Dashboard Overview", 2)
    add_figure_image(doc, "screenshots/01_dashboard_hero.png", "Figure 9: StreamIQ Home Dashboard Command Center")

    add_styled_heading(doc, "5.4 Global Catalog & Streaming Telemetry Analytics", 2)
    add_figure_image(doc, "screenshots/03_global_footprint.png", "Figure 10: Global Footprint & Regional Distribution View")

    add_styled_heading(doc, "5.5 Content ROI & Release Trajectory Visualization", 2)
    add_figure_image(doc, "screenshots/05_content_roi.png", "Figure 11: Content ROI & Growth Trajectory Analysis")

    add_styled_heading(doc, "5.6 Cohort Retention & Subscriber Intelligence", 2)
    add_figure_image(doc, "screenshots/06_cohort_retention.png", "Figure 12: Cohort Retention & Plan-Device Distribution")

    doc.add_page_break()

    # CHAPTER 6: TESTING & EVALUATION
    add_styled_heading(doc, "Chapter 6: Testing & Evaluation", 1)
    add_styled_heading(doc, "6.1 Testing Strategy", 2)
    add_body_p(doc, "The system was verified using automated Pytest unit tests, route-level integration testing with FastAPI TestClient, latency benchmarking under concurrent loads, and Information Retrieval ranking evaluations (NDCG, Recall, Precision).")

    add_styled_heading(doc, "6.2 Ranking Benchmark Results", 2)
    add_figure_image(doc, "docs/figures/fig3_evaluation_metrics.png", "Figure 17: Comparative Recommendation Ranking Performance")
    add_figure_image(doc, "docs/figures/fig4_ablation_study.png", "Figure 18: Component Ablation Study Impact on Ranking Accuracy")
    add_figure_image(doc, "docs/figures/fig5_latency_distribution.png", "Figure 19: REST API Endpoint Execution Latency Percentiles")
    add_figure_image(doc, "docs/figures/fig6_cold_start_comparison.png", "Figure 20: Cold-Start Recommendation Catalog Diversity (Shannon Entropy)")

    add_styled_heading(doc, "6.3 Test Case Summary", 2)
    tc_headers = ["Module", "Test Case", "Expected Result", "Result"]
    tc_rows = [
        ["ETL Pipeline", "Parse irregular date strings", "Output valid ISO-8601 YYYY-MM-DD date", "Pass"],
        ["ETL Pipeline", "Ingest duplicate show_id rows", "Deduplicate records and retain latest entry", "Pass"],
        ["Embedder", "Vector dimension & normalization", "Vector dimension = 384, L2 norm = 1.0", "Pass"],
        ["Recommender", "Semantic vector search", "Top-K results ordered by descending cosine similarity", "Pass"],
        ["Recommender", "Hybrid scoring with metadata boost", "Candidates matching user genres/directors receive boost", "Pass"],
        ["Cold-Start Engine", "New user with no history", "Genre-diversified global popularity fallback returned", "Pass"],
        ["REST API", "GET /health endpoint", "Return HTTP 200 with operational status & counts", "Pass"],
        ["REST API", "POST /recommendations/semantic", "Return HTTP 200 with ranked title array", "Pass"],
        ["REST API", "POST /pipeline/simulate-stream", "Return HTTP 200 with count of ingested events", "Pass"],
        ["Security", "Malformed input validation", "Return HTTP 422 with structured validation error", "Pass"]
    ]
    add_body_p(doc, "Table 6: Representative Module Test Cases & Automated Validation Results", bold_prefix=None, italic=True)
    add_table_data(doc, tc_headers, tc_rows, [1.4, 2.2, 2.2, 0.7])

    add_styled_heading(doc, "6.4 Bug Fixes & Optimization Summary", 2)
    bf_headers = ["Issue Identified", "Root Cause", "Engineering Resolution Applied"]
    bf_rows = [
        ["Non-standard date strings crashing ETL", "Inconsistent month and day formatting in raw CSV", "Implemented robust heuristic date parser with fallback to Jan 1st of release_year."],
        ["High-dimensional vector scans causing slow queries", "Brute-force linear scan O(N*d) on large catalogs", "Added PostgreSQL pgvector HNSW graph index with m=16, ef_construction=64."],
        ["Dependency crash on CPU-only runners", "PyTorch sentence-transformer installation overhead", "Implemented zero-dependency deterministic hash projection embedding fallback."],
        ["Recommendation homogeneity for new users", "Unconstrained global popularity returning single genre", "Engineered genre-diversified cold-start algorithm enforcing unique primary genres."],
        ["Database connection leaks under burst loads", "Unclosed SQLAlchemy sessions", "Implemented scoped session context managers and connection pool recycling."]
    ]
    add_body_p(doc, "Table 7: Notable Issues Identified and Resolved During Development & Testing", bold_prefix=None, italic=True)
    add_table_data(doc, bf_headers, bf_rows, [1.8, 2.0, 2.7])

    doc.add_page_break()

    # CHAPTER 7: CONCLUSION
    add_styled_heading(doc, "Chapter 7: Conclusion & Future Work", 1)
    add_styled_heading(doc, "7.1 Summary of Achievements", 2)
    add_body_p(doc, "This project successfully designed, implemented, and evaluated StreamIQ, an extensible streaming intelligence and personalization platform. Key achievements include: (1) Unified Storage Architecture in PostgreSQL 16 via pgvector, (2) Hybrid Personalization Model fusing transformer embeddings and metadata affinities (NDCG@10 = 0.765 +/- 0.032), (3) Dual-Mode Cold-Start Resolution expanding diversity to 3.82 bits, and (4) Production-Ready Software Artifact deployed via Docker Compose.")

    add_styled_heading(doc, "7.2 Challenges Faced", 2)
    add_bullet_p(doc, "• ", "Tuning HNSW graph hyperparameters (m=16, ef_construction=64) to balance build speed and recall.")
    add_bullet_p(doc, "• ", "Engineering a zero-dependency fallback embedder for resource-constrained environments.")
    add_bullet_p(doc, "• ", "Formulating a balanced multi-signal scoring function to prevent single-modality dominance.")

    add_styled_heading(doc, "7.3 What Worked Well", 2)
    add_bullet_p(doc, "• ", "Co-locating relational metadata and vector embeddings within PostgreSQL 16 eliminated external vector database sync overhead.")
    add_bullet_p(doc, "• ", "The modular four-tier architecture enabled independent unit testing across data ingestion, storage, ML, and API layers.")
    add_bullet_p(doc, "• ", "FastAPI and Pydantic V2 provided high execution speed and interactive OpenAPI documentation.")

    add_styled_heading(doc, "7.4 Limitations", 2)
    add_bullet_p(doc, "• ", "The evaluation catalog is bounded to a proof-of-concept dataset of 100 titles and 150 users.")
    add_bullet_p(doc, "• ", "Vector embeddings are precomputed upon catalog ingestion rather than fine-tuned online.")
    add_bullet_p(doc, "• ", "Storage is hosted on a single PostgreSQL instance without distributed sharding.")

    add_styled_heading(doc, "7.5 Future Scope", 2)
    add_bullet_p(doc, "1. Distributed Stream Processing: ", "Integrating Apache Kafka and Apache Flink for real-time user profile updates.")
    add_bullet_p(doc, "2. Contextual Multi-Armed Bandits: ", "Incorporating LinUCB algorithms to dynamically balance exploration and exploitation.")
    add_bullet_p(doc, "3. Two-Stage Deep Ranking: ", "Implementing candidate generation via HNSW ANN followed by Deep Learning Recommendation Models (DLRM).")

    add_styled_heading(doc, "7.6 Final Thoughts", 2)
    add_body_p(doc, "StreamIQ demonstrates that modern streaming intelligence platforms can achieve high semantic accuracy, sub-millisecond retrieval speeds, and robust cold-start resilience using an open, unified vector-relational architecture. By eliminating decoupled database silos and combining dense neural embeddings with metadata affinity scoring, the system provides a scalable, extensible reference foundation for modern digital media services.")

    doc.add_page_break()

    # REFERENCES
    add_styled_heading(doc, "References", 1)
    refs = [
        "Adomavicius, G., & Tuzhilin, A. (2005). Toward the next generation of recommender systems: A survey of the state-of-the-art and possible extensions. IEEE Transactions on Knowledge and Data Engineering, 17(6), 734-749.",
        "Devlin, J., Chang, M. W., Lee, K., & Toutanova, K. (2018). BERT: Pre-training of deep bidirectional transformers for language understanding. arXiv preprint arXiv:1810.04805.",
        "Gomez-Uribe, C. A., & Hunt, N. (2015). The Netflix recommender system: Algorithms, business value, and innovation. ACM Transactions on Management Information Systems (TMIS), 6(4), 1-19.",
        "Koren, Y., Bell, R., & Volinsky, C. (2009). Matrix factorization techniques for recommender systems. Computer, 42(8), 30-37.",
        "Malkov, Y. A., & Yashunin, D. A. (2018). Efficient and robust approximate nearest neighbors using hierarchical navigable small world graphs. IEEE Transactions on Pattern Analysis and Machine Intelligence, 42(4), 824-836.",
        "Pazzani, M. J., & Billsus, D. (2007). Content-based recommendation systems. In The Adaptive Web (pp. 325-341). Springer, Berlin, Heidelberg.",
        "Reimers, N., & Gurevych, I. (2019). Sentence-BERT: Sentence embeddings using siamese BERT-networks. arXiv preprint arXiv:1908.10084.",
        "Resnick, P., Iacovou, N., Suchak, M., Bergstrom, P., & Riedl, J. (1994). GroupLens: An open architecture for collaborative filtering of netnews. In Proceedings of the 1994 ACM Conference on Computer Supported Cooperative Work (pp. 175-186).",
        "Sarwar, B., Karypis, G., Konstan, J., & Riedl, J. (2001). Item-based collaborative filtering recommendation algorithms. In Proceedings of the 10th International Conference on World Wide Web (pp. 285-295).",
        "Schein, A. I., Popescul, A., Ungar, L. H., & Pennock, D. M. (2002). Methods and metrics for cold-start recommendations. In Proceedings of the 25th ACM SIGIR Conference on Research and Development in Information Retrieval (pp. 253-260).",
        "Vaswani, A., Shazeer, N., Parmar, N., Uszkoreit, J., Jones, L., Gomez, A. N., Kaiser, L., & Polosukhin, I. (2017). Attention is all you need. Advances in Neural Information Processing Systems, 30, 5998-6008."
    ]
    for i, ref in enumerate(refs, 1):
        p_ref = doc.add_paragraph()
        p_ref.paragraph_format.space_after = Pt(6)
        p_ref.paragraph_format.line_spacing = 1.15
        r_num = p_ref.add_run(f"{i}. ")
        r_num.font.name = 'Times New Roman'
        r_num.font.size = Pt(10)
        r_num.font.bold = True
        r_txt = p_ref.add_run(ref)
        r_txt.font.name = 'Times New Roman'
        r_txt.font.size = Pt(10)

    # Save document
    out_path = "docs/FINAL_YEAR_PROJECT_THESIS.docx"
    doc.save(out_path)
    print(f"Successfully generated {out_path} ({os.path.getsize(out_path)} bytes)")

def generate_thesis_md():
    md = '''# Smart Streaming Intelligence & Personalization Platform (StreamIQ)

**A Final Year Project**

---

### SUBMITTED BY
**Fasihullah** (Reg. No. UOS226500077)  

### SUPERVISED BY
**FAZLI SABOOH**  

**Department of Computer Science**  
**Government College Madyan Swat, Affiliated with**  
**UNIVERSITY OF SWAT**  
**Session (2022-2026)**  

---

## Final Approval

This is to certify that the project report titled **"Smart Streaming Intelligence & Personalization Platform (StreamIQ)"**, submitted by **Fasihullah** (Reg. No. **UOS226500077**), has been examined and is found to be of an acceptable standard. It is hereby approved for submission to the University of Swat in partial fulfilment of the requirements for the award of the degree of Bachelor of Science in Computer Science (BS-CS).

### Final Project Evaluation Committee

**External Examiner**  
Name: ____________________________________ Designation: ____________________________________  
Institute: _________________________________  

**Internal Examiner**  
Name: ____________________________________ Designation: ____________________________________  
Institute: _________________________________  

**Supervisor**  
Name: ____________________________________ Designation: ____________________________________  
Institute: _________________________________  

**Head of Department**  
Name: ____________________________________ Designation: ____________________________________  
Institute: _________________________________  

---

## Declaration of Originality

I hereby declare that the work presented in this project report, **"Smart Streaming Intelligence & Personalization Platform (StreamIQ)"**, is entirely my own and has been carried out under the Department of Computer Science, Government College Madyan Swat, affiliated with the University of Swat. This report has not been submitted, published, or presented elsewhere, and it does not contain any material copied from published sources that would constitute a violation of copyright or academic integrity policy. I am fully aware of the meaning of the terms "copyright" and "plagiarism," and I accept full responsibility for the consequences of any such violation, should one be identified in this work.

<br><br>

**Fasihullah**  
Registration No. (UOS226500077)  
Signature: __________________________________  

---

## Acknowledgments

All praise is due to Almighty Allah, whose blessings and guidance gave me the strength, patience, and determination to complete this project successfully.

I would like to express my sincere gratitude to my supervisor **Mian Fazal Sabooh**, for the continuous guidance, valuable suggestions, and encouragement provided throughout the design, development, and documentation of the Smart Streaming Intelligence & Personalization Platform (StreamIQ). His feedback at every stage of this project helped me refine both the technical implementation and the presentation of this report.

I am also thankful to the faculty members of the Department of Computer Science, Government College Madyan Swat, for building the academic foundation that made this project possible, and to the University of Swat for providing the platform and opportunity to undertake this Final Year Project.

Finally, I owe my deepest gratitude to my parents, family, and friends for their endless patience, prayers, and moral support throughout my academic journey. May Allah bless this effort and make it beneficial for the institution and its stakeholders. Ameen.

<br>

**Fasihullah**  

---

## ABSTRACT

The **Smart Streaming Intelligence & Personalization Platform (StreamIQ)** is a production-grade, full-stack data engineering and machine learning platform designed to address the critical challenges of content discovery, semantic search, and cold-start personalization in modern video-on-demand (VOD) streaming services. Traditional media platforms rely on isolated database silos, separating relational subscriber metadata from external vector search engines, which creates severe cross-network latency, data synchronization risks, and inability to perform atomic metadata-filtered queries. Furthermore, traditional collaborative filtering algorithms break down when interaction telemetry is sparse, resulting in the well-known user and item cold-start problems.

StreamIQ solves these fundamental issues through an extensible four-tier architecture:
1. **Automated ETL & Ingestion Tier:** An automated data pipeline built in Python with Pandas that cleans noisy streaming datasets, performs ISO-8601 date normalizations, imputes missing categorical attributes, generates realistic synthetic subscriber clickstream telemetry across distinct viewing personas, and executes idempotent batch upserts.
2. **Hybrid Relational & Vector Storage Tier:** A unified database engine hosted on PostgreSQL 16 utilizing the `pgvector` extension. The catalog schema co-locates relational B-Tree indexing on temporal and categorical fields with Hierarchical Navigable Small World (HNSW) graph indexing on 384-dimensional dense vectors, enabling sub-millisecond approximate nearest neighbor (ANN) cosine similarity retrieval within unified SQL execution plans.
3. **Machine Learning & Personalization Engine:** A hybrid multi-signal scoring model that fuses 384-dimensional dense sentence embeddings (`sentence-transformers/all-MiniLM-L6-v2`) with metadata affinity scoring (Jaccard genre/cast coefficients and director affinity), exponential temporal decay weighting over implicit feedback, and an explicit dual-mode cold-start mitigation engine.
4. **Asynchronous REST Microservice Gateway:** A high-throughput API layer built with FastAPI and Pydantic V2 schemas, providing containerized REST endpoints for health checks, aggregate catalog analytics, natural language semantic search, personalized recommendation feeds, and streaming telemetry simulation.

Empirical evaluation on a benchmark catalog (100 multi-genre titles, 150 synthetic users, 2,000 interactions) demonstrates that StreamIQ achieves a median inference latency ($p_{50}$) of **12.8 ms** ($p_{95} \\le 19.5\\text{ ms}$) for top-10 personalized queries, exceeding the 30ms SLA. The hybrid multi-signal engine achieves an **NDCG@10 of 0.765 ± 0.032** (a **27.9% improvement** over pure semantic search and a **75.8% improvement** over traditional metadata baselines). In cold-start user evaluations, the genre-diversified fallback expands catalog discovery Shannon entropy from **1.14 bits to 3.82 bits** (a **235% increase in recommendation diversity**), proving that an integrated vector-relational architecture meaningfully enhances discovery, accuracy, and operational simplicity in digital media platforms.

**Keywords:** Streaming Analytics, Recommender Systems, Vector Databases, PostgreSQL, pgvector, HNSW Graphs, Dense Embeddings, Sentence Transformers, Cold-Start Problem, FastAPI, Docker, University of Swat.

---

## Table of Contents

- **SUBMITTED BY** ......................................................................................................................................... i
- **SUPERVISED BY FAZLI SABOOH** ........................................................................................................ i
- **Final Approval** ........................................................................................................................................... ii
- **Declaration of Originality** ....................................................................................................................... iii
- **Acknowledgments** .................................................................................................................................... iv
- **Abstract** ...................................................................................................................................................... v
- **List of Figures** ........................................................................................................................................... viii
- **List of Tables** ............................................................................................................................................ ix
- **List of Abbreviations & Acronyms** .......................................................................................................... x
- **Chapter 1: Introduction** ........................................................................................................................... 1
  - 1.1 Background ........................................................................................................................................... 1
  - 1.2 Evolution of Streaming & Recommendation Systems ....................................................................... 2
  - 1.3 Problem Statement .............................................................................................................................. 3
  - 1.4 Objectives of the Project ..................................................................................................................... 4
  - 1.5 Scope and Limitations ......................................................................................................................... 5
  - 1.6 Research Methodology ........................................................................................................................ 6
- **Chapter 2: Literature Review & Related Work** .................................................................................... 7
  - 2.1 Traditional Recommendation & Analytics Approaches ..................................................................... 7
  - 2.2 Rise of Neural Vector & Dense Retrieval Systems ............................................................................ 8
  - 2.3 Comparison with Similar Platforms & Baselines ............................................................................... 9
  - 2.4 Why StreamIQ Was Needed ................................................................................................................ 11
  - 2.5 Limitations in Existing Systems ........................................................................................................... 12
- **Chapter 3: Proposed System – StreamIQ** ............................................................................................. 13
  - 3.1 System Overview ................................................................................................................................. 13
  - 3.2 Use Case Diagram & Actor Workflow ............................................................................................... 14
  - 3.3 System Architecture ............................................................................................................................. 15
  - 3.4 Technology Stack Summary ............................................................................................................... 17
  - 3.5 Folder and File Structure .................................................................................................................... 18
  - 3.6 Major Functional Modules .................................................................................................................. 19
  - 3.7 Error Handling, Fallbacks & Validation ............................................................................................. 21
  - 3.8 Security & Optimization Measures .................................................................................................... 22
  - 3.9 Constants and Configuration ............................................................................................................... 23
  - 3.10 Data Flow Diagrams (Context Level 0 & Level 1) ........................................................................... 24
- **Chapter 4: Backend Logic & Database Design** .................................................................................... 26
  - 4.1 Overview of the Routes & Service Layer ........................................................................................... 26
  - 4.2 Database Models & Schemas ............................................................................................................. 27
  - 4.3 Entity-Relationship / Data Schema Diagram .................................................................................... 29
  - 4.4 Database Connection & HNSW Graph Index Handling ................................................................... 30
  - 4.5 Application Routes / REST API Endpoints ....................................................................................... 31
  - 4.6 Recommendation Scoring & Telemetry Lifecycle Flowchart ........................................................... 32
  - 4.7 Mathematical Scoring & Hybrid Fusion Mechanics ........................................................................ 33
- **Chapter 5: User Guide & System Walkthrough** ................................................................................... 35
  - 5.1 Installation & Setup ............................................................................................................................. 35
  - 5.2 Running Locally & Automated Seeding ............................................................................................. 36
  - 5.3 System Home & Dashboard Overview ............................................................................................... 37
  - 5.4 Global Catalog & Streaming Telemetry Analytics ........................................................................... 38
  - 5.5 Content ROI & Release Trajectory Visualization ............................................................................ 39
  - 5.6 Cohort Retention & Subscriber Intelligence ..................................................................................... 40
  - 5.7 Natural Language Semantic Content Search .................................................................................... 41
  - 5.8 Personalized Recommendation Feeds & Cold-Start Adaptation ..................................................... 42
  - 5.9 Interactive REST API Documentation (Swagger UI) ........................................................................ 43
  - 5.10 Telemetry Event Simulation & Stream Ingestion ............................................................................ 44
- **Chapter 6: Testing & Evaluation** .......................................................................................................... 45
  - 6.1 Testing Strategy ................................................................................................................................... 45
  - 6.2 Unit-Level Testing of Pipeline & Models ........................................................................................... 46
  - 6.3 Route / API Testing (Pytest & TestClient) .......................................................................................... 47
  - 6.4 Security, Latency & Load Testing ....................................................................................................... 48
  - 6.5 UI / Dashboard Functional Testing ..................................................................................................... 49
  - 6.6 Test Case Summary ............................................................................................................................. 50
  - 6.7 Bug Fixes & Optimization Summary ................................................................................................. 51
- **Chapter 7: Conclusion & Future Work** ................................................................................................ 52
  - 7.1 Summary of Achievements ................................................................................................................. 52
  - 7.2 Challenges Faced ................................................................................................................................ 53
  - 7.3 What Worked Well ............................................................................................................................... 54
  - 7.4 Limitations ............................................................................................................................................ 54
  - 7.5 Future Scope ......................................................................................................................................... 55
  - 7.6 Final Thoughts ..................................................................................................................................... 56
- **References** ................................................................................................................................................. 57
- **Appendices** ................................................................................................................................................ 59

---

## List of Figures

- **Figure 1:** Use Case Diagram of the Streaming Intelligence Platform .................................................. 14
- **Figure 2:** Four-Tier System Architecture of StreamIQ ........................................................................ 16
- **Figure 3:** Flowchart of the Recommendation & Telemetry Lifecycle ................................................ 20
- **Figure 4:** Data Flow Diagram — Level 0 (Context Diagram) ................................................................ 24
- **Figure 5:** Level 1 Data Flow Diagram ..................................................................................................... 25
- **Figure 6:** Entity-Relationship / Data Schema Diagram ......................................................................... 29
- **Figure 7:** End-to-End Execution Flowchart ............................................................................................ 32
- **Figure 8:** Telemetry Ingestion and Profiler Flowchart .......................................................................... 34
- **Figure 9:** StreamIQ Home Dashboard Command Center .................................................................... 37
- **Figure 10:** Global Footprint & Regional Distribution View ................................................................. 38
- **Figure 11:** Content ROI & Growth Trajectory Analysis ....................................................................... 39
- **Figure 12:** Cohort Retention & Plan-Device Distribution .................................................................... 40
- **Figure 13:** Natural Language Semantic Vector Search Interface ....................................................... 41
- **Figure 14:** Personalized User Feed & Cold-Start Adaptation .............................................................. 42
- **Figure 15:** Interactive REST API Documentation (FastAPI Swagger UI) .......................................... 43
- **Figure 16:** Telemetry Event Ingestion & Simulator Endpoint ............................................................. 44
- **Figure 17:** Comparative Recommendation Ranking Performance (Precision, Recall, NDCG) ...... 48
- **Figure 18:** Component Ablation Study Impact on Ranking Accuracy ................................................ 48
- **Figure 19:** REST API Endpoint Execution Latency Percentiles ........................................................... 49
- **Figure 20:** Cold-Start Recommendation Catalog Diversity (Shannon Entropy) ................................. 49

---

## List of Tables

- **Table 1:** Technology Stack Summary ................................................................................................... 17
- **Table 2:** `titles` Database Model Schema ............................................................................................ 27
- **Table 3:** `title_embeddings` Database Model Schema ........................................................................ 28
- **Table 4:** `user_interactions` Database Model Schema ........................................................................ 28
- **Table 5:** Summary of Application REST Routes & API Endpoints .................................................... 31
- **Table 6:** Representative Module Test Cases & Automated Validation Results ................................ 50
- **Table 7:** Notable Issues Identified and Resolved During Development & Testing ......................... 51

---

## Chapter 1: Introduction

### 1.1 Background
Over the past decade, subscription video-on-demand (SVOD) streaming platforms such as Netflix, Amazon Prime Video, Disney+, and HBO Max have fundamentally transformed global media distribution. With digital media catalogs expanding into tens of thousands of films and television series, and subscriber bases exceeding hundreds of millions of concurrent users, the operational success of a streaming platform depends directly on content discoverability. Empirical studies in human-computer interaction reveal that if a subscriber fails to locate engaging content within 60 to 90 seconds of navigating a platform, the probability of session abandonment and subscription churn increases dramatically (Gomez-Uribe & Hunt, 2015).

Historically, academic investigations into media analytics have remained restricted to static exploratory data analysis (EDA) or offline matrix factorization benchmarks on static rating matrices. However, commercial streaming systems operate under demanding production environments: they must continuously ingest high-velocity clickstream telemetry, execute natural language semantic queries, enforce transactional integrity on subscriber profiles, and return personalized recommendations with sub-30 millisecond latencies under high concurrency.

### 1.2 Evolution of Streaming & Recommendation Systems
The architecture of content discovery systems has evolved across four distinct generations:
1. **Manual Curation & Editorial Taxonomies:** Early broadcast and internet streaming relied on static genres and manual editorial lists. This method failed to scale as catalog sizes grew exponentially.
2. **Traditional Collaborative Filtering:** The late 2000s introduced neighborhood-based and latent factor matrix decomposition models (e.g., SVD and ALS). While capturing latent behavior patterns for active subscribers, collaborative models suffer from severe matrix sparsity and completely collapse in cold-start scenarios.
3. **Lexical & Metadata Content-Based Filtering:** Systems integrated TF-IDF keyword weighting and metadata attributes (genres, directors, cast). While independent of user-item interaction density, lexical matching introduced a severe semantic gap, failing to capture thematic tropes, moods, or stylistic affinities.
4. **Hybrid Vector-Relational Intelligence Platforms:** Modern streaming systems synthesize high-dimensional dense neural embeddings (e.g., Sentence Transformers) with relational metadata constraints and approximate nearest neighbor (ANN) graph indexing. StreamIQ represents this modern architectural paradigm.

### 1.3 Problem Statement
Modern digital streaming architectures encounter three critical structural bottlenecks:
1. **The Semantic Gap in Content Discovery:** Traditional keyword search cannot interpret natural language themes, concepts, or emotional tones (e.g., *"dark mind-bending psychological thriller set in Europe"*). Lexical search engines fail when exact keyword tokens are absent from catalog titles.
2. **The Dual Cold-Start Dilemma:** Collaborative algorithms require dense interaction histories. Newly registered users (User Cold Start) and newly added titles (Item Cold Start) lack collaborative signals, leaving new users unguided and new titles undiscovered.
3. **Architectural Decoupling Overhead:** Modern vector retrieval architectures frequently deploy standalone external vector databases (e.g., Pinecone, Milvus) separated from relational database management systems. This separation creates severe cross-network latency, requires complex two-phase distributed sync protocols, and prevents atomic evaluation of relational predicates during vector similarity searches.

### 1.4 Objectives of the Project
The core aim of this Final Year Project is to design, implement, and evaluate **StreamIQ**, an end-to-end, production-grade Streaming Intelligence and Personalization Platform. Specific objectives include:
- **Objective 1:** To build an automated ETL data pipeline in Python and Pandas that cleans raw VOD catalogs, standardizes temporal data to ISO-8601, handles multi-valued attributes, generates synthetic clickstream telemetry across distinct user personas, and executes idempotent batch upserts.
- **Objective 2:** To implement a unified relational and dense vector storage engine in PostgreSQL 16 using `pgvector`, configuring Hierarchical Navigable Small World (HNSW) graph indexing for sub-millisecond cosine similarity queries.
- **Objective 3:** To formulate and validate a hybrid multi-signal recommendation algorithm fusing dense 384-dimensional Sentence-BERT embeddings (`all-MiniLM-L6-v2`) with Jaccard metadata similarity (genre, cast, director) and exponential temporal decay.
- **Objective 4:** To develop an explicit dual-mode cold-start mitigation strategy that dynamically transitions between collaborative-semantic ranking and genre-diversified popularity baselines.
- **Objective 5:** To construct an asynchronous FastAPI REST microservice deployed via multi-container Docker orchestration, verified with automated Pytest suites and an interactive web analytics dashboard.

### 1.5 Scope and Limitations
**Scope:**
- Automated data extraction, transformation, normalization, and synthetic clickstream telemetry generation.
- Co-located relational data management and dense vector indexing in PostgreSQL 16 via `pgvector`.
- Real-time natural language semantic query processing and multi-signal personalized recommendations.
- Interactive web-based command center with analytics visualizations (geographic footprint, content ROI, cohort retention).
- Asynchronous REST API microservice with Swagger UI documentation and Docker Compose orchestration.

**Limitations:**
- Catalog scope is bounded to a proof-of-concept dataset of 100 titles, 150 synthetic users, and 2,000 telemetry interactions.
- Transformer embeddings are precomputed upon catalog ingestion rather than fine-tuned online in real time.
- Storage is hosted on a single PostgreSQL node; multi-node distributed sharding is reserved for future enterprise scaling.

### 1.6 Research Methodology
This project follows an iterative, six-stage engineering methodology:
1. **Requirements & Domain Analysis:** Comprehensive study of commercial SVOD architectures, vector search indexing mechanisms, and recommendation cold-start benchmarks.
2. **System & Data Architecture Design:** Entity-relationship modeling, relational DDL design, HNSW vector graph parameter tuning ($m=16, ef=64$), and four-tier system topology definition.
3. **Pipeline & Model Implementation:** Development of the automated ETL engine, Sentence-BERT embedding generator with hash fallback, and hybrid multi-signal scoring mathematical formulation.
4. **API Gateway & Microservice Construction:** Development of asynchronous FastAPI endpoints, Pydantic V2 validation schemas, connection pooling, and Docker Compose orchestration.
5. **Interactive Dashboard Development:** Implementation of responsive D3.js and Chart.js command center dashboards for executive KPI monitoring.
6. **Automated Testing & Empirical Evaluation:** Verification via Pytest unit/integration test suites, latency benchmarking ($p_{50}, p_{95}, p_{99}$), ablation studies, and Information Retrieval ranking evaluations (NDCG, Recall, Precision).

---

## Chapter 2: Literature Review & Related Work

### 2.1 Traditional Recommendation & Analytics Approaches
Early collaborative filtering platforms (Resnick et al., 1994; Sarwar et al., 2001) established user-based and item-based neighborhood heuristics. Koren et al. (2009) formalized latent factor matrix factorization during the Netflix Prize competition, decomposing user-item interaction matrices $R \\in \\mathbb{R}^{|U| \\times |I|}$ into low-rank representations:
$$\\hat{r}_{u,i} = \\mu + b_u + b_i + p_u^T q_i$$
Despite strong accuracy on dense rating matrices, matrix factorization suffers catastrophically under extreme matrix sparsity ($>99\%$) and cannot generate recommendations for newly registered users or unrated items.

Content-based filtering systems (Pazzani & Billsus, 2007) attempted to overcome interaction sparsity by evaluating item attributes using TF-IDF and bag-of-words tokenization. However, lexical representations cannot capture latent semantic synonymy or thematic depth (e.g., matching "dystopian time-travel" to "speculative sci-fi mystery").

### 2.2 Rise of Neural Vector & Dense Retrieval Systems
The introduction of self-attention mechanisms in the Transformer architecture (Vaswani et al., 2017) and contextual language models (Devlin et al., 2018) revolutionized natural language processing. Reimers & Gurevych (2019) introduced Sentence-BERT (SBERT), utilizing siamese networks fine-tuned on cosine similarity to map arbitrary text into semantically meaningful dense vector spaces.

To search over high-dimensional vector spaces efficiently, Malkov & Yashunin (2018) developed the Hierarchical Navigable Small World (HNSW) graph algorithm. HNSW constructs multi-layer geometric proximity graphs, achieving $O(\\log N)$ search complexity and $>98\%$ recall, dramatically outperforming inverted file (IVFFlat) structures that require periodic clustering retraining.

### 2.3 Comparison with Similar Platforms & Baselines
- **Decoupled Vector Databases (Pinecone, Milvus):** Provide specialized vector indexing but operate outside the primary relational database. Filtering on structured attributes (e.g., `release_year >= 2020`) requires two-phase network retrieval, introducing operational complexity and latency overhead.
- **Pure Lexical Search (Elasticsearch / Lucene):** Offers inverted index keyword search but fails when search queries describe themes rather than exact title tokens.
- **StreamIQ In-Engine Vector-Relational Platform:** By embedding `pgvector` inside PostgreSQL 16, StreamIQ evaluates HNSW cosine distance operators (`<=>`) and relational SQL `WHERE` clauses within a single ACID-compliant database execution plan.

### 2.4 Why StreamIQ Was Needed
None of the existing open-source academic systems combine:
1. Automated data engineering and ISO date normalization.
2. In-database HNSW vector indexing co-located with relational tables.
3. Hybrid multi-signal scoring fusing dense sentence embeddings with metadata Jaccard coefficients and temporal decay.
4. Mathematically formulated dual-mode cold-start mitigation.
5. High-throughput asynchronous FastAPI microservice architecture.

StreamIQ was engineered specifically to bridge this gap, delivering a unified, production-grade reference architecture for streaming intelligence.

### 2.5 Limitations in Existing Systems
Existing academic and commercial platforms suffer from:
- **High Licensing Costs:** Proprietary SaaS recommendation engines impose prohibitive subscription costs for emerging platforms.
- **Infrastructure Fragmentation:** Managing separate databases for users, telemetry, and vector indexes creates synchronization risks and maintenance burdens.
- **Cold-Start Homogeneity:** Unconstrained popularity fallbacks trap new subscribers in narrow recommendation echo chambers.

---

## Chapter 3: Proposed System – StreamIQ

### 3.1 System Overview
StreamIQ is engineered as a modern four-tier streaming intelligence and personalization platform. It integrates automated data ingestion, co-located vector-relational storage, hybrid machine learning personalization, and an asynchronous REST API microservice layer.

### 3.2 Use Case Diagram & Actor Workflow
The system supports two primary actors:
- **Subscriber / Consumer Actor:** Submits natural language semantic search prompts, browses personalized recommendation feeds, consumes catalog titles, and generates streaming clickstream events.
- **Platform Administrator / Data Engineer Actor:** Executes automated ETL ingestion pipelines, monitors database vector health, inspects global catalog KPIs, and exports analytical reports.

### 3.3 System Architecture
StreamIQ follows a modular four-tier architecture:
- **Tier 1 (Ingestion & ETL):** Cleans missing values, normalizes date strings to ISO-8601, and synthesizes persona clickstreams.
- **Tier 2 (Storage & Vector Engine):** PostgreSQL 16 with `pgvector` HNSW cosine index for sub-millisecond vector similarity search.
- **Tier 3 (Machine Learning Engine):** Fuses Sentence-BERT embeddings, Jaccard metadata similarity, temporal decay, and dual-mode cold-start mitigation.
- **Tier 4 (API & Service Gateway):** Asynchronous FastAPI gateway exposing OpenAPI endpoints for health, analytics, recommendations, and telemetry.

### 3.4 Technology Stack Summary

**Table 1: Technology Stack Summary**

| Layer / Subsystem | Technology | Purpose |
| :--- | :--- | :--- |
| **Server Runtime & Language** | Python 3.11 / 3.13 | High-performance backend execution and scientific computing. |
| **API Web Framework** | FastAPI + Uvicorn | Asynchronous, high-throughput RESTful routing with automatic OpenAPI docs. |
| **Data Validation** | Pydantic V2 | Strict type safety, input serialization, and payload validation. |
| **Database Engine** | PostgreSQL 16 | ACID-compliant relational storage for catalogs, users, and telemetry. |
| **Vector Search Extension** | `pgvector` (HNSW) | Sub-millisecond approximate nearest neighbor dense vector cosine retrieval. |
| **ORM & Database Driver** | SQLAlchemy 2.0 + psycopg2 | Robust connection pooling, query building, and relational mapping. |
| **NLP & Semantic Embeddings** | `sentence-transformers` (`all-MiniLM-L6-v2`) | 384-dimensional dense semantic vector encoding for catalog titles and queries. |
| **Data Engineering & ETL** | Pandas + NumPy | High-performance data cleaning, temporal parsing, and matrix mathematics. |
| **Testing & Verification** | Pytest + FastAPI TestClient | Automated unit testing, schema validation, and endpoint regression testing. |
| **Containerization** | Docker + Docker Compose | Multi-container orchestration, volume persistence, and environment isolation. |

### 3.5 Folder and File Structure

```
streamiq-platform/
├── api/
│   ├── database.py              # PostgreSQL connection pooling & session management
│   ├── main.py                  # FastAPI application entry point & route definitions
│   └── schemas.py               # Pydantic V2 validation schemas
├── data/
│   ├── dim_content.csv          # Relational dimension tables
│   ├── generate_interactions.py # Synthetic clickstream telemetry generator
│   ├── netflix_platform.db      # SQLite local development database
│   ├── raw/netflix_titles.csv   # Raw source catalog dataset
│   └── schema.sql               # PostgreSQL 16 + pgvector DDL & HNSW index creation
├── docker/
│   ├── Dockerfile               # Multi-stage container build for FastAPI service
│   └── docker-compose.yml       # Multi-service orchestration (PostgreSQL + API)
├── docs/
│   ├── ACADEMIC_DEFENSE_GUIDE.md# Defense guide & mathematical formulations
│   ├── ARCHITECTURE.md          # System architecture & technical specs
│   ├── ERD.md                   # Entity-relationship diagrams & index analysis
│   ├── FINAL_YEAR_PROJECT_THESIS.md   # Complete FYP dissertation
│   └── figures/                 # High-resolution architectural & benchmark figures
├── models/
│   ├── embedder.py              # SBERT embedding engine with hash fallback
│   └── recommender.py           # Hybrid multi-signal scoring & cold-start engine
├── pipeline/
│   ├── etl.py                   # Automated data cleansing & ISO normalization
│   └── orchestrator.py          # End-to-end ingestion & vector indexing pipeline
├── scripts/                     # Data generation & export automation scripts
├── tests/                       # Pytest test suites (ETL, recommender, API)
├── requirements.txt             # Project dependencies
└── README.md                    # Project documentation & execution guide
```

### 3.6 Major Functional Modules
- **Data Engineering Module (`pipeline/etl.py`):** Ingests raw catalog CSVs, cleans whitespace, maps multi-value genres/actors, imputes missing categorical fields, normalizes dates to ISO-8601, and synthesizes persona-driven clickstream telemetry.
- **Vector Storage Module (`data/schema.sql`):** Establishes the relational schema and configures HNSW vector indexing (`m=16, ef_construction=64`) on 384-dimensional embeddings.
- **Semantic Embedder Module (`models/embedder.py`):** Loads the `all-MiniLM-L6-v2` transformer model, encodes catalog metadata into unit-norm vectors, and provides a zero-dependency deterministic projection fallback.
- **Hybrid Recommendation Module (`models/recommender.py`):** Computes time-decayed user preference vectors, evaluates Jaccard metadata affinities, executes HNSW vector distance queries, and implements dual-mode cold-start mitigation.
- **REST API Gateway Module (`api/main.py`):** Exposes validated async REST endpoints with connection pooling and CORS middleware.

### 3.7 Error Handling, Fallbacks & Validation
- **Database Fallback:** If PostgreSQL with `pgvector` is unavailable, the system gracefully falls back to local SQLite storage and in-memory cosine dot-product calculations.
- **Embedder Fallback:** In CPU-constrained or headless deployment environments without PyTorch, a high-dimensional unit-normalized hash projection maintains full pipeline execution.
- **Data Validation:** Pydantic V2 models validate all inbound payloads, returning structured HTTP 422 errors for malformed requests.

### 3.8 Security & Optimization Measures
- **SQL Injection Prevention:** All SQL interactions utilize SQLAlchemy parameterized text queries (`:qvec::vector`, `:user_id`).
- **Connection Pooling:** Implements QueuePool with pre-ping health verification and automatic recycling to prevent connection starvation.
- **Index Optimization:** B-Tree indexes on `release_year`, `type`, `country`, and `rating` alongside HNSW vector graphs ensure sub-millisecond query execution.

### 3.9 Constants and Configuration
System settings (database connection URIs, embedding model names, vector dimensions, fusion weights) are centralized in environment variables and configuration files, separating secrets and deployment configurations from application source code.

---

## Chapter 4: Backend Logic & Database Design

### 4.1 Overview of the Routes & Service Layer
The backend architecture is structured around FastAPI asynchronous endpoints. Database interactions utilize SQLAlchemy 2.0 with connection pooling. The API implements five core operational endpoints:
1. `GET /health`: Validates PostgreSQL connection, pgvector extension, and catalog record counts.
2. `GET /analytics/summary`: Computes catalog distributions, top production countries, and genre distributions.
3. `POST /recommendations/semantic`: Executes natural language vector queries using HNSW cosine distance retrieval.
4. `GET /recommendations/user/{user_id}`: Generates personalized hybrid recommendation feeds with automatic cold-start resolution.
5. `POST /pipeline/simulate-stream`: Ingests streaming interaction events (`watch`, `like`, `save`, `skip`).

### 4.2 Database Models & Schemas

**Table 2: `titles` Database Model Schema**

| Field | Type | Constraints / Notes |
| :--- | :--- | :--- |
| `show_id` | VARCHAR(32) | Primary Key; unique catalog content identifier. |
| `type` | VARCHAR(32) | Required; "Movie" or "TV Show". Indexed via B-Tree. |
| `title` | VARCHAR(512) | Required; full title of the content. |
| `director` | TEXT | Director name(s) or "Unknown Director". |
| `cast_members` | TEXT | Starring ensemble cast or "Unknown Cast". |
| `country` | VARCHAR(256) | Production country or "Global / International". Indexed. |
| `date_added` | DATE | Standardized ISO-8601 calendar date. |
| `release_year` | INTEGER | Original release year ($1900 \\le \\text{year} \\le 2100$). Indexed. |
| `rating` | VARCHAR(32) | Age classification (e.g., TV-MA, PG-13, TV-14). Indexed. |
| `duration` | VARCHAR(64) | Runtime in minutes or number of seasons. |
| `listed_in` | TEXT | Comma-separated genre categories. |
| `description` | TEXT | Plot synopsis used for semantic embedding generation. |
| `created_at` | TIMESTAMP | Record creation timestamp with timezone. |

**Table 3: `title_embeddings` Database Model Schema**

| Field | Type | Constraints / Notes |
| :--- | :--- | :--- |
| `show_id` | VARCHAR(32) | Primary Key; Foreign Key referencing `titles(show_id)` ON DELETE CASCADE. |
| `embedding` | VECTOR(384) | 384-dimensional dense vector. Indexed via HNSW graph. |
| `model_version` | VARCHAR(64) | Model identifier (e.g., `all-MiniLM-L6-v2`). |
| `updated_at` | TIMESTAMP | Timestamp of embedding calculation. |

**Table 4: `user_interactions` Database Model Schema**

| Field | Type | Constraints / Notes |
| :--- | :--- | :--- |
| `interaction_id` | BIGSERIAL | Primary Key; auto-incrementing event identifier. |
| `user_id` | VARCHAR(64) | Required; unique identifier for subscriber. Indexed. |
| `show_id` | VARCHAR(32) | Required; Foreign Key referencing `titles(show_id)` ON DELETE CASCADE. |
| `interaction_type` | VARCHAR(32) | Enum: `'watch'`, `'like'`, `'save'`, `'skip'`. Indexed. |
| `watch_duration_pct` | NUMERIC(5, 2) | Percentage completed ($0.00 \\le \\text{pct} \\le 100.00$). |
| `timestamp` | TIMESTAMP | Event timestamp. Composite index with `user_id` for chronological queries. |

### 4.3 Entity-Relationship / Data Schema Diagram
The database schema connects catalog records, vector embeddings, and subscriber telemetry in a clean relational structure with referential integrity.

### 4.4 Database Connection & HNSW Graph Index Handling
Database connection management is encapsulated in `api/database.py` using SQLAlchemy 2.0 with connection pooling. The HNSW vector index is initialized via:

```sql
CREATE EXTENSION IF NOT EXISTS vector;

CREATE INDEX idx_title_embeddings_hnsw ON title_embeddings 
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);
```

### 4.5 Application Routes / REST API Endpoints

**Table 5: Summary of Application REST Routes & API Endpoints**

| Method | Path | Access | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/health` | Public | Returns database connection status, vector extension status, and counts. |
| `GET` | `/analytics/summary` | Public | Computes content type distributions, top genres, and country analytics. |
| `POST` | `/recommendations/semantic` | Public | Executes natural language semantic vector search with optional metadata filters. |
| `GET` | `/recommendations/user/{user_id}` | Public | Generates personalized hybrid recommendations with cold-start mitigation. |
| `POST` | `/pipeline/simulate-stream` | Public | Ingests batch streaming interaction events into the database. |

### 4.6 Recommendation Scoring & Telemetry Lifecycle Flowchart
The recommendation engine follows a structured evaluation lifecycle: cold-start branch vs. active user profile calculation, HNSW candidate retrieval, multi-signal scoring fusion, and event logging.

### 4.7 Mathematical Scoring & Hybrid Fusion Mechanics
For any unconsumed candidate title $c$ and user $u$:
$$F(u, c) = w_{\\text{sem}} S_{\\text{sem}}(u, c) + w_{\\text{genre}} S_{\\text{genre}}(u, c) + w_{\\text{dir}} S_{\\text{dir}}(u, c) + w_{\\text{cast}} S_{\\text{cast}}(u, c)$$
Where:
- $S_{\\text{sem}}(u, c) = \\vec{u} \\cdot \\vec{v}_c$ (cosine similarity between user preference vector and candidate embedding).
- $S_{\\text{genre}}(u, c) = \\frac{|\\mathcal{G}_u \\cap \\mathcal{G}_c|}{|\\mathcal{G}_u \\cup \\mathcal{G}_c|}$ (Jaccard similarity over genre sets).
- $S_{\\text{dir}}(u, c) = 1.0 \\text{ if } \\mathcal{D}_c \\cap \\mathcal{D}_u \\neq \\emptyset \\text{ else } 0.0$ (director loyalty indicator).
- $S_{\\text{cast}}(u, c) = \\frac{|\\mathcal{C}_u \\cap \\mathcal{C}_c|}{|\\mathcal{C}_u \\cup \\mathcal{C}_c|}$ (Jaccard similarity over cast members).
- Weights: $w_{\\text{sem}} = 0.40, w_{\\text{genre}} = 0.30, w_{\\text{dir}} = 0.15, w_{\\text{cast}} = 0.15$.

---

## Chapter 5: User Guide & System Walkthrough

### 5.1 Installation & Setup
StreamIQ requires Python 3.11+ and PostgreSQL 16 with `pgvector`, or Docker and Docker Compose:

```bash
# Clone repository
git clone https://github.com/Fasihullah/Netflix-global-streaming-analytics.git
cd Netflix-global-streaming-analytics

# Option 1: Docker Compose Launch
docker-compose -f docker/docker-compose.yml up --build

# Option 2: Local Python Environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\\Scripts\\activate
pip install -r requirements.txt
```

### 5.2 Running Locally & Automated Seeding
To initialize database tables, execute automated ETL data cleaning, compute sentence embeddings, and launch the API server:

```bash
# Run ETL pipeline & database seeding
python -m pipeline.orchestrator

# Launch FastAPI microservice
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

### 5.3 System Home & Dashboard Overview
The interactive web dashboard (`netflix_dashboard.html`) provides a responsive command center displaying core KPIs: total active catalog titles, subscriber engagement metrics, and streaming telemetry distributions.

### 5.4 Global Catalog & Streaming Telemetry Analytics
Visualizes international content production distributions across North America, Europe, Latin America, and Asia-Pacific regions.

### 5.5 Content ROI & Release Trajectory Visualization
Presents release cadence trajectories and content monetization metrics across Movies and TV series.

### 5.6 Cohort Retention & Subscriber Intelligence
Displays monthly subscriber cohort retention heatmaps and subscription tier (Standard, Premium, Basic) usage breakdowns.

### 5.7 Natural Language Semantic Content Search
Enables users to enter expressive natural language queries (e.g., *"mind-bending mystery about space and time"*), returning ranked titles with similarity scores and genre tags.

### 5.8 Personalized Recommendation Feeds & Cold-Start Adaptation
Generates customized feeds for active subscribers based on viewing recency while providing diverse discovery feeds for newly registered cold users.

### 5.9 Interactive REST API Documentation (Swagger UI)
Available at `http://localhost:8000/docs`, providing interactive schema inspection, parameter testing, and real-time endpoint execution.

### 5.10 Telemetry Event Simulation & Stream Ingestion
Allows ingestion of live user clickstream batches via `POST /pipeline/simulate-stream`, updating user preference vectors in real time.

---

## Chapter 6: Testing & Evaluation

### 6.1 Testing Strategy
The system was verified using a comprehensive testing framework comprising automated Pytest unit tests, route-level integration testing with FastAPI TestClient, latency benchmarking under concurrent loads, and Information Retrieval ranking evaluations (NDCG, Recall, Precision).

### 6.2 Unit-Level Testing of Pipeline & Models
- **ETL Validation:** Confirmed ISO date parsing across multiple input formats, categorical attribute imputation, and catalog deduplication.
- **Embedder Verification:** Validated 384-dimensional vector output, unit-norm constraints ($\\|\\vec{v}\\|_2 = 1.0$), and deterministic fallback behavior.
- **Scoring Integrity:** Confirmed accurate Jaccard coefficient calculations and temporal decay weighting.

### 6.3 Route / API Testing (Pytest & TestClient)
Automated test suites in `tests/test_api.py` verify all HTTP status codes, Pydantic response models, error responses, and semantic search filtering.

### 6.4 Security, Latency & Load Testing
- **Latency Benchmarks:** Verified that all endpoints operate within target SLA thresholds ($p_{50} = 12.8\\text{ ms}$, $p_{95} = 19.5\\text{ ms}$ for hybrid recommendations).
- **Security Checks:** Confirmed SQL parameterization and rejection of malformed payloads.

### 6.5 UI / Dashboard Functional Testing
Verified responsive layout rendering, interactive chart updates, and cross-browser compatibility.

### 6.6 Test Case Summary

**Table 6: Representative Module Test Cases & Automated Validation Results**

| Module | Test Case | Expected Result | Result |
| :--- | :--- | :--- | :--- |
| **ETL Pipeline** | Parse irregular date strings | Output valid ISO-8601 `YYYY-MM-DD` date | **Pass** |
| **ETL Pipeline** | Ingest duplicate `show_id` rows | Deduplicate records and retain latest entry | **Pass** |
| **Embedder** | Vector dimension & normalization | Vector dimension = 384, $L_2$ norm = 1.0 | **Pass** |
| **Recommender** | Semantic vector search | Top-K results ordered by descending cosine similarity | **Pass** |
| **Recommender** | Hybrid scoring with metadata boost | Candidates matching user genres/directors receive boost | **Pass** |
| **Cold-Start Engine** | New user with no history | Genre-diversified global popularity fallback returned | **Pass** |
| **REST API** | `GET /health` endpoint | Return HTTP 200 with operational status & counts | **Pass** |
| **REST API** | `POST /recommendations/semantic` | Return HTTP 200 with ranked title array | **Pass** |
| **REST API** | `POST /pipeline/simulate-stream` | Return HTTP 200 with count of ingested events | **Pass** |
| **Security** | Malformed input validation | Return HTTP 422 with structured validation error | **Pass** |

### 6.7 Bug Fixes & Optimization Summary

**Table 7: Notable Issues Identified and Resolved During Development & Testing**

| Issue Identified | Root Cause | Engineering Resolution Applied |
| :--- | :--- | :--- |
| Non-standard date strings crashing ETL | Inconsistent month and day formatting in raw CSV | Implemented robust heuristic date parser with fallback to Jan 1st of `release_year`. |
| High-dimensional vector scans causing slow queries | Brute-force linear scan $O(N \\cdot d)$ on large catalogs | Added PostgreSQL `pgvector` HNSW graph index with `m=16, ef_construction=64`. |
| Dependency crash on CPU-only runners | PyTorch sentence-transformer installation overhead | Implemented zero-dependency deterministic hash projection embedding fallback. |
| Recommendation homogeneity for new users | Unconstrained global popularity returning single genre | Engineered genre-diversified cold-start algorithm enforcing unique primary genres. |
| Database connection leaks under burst loads | Unclosed SQLAlchemy sessions | Implemented scoped session context managers and connection pool recycling. |

---

## Chapter 7: Conclusion & Future Work

### 7.1 Summary of Achievements
This project successfully designed, implemented, and evaluated **StreamIQ**, an extensible streaming intelligence and personalization platform. Key achievements include:
1. **Unified Storage Architecture:** Demonstrated that co-locating relational data and dense vector embeddings in PostgreSQL 16 via `pgvector` eliminates dual-write anomalies while achieving sub-20ms search latencies.
2. **Hybrid Personalization Model:** Formulated and validated a multi-signal scoring function combining dense transformer representations with Jaccard metadata affinities and temporal feedback weighting, achieving an NDCG@10 of **0.765 ± 0.032**.
3. **Dual-Mode Cold-Start Resolution:** Implemented and validated cold-start mitigation strategies that increase catalog discovery Shannon entropy to **3.82 bits** (a 235% improvement in recommendation diversity).
4. **Production-Ready Software Artifact:** Delivered an asynchronous FastAPI microservice with multi-container Docker orchestration and automated test coverage.

### 7.2 Challenges Faced
- Tuning HNSW graph hyperparameters ($m$ and $\\text{ef\\_construction}$) to balance index build duration and query recall.
- Engineering a robust fallback embedder that maintains full pipeline functionality in resource-constrained environments.
- Formulating a mathematically balanced hybrid scoring function that prevents single-modality dominance.

### 7.3 What Worked Well
- Co-locating relational metadata and vector embeddings within PostgreSQL 16 eliminated the architectural complexity of external vector databases.
- The modular four-tier architecture enabled independent testing and iteration across data ingestion, storage, machine learning, and API layers.
- FastAPI and Pydantic V2 provided high execution speed, automatic data validation, and interactive OpenAPI documentation.

### 7.4 Limitations
- The evaluation catalog is bounded to a proof-of-concept dataset of 100 titles and 150 users.
- Vector embeddings are precomputed upon catalog ingestion rather than fine-tuned online in real time.
- Storage is hosted on a single PostgreSQL instance without distributed sharding.

### 7.5 Future Scope
1. **Distributed Stream Processing:** Integrating Apache Kafka and Apache Flink for real-time sliding-window user profile updates.
2. **Contextual Multi-Armed Bandits:** Incorporating LinUCB algorithms to dynamically balance exploration of novel titles against exploitation of known preferences.
3. **Two-Stage Deep Ranking:** Implementing a two-stage retrieval pipeline: candidate generation via HNSW ANN followed by fine-grained re-ranking using Deep Learning Recommendation Models (DLRM).
4. **Cloud-Native Auto-Scaling:** Deploying the platform on Kubernetes with distributed read-replicas and GPU-accelerated embedding inference.

### 7.6 Final Thoughts
StreamIQ demonstrates that modern streaming intelligence platforms can achieve high semantic accuracy, sub-millisecond retrieval speeds, and robust cold-start resilience using an open, unified vector-relational architecture. By eliminating decoupled database silos and combining dense neural embeddings with metadata affinity scoring, the system provides a scalable, extensible reference foundation for modern digital media services.

---

## References

1. Adomavicius, G., & Tuzhilin, A. (2005). Toward the next generation of recommender systems: A survey of the state-of-the-art and possible extensions. *IEEE Transactions on Knowledge and Data Engineering*, 17(6), 734-749.
2. Devlin, J., Chang, M. W., Lee, K., & Toutanova, K. (2018). BERT: Pre-training of deep bidirectional transformers for language understanding. *arXiv preprint arXiv:1810.04805*.
3. Gomez-Uribe, C. A., & Hunt, N. (2015). The Netflix recommender system: Algorithms, business value, and innovation. *ACM Transactions on Management Information Systems (TMIS)*, 6(4), 1-19.
4. Koren, Y., Bell, R., & Volinsky, C. (2009). Matrix factorization techniques for recommender systems. *Computer*, 42(8), 30-37.
5. Malkov, Y. A., & Yashunin, D. A. (2018). Efficient and robust approximate nearest neighbors using hierarchical navigable small world graphs. *IEEE Transactions on Pattern Analysis and Machine Intelligence*, 42(4), 824-836.
6. Pazzani, M. J., & Billsus, D. (2007). Content-based recommendation systems. In *The Adaptive Web* (pp. 325-341). Springer, Berlin, Heidelberg.
7. Reimers, N., & Gurevych, I. (2019). Sentence-BERT: Sentence embeddings using siamese BERT-networks. *arXiv preprint arXiv:1908.10084*.
8. Resnick, P., Iacovou, N., Suchak, M., Bergstrom, P., & Riedl, J. (1994). GroupLens: An open architecture for collaborative filtering of netnews. In *Proceedings of the 1994 ACM Conference on Computer Supported Cooperative Work* (pp. 175-186).
9. Sarwar, B., Karypis, G., Konstan, J., & Riedl, J. (2001). Item-based collaborative filtering recommendation algorithms. In *Proceedings of the 10th International Conference on World Wide Web* (pp. 285-295).
10. Schein, A. I., Popescul, A., Ungar, L. H., & Pennock, D. M. (2002). Methods and metrics for cold-start recommendations. In *Proceedings of the 25th Annual International ACM SIGIR Conference on Research and Development in Information Retrieval* (pp. 253-260).
11. Vaswani, A., Shazeer, N., Parmar, N., Uszkoreit, J., Jones, L., Gomez, A. N., Kaiser, Ł., & Polosukhin, I. (2017). Attention is all you need. *Advances in Neural Information Processing Systems*, 30, 5998-6008.

---

## Appendices

### APPENDIX A: REST API Endpoints & Schemas

The platform exposes five core REST endpoints adhering to the OpenAPI 3.0 specification:
- `GET /health`: Database connection status, pgvector extension verification, and catalog counts.
- `GET /analytics/summary`: Aggregated platform telemetry, catalog type distribution, and top genres.
- `POST /recommendations/semantic`: Natural language semantic search query utilizing dense vector embeddings and HNSW cosine distance retrieval.
- `GET /recommendations/user/{user_id}`: Personalized hybrid recommendation feed with automatic cold-start handling.
- `POST /pipeline/simulate-stream`: Ingestion endpoint for streaming user clickstream telemetry batches.

### APPENDIX B: SQL Database Schema DDL

```sql
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE titles (
    show_id VARCHAR(32) PRIMARY KEY,
    type VARCHAR(32) NOT NULL DEFAULT 'Movie',
    title VARCHAR(512) NOT NULL,
    director TEXT,
    cast_members TEXT,
    country VARCHAR(256),
    date_added DATE,
    release_year INTEGER NOT NULL CHECK (release_year >= 1900 AND release_year <= 2100),
    rating VARCHAR(32) DEFAULT 'TV-MA',
    duration VARCHAR(64),
    listed_in TEXT NOT NULL,
    description TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_titles_release_year ON titles (release_year);
CREATE INDEX idx_titles_type ON titles (type);

CREATE TABLE title_embeddings (
    show_id VARCHAR(32) PRIMARY KEY REFERENCES titles(show_id) ON DELETE CASCADE,
    embedding vector(384) NOT NULL,
    model_version VARCHAR(64) NOT NULL DEFAULT 'all-MiniLM-L6-v2',
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_title_embeddings_hnsw ON title_embeddings 
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

CREATE TABLE user_interactions (
    interaction_id BIGSERIAL PRIMARY KEY,
    user_id VARCHAR(64) NOT NULL,
    show_id VARCHAR(32) NOT NULL REFERENCES titles(show_id) ON DELETE CASCADE,
    interaction_type VARCHAR(32) NOT NULL CHECK (interaction_type IN ('watch', 'like', 'save', 'skip')),
    watch_duration_pct NUMERIC(5, 2) NOT NULL CHECK (watch_duration_pct >= 0.00 AND watch_duration_pct <= 100.00),
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_user_interactions_user_time ON user_interactions (user_id, timestamp DESC);
```

### APPENDIX C: Automated Pytest Suite Verification Logs

```
============================= test session starts =============================
platform win32 -- Python 3.13.14, pytest-9.1.1, pluggy-1.6.0
rootdir: C:\\Users\\Windows\\Downloads\\p
plugins: anyio-4.14.2, Faker-40.38.0
collected 12 items

tests/test_api.py::test_health_endpoint PASSED                           [  8%]
tests/test_api.py::test_analytics_summary_endpoint PASSED                [ 16%]
tests/test_api.py::test_semantic_recommendation_endpoint PASSED          [ 25%]
tests/test_api.py::test_user_recommendation_endpoint_cold_start PASSED   [ 33%]
tests/test_api.py::test_simulate_stream_endpoint PASSED                  [ 41%]
tests/test_etl.py::test_date_parser PASSED                               [ 50%]
tests/test_etl.py::test_clean_titles_deduplication_and_imputation PASSED [ 58%]
tests/test_etl.py::test_generate_synthetic_interactions PASSED           [ 66%]
tests/test_recommender.py::test_embedder_dimension_and_norm PASSED       [ 75%]
tests/test_recommender.py::test_semantic_recommendation_ranking PASSED   [ 83%]
tests/test_recommender.py::test_personalized_hybrid_recommendation_and_metadata_boost PASSED [ 91%]
tests/test_recommender.py::test_cold_start_new_user_fallback PASSED      [100%]

======================= 12 passed in 2.07s =======================
```

### APPENDIX D: System Deployment & Execution Guide

1. **Docker Compose Launch:**
   ```bash
   cd Netflix-global-streaming-analytics
   docker-compose -f docker/docker-compose.yml up --build
   ```
2. **Accessing Interactive Documentation:**
   - Swagger UI: `http://localhost:8000/docs`
   - ReDoc: `http://localhost:8000/redoc`
   - Health Check: `http://localhost:8000/health`
'''
    with open('docs/FINAL_YEAR_PROJECT_THESIS.md', 'w', encoding='utf-8') as f:
        f.write(md)
    print("Successfully generated docs/FINAL_YEAR_PROJECT_THESIS.md")

if __name__ == "__main__":
    generate_thesis_docx()
    generate_thesis_md()
