"""
Streamlit Dashboard for Cybersecurity News Aggregator
"""
import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

# Configuration
API_URL = "http://localhost:8000"
st.set_page_config(
    page_title="Cyber Radar - Security News Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .article-card {
        background-color: #ffffff;
        padding: 1.5rem;
        border-radius: 0.5rem;
        border: 1px solid #e0e0e0;
        margin-bottom: 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .category-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 1rem;
        font-size: 0.85rem;
        font-weight: 600;
        margin-right: 0.5rem;
    }
    .vulnerability { background-color: #ff4b4b; color: white; }
    .threat { background-color: #ffa500; color: white; }
    .breach { background-color: #dc143c; color: white; }
    .malware { background-color: #8b0000; color: white; }
    .news { background-color: #1f77b4; color: white; }
    .other { background-color: #808080; color: white; }
</style>
""", unsafe_allow_html=True)


# Helper Functions
@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_articles(limit=100, search=None, source=None, category=None, start_date=None):
    """Fetch articles from API"""
    try:
        params = {'limit': limit}
        if search:
            params['search'] = search
        if source:
            params['source'] = source
        if category:
            params['category'] = category
        if start_date:
            params['start_date'] = start_date.strftime('%Y-%m-%d')
        
        response = requests.get(f"{API_URL}/api/v1/vulnerabilities", params=params, timeout=40)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        st.error("Cannot connect to API. Make sure the server is running!")
        st.code("python run.py", language="bash")
        return None
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return None


@st.cache_data(ttl=300)
def get_statistics():
    """Fetch statistics from API"""
    try:
        response = requests.get(f"{API_URL}/api/v1/stats", timeout=30)
        response.raise_for_status()
        return response.json()
    except:
        return None


@st.cache_data(ttl=300)
def get_sources():
    """Fetch available sources"""
    try:
        response = requests.get(f"{API_URL}/api/v1/sources", timeout=30)
        response.raise_for_status()
        return response.json()
    except:
        return []


@st.cache_data(ttl=300)
def get_categories():
    """Fetch available categories"""
    try:
        response = requests.get(f"{API_URL}/api/v1/categories", timeout=30)
        response.raise_for_status()
        return response.json()
    except:
        return []


def trigger_scrape():
    """Trigger manual scraping"""
    try:
        response = requests.post(f"{API_URL}/api/v1/scrape", timeout=120)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Error triggering scrape: {e}")
        return None


def format_category_badge(category):
    """Format category as HTML badge"""
    return f'<span class="category-badge {category}">{category.upper()}</span>'


def display_article_card(article):
    """Display article in a card format"""
    published = datetime.fromisoformat(article['published'].replace('Z', '+00:00'))
    time_ago = get_time_ago(published)
    
    st.markdown(f"""
    <div class="article-card">
        <h3>{article['title']}</h3>
        <p>
            {format_category_badge(article['category'])}
            <strong>Source:</strong> {article['source']} | 
            <strong>Published:</strong> {time_ago}
        </p>
        <p>{article['description'][:300]}...</p>
        <a href="{article['link']}" target="_blank">Read Full Article</a>
    </div>
    """, unsafe_allow_html=True)


def get_time_ago(dt):
    """Get human-readable time ago"""
    now = datetime.now(dt.tzinfo)
    diff = now - dt
    
    if diff.days > 0:
        return f"{diff.days} day{'s' if diff.days > 1 else ''} ago"
    elif diff.seconds >= 3600:
        hours = diff.seconds // 3600
        return f"{hours} hour{'s' if hours > 1 else ''} ago"
    elif diff.seconds >= 60:
        minutes = diff.seconds // 60
        return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
    else:
        return "Just now"


# Main Dashboard
def main():
    # Header
    st.markdown('<h1 class="main-header">Cyber Radar</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center; font-size: 1.2rem; color: #666;">Real-time Cybersecurity News Aggregator</p>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        # st.image("https://cdn-icons-png.flaticon.com/512/6195/6195699.png", width=100)
        st.title("Controls")
        
        # Manual scrape button
        st.markdown("### Manual Scrape")
        if st.button("Scrape Now", type="primary", use_container_width=True):
            with st.spinner("Scraping feeds..."):
                result = trigger_scrape()
                if result:
                    st.success(f"Added {result['new_articles']} new articles!")
                    st.cache_data.clear()
                    st.rerun()
        
        st.markdown("---")
        
        # Filters
        st.markdown("### 🔍 Filters")
        
        search_query = st.text_input("🔎 Search", placeholder="Enter keyword...")
        
        sources = get_sources()
        selected_source = st.selectbox("📰 Source", ["All"] + sources)
        
        categories = get_categories()
        selected_category = st.selectbox("🏷️ Category", ["All"] + categories)
        
        date_filter = st.selectbox("📅 Date Range", 
                                   ["Today", "Last 2 Days", "Last Week", "All Time"])
        
        limit = st.slider("📊 Number of Articles", 10, 500, 100, 10)
        
        st.markdown("---")
        
        # Statistics
        stats = get_statistics()
        if stats:
            st.markdown("### System Stats")
            st.metric("Total Articles", stats['database']['total_articles'])
            if stats['scheduler']['last_scrape']:
                last_scrape = datetime.fromisoformat(stats['scheduler']['last_scrape'])
                st.caption(f"Last scrape: {get_time_ago(last_scrape)}")
    
    # Calculate date filter
    start_date = None
    if date_filter == "Today":
        start_date = datetime.now().replace(hour=0, minute=0, second=0)
    elif date_filter == "Last 2 Days":
        start_date = datetime.now() - timedelta(days=2)
    elif date_filter == "Last Week":
        start_date = datetime.now() - timedelta(days=7)
    
    # Fetch articles
    data = get_articles(
        limit=limit,
        search=search_query if search_query else None,
        source=selected_source if selected_source != "All" else None,
        category=selected_category if selected_category != "All" else None,
        start_date=start_date
    )
    
    if not data:
        st.stop()
    
    articles = data['articles']
    total = data['total']
    
    # Overview Metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📰 Total Articles", total)
    
    with col2:
        sources_count = len(set(a['source'] for a in articles))
        st.metric("📡 Sources", sources_count)
    
    with col3:
        today_count = sum(1 for a in articles 
                         if datetime.fromisoformat(a['published'].replace('Z', '+00:00')).date() == datetime.now().date())
        st.metric("📅 Today's Articles", today_count)
    
    with col4:
        vuln_count = sum(1 for a in articles if a['category'] == 'vulnerability')
        st.metric("🛡️ Vulnerabilities", vuln_count)
    
    st.markdown("---")
    
    # Tabs
    tab1, tab2, tab3 = st.tabs(["📰 Articles", "📊 Analytics", "ℹ️ About"])
    
    with tab1:
        st.markdown("### Latest Cybersecurity News")
        
        if not articles:
            st.info("No articles found. Try adjusting your filters.")
        else:
            for article in articles:
                display_article_card(article)
    
    with tab2:
        st.markdown("### 📊 Analytics Dashboard")
        
        if articles:
            df = pd.DataFrame(articles)
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Articles by Source
                st.markdown("#### Articles by Source")
                source_counts = df['source'].value_counts()
                fig = px.pie(values=source_counts.values, 
                           names=source_counts.index,
                           hole=0.4,
                           color_discrete_sequence=px.colors.qualitative.Set3)
                fig.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Articles by Category
                st.markdown("#### Articles by Category")
                category_counts = df['category'].value_counts()
                fig = px.bar(x=category_counts.index, 
                           y=category_counts.values,
                           color=category_counts.index,
                           labels={'x': 'Category', 'y': 'Count'},
                           color_discrete_sequence=px.colors.qualitative.Bold)
                fig.update_layout(showlegend=False)
                st.plotly_chart(fig, use_container_width=True)
            
            # Timeline
            st.markdown("#### Publication Timeline")
            df['published_date'] = pd.to_datetime(df['published']).dt.date
            timeline_data = df.groupby('published_date').size().reset_index(name='count')
            fig = px.line(timeline_data, x='published_date', y='count',
                         markers=True,
                         labels={'published_date': 'Date', 'count': 'Articles'})
            fig.update_traces(line_color='#1f77b4', line_width=3)
            st.plotly_chart(fig, use_container_width=True)
            
            # Top Keywords
            st.markdown("#### Top Keywords in Titles")
            from collections import Counter
            import re
            
            all_words = []
            for title in df['title']:
                words = re.findall(r'\b[A-Za-z]{4,}\b', title.lower())
                all_words.extend(words)
            
            # Remove common words
            stop_words = {'with', 'from', 'that', 'this', 'have', 'been', 'were', 'they', 'their', 'about', 'after', 'more'}
            filtered_words = [w for w in all_words if w not in stop_words]
            
            word_counts = Counter(filtered_words).most_common(15)
            if word_counts:
                words_df = pd.DataFrame(word_counts, columns=['Word', 'Count'])
                fig = px.bar(words_df, x='Count', y='Word', orientation='h',
                           color='Count',
                           color_continuous_scale='Blues')
                fig.update_layout(showlegend=False, yaxis={'categoryorder':'total ascending'})
                st.plotly_chart(fig, use_container_width=True)
    
    with tab3:
        st.markdown("### About Cyber Radar")
        
        st.markdown("""
        **Cyber Radar** is a real-time cybersecurity news aggregator that collects and analyzes 
        security news from multiple trusted sources.
        
        #### Data Sources
        - National Vulnerability Database (NVD)
        - CISA Cybersecurity Advisories
        - SecurityWeek
        - BleepingComputer
        - The Hacker News
        - Krebs on Security
        
        #### Update Schedule
        - Automatic scraping every 24 hours
        - Manual scraping available via sidebar
        - Articles from the last 7 days
        
        #### Categories
        - **Vulnerability**: CVEs and security vulnerabilities
        - **Threat**: Threat actors and campaigns
        - **Breach**: Data breaches and compromises
        - **Malware**: Malware and ransomware
        - **News**: General security news
        - **Other**: Uncategorized articles
        
        #### Technology Stack
        - **Backend**: FastAPI
        - **Scraping**: aiohttp + feedparser
        - **Storage**: CSV
        - **Dashboard**: Streamlit
        - **Visualization**: Plotly
        
        #### API Documentation
        Access the full API documentation at: [http://localhost:8000/docs](http://localhost:8000/docs)
        
        ---
        
        **Version**: 1.0.0  
        **Last Updated**: November 2025
        """)
        
        # System health
        st.markdown("#### System Health")
        health_data = get_statistics()
        if health_data:
            col1, col2 = st.columns(2)
            with col1:
                st.success("API: Online")
                st.info(f"Database: {health_data['database']['total_articles']} articles")
            with col2:
                st.success("Scheduler: Running")
                if health_data['scheduler']['next_scrape']:
                    next_scrape = datetime.fromisoformat(health_data['scheduler']['next_scrape'])
                    st.info(f"Next Scrape: {get_time_ago(next_scrape)}")


if __name__ == "__main__":
    main()