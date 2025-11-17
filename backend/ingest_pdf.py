"""
PDF Ingestion Script for Usool al-Hadith
Processes the PDF and uploads embeddings to Pinecone
"""
import os
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone, ServerlessSpec

load_dotenv()

# Use local embeddings (free) instead of OpenAI
EMBEDDING_MODEL = "intfloat/multilingual-e5-large"
EMBEDDING_DIMENSION = 1024  # Dimension for multilingual-e5-large

def ingest_pdf(pdf_path: str):
    """
    Ingest PDF into Pinecone vector database

    Args:
        pdf_path: Path to the PDF file
    """
    print(f"Loading PDF from {pdf_path}...")

    # Load PDF
    loader = PyPDFLoader(pdf_path)
    documents = loader.load()

    print(f"Loaded {len(documents)} pages from PDF")

    # Split documents into chunks
    chunk_size = int(os.getenv("CHUNK_SIZE", "1000"))
    chunk_overlap = int(os.getenv("CHUNK_OVERLAP", "200"))

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        separators=["\n\n", "\n", " ", ""]
    )

    chunks = text_splitter.split_documents(documents)
    print(f"Split into {len(chunks)} chunks")

    # Initialize Pinecone
    pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
    index_name = os.getenv("PINECONE_INDEX_NAME", "usool-hadith-index")

    # Create index if it doesn't exist
    existing_indexes = [index.name for index in pc.list_indexes()]

    if index_name not in existing_indexes:
        print(f"Creating new Pinecone index: {index_name}")
        pc.create_index(
            name=index_name,
            dimension=EMBEDDING_DIMENSION,  # Using local model dimension
            metric="cosine",
            spec=ServerlessSpec(
                cloud="aws",
                region=os.getenv("PINECONE_ENVIRONMENT", "us-east-1")
            )
        )
    else:
        print(f"Using existing Pinecone index: {index_name}")

    # Initialize embeddings (FREE - runs locally!)
    print(f"Loading embedding model: {EMBEDDING_MODEL}")
    embeddings = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={'device': 'cpu'},
        encode_kwargs={'normalize_embeddings': True}
    )

    # Upload to Pinecone
    print("Uploading embeddings to Pinecone...")
    vector_store = PineconeVectorStore.from_documents(
        documents=chunks,
        embedding=embeddings,
        index_name=index_name
    )

    print("✓ PDF ingestion complete!")
    print(f"✓ {len(chunks)} chunks uploaded to Pinecone index '{index_name}'")

    return vector_store

if __name__ == "__main__":
    # Path to the Usool al-Hadith PDF
    pdf_path = os.path.join(os.path.dirname(__file__), "..", "usool-al-hadith.pdf")

    if not os.path.exists(pdf_path):
        print(f"Error: PDF not found at {pdf_path}")
        exit(1)

    ingest_pdf(pdf_path)
