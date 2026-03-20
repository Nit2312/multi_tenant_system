import os
import pandas as pd
from dotenv import load_dotenv
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_astradb import AstraDBVectorStore
from langchain_community.embeddings import HuggingFaceEmbeddings
from huggingface_hub import InferenceClient
from astrapy import DataAPIClient
import fitz  # PyMuPDF
from pathlib import Path

load_dotenv()

def resolve_data_source():
    data_url = os.getenv("DATA_FILE_URL")
    if data_url:
        return data_url

    data_path = os.getenv("DATA_FILE_PATH")
    if data_path:
        return data_path

    default_paths = ["10yearsdata.xls"]
    for path in default_paths:
        if os.path.exists(path):
            return path

    return None

def get_astra_config():
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
        result = self._client.feature_extraction(texts)
        if isinstance(result, list) and result and isinstance(result[0], float):
            return [result]
        return result

    def embed_query(self, text):
        return self.embed_documents([text])[0]


def build_embeddings():
    model_name = "sentence-transformers/all-mpnet-base-v2"
    backend = os.getenv("EMBEDDINGS_BACKEND", "local").strip().lower()

    if backend == "endpoint":
        embeddings = RouterHuggingFaceEmbeddings(
            api_key=os.getenv("HF_TOKEN"),
            model_name=model_name,
        )
        try:
            embeddings.embed_query("health check")
            return embeddings
        except Exception as e:
            print(f"Warning: endpoint embeddings failed ({e}); falling back to local.")

    return HuggingFaceEmbeddings(model_name=model_name)


def extract_text_from_pdf(pdf_path):
    """Extract text from PDF using PyMuPDF"""
    try:
        doc = fitz.open(pdf_path)
        text = ""
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            text += page.get_text()
        doc.close()
        return text
    except Exception as e:
        print(f"Error reading {pdf_path}: {e}")
        return None

def extract_book_metadata(pdf_file):
    """Extract comprehensive metadata from PDF filename and path"""
    filename = pdf_file.name.lower()
    path_parts = pdf_file.parts
    
    # Determine book name from filename
    book_mapping = {
        'theeducationofavlaueinvestor.pdf': 'the education of a value investor',
        'the-education-of-a-value-investor.pdf': 'the education of a value investor',
        'rich_dad_poor_dad.pdf': 'rich dad poor dad',
        'rich-dad-poor-dad-ebook.pdf': 'rich dad poor dad',
        'rich-dad-poor-dad-ebook.pdf': 'rich dad poor dad',
        'rich-dad-poor-dad.pdf': 'rich dad poor dad',
        'rich-dad-poor-dad-ebook.pdf': 'rich dad poor dad',
        'intelligent_investor.pdf': 'the intelligent investor',
        'the-intelligent-investor.pdf': 'the intelligent investor',
        'the-intelligent-investor.pdf': 'the intelligent investor',
        'the intelligent investor - benjamin graham.pdf': 'the intelligent investor',
        'security_analysis.pdf': 'security analysis',
        'one_up_wall_street.pdf': 'one up on wall street',
        'one-up-wall-street.pdf': 'one up on wall street',
        'common_stocks_uncommon_profits.pdf': 'common stocks uncommon profits',
        'common-stocks-uncommon-profits.pdf': 'common stocks uncommon profits',
        'little_book_common_sense.pdf': 'the little book of common sense investing',
        'the-little-book-of-common-sense-investing.pdf': 'the little book of common sense investing',
        'random_walk_wall_street.pdf': 'a random walk down wall street',
        'a-random-walk-down-wall-street.pdf': 'a random walk down wall street',
        'a-random-walk-down-wall-street.pdf': 'a random walk down wall street',
        'buffett_essays.pdf': 'the essays of warren buffett',
        'the-essays-of-warren-buffett.pdf': 'the essays of warren buffett',
        'win_friends_influence.pdf': 'how to win friends and influence people',
        'how-to-win-friends-and-influence-people.pdf': 'how to win friends and influence people',
        'how to win friends and influence people - carnegie, dale.pdf': 'how to win friends and influence people',
        '16-05-2021-070111the-richest-man-in-babylon.pdf': 'the richest man in babylon',
        'the-richest-man-in-babylon.pdf': 'the richest man in babylon',
        'cf0-leadership-manual-v2.pdf': 'cfo leadership manual',
        'how-to-make-money-in-stocks-forex.pdf': 'how to make money in stocks forex',
        'i-will-teach-you-to-be-rich-chapter1.pdf': 'i will teach you to be rich',
        'just-keep-buying-pdf.pdf': 'just keep buying',
        'poor-charlie-s-almanack-the-wit-and-wisdom-of-charles-t-munger.pdf': 'poor charlie s almanack',
        'the-wit-and-wisdom-of-charles-t-munger.pdf': 'the wit and wisdom of charles t munger',
        'principles-life-and-work-ray-dalio.pdf': 'principles life and work ray dalio',
        'the-little-book-that-beats-the-market.pdf': 'the little book that beats the market',
        'the-millionaire-next-door-surprising-secrets.pdf': 'the millionaire next door surprising secrets',
        'the-psychology-of-money.pdf': 'the psychology of money',
        'napoleon-hill-think-and-grow-rich.pdf': 'think and grow rich',
        'the-total-money-makeover-dave-ramsey.pdf': 'the total money makeover dave ramsey',
        'schroeder-the-snowball.pdf': 'the snowball',
        'will-teach-you-to-be-rich-next-door-surprising-secrets.pdf': 'will teach you to be rich next door surprising secrets'
    }
    
    # Try to match filename to book
    book_name = book_mapping.get(filename, filename.replace('.pdf', ''))
    
    # Determine category from path
    category = 'general'
    if 'finance' in path_parts:
        category = 'finance'
    elif 'marketing' in path_parts:
        category = 'marketing'
    
    # Extract author information
    author_mapping = {
        'the education of a value investor': 'seth klarman',
        'rich dad poor dad': 'robert kiyosaki',
        'the intelligent investor': 'benjamin graham',
        'security analysis': 'benjamin graham',
        'one up on wall street': 'peter lynch',
        'common stocks uncommon profits': 'philip fisher',
        'the little book of common sense investing': 'john bogle',
        'a random walk down wall street': 'burton malkiel',
        'the essays of warren buffett': 'warren buffett',
        'how to win friends and influence people': 'dale carnegie',
        'the richest man in babylon': 'george s clason',
        'cfo leadership manual': 'cfo leadership',
        'how to make money in stocks forex': 'forex trading',
        'i will teach you to be rich': 'general wealth building',
        'just keep buying': 'investment strategy',
        'the wit and wisdom of charles t munger': 'charles munger',
        'principles life and work ray dalio': 'ray dalio',
        'the little book that beats the market': 'market beating strategies',
        'the millionaire next door surprising secrets': 'wealth building',
        'the psychology of money': 'financial psychology',
        'think and grow rich': 'napoleon hill',
        'the total money makeover dave ramsey': 'dave ramsey',
        'the snowball': 'debt reduction'
    }
    
    author = author_mapping.get(book_name, 'unknown')
    
    return {
        'book_name': book_name,
        'author': author,
        'category': category,
        'filename': pdf_file.name,
        'file_path': str(pdf_file),
        'type': 'pdf_document',
        'source': str(pdf_file)
    }

def ingest_pdfs_from_data_folder(data_folder="data", category=None):
    """Ingest all PDF files from a specific category folder (finance or marketing)"""
    pdf_documents = []
    
    if category:
        data_path = Path(data_folder) / category
    else:
        data_path = Path(data_folder)
    
    if not data_path.exists():
        print(f"Data folder {data_path} not found")
        return pdf_documents
    
    # Find all PDF files
    pdf_files = list(data_path.glob("*.pdf"))
    print(f"Found {len(pdf_files)} PDF files in {data_path}")
    
    for pdf_file in pdf_files:
        print(f"Processing: {pdf_file.name}")
        text = extract_text_from_pdf(pdf_file)
        
        if text and text.strip():  # Only add if text is not empty
            # Extract comprehensive metadata
            metadata = extract_book_metadata(pdf_file)
            
            doc = Document(
                page_content=text,
                metadata=metadata
            )
            pdf_documents.append(doc)
            print(f"  - Book: {metadata['book_name']}")
            print(f"  - Author: {metadata['author']}")
            print(f"  - Category: {metadata['category']}")
        else:
            print(f"Warning: No text extracted from {pdf_file.name}")
    
    return pdf_documents

def clean_excel_data(df):
    """Comprehensive data cleaning for Excel data - removes ANY row with empty data"""
    print("Original data shape:", df.shape)
    print("Original null counts:")
    print(df.isnull().sum())
    
    # Select relevant columns
    df_clean = df[["CaseID", "Job_Name", "Case_Problem", "Case_Resolution_Notes"]].copy()
    
    # Remove ANY row that has empty/NaN data in ANY column
    df_clean = df_clean.dropna()
    
    # Also remove rows with empty strings after stripping whitespace
    for col in df_clean.columns:
        df_clean = df_clean[df_clean[col].astype(str).str.strip() != '']
    
    # Reset index after cleaning
    df_clean = df_clean.reset_index(drop=True)
    
    print(f"\nCleaned data shape: {df_clean.shape}")
    print(f"Removed {df.shape[0] - df_clean.shape[0]} rows with ANY empty data")
    print("\nNull counts after cleaning:")
    print(df_clean.isnull().sum())
    
    return df_clean

def create_vector_store(documents, collection_name, embeddings, astra_config):
    """Create a vector store for a specific collection"""
    if not documents:
        print(f"No documents to process for collection {collection_name}")
        return
    
    # Process documents
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1200,
        chunk_overlap=300,
        length_function=len,
        separators=["\n\n", "\n", ". ", "", ""],
    )
    
    chunks = text_splitter.split_documents(documents)
    print(f"Created {len(chunks)} chunks for collection {collection_name}")
    
    # Reset collection to ensure fresh data
    print(f"Resetting Astra DB collection: {collection_name}...")
    client = DataAPIClient(astra_config["token"])
    
    # Use keyspace instead of deprecated namespace
    try:
        db = client.get_database(astra_config["api_endpoint"], keyspace=astra_config["namespace"])
        db.drop_collection(collection_name)
        print(f"Dropped collection: {collection_name}")
    except Exception as e:
        print(f"Warning: failed to drop collection '{collection_name}': {e}")
        # Try with namespace as fallback
        try:
            db = client.get_database(astra_config["api_endpoint"], namespace=astra_config["namespace"])
            db.drop_collection(collection_name)
            print(f"Dropped collection with namespace fallback: {collection_name}")
        except Exception as e2:
            print(f"Warning: failed to drop collection with fallback: {e2}")
    
    # Create new collection with AstraDBVectorStore
    print(f"Creating new Astra DB collection: {collection_name}...")
    AstraDBVectorStore.from_documents(
        documents=chunks,
        embedding=embeddings,
        api_endpoint=astra_config["api_endpoint"],
        token=astra_config["token"],
        namespace=astra_config["namespace"],
        collection_name=collection_name,
    )
    
    print(f"Successfully ingested {len(documents)} documents into collection {collection_name}")
    print(f"Total chunks created: {len(chunks)}")


def main():
    # Process finance documents
    print("=== Processing Finance Documents ===")
    finance_docs = ingest_pdfs_from_data_folder("data", "finance")
    
    # Process marketing documents
    print("\n=== Processing Marketing Documents ===")
    marketing_docs = ingest_pdfs_from_data_folder("data", "marketing")
    
    if not finance_docs and not marketing_docs:
        print("No documents found in finance or marketing folders")
        return
    
    embeddings = build_embeddings()
    astra_config = get_astra_config()
    
    # Create separate collections for each category
    if finance_docs:
        create_vector_store(finance_docs, "finance", embeddings, astra_config)
    
    if marketing_docs:
        create_vector_store(marketing_docs, "marketing", embeddings, astra_config)
    
    print("\n=== Summary ===")
    print(f"Finance documents processed: {len(finance_docs)}")
    print(f"Marketing documents processed: {len(marketing_docs)}")
    print("Vector stores created successfully!")


if __name__ == "__main__":
    main()
