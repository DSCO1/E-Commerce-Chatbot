import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from .env (local dev)
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)
if not os.getenv("GROQ_API_KEY"):
    load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")

# Streamlit Cloud secrets fallback: if .env didn't load, try st.secrets
if not os.getenv("GROQ_API_KEY"):
    try:
        import streamlit as _st
        if hasattr(_st, "secrets"):
            for key in ("GROQ_API_KEY", "GROQ_MODEL"):
                if key in _st.secrets:
                    os.environ[key] = _st.secrets[key]
    except Exception:
        pass

# Force Hugging Face offline mode ONLY if the model is already cached locally.
# On fresh cloud deploys, we need to allow the first download.
_hf_cache = Path.home() / ".cache" / "huggingface" / "hub"
_model_cached = (_hf_cache / "models--sentence-transformers--all-MiniLM-L6-v2").exists()
if _model_cached:
    os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

import importlib
import router
import faq
import sql

# Force reload modules so Streamlit picks up changes in sub-files
importlib.reload(router)
importlib.reload(faq)
importlib.reload(sql)

import streamlit as st
from router import router
from faq import ingest_faq_data, faq_chain
from sql import sql_chain_structured, scrape_and_populate_db, extract_specs_from_title
import sqlite3
import pandas as pd
import altair as alt

# Set Page Config
st.set_page_config(
    page_title="ShopAI - E-Commerce Chatbot",
    page_icon="🛍️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load FAQs
faqs_path = Path(__file__).parent / "Resources/FAQ.csv"
ingest_faq_data(faqs_path)

db_path = Path(__file__).parent / "db.sqlite"

# Helper: Route and get response
def ask(query):
    route = router(query).name
    if route == 'faq':
        return faq_chain(query), []
    else:
        return sql_chain_structured(query)

# Load catalog details
def get_catalog_stats():
    try:
        with sqlite3.connect(db_path) as conn:
            df_db = pd.read_sql_query("SELECT brand, title, price, avg_rating, image_url, product_link FROM product", conn)
            return df_db
    except Exception:
        return pd.DataFrame()

def get_catalog_categories():
    """Fetch all categories and their counts from the category table."""
    try:
        with sqlite3.connect(db_path) as conn:
            df_cats = pd.read_sql_query(
                "SELECT id, name, slug, icon, image, product_count FROM category ORDER BY product_count DESC",
                conn
            )
            return df_cats
    except Exception:
        return pd.DataFrame()

df_db = get_catalog_stats()
total_products = len(df_db) if not df_db.empty else 0

# Image Fallback Mapping
def get_product_image(row):
    img = row.get('image_url', '')
    if img and isinstance(img, str) and img.startswith('http'):
        return img
    
    title = str(row.get('title', '')).lower()
    
    if any(k in title for k in ['pen drive', 'pendrive', 'flash drive', 'usb drive', 'utility drive']):
        return "https://images.unsplash.com/photo-1601524909162-be87252be298?w=400&q=80"
    elif any(k in title for k in ['speaker', 'soundbar', 'headphone', 'earphone', 'headset', 'audio', 'sound']):
        return "https://images.unsplash.com/photo-1545454675-3531b543be5d?w=400&q=80"
    elif any(k in title for k in ['phone', 'smartphone', 'mobile', 'galaxy', 'iphone']):
        return "https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?w=400&q=80"
    elif any(k in title for k in ['laptop', 'notebook', 'macbook', 'expertbook', 'chromebook']):
        return "https://images.unsplash.com/photo-1588872657578-7efd1f1555ed?w=400&q=80"
    elif any(k in title for k in ['tv', 'television', 'led smart', 'qled', 'monitor']):
        return "https://images.unsplash.com/photo-1593305841991-05c297ba4575?w=400&q=80"
    elif any(k in title for k in ['cooler', 'air cooler']):
        return "https://images.unsplash.com/photo-1621905251189-08b45d6a269e?w=400&q=80"
    elif any(k in title for k in ['fan', 'ceiling fan']):
        return "https://images.unsplash.com/photo-1618945209355-6bcfc23d069b?w=400&q=80"
    elif any(k in title for k in ['washing machine', 'washer', 'dryer']):
        return "https://images.unsplash.com/photo-1626806787461-102c1bfaaea1?w=400&q=80"
    elif any(k in title for k in ['fridge', 'refrigerator']):
        return "https://images.unsplash.com/photo-1584622650111-993a426fbf0a?w=400&q=80"
    elif any(k in title for k in ['induction', 'cooktop', 'cooker']):
        return "https://images.unsplash.com/photo-1574269909862-7e1d70bb8078?w=400&q=80"
    elif any(k in title for k in ['shoes', 'shoe', 'sneaker']):
        return "https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=400&q=80"
    elif any(k in title for k in ['watch', 'smartwatch']):
        return "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=400&q=80"
    
    return "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=400&q=80"

# Set Default Page State
if "active_page" not in st.session_state:
    st.session_state["active_page"] = "Chat"

# Handle Query Parameters
if "category" in st.query_params:
    st.session_state["active_page"] = "All Products"
    st.session_state["filter_category"] = st.query_params["category"]
    st.query_params.clear()

# Inject Global Premium Stylesheet
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700&family=Inter:wght@400;500;600&display=swap');
    
    .stApp {
        background-color: #0c0d14;
        font-family: 'Outfit', 'Inter', sans-serif;
        color: #f8fafc;
    }
    
    section[data-testid="stSidebar"] {
        background-color: #0c0d12 !important;
        border-right: 1px solid #1c1d29;
    }
    
    .sidebar-brand {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-top: 10px;
        margin-bottom: 24px;
        font-weight: 700;
        font-size: 24px;
        color: #ffffff;
    }
    .sidebar-brand span { color: #635bff; }
    
    .sidebar-brand-desc {
        font-size: 12px;
        color: #718096;
        margin-top: -24px;
        margin-bottom: 24px;
        font-weight: 500;
    }
    
    .sidebar-header {
        font-size: 11px;
        font-weight: 700;
        color: #4a5568 !important;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-top: 24px;
        margin-bottom: 12px;
    }
    
    /* Style Streamlit Buttons inside Sidebar to look like premium menu items */
    div[data-testid="stSidebar"] div.stButton button {
        display: flex !important;
        align-items: center !important;
        justify-content: flex-start !important;
        background-color: transparent !important;
        border: none !important;
        border-radius: 8px !important;
        color: #a0aec0 !important;
        padding: 10px 14px !important;
        font-size: 14px !important;
        font-weight: 500 !important;
        text-align: left !important;
        width: 100% !important;
        margin-bottom: 4px !important;
        box-shadow: none !important;
        transition: all 0.2s ease !important;
    }
    
    div[data-testid="stSidebar"] div.stButton button:hover {
        background-color: #1a1c2a !important;
        color: #ffffff !important;
    }
    
    /* Wrapper style overrides for Active states */
    .active-menu-btn div.stButton button {
        background-color: #161826 !important;
        color: #ffffff !important;
        border-left: 3px solid #635bff !important;
        border-radius: 0 8px 8px 0 !important;
        padding-left: 11px !important;
    }
    
    .sidebar-stats-card {
        background: #12131a;
        border: 1px solid #1e202c;
        border-radius: 12px;
        padding: 16px;
        margin-top: 30px;
    }
    
    .sidebar-stats-title { font-size: 11px; color: #718096; text-transform: uppercase; }
    .sidebar-stats-value { font-size: 24px; font-weight: 700; color: #ffffff; margin: 4px 0; }
    
    
    .chat-greeting-title {
        font-size: 36px;
        font-weight: 700;
        color: #ffffff;
        margin-bottom: 6px;
    }
    .chat-greeting-title span { color: #635bff; }
    .chat-greeting-subtitle { color: #a0aec0; font-size: 15px; margin-bottom: 30px; }
    
    /* Product Slider */
    .product-carousel {
        display: flex;
        overflow-x: auto;
        gap: 16px;
        padding: 12px 4px;
        scroll-behavior: smooth;
    }
    
    .product-carousel::-webkit-scrollbar { height: 6px; }
    .product-carousel::-webkit-scrollbar-thumb { background-color: #242637; border-radius: 4px; }
    
    .product-card {
        background-color: #12131a;
        border: 1px solid #1e202c;
        border-radius: 12px;
        width: 250px;
        flex-shrink: 0;
        padding: 14px;
        position: relative;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    .product-card:hover { border-color: #635bff; }
    .product-badge {
        position: absolute;
        top: 12px;
        left: 12px;
        background-color: #1c6b48;
        color: #ffffff;
        font-size: 10px;
        font-weight: 600;
        padding: 2px 8px;
        border-radius: 20px;
    }
    .product-favorite-icon {
        position: absolute;
        top: 12px;
        right: 12px;
        color: #a0aec0;
        font-size: 16px;
    }
    .product-image-container {
        height: 140px;
        display: flex;
        align-items: center;
        justify-content: center;
        background-color: #191b26;
        border-radius: 8px;
        overflow: hidden;
        margin-bottom: 12px;
    }
    .product-image { max-height: 100%; max-width: 100%; object-fit: contain; }
    .product-title {
        font-size: 15px;
        font-weight: 600;
        color: #ffffff;
        margin-bottom: 2px;
        display: -webkit-box;
        -webkit-line-clamp: 1;
        -webkit-box-orient: vertical;
        overflow: hidden;
    }
    .product-specs {
        font-size: 12px;
        color: #718096;
        margin-bottom: 8px;
        display: -webkit-box;
        -webkit-line-clamp: 1;
        -webkit-box-orient: vertical;
        overflow: hidden;
    }
    .product-price-row { display: flex; align-items: baseline; gap: 6px; margin-bottom: 8px; }
    .product-price { font-size: 18px; font-weight: 700; color: #38a169; }
    .product-old-price { font-size: 13px; color: #718096; text-decoration: line-through; }
    .product-discount { font-size: 12px; font-weight: 600; color: #38a169; }
    .product-rating { font-size: 12px; color: #d69e2e; margin-bottom: 14px; }
    .product-actions { display: flex; gap: 8px; }
    
    .product-btn-solid {
        flex: 1;
        background-color: #635bff;
        color: white;
        text-align: center;
        padding: 8px 0;
        border-radius: 6px;
        font-size: 12px;
        font-weight: 600;
        text-decoration: none !important;
    }
    .product-btn-outline {
        flex: 1;
        background-color: transparent;
        border: 1px solid #2d3748;
        color: #e2e8f0;
        text-align: center;
        padding: 8px 0;
        border-radius: 6px;
        font-size: 12px;
        font-weight: 600;
        text-decoration: none !important;
    }
    
    .chips-row { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 12px; color: #718096; font-size: 12px; }
    .chip-item {
        background-color: #12131a;
        border: 1px solid #1e202c;
        color: #a0aec0;
        padding: 6px 14px;
        border-radius: 20px;
    }
    
    /* Layout page titles */
    .view-title { font-size: 28px; font-weight: 700; color: #ffffff; margin-bottom: 8px; }
    .view-desc { color: #a0aec0; font-size: 14px; margin-bottom: 24px; }
    
    /* Dashboard view stats cards grid */
    .dashboard-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin-bottom: 24px; }
    .dashboard-stat-card {
        background: #12131a;
        border: 1px solid #1e202c;
        border-radius: 12px;
        padding: 20px;
    }
    .dashboard-stat-label { font-size: 13px; color: #718096; text-transform: uppercase; }
    .dashboard-stat-value { font-size: 32px; font-weight: 700; color: #ffffff; margin-top: 8px; }
    
    /* Premium Chat message delete button */
    div[data-testid="stChatMessage"] div.stButton button {
        background-color: transparent !important;
        border: none !important;
        color: #718096 !important;
        padding: 4px 8px !important;
        font-size: 14px !important;
        box-shadow: none !important;
        min-height: unset !important;
        height: auto !important;
        line-height: 1 !important;
        transition: all 0.2s ease !important;
        margin-top: -6px !important;
    }
    div[data-testid="stChatMessage"] div.stButton button:hover {
        color: #ef4444 !important;
        background-color: #1e1b29 !important;
    }
    
    /* Database Catalog Grid */
    .card-header-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 8px;
    }
    .card-header-title {
        font-size: 16px;
        font-weight: 700;
        color: #ffffff;
        margin: 0;
    }
    .card-header-badge-live {
        background-color: rgba(16, 185, 129, 0.12);
        color: #10b981;
        padding: 3px 8px;
        border-radius: 12px;
        font-size: 11px;
        font-weight: 600;
        display: inline-flex;
        align-items: center;
        gap: 5px;
    }
    .card-header-badge-dot {
        width: 6px;
        height: 6px;
        background-color: #10b981;
        border-radius: 50%;
        display: inline-block;
    }
    .card-header-link {
        font-size: 12px;
        color: #7c3aed !important;
        font-weight: 600;
        text-decoration: none !important;
        transition: color 0.15s ease;
    }
    .card-header-link:hover {
        color: #9061f9 !important;
    }
    
    .catalog-card-grid {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 8px;
        margin-top: 14px;
        margin-bottom: 14px;
        width: 100%;
    }
    .catalog-grid-item {
        background: #12131a;
        border: 1px solid #1e202c;
        border-radius: 8px;
        padding: 8px;
        display: flex;
        align-items: center;
        gap: 8px;
        text-decoration: none !important;
        transition: all 0.2s ease;
        min-width: 0; /* Prevents overflow inside grid cell */
    }
    .catalog-grid-item:hover {
        border-color: #635bff;
        background-color: #161826;
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(99,91,255,0.08);
    }
    .catalog-grid-item-img {
        width: 32px;
        height: 32px;
        border-radius: 6px;
        object-fit: cover;
        flex-shrink: 0;
    }
    .catalog-grid-item-info {
        display: flex;
        flex-direction: column;
        min-width: 0;
        flex: 1; /* Occupy remaining space */
    }
    .catalog-grid-item-title {
        font-size: 12px;
        font-weight: 600;
        color: #ffffff !important;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        line-height: 1.2;
    }
    .catalog-grid-item-count {
        font-size: 10px;
        color: #718096 !important;
        margin-top: 2px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    
    .catalog-view-all-btn {
        display: block;
        width: 100%;
        background: transparent;
        border: 1px solid #2d3748;
        color: #e2e8f0 !important;
        text-align: center;
        padding: 8px 0;
        border-radius: 8px;
        font-size: 13px;
        font-weight: 600;
        text-decoration: none !important;
        transition: all 0.2s ease;
    }
    .catalog-view-all-btn:hover {
        border-color: #4a5568;
        color: #ffffff !important;
        background-color: rgba(255,255,255,0.02);
    }

    /* Mobile and tablet-responsive media query overrides */
    @media (max-width: 768px) {
        .chat-greeting-title {
            font-size: 26px !important;
        }
        .chat-greeting-subtitle {
            font-size: 13px !important;
            margin-bottom: 20px !important;
        }
        .catalog-card-grid {
            grid-template-columns: repeat(auto-fill, minmax(110px, 1fr)) !important;
            gap: 6px !important;
        }
        .catalog-grid-item {
            padding: 6px !important;
            gap: 6px !important;
        }
        .catalog-grid-item-img {
            width: 28px !important;
            height: 28px !important;
        }
        .catalog-grid-item-title {
            font-size: 11px !important;
        }
        .catalog-grid-item-count {
            font-size: 9px !important;
        }
        /* Make product cards responsive on narrow viewports */
        .product-card {
            width: 210px !important;
            padding: 10px !important;
        }
        .product-image-container {
            height: 110px !important;
        }
        .product-price {
            font-size: 16px !important;
        }
        .product-title {
            font-size: 13px !important;
        }
    }
</style>
""", unsafe_allow_html=True)

# Premium sidebar custom separator stylesheet
st.markdown("""
<style>
.right-panel-divider {
    height: 1px !important;
    background-color: #1c1d29 !important;
    margin: 16px 0 !important;
    width: 100% !important;
}
</style>
""", unsafe_allow_html=True)

# ----------------- LEFT SIDEBAR -----------------
with st.sidebar:
    st.markdown("""
        <div class="sidebar-brand">
            🛍️ Shop<span>AI</span>
        </div>
        <div class="sidebar-brand-desc">E-commerce Chatbot</div>
    """, unsafe_allow_html=True)
    
    # Active class selection wrapper
    c_chat = "active-menu-btn" if st.session_state["active_page"] == "Chat" else "custom-menu-btn"
    c_products = "active-menu-btn" if st.session_state["active_page"] == "All Products" else "custom-menu-btn"
    
    st.markdown('<div class="sidebar-header">Browse Catalog</div>', unsafe_allow_html=True)
    
    st.markdown(f'<div class="{c_chat}">', unsafe_allow_html=True)
    if st.button("💬 Chat Agent", key="sb_chat", use_container_width=True):
        st.session_state["active_page"] = "Chat"
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown(f'<div class="{c_products}">', unsafe_allow_html=True)
    if st.button(f"📦 All Products ({total_products})", key="sb_products", use_container_width=True):
        st.session_state["active_page"] = "All Products"
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="right-panel-divider"></div>', unsafe_allow_html=True)
    
    # Section 2: Database Catalog Summary Grid (Dynamic from DB)
    df_categories = get_catalog_categories()
    default_image = "https://images.unsplash.com/photo-1586528116311-ad8dd3c8310d?w=200&q=80"
    total_cat = len(df_categories) if not df_categories.empty else 0
    st.markdown(f"""<div class="sidebar-header">
Database Catalog
<a href="?category=" target="_self" class="card-header-link" style="float: right; text-transform: none; letter-spacing: normal; font-weight: normal; margin-top: 1px;">View all →</a>
</div>
<div style="font-size:12.5px; color:#718096; margin-top:4px; margin-bottom:12px;">
{total_products} items across {total_cat} categories
</div>""", unsafe_allow_html=True)
    
    if "show_all_categories" not in st.session_state:
        st.session_state["show_all_categories"] = False

    # Slice categories based on state
    if not df_categories.empty:
        if st.session_state["show_all_categories"]:
            cats_to_show = df_categories
        else:
            cats_to_show = df_categories.head(10)
    else:
        cats_to_show = pd.DataFrame()

    grid_html = '<div class="catalog-card-grid">'
    if not cats_to_show.empty:
        for _, cat_row in cats_to_show.iterrows():
            cat_name = cat_row['name']
            cat_slug = cat_row['slug']
            cat_image = cat_row['image'] if cat_row['image'] else default_image
            cat_count = cat_row['product_count']
            
            grid_html += f'<a href="?category={cat_slug}" target="_self" class="catalog-grid-item">'
            grid_html += f'<img src="{cat_image}" class="catalog-grid-item-img" alt="{cat_name}">'
            grid_html += '<div class="catalog-grid-item-info">'
            grid_html += f'<div class="catalog-grid-item-title">{cat_name}</div>'
            grid_html += f'<div class="catalog-grid-item-count">{cat_count} items</div>'
            grid_html += '</div></a>'
    grid_html += '</div>'
    
    st.markdown(grid_html, unsafe_allow_html=True)

    # Show more/less toggle button
    if total_cat > 10:
        btn_label = "🔼 Show Less" if st.session_state["show_all_categories"] else f"🔽 Show All ({total_cat} Categories)"
        if st.button(btn_label, key="toggle_cats_btn", use_container_width=True):
            st.session_state["show_all_categories"] = not st.session_state["show_all_categories"]
            st.rerun()
    
    st.markdown(f"""
<a href="?category=" target="_self" class="catalog-view-all-btn">
View All Products ({total_products})
</a>
""", unsafe_allow_html=True)

    st.markdown('<div class="right-panel-divider"></div>', unsafe_allow_html=True)

    # Status widget
    st.markdown(f"""
        <div class="sidebar-stats-card" style="margin-top: 10px;">
            <div class="sidebar-stats-title">Products in DB</div>
            <div class="sidebar-stats-value">{total_products}</div>
            <div style="font-size: 11px; color: #718096; margin-top: 8px;">
                Last Updated<br>
                <span style="color: #38a169; font-weight: 600; display: inline-flex; align-items: center; gap: 4px; margin-top: 2px;">
                    ● Today, 10:30 AM
                </span>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    if st.button("Refresh Stats", use_container_width=True):
        st.rerun()

# ----------------- MAIN PANEL LAYOUT -----------------
col_chat = st.container()

# Initialize message list
if "messages" not in st.session_state:
    st.session_state["messages"] = []

if "delete_msg_idx" in st.session_state and st.session_state["delete_msg_idx"] is not None:
    idx_to_del = st.session_state["delete_msg_idx"]
    if 0 <= idx_to_del < len(st.session_state.messages):
        msg = st.session_state.messages[idx_to_del]
        if msg["role"] == "assistant" and idx_to_del - 1 >= 0 and st.session_state.messages[idx_to_del - 1]["role"] == "user":
            st.session_state.messages.pop(idx_to_del)
            st.session_state.messages.pop(idx_to_del - 1)
        else:
            st.session_state.messages.pop(idx_to_del)
    st.session_state["delete_msg_idx"] = None
    st.rerun()

# ----------------- CENTER PANEL: INTERACTIVE PAGE ROUTING -----------------
with col_chat:
    # Show Download link if export was triggered
    if "export_trigger" in st.session_state and st.session_state["export_trigger"]:
        st.download_button(
            label="📥 Click here to Download products.csv",
            data=st.session_state["export_trigger"],
            file_name="products.csv",
            mime="text/csv",
            key="csv_download_trigger"
        )
        # Clear trigger
        st.session_state["export_trigger"] = None

    active_view = st.session_state["active_page"]

    # 1. Conversational Chat Agent View
    if active_view == "Chat":
        if not st.session_state.messages:
            st.markdown("""
                <div style="margin-top: 20px;">
                    <div class="chat-greeting-title">👋 Hello! I'm <span>ShopAI</span></div>
                    <div class="chat-greeting-subtitle">Ask me anything about products, shipping, or policies.</div>
                </div>
            """, unsafe_allow_html=True)
            
            # Clickable Suggestion Action Cards
            col_s1, col_s2, col_s3, col_s4 = st.columns(4)
            if col_s1.button("💻  Best laptops\nunder ₹60k", key="sug_laptops", use_container_width=True):
                st.session_state.messages.append({"role": "user", "content": "Best laptops under 60000"})
                st.rerun()
            if col_s2.button("📱  Find Samsung\nphones", key="sug_phones", use_container_width=True):
                st.session_state.messages.append({"role": "user", "content": "show me smart phone under 20000 rupee of samsung brand"})
                st.rerun()
            if col_s3.button("🎧  Recommend\nheadphones", key="sug_headphones", use_container_width=True):
                st.session_state.messages.append({"role": "user", "content": "Recommend some good headphones"})
                st.rerun()
            if col_s4.button("🏷️  Today's\nbest deals", key="sug_deals", use_container_width=True):
                st.session_state.messages.append({"role": "user", "content": "show me products with discount greater than 50%"})
                st.rerun()
                
        # Render Chat History
        for idx, msg in enumerate(st.session_state.messages):
            has_response = False
            if msg["role"] == "user" and idx + 1 < len(st.session_state.messages) and st.session_state.messages[idx + 1]["role"] == "assistant":
                has_response = True
                
            with st.chat_message(msg["role"]):
                show_delete = (msg["role"] == "assistant") or (msg["role"] == "user" and not has_response)
                
                col_c, col_d = st.columns([14, 1])
                with col_c:
                    st.markdown(msg["content"])
                with col_d:
                    if show_delete:
                        if st.button("🗑️", key=f"del_msg_{idx}", help="Delete this chat turn"):
                            st.session_state["delete_msg_idx"] = idx
                            st.rerun()
                
                pass
                    
        # Inline Chat Input using Form
        with st.container():
            st.markdown('<div style="margin-top:40px;"></div>', unsafe_allow_html=True)
            
            # Enhanced input bar styles - aggressive selectors for Send button
            st.markdown("""
                <style>
                    /* Form container */
                    div[data-testid="stForm"] {
                        background-color: #12131a !important;
                        border: 1.5px solid #3e445b !important;
                        border-radius: 28px !important;
                        padding: 6px 12px 6px 20px !important;
                        box-shadow: 0 4px 20px rgba(0,0,0,0.3) !important;
                    }
                    div[data-testid="stForm"]:focus-within {
                        border-color: #635bff !important;
                        box-shadow: 0 0 0 1px #635bff, 0 4px 24px rgba(99,91,255,0.15) !important;
                    }
                    div[data-testid="stForm"] > div[data-testid="stVerticalBlock"] {
                        width: 100% !important;
                    }
                    div[data-testid="stForm"] div[data-testid="stHorizontalBlock"] {
                        align-items: center !important;
                        width: 100% !important;
                        gap: 8px !important;
                    }
                    div[data-testid="stForm"] div[data-testid="column"]:first-child {
                        flex: 1 1 auto !important;
                        width: auto !important;
                        max-width: 100% !important;
                    }
                    div[data-testid="stForm"] div[data-testid="column"]:last-child {
                        flex: 0 0 auto !important;
                        width: auto !important;
                        max-width: 100% !important;
                    }
                    /* Remove nested text input boundary and styling */
                    div[data-testid="stForm"] div[data-testid="stTextInput"] label {
                        display: none !important;
                    }
                    div[data-testid="stForm"] div[data-testid="stTextInput"] div[data-testid="stTextInputRootElement"],
                    div[data-testid="stForm"] div[data-testid="stTextInput"] div[data-baseweb="input"],
                    div[data-testid="stForm"] div[data-testid="stTextInput"] div[data-baseweb="base-input"] {
                        background-color: transparent !important;
                        background: transparent !important;
                        border: none !important;
                        box-shadow: none !important;
                        padding: 0 !important;
                    }
                    /* Text input inside form */
                    div[data-testid="stForm"] input[type="text"] {
                        background-color: transparent !important;
                        background: transparent !important;
                        border: none !important;
                        color: #e2e8f0 !important;
                        font-size: 15px !important;
                        padding: 8px 0 !important;
                        font-family: 'Outfit', 'Inter', sans-serif !important;
                        width: 100% !important;
                    }
                    div[data-testid="stForm"] input[type="text"]::placeholder {
                        color: #4a5568 !important;
                    }
                    div[data-testid="stForm"] input[type="text"]:focus {
                        box-shadow: none !important;
                        border: none !important;
                        background: transparent !important;
                        background-color: transparent !important;
                    }
                    /* Voice search button hover reset */
                    #voice-search-btn {
                        transition: all 0.2s ease !important;
                    }
                    /* SEND BUTTON styling */
                    div[data-testid="stForm"] div[data-testid="stFormSubmitButton"] {
                        display: flex !important;
                        justify-content: flex-end !important;
                    }
                    div[data-testid="stForm"] button[data-testid="stBaseButton-secondaryFormSubmit"],
                    div[data-testid="stForm"] div[data-testid="stFormSubmitButton"] button {
                        background-image: linear-gradient(135deg, #7c3aed 0%, #635bff 100%) !important;
                        background-color: transparent !important;
                        background: linear-gradient(135deg, #7c3aed 0%, #635bff 100%) !important;
                        color: white !important;
                        border: none !important;
                        border-radius: 20px !important;
                        padding: 8px 24px !important;
                        font-weight: 600 !important;
                        font-size: 14px !important;
                        font-family: 'Outfit', 'Inter', sans-serif !important;
                        min-height: 38px !important;
                        box-shadow: 0 2px 10px rgba(99,91,255,0.3) !important;
                        transition: all 0.25s ease !important;
                        cursor: pointer !important;
                        letter-spacing: 0.3px !important;
                    }
                    div[data-testid="stForm"] button[data-testid="stBaseButton-secondaryFormSubmit"]:hover,
                    div[data-testid="stForm"] div[data-testid="stFormSubmitButton"] button:hover {
                        background-image: linear-gradient(135deg, #6d28d9 0%, #4f46e5 100%) !important;
                        background-color: transparent !important;
                        background: linear-gradient(135deg, #6d28d9 0%, #4f46e5 100%) !important;
                        box-shadow: 0 6px 20px rgba(99,91,255,0.5) !important;
                        transform: translateY(-1px) !important;
                    }
                </style>
            """, unsafe_allow_html=True)
            
            with st.form("chat_input_form", clear_on_submit=True):
                input_col, send_col = st.columns([15, 2])
                with input_col:
                    user_query = st.text_input(
                        label="Chat input",
                        placeholder="Ask me anything about products...",
                        label_visibility="collapsed"
                    )
                with send_col:
                    submit_button = st.form_submit_button("✦ Send", use_container_width=True)

            
            # Disclaimer
            st.markdown(
                '<div style="text-align:center; color:#4a5568; font-size:12px; margin-top:8px;">'
                'Shop AI can make mistakes. Please verify important information.'
                '</div>',
                unsafe_allow_html=True
            )
            
        if submit_button and user_query:
            st.session_state["voice_input"] = ""
            st.session_state.messages.append({"role": "user", "content": user_query})
            st.rerun()

    # 2. All Products Catalog Explorer
    elif active_view == "All Products":
        st.markdown('<div class="view-title">📦 All Products Catalog</div>', unsafe_allow_html=True)
        st.markdown('<div class="view-desc">Search, filter, and inspect items stored in the SQLite database.</div>', unsafe_allow_html=True)
        
        # Prefill category search filter if selected from catalog card
        default_search = ""
        if "filter_category" in st.session_state and st.session_state["filter_category"]:
            default_search = st.session_state["filter_category"]
            # Clear to allow custom updates
            st.session_state["filter_category"] = ""
            
        search_filter = st.text_input("🔍 Search product title, brand or category...", value=default_search)
        
        if not df_db.empty:
            filtered_df = df_db.copy()
            if search_filter:
                # Check if the filter matches a category slug from the database
                df_cats = get_catalog_categories()
                matched_category_name = None
                if not df_cats.empty:
                    slug_match = df_cats[df_cats['slug'] == search_filter]
                    if not slug_match.empty:
                        matched_category_name = slug_match.iloc[0]['name']
                
                if matched_category_name:
                    # Filter products by their stored category_name
                    try:
                        with sqlite3.connect(db_path) as conn:
                            cat_products = pd.read_sql_query(
                                "SELECT brand, title, price, avg_rating, image_url, product_link FROM product WHERE category_name = ?",
                                conn, params=[matched_category_name]
                            )
                        if not cat_products.empty:
                            filtered_df = cat_products
                        else:
                            filtered_df = filtered_df[
                                filtered_df['title'].str.contains(search_filter, case=False, na=False) |
                                filtered_df['brand'].str.contains(search_filter, case=False, na=False)
                            ]
                    except Exception:
                        filtered_df = filtered_df[
                            filtered_df['title'].str.contains(search_filter, case=False, na=False) |
                            filtered_df['brand'].str.contains(search_filter, case=False, na=False)
                        ]
                else:
                    # Freeform search by title or brand
                    filtered_df = filtered_df[
                        filtered_df['title'].str.contains(search_filter, case=False, na=False) |
                        filtered_df['brand'].str.contains(search_filter, case=False, na=False)
                    ]
            
            st.markdown(f"**Showing {len(filtered_df)} matching products**")
            st.dataframe(
                filtered_df[['brand', 'title', 'price', 'avg_rating', 'product_link']], 
                use_container_width=True,
                column_config={
                    "brand": st.column_config.TextColumn("Brand"),
                    "title": st.column_config.TextColumn("Title"),
                    "price": st.column_config.NumberColumn("Price", format="₹%d"),
                    "avg_rating": st.column_config.NumberColumn("Rating", format="★ %.1f"),
                    "product_link": st.column_config.LinkColumn("Product Link", display_text="Open on Flipkart")
                }
            )
        else:
            st.info("The catalog database is currently empty.")

# Run the response generation (Chat view only)
if st.session_state["active_page"] == "Chat" and st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
    last_query = st.session_state.messages[-1]["content"]
    with col_chat:
        with st.chat_message("assistant"):
            with st.spinner("Analyzing database and live products..."):
                response_text, products = ask(last_query)
                st.markdown(response_text)
                pass
                    
            st.session_state.messages.append({
                "role": "assistant",
                "content": response_text,
                "products": products
            })
            st.rerun()

# Right panel removed - all widgets consolidated in left sidebar
