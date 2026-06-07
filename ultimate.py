from dotenv import load_dotenv
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

# =========================================
# SETUP
# =========================================

load_dotenv()

# =========================================
# LOAD & CHUNK
# =========================================

with open("stockNews.txt", encoding="utf-8") as f:
    raw_text = f.read()

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200
)

texts = text_splitter.create_documents([raw_text])

# =========================================
# EMBEDDINGS & VECTOR STORE
# =========================================

embeddings = OpenAIEmbeddings(model="text-embedding-3-large")

vector_store = Chroma(
    collection_name="stock_news",
    embedding_function=embeddings
)

vector_store.add_documents(texts)
print(f"Stored {len(texts)} chunks in ChromaDB.\n")

# =========================================
# RAG CHAIN
# =========================================

retriever = vector_store.as_retriever(search_kwargs={"k": 5})

llm = ChatOpenAI(model="gpt-4o")

def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

prompt_template = """You are a South African equity research analyst.
Use ONLY the context provided to answer the question.
If the answer is not in the context, say you don't know.

Context:
{context}

Question:
{query}

Answer:"""

custom_rag_prompt = PromptTemplate.from_template(prompt_template)

rag_chain = (
    {"context": retriever | format_docs, "query": RunnablePassthrough()}
    | custom_rag_prompt
    | llm
    | StrOutputParser()
)

# =========================================
# ASK QUESTIONS
# =========================================

if __name__ == "__main__":
    print("Stock News RAG ready. Type 'quit' to exit.\n")

    while True:
        question = input("Your question: ").strip()

        if question.lower() in ("quit", "exit", "q"):
            print("Goodbye.")
            break

        if not question:
            continue

        answer = rag_chain.invoke(question)
        print(f"\nAnswer:\n{answer}\n")
        print("=" * 60 + "\n")