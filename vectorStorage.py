import os
import shutil
from dotenv import load_dotenv
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings

load_dotenv()

def build_vector_store():

    # =========================================
    # WIPE ENTIRE CHROMA FOLDER
    # =========================================
    if os.path.exists("./chroma_db"):
        shutil.rmtree("./chroma_db")
        print("Deleted chroma_db folder")

    # =========================================
    # LOAD DATA
    # =========================================
    with open("stockInfo.txt", encoding="utf-8") as f:
        raw_text = f.read()

    print(f"Loaded {len(raw_text)} characters")

    # =========================================
    # CHUNK
    # =========================================
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=100
    )

    texts = text_splitter.create_documents([raw_text])
    print(f"Created {len(texts)} chunks")

    # =========================================
    # EMBED + STORE
    # =========================================
    embeddings = OpenAIEmbeddings(
    model="text-embedding-3-small",
    api_key="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"
    )



    vector_store = Chroma(
        collection_name="stock_news",
        embedding_function=embeddings,
        persist_directory="./chroma_db"
    )

    vector_store.add_documents(texts)
    print(texts)
    print(f"DONE: Stored {len(texts)} chunks in fresh chroma_db")


if __name__ == "__main__":
    build_vector_store()