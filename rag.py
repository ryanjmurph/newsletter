from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from openai import OpenAI
import markdown
import json
from charts import generate_charts, inject_charts_into_html

load_dotenv()

def generate_newsletter():

    # =========================================
    # EMBEDDINGS & VECTOR STORE
    # =========================================

    API_KEY = "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"

    embeddings = OpenAIEmbeddings(model="text-embedding-3-small",api_key = API_KEY)

    vector_store = Chroma(
        collection_name="stock_news",
        embedding_function=embeddings,
        persist_directory="./chroma_db"
    )

    retriever = vector_store.as_retriever(search_kwargs={"k": 20})

    llm = ChatOpenAI(model="gpt-4o", temperature=0,api_key = API_KEY)

    # =========================================
    # RETRIEVE CONTEXT
    # =========================================
    def format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)

    docs = retriever.invoke(
        "South African equity market today JSE stocks news prices macro bond yields ZARONIA"
    )
    context = format_docs(docs)

    # =========================================
    # STEP 1 — Extract tickers GPT will mention
    # Ask GPT which tickers it will reference so
    # we know which charts to generate
    # =========================================
    print("Extracting tickers from context...")

    client = OpenAI(api_key = API_KEY)
    ticker_response = client.chat.completions.create(
        model="gpt-4o",
        temperature=0,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a financial data extractor. "
                    "Given market data, return ONLY a JSON array of JSE ticker symbols "
                    "(without .JO) that are meaningfully discussed. "
                    "Maximum 1 ticker. Most important/moved ones only. "
                    "Example: [\"SBK\", \"NPN\", \"AGL\"]. "
                    "Return ONLY the JSON array, nothing else."
                )
            },
            {
                "role": "user",
                "content": context
            }
        ]
    )

    try:
        tickers = json.loads(ticker_response.choices[0].message.content.strip())
        print(f"Tickers to chart: {tickers}")
    except Exception:
        tickers = []
        print("Could not extract tickers, skipping charts")

    # =========================================
    # STEP 2 — Generate charts for those tickers
    # =========================================
    charts = generate_charts(tickers) if tickers else {}

    # =========================================
    # STEP 3 — Generate newsletter
    # =========================================
    prompt = PromptTemplate.from_template("""
You are a seasoned equity analyst and fund manager with 25+ years of experience analyzing emerging market equities, particularly South African stocks.

You have deep knowledge of:
- JSE-listed companies
- macroeconomic drivers
- sector dynamics
- valuation narratives
- institutional investor thinking

                                        
Your task is to write a professional daily South African market newsletter.

============================================================
MARKET DATA + NEWS CONTEXT
============================================================

{context}

============================================================
NEWSLETTER STRUCTURE
============================================================

Use proper markdown formatting: ## for section headers, **bold** for key figures and stock names.
When referencing a JSE ticker (e.g. SBK, NPN), always bold it like **SBK**.

Include:

## 1. Market Snapshot
2-3 sentences summarising the day.

## 2. What Drove Today's Moves
1-2 paragraphs explaining the why behind price action.

## 3. Mining & Resources
1-2 paragraphs on the sector.

## 4. Banking Sector
1-2 paragraphs on the sector.

## 5. Bond Yields
1-2 sentences on R2030 and R2036 yields from the context.

## 6. ZARONIA & Foreign Currencies
1-2 sentences on ZARONIA, ZAR/USD, ZAR/GBP, ZAR/EUR from the context.

## 7. Stories to Watch
Two relevant summarised stories from the articles given to you (Moneyweb, Daily Investor, BusinessLive).
Both must have a URL. If no URL exists for a story, skip it.
Do not make up stories not in the context.

## 8. Sources
List all URLs used.

============================================================
STYLE
============================================================

- Institutional fund manager tone
- Analytical, forward-looking, concise
- Reference specific stocks, tickers, and figures
- Explain WHY markets moved
- Do not guess — only use what is in the context
- 800-900 words
- You have yesterday's newsletter. Try to not talk about the same topic twice unless its necessary.
                                                                                    
""")

    chain = prompt | llm | StrOutputParser()

    print("\nGenerating newsletter...\n")
    result = chain.invoke({"context": context})
    print(result)

    # =========================================
    # STEP 4 — Save markdown
    # =========================================
    with open("newsletter.md", "w", encoding="utf-8") as f:
        f.write(result)

    with open("newsletter.txt", "w", encoding="utf-8") as f:
        f.write(result)
        

    # =========================================
    # STEP 5 — Convert to HTML
    # =========================================
    html_body = markdown.markdown(result, extensions=["tables", "nl2br"])

    # =========================================
    # STEP 6 — Inject charts after ticker mentions
    # =========================================
    if charts:
        html_body = inject_charts_into_html(html_body, charts)

    html_full = f"""
    <html>
    <head>
        <style>
            body {{
                font-family: Georgia, serif;
                max-width: 680px;
                margin: 0 auto;
                padding: 24px;
                color: #1a1a1a;
                line-height: 1.7;
                background: #ffffff;
            }}
            h1 {{
                color: #0f1117;
                font-size: 1.5em;
                border-bottom: 2px solid #0f1117;
                padding-bottom: 8px;
            }}
            h2 {{
                color: #1a1a2e;
                font-size: 1.05em;
                margin-top: 28px;
                border-bottom: 1px solid #e0e0e0;
                padding-bottom: 4px;
            }}
            strong {{ color: #000; }}
            a {{ color: #1a5276; }}
            p {{ margin: 10px 0; }}
            img {{ display: block; margin: 12px 0; }}
        </style>
    </head>
    <body>
        <h1>Daily Market Newsletter</h1>
        {html_body}
    </body>
    </html>
    """

    with open("newsletter.html", "w", encoding="utf-8") as f:
        f.write(html_full)

    print("DONE: newsletter.md and newsletter.html saved")
    return html_full


if __name__ == "__main__":
    generate_newsletter()

