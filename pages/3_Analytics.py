import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sys
import os

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import DatabaseManager
from utils import (
    create_claim_status_chart, create_food_type_chart, 
    create_provider_type_chart, create_city_distribution_chart,
    create_meal_type_chart, get_expiry_analysis
)

st.set_page_config(page_title="Analytics Dashboard", page_icon="📈", layout="wide")

# Initialize database
@st.cache_resource
def get_database():
    return DatabaseManager()

db = get_database()

st.title("📈 Analytics Dashboard")
st.markdown("Comprehensive data visualization and insights for food waste management")

# Sidebar for analytics options
st.sidebar.title("Analytics Options")
analysis_type = st.sidebar.selectbox(
    "Select Analysis Type:",
    ["Overview Dashboard", "Provider Analysis", "Food Distribution", "Claims Analysis", "Geographic Analysis", "Temporal Analysis"]
)

if analysis_type == "Overview Dashboard":
    st.header("🎯 System Overview")
    
    # Key metrics row
    col1, col2, col3, col4 = st.columns(4)
    
    try:
        # Get key metrics
        total_providers = db.execute_query("SELECT COUNT(*) FROM providers")[0][0]
        total_receivers = db.execute_query("SELECT COUNT(*) FROM receivers")[0][0]
        total_food_items = db.execute_query("SELECT COUNT(*) FROM food_listings")[0][0]
        total_quantity = db.execute_query("SELECT SUM(Quantity) FROM food_listings")[0][0] or 0
        total_claims = db.execute_query("SELECT COUNT(*) FROM claims")[0][0]
        completed_claims = db.execute_query("SELECT COUNT(*) FROM claims WHERE Status = 'Completed'")[0][0]
        
        with col1:
            st.metric("🏪 Total Providers", f"{total_providers:,}")
            st.metric("👥 Total Receivers", f"{total_receivers:,}")
        
        with col2:
            st.metric("🍎 Food Items Listed", f"{total_food_items:,}")
            st.metric("📦 Total Food Quantity", f"{total_quantity:,}")
        
        with col3:
            st.metric("📋 Total Claims", f"{total_claims:,}")
            completion_rate = (completed_claims / total_claims * 100) if total_claims > 0 else 0
            st.metric("✅ Completion Rate", f"{completion_rate:.1f}%")
        
        with col4:
            # Calculate waste reduction estimate
            claimed_quantity = db.execute_query("""
                SELECT SUM(fl.Quantity) 
                FROM food_listings fl 
                JOIN claims c ON fl.Food_ID = c.Food_ID 
                WHERE c.Status = 'Completed'
            """)[0][0] or 0
            
            waste_reduction = (claimed_quantity / total_quantity * 100) if total_quantity > 0 else 0
            st.metric("♻️ Waste Reduction", f"{waste_reduction:.1f}%")
            st.metric("🍽️ Food Rescued", f"{claimed_quantity:,} units")
        
        # Charts row
        col1, col2 = st.columns(2)
        
        with col1:
            # Claim status distribution
            fig = create_claim_status_chart(db)
            if fig:
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Food type distribution
            fig = create_food_type_chart(db)
            if fig:
                st.plotly_chart(fig, use_container_width=True)
        
        # Provider type analysis
        st.subheader("📊 Provider Type Analysis")
        fig = create_provider_type_chart(db)
        if fig:
            st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        st.error(f"Error loading overview data: {str(e)}")

elif analysis_type == "Provider Analysis":
    st.header("🏪 Provider Analysis")
    
    try:
        # Provider type distribution
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Provider Type Distribution")
            provider_types = db.execute_query("""
                SELECT Type, COUNT(*) as count 
                FROM providers 
                GROUP BY Type
            """)
            
            if provider_types:
                df = pd.DataFrame(provider_types, columns=['Type', 'Count'])
                fig = px.pie(df, values='Count', names='Type', title='Providers by Type')
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("Top Contributing Providers")
            top_providers = db.execute_query("""
                SELECT p.Name, p.Type, SUM(fl.Quantity) as total_quantity
                FROM providers p
                JOIN food_listings fl ON p.Provider_ID = fl.Provider_ID
                GROUP BY p.Provider_ID, p.Name, p.Type
                ORDER BY total_quantity DESC
                LIMIT 10
            """)
            
            if top_providers:
                df = pd.DataFrame(top_providers, columns=['Provider', 'Type', 'Total_Quantity'])
                fig = px.bar(df, x='Provider', y='Total_Quantity', color='Type',
                           title='Top 10 Providers by Food Quantity')
                fig.update_xaxes(tickangle=45)
                st.plotly_chart(fig, use_container_width=True)
        
        # City-wise provider distribution
        st.subheader("📍 Geographic Distribution of Providers")
        city_providers = db.execute_query("""
            SELECT City, COUNT(*) as provider_count
            FROM providers
            GROUP BY City
            ORDER BY provider_count DESC
            LIMIT 20
        """)
        
        if city_providers:
            df = pd.DataFrame(city_providers, columns=['City', 'Provider_Count'])
            fig = px.bar(df, x='City', y='Provider_Count',
                       title='Top 20 Cities by Number of Providers')
            fig.update_xaxes(tickangle=45)
            st.plotly_chart(fig, use_container_width=True)
        
        # Provider performance analysis
        st.subheader("🎯 Provider Performance Analysis")
        provider_performance = db.execute_query("""
            SELECT 
                p.Name,
                p.Type,
                COUNT(fl.Food_ID) as total_listings,
                SUM(fl.Quantity) as total_quantity,
                COUNT(c.Claim_ID) as total_claims,
                COUNT(CASE WHEN c.Status = 'Completed' THEN 1 END) as completed_claims
            FROM providers p
            LEFT JOIN food_listings fl ON p.Provider_ID = fl.Provider_ID
            LEFT JOIN claims c ON fl.Food_ID = c.Food_ID
            GROUP BY p.Provider_ID, p.Name, p.Type
            HAVING total_listings > 0
            ORDER BY completed_claims DESC
            LIMIT 15
        """)
        
        if provider_performance:
            df = pd.DataFrame(provider_performance, columns=[
                'Provider', 'Type', 'Total_Listings', 'Total_Quantity', 
                'Total_Claims', 'Completed_Claims'
            ])
            
            # Calculate success rate
            df['Success_Rate'] = (df['Completed_Claims'] / df['Total_Claims'] * 100).fillna(0)
            
            st.dataframe(df, use_container_width=True)
        
    except Exception as e:
        st.error(f"Error loading provider analysis: {str(e)}")

elif analysis_type == "Food Distribution":
    st.header("🍽️ Food Distribution Analysis")
    
    try:
        # Food type and meal type analysis
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Food Type Distribution")
            food_types = db.execute_query("""
                SELECT Food_Type, COUNT(*) as count, SUM(Quantity) as total_quantity
                FROM food_listings
                GROUP BY Food_Type
            """)
            
            if food_types:
                df = pd.DataFrame(food_types, columns=['Food_Type', 'Count', 'Total_Quantity'])
                fig = px.bar(df, x='Food_Type', y='Total_Quantity',
                           title='Total Food Quantity by Type')
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Meal type chart
            fig = create_meal_type_chart(db)
            if fig:
                st.plotly_chart(fig, use_container_width=True)
        
        # Most popular food items
        st.subheader("🏆 Most Popular Food Items")
        popular_foods = db.execute_query("""
            SELECT 
                fl.Food_Name,
                fl.Food_Type,
                COUNT(c.Claim_ID) as claim_count,
                SUM(fl.Quantity) as total_quantity_available
            FROM food_listings fl
            LEFT JOIN claims c ON fl.Food_ID = c.Food_ID
            GROUP BY fl.Food_Name, fl.Food_Type
            ORDER BY claim_count DESC
            LIMIT 15
        """)
        
        if popular_foods:
            df = pd.DataFrame(popular_foods, columns=[
                'Food_Name', 'Food_Type', 'Claim_Count', 'Total_Quantity_Available'
            ])
            
            fig = px.bar(df, x='Food_Name', y='Claim_Count', color='Food_Type',
                       title='Most Claimed Food Items')
            fig.update_xaxes(tickangle=45)
            st.plotly_chart(fig, use_container_width=True)
            
            st.dataframe(df, use_container_width=True)
        
        # Food expiry analysis
        st.subheader("⏰ Food Expiry Analysis")
        expiry_df = get_expiry_analysis(db)
        
        if not expiry_df.empty:
            fig = px.bar(expiry_df, x='Expiry_Status', y='Total_Quantity',
                       title='Food Quantity by Expiry Status')
            st.plotly_chart(fig, use_container_width=True)
            
            # Show expiry statistics
            col1, col2, col3 = st.columns(3)
            
            expired_items = expiry_df[expiry_df['Expiry_Status'] == 'Expired']['Item_Count'].sum()
            expiring_soon = expiry_df[expiry_df['Expiry_Status'] == 'Expiring Soon']['Item_Count'].sum()
            fresh_items = expiry_df[expiry_df['Expiry_Status'] == 'Fresh']['Item_Count'].sum()
            
            with col1:
                st.metric("🔴 Expired Items", expired_items)
            with col2:
                st.metric("🟡 Expiring Soon", expiring_soon)
            with col3:
                st.metric("🟢 Fresh Items", fresh_items)
    
    except Exception as e:
        st.error(f"Error loading food distribution analysis: {str(e)}")

elif analysis_type == "Claims Analysis":
    st.header("📋 Claims Analysis")
    
    try:
        # Claims overview
        col1, col2, col3 = st.columns(3)
        
        pending_claims = db.execute_query("SELECT COUNT(*) FROM claims WHERE Status = 'Pending'")[0][0]
        completed_claims = db.execute_query("SELECT COUNT(*) FROM claims WHERE Status = 'Completed'")[0][0]
        cancelled_claims = db.execute_query("SELECT COUNT(*) FROM claims WHERE Status = 'Cancelled'")[0][0]
        
        with col1:
            st.metric("⏳ Pending Claims", pending_claims)
        with col2:
            st.metric("✅ Completed Claims", completed_claims)
        with col3:
            st.metric("❌ Cancelled Claims", cancelled_claims)
        
        # Claims by receiver type
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Claims by Receiver Type")
            receiver_claims = db.execute_query("""
                SELECT r.Type, COUNT(c.Claim_ID) as claim_count
                FROM receivers r
                JOIN claims c ON r.Receiver_ID = c.Receiver_ID
                GROUP BY r.Type
                ORDER BY claim_count DESC
            """)
            
            if receiver_claims:
                df = pd.DataFrame(receiver_claims, columns=['Receiver_Type', 'Claim_Count'])
                fig = px.pie(df, values='Claim_Count', names='Receiver_Type',
                           title='Claims Distribution by Receiver Type')
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("Top Claiming Receivers")
            top_receivers = db.execute_query("""
                SELECT r.Name, r.Type, COUNT(c.Claim_ID) as claim_count
                FROM receivers r
                JOIN claims c ON r.Receiver_ID = c.Receiver_ID
                GROUP BY r.Receiver_ID, r.Name, r.Type
                ORDER BY claim_count DESC
                LIMIT 10
            """)
            
            if top_receivers:
                df = pd.DataFrame(top_receivers, columns=['Receiver', 'Type', 'Claim_Count'])
                fig = px.bar(df, x='Receiver', y='Claim_Count', color='Type',
                           title='Top 10 Receivers by Claims')
                fig.update_xaxes(tickangle=45)
                st.plotly_chart(fig, use_container_width=True)
        
        # Claims success rate by provider
        st.subheader("🎯 Provider Success Rates")
        provider_success = db.execute_query("""
            SELECT 
                p.Name,
                p.Type,
                COUNT(c.Claim_ID) as total_claims,
                COUNT(CASE WHEN c.Status = 'Completed' THEN 1 END) as completed_claims,
                ROUND(COUNT(CASE WHEN c.Status = 'Completed' THEN 1 END) * 100.0 / COUNT(c.Claim_ID), 2) as success_rate
            FROM providers p
            JOIN food_listings fl ON p.Provider_ID = fl.Provider_ID
            JOIN claims c ON fl.Food_ID = c.Food_ID
            GROUP BY p.Provider_ID, p.Name, p.Type
            HAVING total_claims >= 5
            ORDER BY success_rate DESC
            LIMIT 15
        """)
        
        if provider_success:
            df = pd.DataFrame(provider_success, columns=[
                'Provider', 'Type', 'Total_Claims', 'Completed_Claims', 'Success_Rate'
            ])
            
            fig = px.bar(df, x='Provider', y='Success_Rate', color='Type',
                       title='Provider Success Rates (Providers with 5+ claims)')
            fig.update_xaxes(tickangle=45)
            fig.update_yaxes(title='Success Rate (%)')
            st.plotly_chart(fig, use_container_width=True)
            
            st.dataframe(df, use_container_width=True)
    
    except Exception as e:
        st.error(f"Error loading claims analysis: {str(e)}")

elif analysis_type == "Geographic Analysis":
    st.header("🗺️ Geographic Analysis")
    
    try:
        # City-wise distribution
        fig = create_city_distribution_chart(db)
        if fig:
            st.plotly_chart(fig, use_container_width=True)
        
        # Detailed city analysis
        st.subheader("📊 City-wise Detailed Analysis")
        city_analysis = db.execute_query("""
            SELECT 
                COALESCE(p.City, r.City, fl.Location) as City,
                COUNT(DISTINCT p.Provider_ID) as providers,
                COUNT(DISTINCT r.Receiver_ID) as receivers,
                COUNT(DISTINCT fl.Food_ID) as food_listings,
                SUM(fl.Quantity) as total_food_quantity,
                COUNT(DISTINCT c.Claim_ID) as total_claims
            FROM providers p
            FULL OUTER JOIN receivers r ON p.City = r.City
            FULL OUTER JOIN food_listings fl ON COALESCE(p.City, r.City) = fl.Location
            LEFT JOIN claims c ON fl.Food_ID = c.Food_ID
            GROUP BY COALESCE(p.City, r.City, fl.Location)
            ORDER BY total_food_quantity DESC NULLS LAST
            LIMIT 20
        """)
        
        # Modified query for SQLite
        city_analysis = db.execute_query("""
            SELECT 
                City,
                SUM(providers) as providers,
                SUM(receivers) as receivers,
                SUM(food_listings) as food_listings,
                SUM(total_food_quantity) as total_food_quantity,
                SUM(total_claims) as total_claims
            FROM (
                SELECT City, COUNT(*) as providers, 0 as receivers, 0 as food_listings, 0 as total_food_quantity, 0 as total_claims
                FROM providers GROUP BY City
                UNION ALL
                SELECT City, 0 as providers, COUNT(*) as receivers, 0 as food_listings, 0 as total_food_quantity, 0 as total_claims
                FROM receivers GROUP BY City
                UNION ALL
                SELECT Location as City, 0 as providers, 0 as receivers, COUNT(*) as food_listings, SUM(Quantity) as total_food_quantity, 0 as total_claims
                FROM food_listings GROUP BY Location
                UNION ALL
                SELECT fl.Location as City, 0 as providers, 0 as receivers, 0 as food_listings, 0 as total_food_quantity, COUNT(*) as total_claims
                FROM claims c JOIN food_listings fl ON c.Food_ID = fl.Food_ID GROUP BY fl.Location
            )
            GROUP BY City
            ORDER BY total_food_quantity DESC
            LIMIT 20
        """)
        
        if city_analysis:
            df = pd.DataFrame(city_analysis, columns=[
                'City', 'Providers', 'Receivers', 'Food_Listings', 'Total_Food_Quantity', 'Total_Claims'
            ])
            
            st.dataframe(df, use_container_width=True)
            
            # Calculate efficiency metrics
            df['Efficiency_Score'] = ((df['Total_Claims'] / df['Food_Listings']) * 100).fillna(0)
            
            fig = px.scatter(df, x='Food_Listings', y='Total_Claims', 
                           size='Total_Food_Quantity', color='Efficiency_Score',
                           hover_name='City',
                           title='City Efficiency: Food Listings vs Claims')
            st.plotly_chart(fig, use_container_width=True)
    
    except Exception as e:
        st.error(f"Error loading geographic analysis: {str(e)}")

elif analysis_type == "Temporal Analysis":
    st.header("📅 Temporal Analysis")
    
    try:
        # Claims timeline
        st.subheader("📈 Claims Timeline")
        claims_timeline = db.execute_query("""
            SELECT 
                date(Timestamp) as claim_date,
                Status,
                COUNT(*) as count
            FROM claims
            WHERE Timestamp IS NOT NULL
            GROUP BY date(Timestamp), Status
            ORDER BY claim_date
        """)
        
        if claims_timeline:
            df = pd.DataFrame(claims_timeline, columns=['Date', 'Status', 'Count'])
            
            fig = px.line(df, x='Date', y='Count', color='Status',
                         title='Daily Claims by Status')
            st.plotly_chart(fig, use_container_width=True)
        
        # Monthly trends
        st.subheader("📊 Monthly Trends")
        monthly_trends = db.execute_query("""
            SELECT 
                strftime('%Y-%m', Timestamp) as month,
                COUNT(*) as total_claims,
                COUNT(CASE WHEN Status = 'Completed' THEN 1 END) as completed_claims,
                COUNT(CASE WHEN Status = 'Pending' THEN 1 END) as pending_claims,
                COUNT(CASE WHEN Status = 'Cancelled' THEN 1 END) as cancelled_claims
            FROM claims
            WHERE Timestamp IS NOT NULL
            GROUP BY strftime('%Y-%m', Timestamp)
            ORDER BY month
        """)
        
        if monthly_trends:
            df = pd.DataFrame(monthly_trends, columns=[
                'Month', 'Total_Claims', 'Completed_Claims', 'Pending_Claims', 'Cancelled_Claims'
            ])
            
            # Create subplots
            fig = make_subplots(
                rows=2, cols=1,
                subplot_titles=('Total Claims by Month', 'Claims Status Distribution by Month'),
                vertical_spacing=0.1
            )
            
            # Total claims
            fig.add_trace(
                go.Bar(x=df['Month'], y=df['Total_Claims'], name='Total Claims'),
                row=1, col=1
            )
            
            # Status distribution
            fig.add_trace(
                go.Bar(x=df['Month'], y=df['Completed_Claims'], name='Completed'),
                row=2, col=1
            )
            fig.add_trace(
                go.Bar(x=df['Month'], y=df['Pending_Claims'], name='Pending'),
                row=2, col=1
            )
            fig.add_trace(
                go.Bar(x=df['Month'], y=df['Cancelled_Claims'], name='Cancelled'),
                row=2, col=1
            )
            
            fig.update_layout(height=600, title_text="Claims Temporal Analysis")
            st.plotly_chart(fig, use_container_width=True)
            
            # Show monthly statistics
            st.dataframe(df, use_container_width=True)
    
    except Exception as e:
        st.error(f"Error loading temporal analysis: {str(e)}")

# Footer with insights
st.markdown("---")
st.markdown("### 💡 Key Insights")

try:
    # Generate some key insights
    total_food = db.execute_query("SELECT SUM(Quantity) FROM food_listings")[0][0] or 0
    rescued_food = db.execute_query("""
        SELECT SUM(fl.Quantity) 
        FROM food_listings fl 
        JOIN claims c ON fl.Food_ID = c.Food_ID 
        WHERE c.Status = 'Completed'
    """)[0][0] or 0
    
    rescue_rate = (rescued_food / total_food * 100) if total_food > 0 else 0
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.info(f"""
        **Food Rescue Impact:**
        - Total food available: {total_food:,} units
        - Food successfully rescued: {rescued_food:,} units
        - Current rescue rate: {rescue_rate:.1f}%
        """)
    
    with col2:
        # Most active city
        most_active_city = db.execute_query("""
            SELECT Location, COUNT(*) as activity_score
            FROM food_listings
            GROUP BY Location
            ORDER BY activity_score DESC
            LIMIT 1
        """)
        
        if most_active_city:
            city_name = most_active_city[0][0]
            activity_score = most_active_city[0][1]
            
            st.info(f"""
            **Most Active Location:**
            - City: {city_name}
            - Food listings: {activity_score}
            - This represents the highest food redistribution activity
            """)

except Exception as e:
    st.error(f"Error generating insights: {str(e)}")
