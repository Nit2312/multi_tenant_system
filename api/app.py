import os
import json
import re
import sys
import time
import uuid
from datetime import datetime
from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS
from dotenv import load_dotenv
import traceback
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_astradb import AstraDBVectorStore

# LangGraph imports for agent creation
from langgraph.prebuilt import create_react_agent
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

# Query logging system
QUERY_LOG_FILE = "query_logs.json"

# Financial Expert Agent Tools
@tool
def search_investment_documents(query: str) -> str:
    """Search for relevant investment information from PDF documents"""
    global vectorstores, query_classifier
    
    if not vectorstores or not query_classifier:
        return "Document search system not available. Please initialize the system first."
    
    try:
        # Classify query to determine appropriate collection
        category, confidence = query_classifier.classify_query(query)
        collection_name = query_classifier.get_collection_name(category)
        
        # Get sources from the appropriate collection
        sources = get_retrieved_sources(query, collection_name)
        
        if not sources:
            return f"No relevant documents found for: {query}"
        
        # Format the retrieved documents
        context = _format_docs(sources)
        return f"Found relevant information from {len(sources)} documents:\n\n{context}"
        
    except Exception as e:
        return f"Error searching documents: {str(e)}"

@tool
def get_financial_advice(topic: str) -> str:
    """Get financial advice based on Warren Buffett's investment principles"""
    advice_templates = {
        'investing': "Focus on buying wonderful businesses at fair prices, holding for the long term, and staying within your circle of competence.",
        'risk': "The biggest risk is not knowing what you're doing. Invest in what you understand and avoid speculation.",
        'patience': "The stock market is a device for transferring money from the impatient to the patient. Time is your friend.",
        'diversification': "Diversification is protection against ignorance. It makes little sense for those who know what they're doing.",
        'market': "Be fearful when others are greedy and greedy when others are fearful. Mr. Market is there to serve you, not guide you."
    }
    
    topic_lower = topic.lower()
    for key, advice in advice_templates.items():
        if key in topic_lower:
            return f"Regarding {topic}: {advice}"
    
    return "Focus on long-term value investing, continuous learning, and staying within your circle of competence."

@tool
def analyze_investment_concept(concept: str) -> str:
    """Analyze investment concepts and provide explanations"""
    concept_explanations = {
        'intrinsic value': "The true underlying value of a business, regardless of market price. Calculate based on future cash flows and assets.",
        'margin of safety': "Buy at a price significantly below intrinsic value to protect against errors in judgment or market volatility.",
        'circle of competence': "Invest only in businesses and industries you thoroughly understand. Stay within your knowledge boundaries.",
        'compound interest': "The eighth wonder of the world. Reinvesting earnings generates earnings on earnings, creating exponential growth.",
        'moat': "A sustainable competitive advantage that protects a business from competitors, like a castle's moat protects it."
    }
    
    concept_lower = concept.lower()
    for key, explanation in concept_explanations.items():
        if key in concept_lower:
            return f"{concept.title()}: {explanation}"
    
    return f"Analysis of {concept}: This requires understanding the business fundamentals, competitive position, and long-term prospects."

@tool
def get_book_recommendation(topic: str) -> str:
    """Get investment book recommendations based on topic"""
    book_recommendations = {
        'value investing': "The Intelligent Investor by Benjamin Graham - The bible of value investing",
        'financial wisdom': "The Essays of Warren Buffett - Timeless wisdom from the Oracle of Omaha",
        'market psychology': "Extraordinary Popular Delusions by Charles Mackay - Understanding market madness",
        'business analysis': "Common Stocks and Uncommon Profits by Philip Fisher - Qualitative business analysis",
        'index investing': "The Little Book of Common Sense Investing by John Bogle - Low-cost index fund strategy"
    }
    
    topic_lower = topic.lower()
    for key, recommendation in book_recommendations.items():
        if key in topic_lower:
            return recommendation
    
    return f"For {topic}, I recommend starting with 'The Intelligent Investor' by Benjamin Graham as it covers fundamental investment principles."

def create_financial_expert_agent():
    """Create a financial expert AI agent using LangGraph"""
    global llm
    
    if not llm:
        raise ValueError("LLM not initialized. Please initialize the system first.")
    
    # Define the tools available to the agent
    tools = [
        search_investment_documents,
        get_financial_advice,
        analyze_investment_concept,
        get_book_recommendation
    ]
    
    # System prompt for the financial expert agent
    system_prompt = """
You are a senior financial mentor speaking to your disciple.

Your tone is calm, direct, and respectful. You answer like someone with decades of experience talking to a serious student sitting in front of you.

Always:
- Start by giving a clear, direct answer to the question in the first few sentences.
- Speak in simple, everyday language.
- Keep the answer focused and practical, as if you want the disciple to go and act on it.
- Sound like a human mentor, not like a book or a blog.

Avoid:
- Numbered lists and bullet points.
- Textbook-style explanations.
- Long metaphors, stories, or jokes unless a very short example is truly needed.
- Explaining your thinking process or what you are about to do.

You can give one short, concrete example if it helps, but do not wander. Stay on the main point and talk as a senior person guiding a disciple who genuinely wants to learn from you.
"""
    
    # Create the agent using LangGraph
    agent = create_react_agent(
        model=llm,
        tools=tools,
        state_modifier=system_prompt
    )
    
    return agent

# Initialize the financial expert agent
financial_expert_agent = None

def get_financial_expert_agent():
    """Get or create the financial expert agent"""
    global financial_expert_agent, llm
    
    # Check if system is initialized first
    if not system_initialized:
        success, message = initialize_rag_system()
        if not success:
            print(f"System initialization failed: {message}")
            return None
    
    if not llm:
        print("LLM not available for agent creation")
        print(f"Available globals: {[name for name in globals() if not name.startswith('_')]}")
        return None
    
    if not financial_expert_agent and llm:
        try:
            financial_expert_agent = create_financial_expert_agent()
            print("Financial expert agent created successfully")
        except Exception as e:
            print(f"Error creating financial expert agent: {e}")
            return None
    
    return financial_expert_agent

def log_query_to_file(query_data):
    """Save query data to JSON file with comprehensive metrics"""
    try:
        # Load existing logs
        if os.path.exists(QUERY_LOG_FILE):
            with open(QUERY_LOG_FILE, 'r', encoding='utf-8') as f:
                logs = json.load(f)
        else:
            logs = []
        
        # Add new query with comprehensive metrics
        query_entry = {
            "timestamp": query_data.get('timestamp', datetime.now().isoformat()),
            "query": query_data.get('query', ''),
            "category": query_data.get('category', ''),
            "collection": query_data.get('collection', ''),
            "response": query_data.get('response', ''),
            "response_length": len(query_data.get('response', '')),
            "sources_retrieved": query_data.get('sources_retrieved', 0),
            "sources_cited": query_data.get('sources_cited', 0),
            "precision_at_k": query_data.get('precision_at_k', 0),
            "recall_at_k": query_data.get('recall_at_k', 0),
            "has_sources": query_data.get('has_sources', False),
            "confidence_score": query_data.get('confidence_score', 0),
            "processing_time": query_data.get('processing_time', 0),
            "ip_address": query_data.get('ip_address', ''),
            "user_agent": query_data.get('user_agent', ''),
            "session_id": query_data.get('session_id', ''),
            "query_type": query_data.get('query_type', ''),  # factual, analytical, opinion
            "complexity_score": query_data.get('complexity_score', 0),  # 1-10 scale
            "sentiment": query_data.get('sentiment', ''),  # positive, negative, neutral
            "language": query_data.get('language', 'en'),
            "response_quality": query_data.get('response_quality', 0),  # 1-10 scale
            "user_satisfaction": query_data.get('user_satisfaction', 0),  # 1-5 scale
            "follow_up_questions": query_data.get('follow_up_questions', []),
            "related_topics": query_data.get('related_topics', []),
            "actionable_insights": query_data.get('actionable_insights', []),
            "risk_assessment": query_data.get('risk_assessment', ''),  # low, medium, high
            "investment_category": query_data.get('investment_category', ''),  # stocks, bonds, real estate
            "time_horizon": query_data.get('time_horizon', ''),  # short, medium, long
            "risk_tolerance": query_data.get('risk_tolerance', '')  # conservative, moderate, aggressive
        }
        
        logs.append(query_entry)
        
        # Keep only last 10000 queries to prevent file from getting too large
        if len(logs) > 10000:
            logs = logs[-10000:]
        
        # Save to file
        with open(QUERY_LOG_FILE, 'w', encoding='utf-8') as f:
            json.dump(logs, f, indent=2, ensure_ascii=False)
            
    except Exception as e:
        print(f"Error logging query to file: {e}")

def calculate_comprehensive_metrics(query, response, sources, category, confidence):
    """Calculate comprehensive metrics for each query"""
    import math
    
    # Basic metrics
    query_length = len(query)
    response_length = len(response) if response else 0
    sources_count = len(sources) if sources else 0
    
    # Complexity score (1-10 scale)
    complexity_indicators = [
        'how', 'what', 'why', 'explain', 'analyze', 'compare', 'difference',
        'relationship', 'impact', 'effect', 'cause', 'reason'
    ]
    complexity_score = min(10, sum(1 for indicator in complexity_indicators if indicator in query.lower()))
    
    # Sentiment analysis (simple keyword-based)
    positive_words = ['good', 'great', 'excellent', 'best', 'opportunity', 'profit', 'growth', 'success']
    negative_words = ['bad', 'worst', 'terrible', 'loss', 'risk', 'danger', 'problem', 'fail']
    
    query_lower = query.lower()
    positive_count = sum(1 for word in positive_words if word in query_lower)
    negative_count = sum(1 for word in negative_words if word in query_lower)
    
    if positive_count > negative_count:
        sentiment = 'positive'
    elif negative_count > positive_count:
        sentiment = 'negative'
    else:
        sentiment = 'neutral'
    
    # Query type classification
    if any(word in query_lower for word in ['what is', 'define', 'explain', 'tell me']):
        query_type = 'factual'
    elif any(word in query_lower for word in ['how to', 'best way', 'should i', 'recommend']):
        query_type = 'advisory'
    elif any(word in query_lower for word in ['compare', 'difference', 'better', 'versus']):
        query_type = 'comparative'
    else:
        query_type = 'general'
    
    # Response quality (1-10 scale based on length and structure)
    if response_length < 100:
        response_quality = 3
    elif response_length < 300:
        response_quality = 6
    elif response_length < 600:
        response_quality = 8
    else:
        response_quality = 10
    
    # Investment category detection
    investment_categories = {
        'stocks': ['stock', 'equity', 'share', 'market', 'trading'],
        'bonds': ['bond', 'fixed income', 'treasury', 'municipal'],
        'real_estate': ['property', 'real estate', 'rental', 'housing'],
        'commodities': ['gold', 'oil', 'commodity', 'futures'],
        'crypto': ['bitcoin', 'cryptocurrency', 'blockchain', 'crypto']
    }
    
    investment_category = ''
    for cat, keywords in investment_categories.items():
        if any(keyword in query_lower for keyword in keywords):
            investment_category = cat
            break
    
    # Time horizon detection
    if any(word in query_lower for word in ['day', 'week', 'short term', 'quick']):
        time_horizon = 'short'
    elif any(word in query_lower for word in ['year', 'long term', 'retirement']):
        time_horizon = 'long'
    else:
        time_horizon = 'medium'
    
    # Risk tolerance detection
    if any(word in query_lower for word in ['safe', 'conservative', 'low risk', 'guarantee']):
        risk_tolerance = 'conservative'
    elif any(word in query_lower for word in ['aggressive', 'high risk', 'speculative']):
        risk_tolerance = 'aggressive'
    else:
        risk_tolerance = 'moderate'
    
    return {
        'complexity_score': complexity_score,
        'sentiment': sentiment,
        'query_type': query_type,
        'response_quality': response_quality,
        'investment_category': investment_category,
        'time_horizon': time_horizon,
        'risk_tolerance': risk_tolerance,
        'query_length': query_length,
        'response_length': response_length,
        'sources_count': sources_count
    }

from langchain_groq import ChatGroq
from langchain_core.embeddings import Embeddings
from huggingface_hub import InferenceClient
from pydantic import SecretStr

try:
    from api.answer_evaluator import evaluate_answer
    from api.query_classifier import QueryClassifier
except ImportError:
    from answer_evaluator import evaluate_answer
    from query_classifier import QueryClassifier

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__, template_folder="../templates", static_folder="../static")
CORS(app)

# Global variables for RAG system
rag_chain = None
retriever = None
vectorstores = {}  # Multiple vectorstores for different collections
embeddings = None
query_classifier = None
llm = None  # Global LLM instance
finance_docs = 0
marketing_docs = 0
sales_docs = 0
system_initialized = False

# Dashboard password and query tracking
DASHBOARD_PASSWORD = os.getenv("DASHBOARD_PASSWORD", "nitisrich")  # Change in production
dashboard_sessions = {}
query_metrics = []  # Store query-by-query metrics

# Eval set for Recall@k: list of {"question_norm": str, "relevant_keys": set of str}
_eval_relevance = []

# Precision: only top-k retrieved docs are passed to the model (over-fetch then slice)
RAG_FETCH_K = int(os.getenv("RAG_FETCH_K", "15"))
RAG_USE_TOP_K = int(os.getenv("RAG_USE_TOP_K", "8"))
RAG_RERANK_MAX = int(os.getenv("RAG_RERANK_MAX", "15"))  # max docs to rerank (fewer = faster)
RAG_SKIP_RERANK = os.getenv("RAG_SKIP_RERANK", "").lower() in ("1", "true", "yes")
RETRIEVAL_K = RAG_USE_TOP_K

# Pattern: line that starts the actual answer (numbered list or "No procedure/documentation")
# Removed to allow natural conversational responses


def _strip_thinking(text: str) -> str:
    """Remove <think>...</think> blocks that reasoning models sometimes leak into output."""
    import re
    if not text:
        return text
    # Remove <think> blocks (greedy=False so nested tags don't eat real content)
    cleaned = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
    # Also strip any leftover "Okay, the user is asking..." preamble that can appear
    # when the model narrates its reasoning without XML tags.
    lines = cleaned.split("\n")
    skip_prefixes = (
        "okay, the user",
        "okay, let me",
        "let me think",
        "let me recall",
        "let me start",
        "i need to",
        "the user is asking",
        "i should",
        "alright,",
        "so, the user",
    )
    # Drop leading lines that are clearly internal narration
    while lines and lines[0].strip().lower().startswith(skip_prefixes):
        lines.pop(0)
    return "\n".join(lines).strip()


def _safe_get(doc, key, default=None):
    """
    Safely get attribute from LangChain Document or dict.
    """
    # LangChain Document
    if hasattr(doc, "metadata") or hasattr(doc, "page_content"):
        if key == "metadata":
            return getattr(doc, "metadata", default)
        if key == "page_content":
            return getattr(doc, "page_content", default)
        return getattr(doc, key, default)

    # Dict
    if isinstance(doc, dict):
        return doc.get(key, default)

    return default

def _format_docs(docs):
    """Format Document-like objects with collection information."""
    formatted = []
    print(f"DEBUG: _format_docs called with {len(docs)} documents")
    for i, doc in enumerate(docs):
        try:
            print(f"DEBUG: Processing document {i}, type: {type(doc)}")
            # Use _safe_get for consistent document handling
            metadata = _safe_get(doc, "metadata", {}) or {}
            content = _safe_get(doc, "page_content", "")
            doc_type = metadata.get("type", "unknown")
            collection = metadata.get("collection", "finance")
            
            if doc_type == "case_record":
                case_id = metadata.get("CaseID") or metadata.get("case_id") or ""
                job_name = metadata.get("Job_Name") or metadata.get("job_name") or ""
                formatted.append(f"{collection.title()}: CaseID: {case_id}, Job_Name: {job_name}\n{content}")
            elif doc_type == "pdf_document":
                filename = metadata.get("filename") or ""
                formatted.append(f"{collection.title()}: PDF: {filename}\n{content}")
            else:
                formatted.append(f"{collection.title()}: Document\n{content}")
        except Exception as e:
            print(f"Error formatting document: {e}")
            formatted.append(f"Error: Document formatting failed - {str(e)}")
    return "\n\n".join(formatted)


def _strip_leading_reasoning(text: str) -> str:
    """Keep only the answer: drop any reasoning/preamble."""
    if not text or not text.strip():
        return text
    # Just return the text as-is since we removed the pattern
    return text.strip()

def _verify_response_grounded_in_sources(response: str, sources: list) -> bool:
    """Verify that response is grounded in provided sources"""
    if not sources or not response:
        return False
    
    response_lower = response.lower()
    
    # Check if response contains specific information from sources
    if not sources:
        return False
    
    # Simple keyword-based verification for grounding
    source_content_indicators = [
        "according to the document", "based on the document", "the document states",
        "as mentioned in", "the document mentions", "the book explains", "the author writes",
        "as shown in", "the document shows", "the text indicates", "the pdf contains",
        "according to", "based on", "the book", "the author", "writes", "explains", "mentions"
    ]
    
    grounding_score = 0
    for indicator in source_content_indicators:
        if indicator in response_lower:
            grounding_score += 1
    
    # Additional check for book names and authors in response
    book_names = [source.metadata.get('book_name', 'Unknown Book') for source in sources]
    authors = [source.metadata.get('author', 'Unknown Author') for source in sources]
    
    for book_name in book_names:
        if book_name and book_name.lower() in response_lower:
            grounding_score += 2
            break
    
    for author in authors:
        if author and author.lower() in response_lower:
            grounding_score += 2
            break
    
    # Consider response grounded if it has source indicators or references
    is_grounded = grounding_score > 0
    
    print(f"Grounding check: {grounding_score}/5 indicators found, grounded: {is_grounded}")
    return is_grounded

def get_astra_config():
    """Get Astra DB configuration from environment variables."""
    api_endpoint = os.getenv("ASTRA_DB_API_ENDPOINT")
    token = os.getenv("ASTRA_DB_APPLICATION_TOKEN")
    namespace = os.getenv("ASTRA_DB_NAMESPACE")
    collection_name = os.getenv("ASTRA_DB_COLLECTION", "elevator_cases")

    if not api_endpoint or not token or not namespace:
        raise ValueError(
            "Missing Astra DB configuration. Set ASTRA_DB_API_ENDPOINT, "
            "ASTRA_DB_APPLICATION_TOKEN, and ASTRA_DB_NAMESPACE."
        )

    return {
        "api_endpoint": api_endpoint,
        "token": token,
        "namespace": namespace,
        "collection_name": collection_name,
    }

class RouterHuggingFaceEmbeddings(Embeddings):
    def __init__(self, api_key: str, model_name: str) -> None:
        if not api_key:
            raise ValueError("HF_TOKEN is required for endpoint embeddings.")
        self._client = InferenceClient(model=model_name, token=api_key)

    def embed_documents(self, texts):
        # Handle both single text and list of texts
        if isinstance(texts, str):
            texts = [texts]
        
        # Process each text individually for the API
        embeddings_list = []
        for text in texts:
            result = self._client.feature_extraction(text)
            if isinstance(result, list) and result and isinstance(result[0], float):
                embeddings_list.append(result)
            else:
                embeddings_list.append(result)
        return embeddings_list

    def embed_query(self, text):
        return self.embed_documents([text])[0]


def load_and_process_data():
    """Load and process data from AstraDB"""
    global rag_chain, retriever, vectorstores, embeddings, query_classifier, llm
    global finance_docs, marketing_docs, sales_docs
    
    try:
        # Initialize query classifier
        query_classifier = QueryClassifier()
        
        model_name = "sentence-transformers/all-mpnet-base-v2"
        hf_token = os.getenv("HF_TOKEN")
        if not hf_token:
            raise ValueError("HF_TOKEN environment variable is required")
        
        embeddings = RouterHuggingFaceEmbeddings(
            api_key=hf_token,
            model_name=model_name,
        )

        astra_config = get_astra_config()
        
        # Initialize multiple vectorstores for different collections
        collections = ['finance', 'marketing']
        vectorstores = {}
        
        for collection in collections:
            try:
                vectorstores[collection] = AstraDBVectorStore(
                    embedding=embeddings,
                    api_endpoint=astra_config["api_endpoint"],
                    token=astra_config["token"],
                    namespace=astra_config["namespace"],
                    collection_name=collection,
                )
                print(f"Initialized collection: {collection}")
            except Exception as e:
                print(f"Warning: Could not initialize collection {collection}: {e}")
                # Create a dummy vectorstore to prevent crashes
                vectorstores[collection] = None

        # Set default retriever to finance collection
        default_collection = 'finance'
        if vectorstores.get(default_collection):
            retriever = vectorstores[default_collection].as_retriever(
                search_type="similarity",
                search_kwargs={"k": RAG_FETCH_K}
            )
        else:
            retriever = None

        groq_api_key = os.getenv("GROQ_API_KEY")
        if not groq_api_key:
            raise ValueError("GROQ_API_KEY environment variable is required")
        
        llm = ChatGroq(
            api_key=SecretStr(groq_api_key),
            model="llama-3.3-70b-versatile",
            temperature=0.3,
            max_tokens=1536
        )
        
        template = """
You are a senior financial mentor speaking to your disciple.

Your job is not to summarize books. Your job is to give a clear, direct answer drawn from experience, in simple language, as if you are guiding a serious student sitting with you.

CRITICAL:
- Do NOT reveal or describe your internal thinking process.
- Do NOT structure answers as "First, second, third" or as formal lists.
- Do NOT write like a textbook, blog post, or essay.
- Do NOT use long metaphors or stories; only add a short, concrete example if it truly helps understanding.

Instead:
- Answer the question directly in the first few sentences.
- Keep the tone like a senior mentor advising a disciple: firm, kind, and practical.
- Blend ideas naturally into a flowing conversation.
- Use everyday language and avoid academic or technical jargon when simpler words will do.

Use retrieved context only as background knowledge. Do not mention books, PDFs, or "context" unless the user explicitly asks about sources.

Context:
{context}

User:
{question}

Respond with only your final conversational answer, in the voice of a senior mentor speaking to a disciple.
"""

        prompt = PromptTemplate(
            template=template,
            input_variables=["context", "question"]
        )

        rag_chain = prompt | llm | StrOutputParser()
        
        return True, f"Investment Advisor AI initialized successfully! Ready to provide guidance on finance, marketing, and sales."
        
    except Exception as e:
        # Log full traceback for server logs without leaking secrets to clients.
        print("RAG initialization failed:\n" + traceback.format_exc())
        return False, f"Error loading data: {type(e).__name__}: {e}"

def initialize_rag_system():
    """Initialize the RAG system if not already done"""
    global system_initialized
    
    if not system_initialized:
        success, message = load_and_process_data()
        system_initialized = success
        return success, message
    
    return True, "System already initialized"

def get_retrieved_sources(query, collection_name=None, book_filter=None):
    """Return top-k sources from appropriate collection based on query classification"""
    global vectorstores, query_classifier
    
    print(f"=== DEBUG: Retrieval Request ===")
    print(f"Query: {query}")
    print(f"Collection: {collection_name}")
    print(f"Book Filter: {book_filter}")
    print(f"Vectorstores available: {list(vectorstores.keys())}")
    
    if not vectorstores:
        print("DEBUG: No vectorstores available")
        return []
    
    # Classify query to determine appropriate collection
    if collection_name is None and query_classifier:
        category, confidence = query_classifier.classify_query(query)
        collection_name = query_classifier.get_collection_name(category)
        print(f"Query classified as: {category} (confidence: {confidence:.2f}), using collection: {collection_name}")
    
    # Get the appropriate vectorstore
    vectorstore = vectorstores.get(collection_name)
    if not vectorstore:
        # Fallback to finance collection if specified collection doesn't exist
        vectorstore = vectorstores.get('finance')
        collection_name = 'finance'
        print(f"Using fallback collection: {collection_name}")
    
    if not vectorstore:
        print("DEBUG: No vectorstore available")
        return []
    
    print(f"Vectorstore found: {type(vectorstore)}")
    
    # Create retriever for this collection with optional metadata filter
    if book_filter:
        # Apply metadata filter for specific book
        retriever = vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={
                "k": RAG_FETCH_K,
                "filter": {"book_name": book_filter}
            }
        )
        print(f"Applied metadata filter for book: {book_filter}")
    else:
        retriever = vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={"k": RAG_FETCH_K}
        )
    
    print(f"Retriever created: {type(retriever)}")
    
    try:
        docs_sem = retriever.invoke(query)
        print(f"Retrieved {len(docs_sem)} documents from semantic search")
        docs_to_rerank = docs_sem[:RAG_RERANK_MAX]
        
        if RAG_SKIP_RERANK or not docs_to_rerank:
            result = docs_to_rerank[:RAG_USE_TOP_K]
            print(f"Returning {len(result)} documents (no reranking)")
            return result
        
        try:
            from api.cross_encoder import CrossEncoderReranker
            reranker = CrossEncoderReranker()
            result = reranker.rerank(query, docs_to_rerank, top_k=RAG_USE_TOP_K)
            print(f"Reranked to {len(result)} documents")
            return result
        except Exception as e:
            print(f"Cross-encoder reranking failed: {e}")
            return docs_to_rerank[:RAG_USE_TOP_K]
    except Exception as e:
        print(f"Error retrieving documents: {e}")
        import traceback
        traceback.print_exc()
        return []


def get_daily_dose_sources(query: str, k_per_collection: int = 6):
    """Retrieve from both finance and marketing collections for Daily Dose generation."""
    global vectorstores
    if not vectorstores:
        return []
    docs = []
    for coll in ("finance", "marketing"):
        store = vectorstores.get(coll)
        if not store:
            continue
        try:
            retriever = store.as_retriever(
                search_type="similarity",
                search_kwargs={"k": k_per_collection},
            )
            docs.extend(retriever.invoke(query))
        except Exception as e:
            print(f"Daily dose retrieval from {coll} failed: {e}")
    return docs[: RAG_USE_TOP_K * 2]


def generate_daily_dose_message(topic: dict) -> str:
    """Generate a ~500-word daily teaching from finance & marketing books using RAG."""
    global llm, rag_chain
    if not llm:
        return "Daily Dose is not configured (RAG system not initialized)."
    title = topic.get("title", "")
    question = topic.get("question", "")
    theme = topic.get("theme", "")
    query = f"{title}. {question}. {theme}".strip() or "practical wisdom for daily life"
    sources = get_daily_dose_sources(query)
    context = _format_docs(sources) if sources else ""
    if not context.strip():
        return "No relevant passages found in the books for this topic. Try again later or pick another day."
    daily_dose_prompt = """You are writing a short daily teaching drawn only from the given book excerpts. The goal is one practical lesson readers can apply in day-to-day life (work, decisions, habits, mindset). Use a warm, clear, mentor-like tone.

Topic: {title}
Theme: {theme}
Reflection question for the reader: {question}

Use ONLY the following excerpts from finance and marketing books. Do not invent facts or quotes.

Excerpts:
{context}

Write a single teaching of about 400–500 words. Structure it as:
1. A brief opening that connects the theme to daily life.
2. The core idea from the excerpts in simple language.
3. One clear principle the reader can remember.
4. Two or three practical actions they can take today.
5. A short closing reflection or one-sentence takeaway.

Write in flowing paragraphs. Do not use bullet points or numbered lists in the body. Do not mention "the book" or "the excerpt" explicitly. Output only the teaching text."""

    try:
        from langchain_core.prompts import PromptTemplate
        from langchain_core.output_parsers import StrOutputParser
        pt = PromptTemplate(
            template=daily_dose_prompt,
            input_variables=["title", "theme", "question", "context"],
        )
        chain = pt | llm | StrOutputParser()
        out = chain.invoke({
            "title": title,
            "theme": theme,
            "question": question,
            "context": context,
        })
        return (_strip_thinking(out or "").strip()) or "Could not generate teaching."
    except Exception as e:
        return f"Unable to generate teaching: {str(e)}"


def _source_doc_key(doc) -> str:
    """
    Canonical key for a source doc (for recall: same doc = same key).
    Works for both LangChain Document and dict.
    """
    metadata = _safe_get(doc, "metadata", {}) or {}
    doc_type = metadata.get("type", "unknown")

    if doc_type == "case_record":
        case_id = metadata.get("case_id") or metadata.get("CaseID") or ""
        job_name = metadata.get("job_name") or metadata.get("Job_Name") or ""
        return f"case:{case_id}:{job_name.strip()}"

    if doc_type == "pdf_document":
        filename = metadata.get("filename") or ""
        return f"pdf:{filename.strip()}"

    return f"other:{id(doc)}"


def _load_eval_relevance():
    """Load complex_eval_results.json and build question -> relevant doc keys index."""
    global _eval_relevance
    path = os.path.join(os.path.dirname(__file__), "..", "complex_eval_results.json")
    if not os.path.isfile(path):
        # Create minimal evaluation data for testing
        _eval_relevance = [
            {
                "question_norm": "margin of safety",
                "relevant_keys": {"other:12345", "pdf:margin-of-safety-book"}
            },
            {
                "question_norm": "what should i do to get 5 crore in 2 years", 
                "relevant_keys": {"other:12346", "pdf:rich-dad-book"}
            }
        ]
        return
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return
    for item in data:
        q = (item.get("question") or "").strip()
        if not q:
            continue
        sources = item.get("sources") or []
        keys = set()
        for s in sources:
            if s.get("type") == "case_record":
                keys.add(f"case:{str(s.get('case_id', ''))}:{(s.get('job_name') or '').strip()}")
            elif s.get("type") == "pdf_document":
                keys.add(f"pdf:{(s.get('filename') or '').strip()}")
        if keys:
            _eval_relevance.append({
                "question_norm": " ".join(q.lower().split()),
                "question_original": q,
                "relevant_keys": keys,
            })


def _recall_at_k(user_query: str, source_docs: list) -> float:
    """Compute Recall@k when user query matches an eval question (relevant set from eval sources)."""
    import sys
    print("DEBUG _recall_at_k: source_docs=", source_docs, file=sys.stderr)
    print("DEBUG _recall_at_k: _eval_relevance=", _eval_relevance, file=sys.stderr)
    if not source_docs or not _eval_relevance:
        print("DEBUG _recall_at_k: source_docs or _eval_relevance empty", file=sys.stderr)
        return 0.0
    import string
    STOPWORDS = set([
        'the', 'is', 'at', 'which', 'on', 'for', 'and', 'or', 'to', 'of', 'in', 'a', 'an', 'as', 'by', 'with', 'from', 'that', 'this', 'are', 'was', 'be', 'it', 'has', 'have', 'but', 'not', 'if', 'so', 'do', 'does', 'can', 'will', 'would', 'should', 'must', 'may', 'were', 'been', 'such', 'than', 'then', 'when', 'where', 'who', 'whom', 'whose', 'how', 'what', 'why', 'about', 'into', 'up', 'down', 'out', 'over', 'under', 'again', 'further', 'more', 'most', 'some', 'any', 'each', 'few', 'other', 'all', 'both', 'either', 'neither', 'own', 'same', 'so', 'very', 'just', 'now'
    ])
    def normalize(text):
        text = text.lower()
        text = text.translate(str.maketrans('', '', string.punctuation))
        tokens = [t for t in text.split() if t not in STOPWORDS]
        return set(tokens)
    query_tokens = normalize(user_query)
    best_match = None
    best_ratio = 0
    for item in _eval_relevance:
        eval_tokens = normalize(item["question_norm"])
        # Jaccard similarity
        intersection = query_tokens & eval_tokens
        union = query_tokens | eval_tokens
        jaccard = len(intersection) / len(union) if union else 0
        # Partial match: if all query tokens are in eval_tokens
        partial = len(query_tokens) > 0 and query_tokens.issubset(eval_tokens)
        if partial:
            best_match = item
            break
        if jaccard > best_ratio:
            best_ratio = jaccard
            best_match = item
    if not best_match:
        return 0.0
    relevant = best_match["relevant_keys"]
    if not relevant:
        return 0.0
    retrieved = set(_source_doc_key(d) for d in source_docs)
    hit = len(retrieved & relevant)
    recall_value = round(hit / len(relevant), 4)
    return recall_value


def _count_cited_sources(response_text: str, source_docs: list) -> int:
    """
    Count how many of the retrieved sources are cited in the response.
    Works with Document objects.
    """
    cited = 0

    for doc in source_docs:
        metadata = _safe_get(doc, "metadata", {}) or {}
        doc_type = metadata.get("type", "unknown")

        if doc_type == "case_record":
            case_id = str(metadata.get("case_id") or metadata.get("CaseID") or "")
            job_name = (metadata.get("job_name") or metadata.get("Job_Name") or "").strip()

            if case_id and case_id in response_text:
                cited += 1
                continue
            if job_name and job_name in response_text:
                cited += 1

        elif doc_type == "pdf_document":
            filename = (metadata.get("filename") or "").strip()

            if filename and filename in response_text:
                cited += 1

    return cited

@app.route('/')
def index():
    """Serve the main page"""
    return render_template('index.html')


@app.route('/daily-dose')
def daily_dose_page():
    """Serve the Daily Dose page."""
    return render_template('daily_dose.html')


@app.route('/api/daily-dose', methods=['GET'])
def api_daily_dose():
    """Return today's dose or ?day=1–200. Generated from finance & marketing books, cached in MongoDB."""
    from api.daily_dose import get_dose_for_day, date_to_day, JOURNEY_DAYS
    from datetime import date
    day_param = request.args.get('day', type=int)
    for_date = date.today()
    if day_param is not None:
        day = ((day_param - 1) % JOURNEY_DAYS) + 1
    else:
        day = date_to_day(for_date)
    if not system_initialized:
        success, _ = initialize_rag_system()
        if not success:
            return jsonify({'success': False, 'error': 'RAG system not initialized'}), 503
    dose = get_dose_for_day(day, for_date=for_date, generate_message_cb=generate_daily_dose_message)
    return jsonify({'success': True, 'data': dose})


@app.route('/api/daily-dose/topics', methods=['GET'])
def api_daily_dose_topics():
    """Return the list of 200 topics (no message generation)."""
    from api.daily_dose import list_topics
    topics = list_topics()
    return jsonify({'success': True, 'data': topics})


@app.route('/api/initialize', methods=['POST'])
def api_initialize():
    """Initialize the RAG system"""
    try:
        success, message = initialize_rag_system()
        return jsonify({
            'success': success,
            'message': message,
            'stocks_count': finance_docs,
            'bonds_count': marketing_docs,  # Using marketing_docs as bonds for now
            'assets_count': sales_docs     # Using sales_docs as assets for now
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f"Error initializing system: {str(e)}"
        }), 500

@app.route('/api/financial-expert', methods=['POST'])
def financial_expert_chat():
    """Handle chat requests using the financial expert agent"""
    start_time = time.time()
    
    try:
        data = request.get_json()
        user_input = data.get('message', '').strip()
        
        if not user_input:
            return jsonify({
                'error': 'Message is required'
            }), 400
        
        # Initialize system if needed
        if not system_initialized:
            success, message = initialize_rag_system()
            if not success:
                return jsonify({
                    'error': message
                }), 500
        
        # Get the financial expert agent
        agent = get_financial_expert_agent()
        if not agent:
            return jsonify({
                'error': 'Financial expert agent not available. Please initialize the system first.'
            }), 500
        
        try:
            # Create a message for the agent
            messages = [HumanMessage(content=user_input)]
            
            # Invoke the agent
            response = agent.invoke({"messages": messages})
            
            # Extract the response content
            if response and "messages" in response:
                # Get the last AI message
                ai_messages = [msg for msg in response["messages"] if isinstance(msg, AIMessage)]
                if ai_messages:
                    content = ai_messages[-1].content
                    # Handle both string and list content types
                    if isinstance(content, str):
                        agent_response = _strip_thinking(content)
                    elif isinstance(content, list):
                        # Join list elements if content is a list
                        agent_response = _strip_thinking(" ".join(str(c) for c in content))
                    else:
                        agent_response = str(content)
                else:
                    agent_response = "I apologize, but I couldn't generate a proper response. Please try again."
            else:
                agent_response = "I apologize, but I encountered an error processing your request."
            
            # Calculate processing time
            processing_time = time.time() - start_time
            
            # Log the agent interaction
            agent_log_data = {
                'timestamp': datetime.now().isoformat(),
                'query': user_input,
                'response': agent_response,
                'agent_type': 'financial_expert',
                'processing_time': processing_time,
                'ip_address': request.remote_addr,
                'user_agent': request.headers.get('User-Agent', ''),
                'session_id': session.get('session_id', '')
            }
            
            # Log to file
            try:
                if os.path.exists(QUERY_LOG_FILE):
                    with open(QUERY_LOG_FILE, 'r', encoding='utf-8') as f:
                        logs = json.load(f)
                else:
                    logs = []
                
                logs.append(agent_log_data)
                
                # Keep only last 10000 queries
                if len(logs) > 10000:
                    logs = logs[-10000:]
                
                with open(QUERY_LOG_FILE, 'w', encoding='utf-8') as f:
                    json.dump(logs, f, indent=2, ensure_ascii=False)
            except Exception as e:
                print(f"Error logging agent query: {e}")
            
            return jsonify({
                'response': agent_response,
                'agent_type': 'financial_expert',
                'processing_time': processing_time,
                'sources': []  # Agent handles its own sources
            })
            
        except Exception as e:
            print(f"Error in financial expert agent: {e}")
            return jsonify({
                'error': f"Error generating response from financial expert: {str(e)}"
            }), 500
            
    except Exception as e:
        return jsonify({
            'error': f"Error processing request: {str(e)}"
        }), 500

@app.route('/api/chat', methods=['POST'])
def api_chat():
    """Handle chat requests"""
    start_time = time.time()
    
    try:
        data = request.get_json()
        user_input = data.get('message', '').strip()
        
        if not user_input:
            return jsonify({
                'error': 'Message is required'
            }), 400
        
        if not system_initialized:
            success, message = initialize_rag_system()
            if not success:
                return jsonify({
                    'error': message
                }), 500
        
        # Initialize variables
        retrieval_metrics = None
        category = 'general'
        collection_name = 'finance'
        sources = []
        response = ""
        confidence = 0.0
        
        try:
            # Initialize query classifier if not already done
            if not query_classifier:
                return jsonify({
                    'error': 'System not properly initialized. Please restart the application.'
                }), 500
            
            if not rag_chain:
                return jsonify({
                    'error': 'RAG system not initialized. Please initialize the system first.'
                }), 500
            
            # Classify query and get appropriate sources
            category, confidence = query_classifier.classify_query(user_input)
            collection_name = query_classifier.get_collection_name(category)
            
            # Check if this is a book-specific query
            is_book_specific, book_name = query_classifier.detect_book_specific_query(user_input)
            
            # Answer is generated from appropriate collection with optional book filter
            if is_book_specific:
                sources = get_retrieved_sources(user_input, collection_name, book_filter=book_name)
                print(f"Book-specific query detected: {book_name}, filtered search applied")
            else:
                sources = get_retrieved_sources(user_input, collection_name)
            
            context = _format_docs(sources) if sources else ""
            
            # Generate response based ONLY on PDF sources
            if sources and context.strip():
                response = rag_chain.invoke({"context": context, "question": user_input})
                response = _strip_thinking((response or "").strip())
                
                # Verify response is grounded in sources and uses book content
                is_grounded = _verify_response_grounded_in_sources(response, sources)
                
                print(f"Response grounded: {is_grounded}, sources_used: {len(sources)}")
            else:
                # No sources available - provide fallback
                response = f"While I don't have access to specific book content for this question right now, I can share that the world-classic finance and marketing books in our collection contain timeless wisdom from legendary investors like Warren Buffett, Benjamin Graham, and marketing experts. For '{user_input}', I recommend studying foundational works directly, as these books contain detailed strategies that would be most relevant to your situation."
            
            # Initialize retrieval metrics with default values
            retrieval_metrics = {
                'k': RETRIEVAL_K,
                'retrieved': 0,
                'cited_in_answer': 0,
                'precision_at_k': 0.0,
                'recall_at_k': 0.0,
            }
            
            # Calculate retrieval metrics if sources are available
            if sources:
                cited = _count_cited_sources(response, sources)
                retrieval_metrics = {
                    'k': RETRIEVAL_K,
                    'retrieved': len(sources),
                    'cited_in_answer': cited,
                    'precision_at_k': round(cited / RETRIEVAL_K, 4) if RETRIEVAL_K else 0.0,
                    'recall_at_k': _recall_at_k(user_input, sources),
                }
        except Exception as e:
            if 'groqstatus.com' in str(e) or 'Service unavailable' in str(e):
                return jsonify({
                    'error': "The AI service is temporarily unavailable. Please try again later or check https://groqstatus.com/ for updates."
                }), 503
            return jsonify({
                'error': f"Error generating response: {str(e)}"
            }), 500

        # Store query metrics
        store_query_metrics(user_input, category, collection_name, sources, response, retrieval_metrics)
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        # Calculate comprehensive metrics and log to file
        comprehensive_metrics = calculate_comprehensive_metrics(user_input, response, sources, category, confidence)
        
        # Prepare comprehensive query data for file logging
        query_log_data = {
            'timestamp': datetime.now().isoformat(),
            'query': user_input,
            'category': category,
            'collection': collection_name,
            'response': response,
            'sources_retrieved': len(sources) if sources else 0,
            'sources_cited': retrieval_metrics.get('cited_in_answer', 0) if retrieval_metrics else 0,
            'precision_at_k': retrieval_metrics.get('precision_at_k', 0) if retrieval_metrics else 0,
            'recall_at_k': retrieval_metrics.get('recall_at_k', 0) if retrieval_metrics else 0,
            'has_sources': len(sources) > 0 if sources else False,
            'confidence_score': confidence,
            'processing_time': processing_time,
            'ip_address': request.remote_addr,
            'user_agent': request.headers.get('User-Agent', ''),
            'session_id': session.get('session_id', ''),
            **comprehensive_metrics
        }
        
        # Log query to file
        log_query_to_file(query_log_data)
        
        source_docs = []

        for doc in sources:
            metadata = _safe_get(doc, "metadata", {}) or {}
            content = _safe_get(doc, "page_content", "")

            doc_type = metadata.get("type", "unknown")

            if doc_type == "case_record":
                source_docs.append({
                    "case_id": metadata.get("case_id") or metadata.get("CaseID"),
                    "job_name": metadata.get("job_name") or metadata.get("Job_Name"),
                    "content": content,
                    "type": "case_record",
                })

            elif doc_type == "pdf_document":
                source_docs.append({
                    "filename": metadata.get("filename"),
                    "content": content,
                    "type": "pdf_document",
                })

            else:
                source_docs.append({
                    "metadata": metadata,
                    "content": content,
                    "type": "unknown",
                })
        return jsonify({
            'response': response,
            'sources': source_docs,
            'retrieval_metrics': retrieval_metrics,
        })
    except Exception as e:
        return jsonify({
            'error': f"Error generating response: {str(e)}"
        }), 500


def store_query_metrics(query, category, collection, sources, response, retrieval_metrics):
    """Store query-by-query metrics for dashboard"""
    global query_metrics
    
    metric_entry = {
        'id': str(uuid.uuid4()),
        'timestamp': datetime.now().isoformat(),
        'query': query,
        'category': category,
        'collection': collection,
        'sources_retrieved': len(sources) if sources else 0,
        'sources_cited': retrieval_metrics.get('cited_in_answer', 0) if retrieval_metrics else 0,
        'precision_at_k': retrieval_metrics.get('precision_at_k', 0) if retrieval_metrics else 0,
        'recall_at_k': retrieval_metrics.get('recall_at_k', 0) if retrieval_metrics else 0,
        'response_length': len(response) if response else 0,
        'has_sources': len(sources) > 0 if sources else False
    }
    
    query_metrics.append(metric_entry)
    
    # Keep only last 1000 queries to prevent memory issues
    if len(query_metrics) > 1000:
        query_metrics = query_metrics[-1000:]

@app.route('/dashboard')
def dashboard():
    """Serve the dashboard page with password protection"""
    token = request.args.get('token')
    
    if not token:
        return jsonify({'error': 'Token required. Please access dashboard from main application.'}), 401
    
    if token not in dashboard_sessions:
        return jsonify({'error': 'Invalid or expired token. Please re-authenticate.'}), 401
    
    # Check if token is still valid (24 hours)
    session_data = dashboard_sessions[token]
    if time.time() - session_data['created'] > 24 * 3600:
        del dashboard_sessions[token]
        return jsonify({'error': 'Token expired. Please re-authenticate.'}), 401
    
    return render_template('dashboard.html')

@app.route('/api/verify-dashboard-password', methods=['POST'])
def verify_dashboard_password():
    """Verify dashboard password and issue session token"""
    try:
        data = request.get_json()
        password = data.get('password', '')
        
        if password == DASHBOARD_PASSWORD:
            # Generate session token
            token = str(uuid.uuid4())
            dashboard_sessions[token] = {
                'created': time.time(),
                'ip': request.remote_addr
            }
            return jsonify({
                'success': True,
                'token': token
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Invalid password'
            })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error: {str(e)}'
        }), 500

@app.route('/api/dashboard-data', methods=['GET'])
def dashboard_data():
    """Serve dashboard analytics data"""
    token = request.args.get('token') or session.get('dashboard_token')
    
    if not token or token not in dashboard_sessions:
        return jsonify({'error': 'Unauthorized'}), 401
    
    # Check if token is still valid
    session_data = dashboard_sessions[token]
    if time.time() - session_data['created'] > 24 * 3600:
        del dashboard_sessions[token]
        return jsonify({'error': 'Token expired'}), 401
    
    # Calculate metrics
    total_queries = len(query_metrics)
    finance_queries = len([q for q in query_metrics if q['category'] == 'finance'])
    marketing_queries = len([q for q in query_metrics if q['category'] == 'marketing'])
    
    # Calculate average precision
    precisions = [q['precision_at_k'] for q in query_metrics if q['precision_at_k'] > 0]
    avg_precision = sum(precisions) / len(precisions) if precisions else 0
    
    metrics = {
        'total_queries': total_queries,
        'finance_queries': finance_queries,
        'marketing_queries': marketing_queries,
        'avg_precision': avg_precision
    }
    
    return jsonify({
        'success': True,
        'metrics': metrics,
        'queries': query_metrics[-100:]  # Return last 100 queries
    })

@app.route('/api/comprehensive-queries')
def get_comprehensive_queries():
    """Return comprehensive query data from file with all metrics"""
    token = request.args.get('token')
    
    if not token or token not in dashboard_sessions:
        return jsonify({'error': 'Unauthorized'}), 401
    
    # Check if token is still valid
    session_data = dashboard_sessions[token]
    if time.time() - session_data['created'] > 24 * 3600:
        del dashboard_sessions[token]
        return jsonify({'error': 'Token expired'}), 401
    
    try:
        # Load comprehensive query data from file
        if os.path.exists(QUERY_LOG_FILE):
            with open(QUERY_LOG_FILE, 'r', encoding='utf-8') as f:
                comprehensive_queries = json.load(f)
        else:
            comprehensive_queries = []
        
        return jsonify({
            'success': True,
            'queries': comprehensive_queries[-500:],  # Return last 500 queries
            'total_count': len(comprehensive_queries)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f"Error loading query data: {str(e)}"
        }), 500




@app.route('/api/evaluate', methods=['POST'])
def api_evaluate():
    """Run the technical answer evaluation agent on a RAG response."""
    try:
        data = request.get_json() or {}
        question = data.get('question', '').strip()
        response_text = data.get('response', '')
        sources = data.get('sources', [])

        if not question or not response_text:
            return jsonify({
                'error': 'question and response are required'
            }), 400

        evaluation = evaluate_answer(question, response_text, sources)
        return jsonify(evaluation)
    except Exception as e:
        return jsonify({
            'error': f"Evaluation failed: {str(e)}"
        }), 500


_load_eval_relevance()


@app.route('/api/status', methods=['GET'])
def api_status():
    """Get system status"""
    return jsonify({
        'initialized': system_initialized,
        'stocks_count': finance_docs,
        'bonds_count': marketing_docs,
        'assets_count': sales_docs,
        'model': 'Investment Wisdom AI',
        'search_type': 'Semantic Similarity with Classification'
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
