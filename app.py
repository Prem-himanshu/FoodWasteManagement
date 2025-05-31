import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from database import DatabaseManager
from utils import load_data, get_summary_stats
import os

# Page configuration
st.set_page_config(
    page_title="Food Waste Management System",
    page_icon="🍽️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize database
@st.cache_resource
def init_database():
    """Initialize database and load data"""
    db = DatabaseManager()
    
    # Check if data files exist in attached_assets folder
    csv_files = {
        'providers': 'attached_assets/providers_data.csv',
        'receivers': 'attached_assets/receivers_data.csv',
        'food_listings': 'attached_assets/food_listings_data.csv',
        'claims': 'attached_assets/claims_data.csv'
    }
    
    # Load data if files exist
    all_exist = all(os.path.exists(file) for file in csv_files.values())
    
    if all_exist:
        try:
            providers_df = pd.read_csv(csv_files['providers'])
            receivers_df = pd.read_csv(csv_files['receivers'])
            food_listings_df = pd.read_csv(csv_files['food_listings'])
            claims_df = pd.read_csv(csv_files['claims'])
            
            # Load data into database
            db.load_data(providers_df, receivers_df, food_listings_df, claims_df)
            st.success("✅ Data loaded successfully into database!")
        except Exception as e:
            st.error(f"❌ Error loading data: {str(e)}")
    else:
        st.warning("⚠️ CSV data files not found. Please ensure all CSV files are in the attached_assets folder.")
    
    return db

# Initialize the database
db = init_database()

# Main title and description
st.title("🍽️ Local Food Wastage Management System")
st.markdown("""
### Connecting Food Providers with Those in Need

This system helps reduce food waste by facilitating the redistribution of surplus food from restaurants, 
grocery stores, and other providers to NGOs, shelters, and individuals in need.
""")

# Sidebar navigation
st.sidebar.title("Navigation")
st.sidebar.markdown("Use the pages in the sidebar to explore different features:")
st.sidebar.markdown("- **Data Management**: CRUD operations")
st.sidebar.markdown("- **SQL Queries**: Execute analytical queries")
st.sidebar.markdown("- **Analytics**: Data visualizations")
st.sidebar.markdown("- **Directory**: Provider/Receiver contacts")

# Main dashboard content
col1, col2, col3, col4 = st.columns(4)

try:
    # Get summary statistics
    stats = get_summary_stats(db)
    
    with col1:
        st.metric(
            label="🏪 Total Providers",
            value=stats['total_providers'],
            help="Total number of registered food providers"
        )
    
    with col2:
        st.metric(
            label="👥 Total Receivers",
            value=stats['total_receivers'],
            help="Total number of registered food receivers"
        )
    
    with col3:
        st.metric(
            label="🍎 Food Listings",
            value=stats['total_food_listings'],
            help="Total number of available food listings"
        )
    
    with col4:
        st.metric(
            label="📋 Total Claims",
            value=stats['total_claims'],
            help="Total number of food claims made"
        )

except Exception as e:
    st.error(f"Error loading summary statistics: {str(e)}")
    # Display empty metrics if data loading fails
    with col1:
        st.metric("🏪 Total Providers", "0")
    with col2:
        st.metric("👥 Total Receivers", "0")
    with col3:
        st.metric("🍎 Food Listings", "0")
    with col4:
        st.metric("📋 Total Claims", "0")

# Dashboard charts
st.markdown("## 📊 Quick Insights")

try:
    # Claims status distribution
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📈 Claims Status Distribution")
        claims_status = db.execute_query("""
            SELECT Status, COUNT(*) as count 
            FROM claims 
            GROUP BY Status
        """)
        
        if claims_status:
            status_df = pd.DataFrame(claims_status, columns=['Status', 'Count'])
            fig = px.pie(
                status_df, 
                values='Count', 
                names='Status',
                title="Distribution of Claim Status"
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No claims data available")
    
    with col2:
        st.subheader("🍽️ Food Types Distribution")
        food_types = db.execute_query("""
            SELECT Food_Type, COUNT(*) as count 
            FROM food_listings 
            GROUP BY Food_Type
        """)
        
        if food_types:
            food_df = pd.DataFrame(food_types, columns=['Food_Type', 'Count'])
            fig = px.bar(
                food_df, 
                x='Food_Type', 
                y='Count',
                title="Available Food by Type"
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No food listings data available")

    # Recent activity
    st.subheader("🕒 Recent Food Listings")
    recent_listings = db.execute_query("""
        SELECT fl.Food_Name, fl.Quantity, fl.Food_Type, fl.Meal_Type, 
               fl.Location, p.Name as Provider_Name
        FROM food_listings fl
        JOIN providers p ON fl.Provider_ID = p.Provider_ID
        ORDER BY fl.Food_ID DESC
        LIMIT 10
    """)
    
    if recent_listings:
        recent_df = pd.DataFrame(recent_listings, columns=[
            'Food Name', 'Quantity', 'Food Type', 'Meal Type', 'Location', 'Provider'
        ])
        st.dataframe(recent_df, use_container_width=True)
    else:
        st.info("No recent listings available")

except Exception as e:
    st.error(f"Error loading dashboard data: {str(e)}")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center'>
<p><strong>Local Food Wastage Management System</strong></p>
<p>Reducing food waste, one meal at a time 🌱</p>
</div>
""", unsafe_allow_html=True)
