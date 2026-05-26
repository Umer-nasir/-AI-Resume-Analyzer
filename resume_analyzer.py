import os
import re
import math
from dotenv import load_dotenv
load_dotenv(override=True)
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

try:
    from langchain_community.vectorstores import Chroma
    HAS_CHROMA = True
except ImportError:
    HAS_CHROMA = False


def setup_resume_rag(pdf_path, openai_api_key):
    loader = PyPDFLoader(pdf_path)
    docs = loader.load()

    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = splitter.split_documents(docs)

    embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key)

    if HAS_CHROMA and not openai_api_key.startswith("gsk_"):
        try:
            vectorstore = Chroma.from_documents(chunks, embeddings)
            return vectorstore
        except Exception as e:
            print(f"Warning: Chroma failed ({e}). Using fallback.")

    class FallbackVectorStore:
        def __init__(self, documents, embeddings_model):
            self.documents = documents
            self.embeddings_model = embeddings_model
            self.texts = [doc.page_content for doc in documents]
            try:
                self.doc_embeddings = embeddings_model.embed_documents(self.texts)
                self.has_embeddings = True
            except Exception as e:
                print(f"Warning: Embedding generation failed ({e}). Using keyword match fallback.")
                self.has_embeddings = False

        def similarity_search(self, query, k=4):
            if self.has_embeddings:
                try:
                    query_emb = self.embeddings_model.embed_query(query)
                    def cosine_similarity(v1, v2):
                        dot = sum(x * y for x, y in zip(v1, v2))
                        m1 = math.sqrt(sum(x * x for x in v1))
                        m2 = math.sqrt(sum(x * x for x in v2))
                        return dot / (m1 * m2) if m1 and m2 else 0
                    scored = [(cosine_similarity(query_emb, emb), doc)
                              for doc, emb in zip(self.documents, self.doc_embeddings)]
                    scored.sort(key=lambda x: x[0], reverse=True)
                    return [doc for _, doc in scored[:k]]
                except Exception as e:
                    print(f"Warning: Query embedding failed ({e}). Falling back to keyword search.")

            # Pure keyword-matching TF-IDF style similarity search
            query_words = set(re.findall(r'\w+', query.lower()))
            if not query_words:
                return self.documents[:k]
            scored = []
            for doc in self.documents:
                doc_words = re.findall(r'\w+', doc.page_content.lower())
                if not doc_words:
                    score = 0
                else:
                    matches = sum(1 for w in doc_words if w in query_words)
                    score = matches / len(doc_words)
                scored.append((score, doc))
            scored.sort(key=lambda x: x[0], reverse=True)
            return [doc for _, doc in scored[:k]]

    return FallbackVectorStore(chunks, embeddings)

    return FallbackVectorStore(chunks, embeddings)


def get_resume_context(vectorstore, job_description):
    results = vectorstore.similarity_search(job_description, k=4)
    return "\n".join([r.page_content for r in results])


def run_agent(llm, system_prompt, user_prompt):
    """Run a single LLM agent with a system and user prompt."""
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", user_prompt)
    ])
    chain = prompt | llm
    response = chain.invoke({})
    return response.content


def analyze_resume(pdf_path, job_description, openai_api_key, model_name="gpt-4o-mini"):
    # 1. RAG setup
    vectorstore = setup_resume_rag(pdf_path, openai_api_key)
    resume_context = get_resume_context(vectorstore, job_description)

    # 2. LLM
    if openai_api_key.startswith("gsk_"):
        groq_model = "llama-3.3-70b-versatile" if model_name == "gpt-4o" else "llama-3.1-8b-instant"
        llm = ChatOpenAI(
            model=groq_model,
            openai_api_key=openai_api_key,
            base_url="https://api.groq.com/openai/v1",
            temperature=0.2
        )
    else:
        llm = ChatOpenAI(model=model_name, openai_api_key=openai_api_key, temperature=0.2)

    # 3. Agent 1 — Resume Extractor
    extracted_info = run_agent(
        llm,
        system_prompt="You are a professional HR assistant specializing in parsing resumes and organizing key profiles.",
        user_prompt=f"Extract skills, experience, education, and achievements from the resume below into a structured bulleted summary:\n\n{resume_context}"
    )

    # 4. Agent 2 — Job Matcher
    match_analysis = run_agent(
        llm,
        system_prompt="You are an expert recruitment manager who knows exactly what credentials and skill levels employers need.",
        user_prompt=f"Compare the following candidate profile with the job requirements.\n\nCandidate Profile:\n{extracted_info}\n\nJob Requirements:\n{job_description}\n\nList matching qualifications, missing skills, and ATS compatibility gaps."
    )

    # 5. Agent 3 — Career Coach
    coach_report = run_agent(
        llm,
        system_prompt="You are an encouraging but realistic career coach who helps candidates optimize their resumes.",
        user_prompt=f"Based on this match analysis, give a MATCH SCORE: [X] / 100 and 3-5 actionable improvement tips.\n\nMatch Analysis:\n{match_analysis}"
    )

    # 6. Agent 4 — Interview Coach
    interview_questions = run_agent(
        llm,
        system_prompt="You are an experienced technical hiring manager who designs interview questions to assess skill gaps.",
        user_prompt=f"Based on the gaps identified and this job:\n{job_description}\n\nGenerate exactly 5 numbered interview questions with a 'Recruiter Focus Hint' for each."
    )

    # 7. Extract match score
    match_score = 50
    for pattern in [r"MATCH SCORE:\s*(\d+)", r"(\d+)\s*/\s*100", r"Score:\s*(\d+)"]:
        m = re.search(pattern, coach_report, re.IGNORECASE)
        if m:
            try:
                match_score = int(m.group(1))
                break
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

    api_key = os.environ.get("GROQ_API_KEY") or os.environ.get("GROK_API_KEY") or os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("Error: API Key (OPENAI_API_KEY, GROQ_API_KEY, or GROK_API_KEY) not set.")
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
        print(f"Error: {resume_path} not found.")
        sys.exit(1)

    results = analyze_resume(resume_path, job_desc, api_key)
    print("\n===== EXTRACTED PROFILE =====")
    print(results["extracted_info"])
    print("\n===== MATCH ANALYSIS =====")
    print(results["match_analysis"])
    print("\n===== SCORE & IMPROVEMENTS =====")
    print(results["improvements"])
    print(f"\nFinal Score: {results['match_score']}/100")
    print("\n===== INTERVIEW QUESTIONS =====")
    print(results["interview_questions"])
