import os
import logging

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from mcp.server.fastmcp import FastMCP
from typing import Any

BASE_PATH = os.path.abspath(os.path.dirname(__file__))

def load_retriever() -> Any:
    """
    Load VectorStore
    Returns:
        Any: A retriever object
    """
    embeddings = HuggingFaceEmbeddings(model_name="BAAI/bge-m3")

    vectorstore = FAISS.load_local(
        folder_path=os.path.join(BASE_PATH, "db"),
        index_name="index",
        embeddings=embeddings,
        allow_dangerous_deserialization=True
    )

    retriever = vectorstore.as_retriever(search_kwargs = {"k" : 3})
    return retriever


def create_retriever() -> Any:
    """
    Creates and returns a document retriever based on FAISS vector store.
    Returns:
        Any: A retriever object that can be used to query the document database
    """
    loader = PyMuPDFLoader(os.path.join(BASE_PATH, "data/sample.pdf"))
    docs = loader.load()

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=50)
    split_documents = text_splitter.split_documents(docs)

    embeddings = HuggingFaceEmbeddings(model_name='BAAI/bge-m3')

    vectorstore = FAISS.from_documents(documents=split_documents, embedding=embeddings)

    if not os.path.exists(os.path.join(BASE_PATH, "db")):
        os.makedirs(os.path.join(BASE_PATH, "db"), exist_ok=True)
        vectorstore.save_local(folder_path=os.path.join(BASE_PATH, "db"))
    retriever = vectorstore.as_retriever()
    return retriever


# Initialize FastMCP server with configuration
mcp = FastMCP(
    "Retriever",
    instructions="A Retriever that can retrieve information from the database.",
    host="0.0.0.0",
    port=8005,
)


@mcp.tool()
async def retrieve(query: str) -> str:
    """
    Retrieves information from the document database based on the query.

    This function creates a retriever, queries it with the provided input,
    and returns the concatenated content of all retrieved documents.

    Args:
        query (str): The search query to find relevant information

    Returns:
        str: Concatenated text content from all retrieved documents
    """
    # Create a new retriever instance for each query
    # Note: In production, consider caching the retriever for better performance
    logging.info(f"PATH is existed : {os.path.exists(os.path.join(BASE_PATH, "db"))}")
    logging.info(f"Current Path : {os.getcwd()}")
    if os.path.exists(os.path.join(BASE_PATH, "db")):
        retriever = load_retriever()
    else:
        retriever = create_retriever()

    # Use the invoke() method to get relevant documents based on the query
    retrieved_docs = retriever.invoke(query)

    # Join all document contents with newlines and return as a single string
    return "\n".join([doc.page_content for doc in retrieved_docs])


if __name__ == "__main__":
    mcp.run(transport="stdio")
