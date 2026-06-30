import streamlit as st
from router import router
from faq import ingest_faq_data, faq_chain
from sql import sql_chain, scrape_and_populate_db
import sqlite3
import pandas as pd
from pathlib import Path

faqs_path = Path(__file__).parent / "Resources/FAQ.csv"
ingest_faq_data(faqs_path)

def ask(query):
    route = router(query).name
    if route == 'faq':
        return faq_chain(query)
    else:
        # Default all other queries (sql or unmatched) to the SQL/product chain
        return sql_chain(query)

# Sidebar Layout - Live Scraper & Database Inspector
st.sidebar.title("E-commerce Control Center")

st.sidebar.header("Flipkart Live Scraper")
st.sidebar.write("Scrape and load any product category from Flipkart directly into the database.")
sync_category = st.sidebar.text_input("Search Term:", value="laptops")
sync_limit = st.sidebar.slider("Products to scrape:", min_value=5, max_value=30, value=10, step=5)

if st.sidebar.button("Scrape & Populate"):
    with st.sidebar.status(f"Scraping '{sync_category}' from Flipkart...", expanded=True) as status:
        try:
            num_inserted = scrape_and_populate_db(sync_category, sync_limit)
            if num_inserted > 0:
                status.update(label=f"Successfully loaded {num_inserted} products!", state="complete")
            else:
                status.update(label="Scraping returned no products. Try another keyword.", state="error")
        except Exception as e:
            status.update(label=f"Scraping failed: {e}", state="error")

st.sidebar.markdown("---")

st.sidebar.header("Database Catalog")
try:
    db_path = Path(__file__).parent / "db.sqlite"
    with sqlite3.connect(db_path) as conn:
        df_db = pd.read_sql_query("SELECT brand, title, price, avg_rating FROM product", conn)
    if not df_db.empty:
        st.sidebar.write(f"Currently storing **{len(df_db)}** products:")
        st.sidebar.dataframe(df_db, use_container_width=True)
    else:
        st.sidebar.info("Database is currently empty.")
except Exception as e:
    st.sidebar.error(f"Could not load database view: {e}")

st.sidebar.markdown("---")
if st.sidebar.button("Clear Chat History"):
    st.session_state["messages"] = []
    st.rerun()

st.title("E-commerce chatbot")


query = st.chat_input("Ask me anything about our products, shipping, or policies!")
if "messages" not in st.session_state:
    st.session_state["messages"]=[]
for message in st.session_state.messages:
    with st.chat_message(message['role']):
        st.markdown(message['content'])
if query:
    with st.chat_message("User"):
        st.markdown(query)
    st.session_state.messages.append({"role": "user","content":query})
    response=ask(query)
    with st.chat_message("Assistant"):
        st.markdown(response)
    st.session_state.messages.append({"role": "assistant","content":response})
