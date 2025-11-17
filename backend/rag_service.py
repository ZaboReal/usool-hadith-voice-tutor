"""
RAG Service for retrieving information from Usool al-Hadith
"""
import os
from typing import List
from dotenv import load_dotenv
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain_core.documents import Document

load_dotenv()

class RAGService:
    """Service for retrieving relevant information from the Hadith book"""

    def __init__(self):
        """Initialize RAG service with Pinecone vector store"""
        # Use local embeddings (FREE - no API costs!)
        # multilingual-e5-large: Great for Arabic + English text
        self.embeddings = HuggingFaceEmbeddings(
            model_name="intfloat/multilingual-e5-large",
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )

        self.index_name = os.getenv("PINECONE_INDEX_NAME", "usool-hadith-index")
        self.top_k = int(os.getenv("TOP_K_RESULTS", "5"))

        # Initialize vector store
        self.vector_store = PineconeVectorStore(
            index_name=self.index_name,
            embedding=self.embeddings
        )

    def retrieve_context(self, query: str, k: int = None) -> List[Document]:
        """
        Retrieve relevant context from the vector store

        Args:
            query: The user's question
            k: Number of results to retrieve (defaults to TOP_K_RESULTS from env)

        Returns:
            List of relevant documents
        """
        if k is None:
            k = self.top_k

        results = self.vector_store.similarity_search(
            query=query,
            k=k
        )

        return results

    def format_context(self, documents: List[Document]) -> str:
        """
        Format retrieved documents into a context string

        Args:
            documents: List of retrieved documents

        Returns:
            Formatted context string
        """
        if not documents:
            return "No relevant information found in the Usool al-Hadith book."

        context_parts = []
        for i, doc in enumerate(documents, 1):
            page_num = doc.metadata.get('page', 'Unknown')
            content = doc.page_content.strip()
            context_parts.append(
                f"[Source {i} - Page {page_num}]:\n{content}"
            )

        return "\n\n".join(context_parts)

    def query(self, question: str) -> str:
        """
        Query the RAG system and return formatted context

        Args:
            question: The user's question

        Returns:
            Formatted context string
        """
        documents = self.retrieve_context(question)
        return self.format_context(documents)
