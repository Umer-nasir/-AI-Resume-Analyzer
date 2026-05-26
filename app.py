import streamlit as st
import os
import tempfile
import plotly.graph_objects as go
from dotenv import load_dotenv

# Import our custom backend modules
from resume_analyzer import analyze_resume
from pdf_generator import generate_resume_report_pdf

# Load system environment variables if present
load_dotenv()

# Page Setup
st.set_page_config(
    page_title="AI Resume Analyzer & Ranker",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CUSTOM CSS FOR PREMIUM DESIGN AESTHETICS ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    
    .main-header {
        background: linear-gradient(135deg, #1E3A8A 0%, #3B82F6 50%, #1D4ED8 100%);
        padding: 2.5rem 2rem;
        border-radius: 20px;
        color: white;
        margin-bottom: 2rem;
        box-shadow: 0 10px 30px rgba(59, 130, 246, 0.2);
        position: relative;
        overflow: hidden;
    }
    .main-header::before {
        content: '';
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0) 80%);
        pointer-events: none;
    }
    
    .main-title {
        font-size: 2.8rem;
        font-weight: 800;
        margin: 0;
        letter-spacing: -1px;
    }
    .main-subtitle {
        font-size: 1.1rem;
        font-weight: 300;
        opacity: 0.9;
        margin-top: 0.5rem;
    }
    
    .custom-card {
        background: rgba(255, 255, 255, 0.7);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.5);
        border-radius: 16px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.03);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    .custom-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 30px rgba(0, 0, 0, 0.06);
    }
    
    .card-title {
        font-size: 1.2rem;
        font-weight: 700;
        color: #1E3A8A;
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    .agent-step {
        background: #F3F4F6;
        border-radius: 10px;
        padding: 0.75rem 1rem;
        margin-bottom: 0.5rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
        border: 1px solid #E5E7EB;
    }
</style>
""", unsafe_allow_html=True)

# --- JOB DESCRIPTION TEMPLATES ---
JOB_TEMPLATES = {
    "Custom": "",
    "Python Developer": """We are hiring a Python Developer with:
- 2+ years Python experience
- Knowledge of Django or Flask
- Experience with REST APIs
- Familiarity with SQL databases (SQLite, PostgreSQL, MySQL)
- Knowledge of Git and Agile methodologies""",
    
    "Data Scientist": """We are looking for a Data Scientist to join our team:
- 3+ years experience with Python (Pandas, NumPy, Scikit-Learn)
- Experience with SQL and relational databases
- Understanding of machine learning models (regression, classification, clustering)
- Experience with data visualization (Matplotlib, Seaborn)
- Degree in Computer Science, Statistics, or Math""",
    
    "Frontend React Engineer": """We are seeking a Frontend React Engineer:
- 2+ years experience building web applications using React.js and TypeScript
- Strong skills in HTML5, CSS3, modern layouts (Flexbox, Grid)
- Experience with state management (Redux, Context API)
- Familiarity with build tools like Vite and version control with Git
- Experience integrating RESTful APIs"""
}

# --- SIDEBAR: AUTH & CONTROLS ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/944/944038.png", width=60)
    st.markdown("### **Analyzer Settings**")
    st.caption("Configure environment parameters below:")
    
    env_key = os.environ.get("OPENAI_API_KEY", "")
    api_key_input = st.text_input(
        "OpenAI API Key",
        value=env_key,
        type="password",
        placeholder="sk-...",
        help="Input your OpenAI API key. We do not store keys; they are stored in-memory for your active session."
    )
    
    selected_model = st.selectbox(
        "Select LLM Model",
        options=["gpt-4o-mini", "gpt-4o"],
        index=0,
        help="gpt-4o-mini is highly recommended for speed and cost efficiency."
    )
    
    st.divider()
    
    selected_template = st.selectbox(
        "Pre-filled Job Descriptions",
        options=list(JOB_TEMPLATES.keys()),
        index=1 # Defaults to Python Developer
    )
    
    st.info("💡 **RAG Engine Details:**\nResumes are parsed as PDFs and split into semantic chunks, allowing the agents to instantly search and review only the relevant sections against the job requirements.")

# --- GLASSMORPHIC HERO BANNER ---
st.markdown("""
<div class="main-header">
    <h1 class="main-title">🎯 AI Resume Analyzer & Ranker</h1>
    <p class="main-subtitle">Elevate your recruitment process. Use 4 collaborative AI agents to extract skills, spot gaps, evaluate compatibility, and generate target interview prep guides.</p>
</div>
""", unsafe_allow_html=True)

# Verify API Key exists
active_api_key = api_key_input if api_key_input else env_key

if not active_api_key:
    st.warning("⚠️ **OpenAI API Key Required**: Please enter your OpenAI API key in the left sidebar to activate the AI agent crew!")
    st.info("Don't worry, keys are kept safely in-memory during execution and are never saved to any database.")
    st.stop()

# --- TABS FOR DUAL MODE ---
tab1, tab2, tab3 = st.tabs(["📊 Single Resume Analyzer", "🏆 Multi-Candidate Ranker", "⚙️ How It Works"])

# --- TAB 1: SINGLE RESUME ANALYZER ---
with tab1:
    col_input, col_config = st.columns([1.2, 1.0])
    
    with col_input:
        st.markdown("### **1. Input Parameters**")
        
        default_job_desc = JOB_TEMPLATES[selected_template]
        job_desc = st.text_area(
            "Job Requirements / Description",
            value=default_job_desc,
            height=200,
            placeholder="Paste the target job description or requirements here..."
        )
        
        uploaded_file = st.file_uploader(
            "Upload Resume PDF",
            type=["pdf"],
            help="Please upload a PDF file containing the candidate resume."
        )
        
        st.caption("Don't have a resume PDF on hand?")
        use_sample = st.checkbox("Use auto-generated sample resume (John Doe)", value=False)
        
        analyze_btn = st.button("🚀 Analyze Profile Compatibility", type="primary", use_container_width=True)

    with col_config:
        st.markdown("### **2. Multi-Agent Crew Dashboard**")
        st.write("When execution begins, the collaborative AI agents will work in sequence:")
        
        st.markdown(f"""
        <div class="agent-step">
            <span>🔍 <b>Stage 1: Resume Extractor</b></span>
            <span style="color: #6B7280; font-size: 0.85rem;">Parses RAG chunks for skills/history</span>
        </div>
        <div class="agent-step">
            <span>⚖️ <b>Stage 2: Job Matcher</b></span>
            <span style="color: #6B7280; font-size: 0.85rem;">Compares profiles against requirements</span>
        </div>
        <div class="agent-step">
            <span>💡 <b>Stage 3: Career Coach</b></span>
            <span style="color: #6B7280; font-size: 0.85rem;">Calculates score and lists improvements</span>
        </div>
        <div class="agent-step">
            <span>🎯 <b>Stage 4: Interview Prep Coach</b></span>
            <span style="color: #6B7280; font-size: 0.85rem;">Designs 5 custom skill-probe questions</span>
        </div>
        """, unsafe_allow_html=True)
        
        st.info("🔍 **What is RAG?**\nVector similarity search extracts the 4 most relevant text segments from the resume. This eliminates irrelevant filler text and feeds the agents only high-density credentials.")

    st.divider()

    if analyze_btn:
        pdf_path = None
        
        if use_sample:
            if os.path.exists("my_resume.pdf"):
                pdf_path = "my_resume.pdf"
            else:
                st.error("Mock resume PDF not found. Generating it in the workspace...")
                try:
                    from generate_mock_resume import create_mock_resume
                    create_mock_resume("my_resume.pdf")
                    pdf_path = "my_resume.pdf"
                except Exception as e:
                    st.error(f"Failed to generate mock resume: {e}")
                    st.stop()
        elif uploaded_file is not None:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
                temp_pdf.write(uploaded_file.read())
                pdf_path = temp_pdf.name
        else:
            st.error("Please upload a resume PDF file or toggle the 'Use auto-generated sample resume' checkbox.")
            st.stop()
            
        if not job_desc.strip():
            st.error("Please enter a valid job description.")
            st.stop()

        with st.spinner("🧙‍♂️ **The Crew is collaborating...** Parsing RAG vector store and executing 4 agents in sequence. This takes about 25-45 seconds..."):
            try:
                results = analyze_resume(pdf_path, job_desc, active_api_key, selected_model)
                
                st.balloons()
                st.success("✅ **Analysis Complete!** View the comprehensive evaluation report below.")
                
                c_score, c_report = st.columns([0.8, 1.2])
                
                score = results["match_score"]
                extracted = results["extracted_info"]
                analysis = results["match_analysis"]
                coach = results["improvements"]
                interview = results["interview_questions"]
                
                c_name = "Uploaded Candidate"
                if use_sample:
                    c_name = "John Doe"
                elif uploaded_file:
                    c_name = uploaded_file.name.replace(".pdf", "").replace("_", " ").title()

                with c_score:
                    st.markdown("### **Compatibility Rating**")
                    
                    gauge_color = "#10B981" if score >= 80 else ("#3B82F6" if score >= 60 else "#EF4444")
                    
                    fig = go.Figure(go.Indicator(
                        mode = "gauge+number",
                        value = score,
                        domain = {'x': [0, 1], 'y': [0, 1]},
                        number = {'suffix': "%", 'font': {'size': 60, 'color': '#1E3A8A', 'family': 'Plus Jakarta Sans'}},
                        title = {'text': "Overall ATS Compatibility", 'font': {'size': 18, 'color': '#475569'}},
                        gauge = {
                            'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "#CBD5E1"},
                            'bar': {'color': gauge_color},
                            'bgcolor': "#E2E8F0",
                            'borderwidth': 2,
                            'bordercolor': "#F1F5F9",
                            'steps': [
                                {'range': [0, 50], 'color': '#FEE2E2'},
                                {'range': [50, 75], 'color': '#EFF6FF'},
                                {'range': [75, 100], 'color': '#ECFDF5'}
                            ],
                        }
                    ))
                    
                    fig.update_layout(
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0,0,0,0)',
                        height=280,
                        margin=dict(l=20, r=20, t=40, b=20)
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                    pdf_data = {
                        "candidate_name": c_name,
                        "job_title": selected_template if selected_template != "Custom" else "Target Role",
                        "match_score": score,
                        "extracted_info": extracted,
                        "match_analysis": analysis,
                        "improvements": coach,
                        "interview_questions": interview
                    }
                    
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                        generate_resume_report_pdf(tmp.name, pdf_data)
                        with open(tmp.name, "rb") as f:
                            pdf_bytes = f.read()
                        os.unlink(tmp.name)
                        
                    st.download_button(
                        label="📥 Download Professional PDF Report",
                        data=pdf_bytes,
                        file_name=f"{c_name.replace(' ', '_')}_Resume_Analysis.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )

                with c_report:
                    st.markdown("### **Executive Summary**")
                    summary_box = f"""
                    <div class="custom-card">
                        <div class="card-title">📝 Profile Overview</div>
                        <p style="font-size: 0.95rem; color: #334155; line-height: 1.5;">
                            <b>Candidate Name:</b> {c_name}<br/>
                            <b>Target Position:</b> {selected_template if selected_template != 'Custom' else 'Target Job Requirements'}<br/>
                            <b>AI Assessment Outcome:</b> The candidate shows a match compatibility index of <b>{score}%</b>. 
                            The multi-agent crew completed semantic inspection of the resume text, evaluated qualifications against technical requirements, 
                            and assembled improvement points along with customized recruiter screen questions below.
                        </p>
                    </div>
                    """
                    st.markdown(summary_box, unsafe_allow_html=True)
                
                st.markdown("### **3. Comprehensive Report Sections**")
                
                res_tab1, res_tab2, res_tab3, res_tab4 = st.tabs([
                    "🔍 Extracted Profile Summary", 
                    "⚖️ Requirements Gap Analysis", 
                    "💡 Coach Actionable Improvements", 
                    "🎯 Interview Prep Questions"
                ])
                
                with res_tab1:
                    st.markdown("#### **Extracted Resume Elements**")
                    st.info(extracted)
                    
                with res_tab2:
                    st.markdown("#### **Skill Alignment & Gaps**")
                    st.markdown(analysis)
                    
                with res_tab3:
                    st.markdown("#### **Resume Optimization Suggestions**")
                    st.markdown(coach)
                    
                with res_tab4:
                    st.markdown("#### **Personalized Recruiter Screening Guide**")
                    st.markdown(interview)
                    
            except Exception as e:
                st.error(f"An unexpected error occurred during analysis: {e}")
                st.info("Double check that your OpenAI API Key is valid and active.")
            
            finally:
                if uploaded_file is not None and pdf_path and not use_sample:
                    try:
                        os.unlink(pdf_path)
                    except:
                        pass

# --- TAB 2: MULTI-RESUME RANKER ---
with tab2:
    st.markdown("### **Rank Multiple Candidates**")
    st.write("Upload up to 5 resumes simultaneously to analyze, score, and rank candidates on a comparative leaderboard.")
    
    col_r1, col_r2 = st.columns([1.0, 1.2])
    
    with col_r1:
        st.markdown("##### **1. Core Requirements Setup**")
        st.info(f"Targeting Profile: **{selected_template if selected_template != 'Custom' else 'Custom Job Requirements'}**")
        
        multi_job_desc = st.text_area(
            "Verify Job Description for Ranking",
            value=default_job_desc,
            height=140,
            key="multi_job_desc"
        )
        
        uploaded_files = st.file_uploader(
            "Upload 2 to 5 Candidate Resumes",
            type=["pdf"],
            accept_multiple_files=True,
            help="Upload multiple resume PDF files to rank them against the job description."
        )
        
        rank_btn = st.button("🏆 Execute Agent Matcher & Rank Leaderboard", type="primary", use_container_width=True)

    with col_r2:
        st.markdown("##### **Leaderboard & Competency Dashboard**")
        
        if rank_btn:
            if not uploaded_files or len(uploaded_files) < 2:
                st.warning("⚠️ Please upload at least 2 candidate resume PDFs to compare and rank.")
                st.stop()
                
            if len(uploaded_files) > 5:
                st.error("For performance, please upload a maximum of 5 files at a time.")
                st.stop()
                
            if not multi_job_desc.strip():
                st.error("Please provide job description criteria to match against.")
                st.stop()
                
            leaderboard_data = []
            
            progress_bar = st.progress(0.0)
            status_text = st.empty()
            
            total_files = len(uploaded_files)
            
            for i, up_file in enumerate(uploaded_files):
                c_filename = up_file.name
                c_name = c_filename.replace(".pdf", "").replace("_", " ").title()
                
                status_text.markdown(f"🧙‍♂️ **Analyzing candidate ({i+1}/{total_files}):** `{c_name}`...")
                
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
                    temp_pdf.write(up_file.read())
                    temp_path = temp_pdf.name
                    
                try:
                    res = analyze_resume(temp_path, multi_job_desc, active_api_key, selected_model)
                    
                    score = res["match_score"]
                    leaderboard_data.append({
                        "name": c_name,
                        "score": score,
                        "file_bytes": up_file,
                        "results": res
                    })
                except Exception as e:
                    st.error(f"Error analyzing `{c_name}`: {e}")
                finally:
                    try:
                        os.unlink(temp_path)
                    except:
                        pass
                
                progress_bar.progress(float(i + 1) / total_files)
                
            status_text.markdown("✅ **Leaderboard generation complete!**")
            
            if leaderboard_data:
                leaderboard_data.sort(key=lambda x: x["score"], reverse=True)
                
                names_list = [c["name"] for c in leaderboard_data]
                scores_list = [c["score"] for c in leaderboard_data]
                
                colors_list = ["#10B981" if s >= 80 else ("#3B82F6" if s >= 60 else "#EF4444") for s in scores_list]
                
                fig_bar = go.Figure(go.Bar(
                    x=scores_list,
                    y=names_list,
                    orientation='h',
                    marker_color=colors_list,
                    text=[f"{s}%" for s in scores_list],
                    textposition='auto',
                ))
                
                fig_bar.update_layout(
                    title="Candidate Match Index Comparison",
                    xaxis=dict(title="Score (%)", range=[0, 100]),
                    yaxis=dict(autorange="reversed"),
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    height=260,
                    margin=dict(l=20, r=20, t=40, b=20)
                )
                
                st.plotly_chart(fig_bar, use_container_width=True)
                
                st.session_state["leaderboard"] = leaderboard_data
            else:
                st.error("Could not parse any candidate resumes successfully.")
                
        if "leaderboard" in st.session_state:
            leaderboard = st.session_state["leaderboard"]
            
            st.markdown("### **🏆 Candidate Rankings**")
            
            for ranking_idx, candidate in enumerate(leaderboard):
                rank_emoji = "🥇" if ranking_idx == 0 else ("🥈" if ranking_idx == 1 else ("🥉" if ranking_idx == 2 else "👤"))
                
                card_html = f"""
                <div style="background-color: #F8FAFC; border: 1px solid #E2E8F0; padding: 1rem 1.5rem; border-radius: 12px; margin-bottom: 0.75rem; display: flex; justify-content: space-between; align-items: center;">
                    <div style="display: flex; align-items: center; gap: 1rem;">
                        <span style="font-size: 1.5rem;">{rank_emoji}</span>
                        <div>
                            <h4 style="margin: 0; color: #1E3A8A; font-weight: 700;">{candidate['name']}</h4>
                            <span style="font-size: 0.8rem; color: #64748B;">Rank {ranking_idx + 1} Candidate</span>
                        </div>
                    </div>
                    <div>
                        <span style="font-size: 1.4rem; font-weight: 800; color: #1E3A8A; margin-right: 0.25rem;">{candidate['score']}</span>
                        <span style="color: #64748B; font-weight: 600;">/100</span>
                    </div>
                </div>
                """
                st.markdown(card_html, unsafe_allow_html=True)
                
                with st.expander(f"🔍 Expand Full Assessment for {candidate['name']}"):
                    cand_res = candidate["results"]
                    
                    sub_col1, sub_col2 = st.columns([1, 1])
                    
                    with sub_col1:
                        st.markdown("**Extracted Profile**")
                        st.caption(cand_res["extracted_info"])
                        
                        st.markdown("**Core Skill Match / Gaps**")
                        st.caption(cand_res["match_analysis"])
                        
                    with sub_col2:
                        st.markdown("**Coach Suggestions**")
                        st.caption(cand_res["improvements"])
                        
                        st.markdown("**Interview Preparation Guide**")
                        st.caption(cand_res["interview_questions"])
                        
                        pdf_payload = {
                            "candidate_name": candidate["name"],
                            "job_title": selected_template if selected_template != "Custom" else "Target Role",
                            "match_score": candidate["score"],
                            "extracted_info": cand_res["extracted_info"],
                            "match_analysis": cand_res["match_analysis"],
                            "improvements": cand_res["improvements"],
                            "interview_questions": cand_res["interview_questions"]
                        }
                        
                        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                            generate_resume_report_pdf(tmp.name, pdf_payload)
                            with open(tmp.name, "rb") as f:
                                pdf_bytes = f.read()
                            os.unlink(tmp.name)
                            
                        st.download_button(
                            label=f"📥 Download PDF Report for {candidate['name']}",
                            data=pdf_bytes,
                            file_name=f"{candidate['name'].replace(' ', '_')}_Analysis.pdf",
                            mime="application/pdf",
                            key=f"dl_{candidate['name'].lower().replace(' ', '_')}"
                        )
        else:
            st.info("Upload resumes and click 'Execute Agent Matcher' on the left to see candidate ranks!")

# --- TAB 3: HOW IT WORKS GUIDE ---
with tab3:
    st.markdown("### **Architectural Breakdown**")
    st.write("This application leverages state-of-the-art Generative AI components linked in a semantic feedback loop:")
    
    st.markdown("""
    ```mermaid
    graph TD
        A[Candidate Resume PDF] -->|PyPDFLoader| B[Document Context]
        B -->|RecursiveCharacterSplitter| C[Semantic Text Chunks]
        C -->|OpenAI Embeddings| D[Chroma DB In-Memory]
        E[Job Requirements] -->|Similarity Search| D
        D -->|Context Retrieval| F[RAG Dense Chunks]
        F -->|Task 1: Extraction| G[Resume Extractor Agent]
        G -->|Task 2: Gap Matching| H[Job Matcher Agent]
        H -->|Task 3: Scoring & Tips| I[Career Coach Agent]
        I -->|Task 4: Mock Prompts| J[Interview Prep Coach Agent]
        J -->|Output Report Assembly| K[Interactive UI & ReportLab PDF]
    ```
    """, unsafe_allow_html=True)
    
    st.markdown("""
    #### **1. Document Ingestion & Retrieval-Augmented Generation (RAG)**
    - **Extraction**: When you upload a PDF, we use `PyPDFLoader` to load and serialize the content into standard text.
    - **Chunking**: To maintain absolute structural precision and prevent token overflows, the text is split into small 500-character chunks with a overlap buffer of 50.
    - **Indexing**: These chunks are converted into dense vector vectors using `text-embedding-3-small` and saved in a localized virtual `Chroma DB`.
    - **Retrieval**: When comparing against a job description, similarity queries retrieve the **4 most relevant chunks** of information.
    
    #### **2. CrewAI Multi-Agent Collaboration**
    - **Sequential Chain**: Four highly specialized agent frameworks run in a structured crew chain.
    - **Persona Profiles**:
      - **Resume Extractor**: Removes noise and compiles resume data.
      - **Job Matcher**: Highlights strengths and maps skill gaps.
      - **Career Coach**: Analyzes ATS alignment, assigns an exact score out of 100, and drafts strategic improvement suggestions.
      - **Interview Prep Coach**: Leverages gaps to construct 5 challenging mock screening questions.
    
    #### **3. Publication Quality Layout Rendering**
    - **ReportLab Engine**: Custom layout designs use coordinate grids, margins, custom tables, padding, leading spaces, and dynamic headers to generate beautiful, ready-to-share PDF document assessments.
    """)
st.caption("AI Resume Analyzer Dashboard - Running Antigravity AI Platform")
