from langchain_core.documents import Document
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
import json

def create_vectorstore(json_file_path):

    with open(json_file_path, "r", encoding="utf-8") as f:
        documents_data = json.load(f)

    documents = [
        Document(page_content=doc["text"], metadata={"title": doc["title"], "id": doc["id"]})
        for doc in documents_data
    ]

    vectorstore = Chroma.from_documents(
        documents,
        embedding=HuggingFaceEmbeddings(model_name="paraphrase-multilingual-MiniLM-L12-v2")
    )
    return vectorstore