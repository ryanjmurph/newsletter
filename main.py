from stockPrices import generate_stock_prices
from stockNews import generate_stock_news
from vectorStorage import build_vector_store
from rag import generate_newsletter
from emailer import send_newsletter

def main():

    print("STEP 1: Scraping news...")
    generate_stock_news()

    print("STEP 2: Fetching prices...")
    generate_stock_prices()

    print("STEP 3: Building vector DB...")
    build_vector_store()

    print("STEP 4: Generating newsletter...")
    generate_newsletter()
    
    print("STEP 5: Sending Email...")
    send_newsletter()

    print("DONE.")

if __name__ == "__main__":
    main()