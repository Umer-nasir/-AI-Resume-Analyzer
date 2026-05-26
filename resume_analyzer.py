import os
import re
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from crewai import Agent, Task, Crew

try:
    from langchain_community.vectorstores import Chroma
    HAS_CHROMA = True
except ImportError:
    HAS_CHROMA = False

def setup_resume_rag(pdf_path, openai_api_key):
    """
    Loads resume PDF, splits into semantic chunks, and stores in Chroma DB (or falls back to in-memory cosine search).
    """
    loader = PyPDFLoader(pdf_path)
    docs = loader.load()
    
    # Split documents into small readable chunks
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = splitter.split_documents(docs)
    
    # Setup embedding
    embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key)
    
    if HAS_CHROMA:
        try:
            # In-memory Chroma database
            vectorstore = Chroma.from_documents(chunks, embeddings)
            return vectorstore
        except Exception as e:
            print(f"Warning: Chroma initialization failed ({e}). Using pure-Python vector search fallback.")
            
    # Pure-Python Cosine Similarity Vector Search Fallback
    class FallbackVectorStore:
        def __init__(self, documents, embeddings_model):
            self.documents = documents
            self.embeddings_model = embeddings_model
            # Extract texts and precompute embeddings
            self.texts = [doc.page_content for doc in documents]
            self.doc_embeddings = embeddings_model.embed_documents(self.texts)
            
        def similarity_search(self, query, k=4):
            query_emb = self.embeddings_model.embed_query(query)
            
            import math
            def cosine_similarity(v1, v2):
                dot_product = sum(x*y for x, y in zip(v1, v2))
                magnitude1 = math.sqrt(sum(x*x for x in v1))
                magnitude2 = math.sqrt(sum(x*x for x in v2))
                if not magnitude1 or not magnitude2:
                    return 0
                return dot_product / (magnitude1 * magnitude2)
                
            scored_docs = []
            for doc, emb in zip(self.documents, self.doc_embeddings):
                score = cosine_similarity(query_emb, emb)
                scored_docs.append((score, doc))
                
            # Sort descending by similarity score
            scored_docs.sort(key=lambda x: x[0], reverse=True)
            return [doc for score, doc in scored_docs[:k]]

    return FallbackVectorStore(chunks, embeddings)

def get_resume_context(vectorstore, job_description):
    """
    Retrieves the most semantically relevant chunks from the vector DB for the job description.
    """
    results = vectorstore.similarity_search(job_description, k=4)
    return "\n".join([r.page_content for r in results])

def analyze_resume(pdf_path, job_description, openai_api_key, model_name="gpt-4o-mini"):
    """
    Executes RAG and initiates the 4-Agent CrewAI workflow to analyze the resume.
    """
    # 1. Setup RAG and retrieve relevant context
    vectorstore = setup_resume_rag(pdf_path, openai_api_key)
    resume_context = get_resume_context(vectorstore, job_description)
    
    # 2. Define the LLM
    llm = ChatOpenAI(model=model_name, openai_api_key=openai_api_key, temperature=0.2)
    
    # 3. Define the 4 Agents
    extractor = Agent(
        role="Resume Extractor",
        goal="Extract all skills, experience, education, achievements from the resume context",
        backstory="You are a professional HR assistant specializing in parsing resumes and organizing key profiles.",
        llm=llm,
        verbose=True
    )

    matcher = Agent(
        role="Job Matcher",
        goal="Compare extracted resume details with job requirements and identify gaps",
        backstory="You are an expert recruitment manager who knows exactly what credentials and skill levels employers need.",
        llm=llm,
        verbose=True
    )

    coach = Agent(
        role="Career Coach",
        goal="Provide a match score out of 100 and suggest 3-5 high-impact improvement tips",
        backstory="You are an encouraging but realistic career coach who helps candidates optimize their resumes to pass ATS and attract hiring managers.",
        llm=llm,
        verbose=True
    )
    
    interview_coach = Agent(
        role="Interview Prep Coach",
        goal="Generate 5 tailored interview questions with hints based on resume gaps",
        backstory="You are an experienced technical hiring manager who knows how to design interview questions that assess potential skill gaps and verify candidate experience.",
        llm=llm,
        verbose=True
    )

    # 4. Define the 4 Tasks
    task1 = Task(
        description=f"Extract skills, experience, education, and achievements from the provided resume text context:\n\n{resume_context}",
        agent=extractor,
        expected_output="A structured, bulleted summary of the candidate's skills, experience, education, and achievements."
    )
    
    task2 = Task(
        description=f"Compare the extracted profile details with the following job requirements:\n\n{job_description}\n\nList exact matching skills/experience and missing skills/experience or other gaps.",
        agent=matcher,
        expected_output="A detailed comparison report covering: matching qualifications, critical missing skills/experience, and general ATS compatibility gaps."
    )
    
    task3 = Task(
        description="Review the match analysis report. Give a final match/compatibility score out of 100 (e.g. MATCH SCORE: 75 / 100) and list 3 to 5 highly actionable improvement tips for the resume.",
        agent=coach,
        expected_output="A summary featuring: MATCH SCORE: [X] / 100, followed by a bulleted list of 3-5 clear improvement tips."
    )
    
    task4 = Task(
        description=f"Based on the identified gaps and the target job:\n{job_description}\n\nProvide exactly 5 custom interview questions that a recruiter might ask this candidate to probe their skills or experience gaps. Give a brief hint/focus area for each question.",
        agent=interview_coach,
        expected_output="Exactly 5 numbered interview questions with a corresponding 'Recruiter Focus Hint' for each."
    )

    # 5. Define and kickoff the Crew
    crew = Crew(
        agents=[extractor, matcher, coach, interview_coach],
        tasks=[task1, task2, task3, task4],
        verbose=True
    )
    
    crew_output = crew.kickoff()
    
    # 6. Parse out separate outputs from tasks_output
    extracted_info = crew_output.tasks_output[0].raw
    match_analysis = crew_output.tasks_output[1].raw
    coach_report = crew_output.tasks_output[2].raw
    interview_questions = crew_output.tasks_output[3].raw
    
    # Extract the numerical match score from the coach_report using regex
    match_score = 50 
    score_match = re.search(r"MATCH SCORE:\s*(\d+)", coach_report, re.IGNORECASE)
    if not score_match:
        score_match = re.search(r"(\d+)\s*/\s*100", coach_report)
    if not score_match:
        score_match = re.search(r"Score:\s*(\d+)", coach_report, re.IGNORECASE)
    
    if score_match:
        try:
            match_score = int(score_match.group(1))
        except ValueError:
            pass
            
    return {
        "extracted_info": extracted_info,
        "match_analysis": match_analysis,
        "improvements": coach_report,
        "match_score": match_score,
        "interview_questions": interview_questions
    }

if __name__ == "__main__":
    import sys
    
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY environment variable not set. Please set it to run the script.")
        sys.exit(1)
        
    job_desc = """
    We are hiring a Python Developer with:
    - 2+ years Python experience
    - Knowledge of Django or Flask
    - Experience with REST APIs
    - Familiarity with SQL databases
    """
    
    resume_path = "my_resume.pdf"
    if not os.path.exists(resume_path):
        print(f"Error: {resume_path} not found. Please place a resume PDF in this folder.")
        sys.exit(1)
        
    print("Starting Resume Analysis Crew...")
    results = analyze_resume(resume_path, job_desc, api_key)
    
    print("\n===== EXTRACTED PROFILE =====")
    print(results["extracted_info"])
    print("\n===== MATCH ANALYSIS =====")
    print(results["match_analysis"])
    print("\n===== SCORE & IMPROVEMENTS =====")
    print(results["improvements"])
    print(f"\nFinal Parsed Score: {results['match_score']}/100")
    print("\n===== INTERVIEW PREP QUESTIONS =====")
    print(results["interview_questions"])
