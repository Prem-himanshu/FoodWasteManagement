import streamlit as st
import pandas as pd
import sys
import os

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import DatabaseManager
from utils import get_unique_values, search_and_filter_food

st.set_page_config(page_title="Directory", page_icon="📞", layout="wide")

# Initialize database
@st.cache_resource
def get_database():
    return DatabaseManager()

db = get_database()

st.title("📞 Provider & Receiver Directory")
st.markdown("Find and contact food providers and receivers in your area")

# Sidebar for directory options
st.sidebar.title("Directory Options")
directory_type = st.sidebar.selectbox(
    "Select Directory Type:",
    ["Food Search", "Provider Directory", "Receiver Directory", "Contact Information"]
)

if directory_type == "Food Search":
    st.header("🔍 Search Available Food")
    st.markdown("Search for available food items with filters")
    
    # Search filters
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        cities = get_unique_values(db, "food_listings", "Location")
        selected_city = st.selectbox("City", ["All"] + cities)
    
    with col2:
        provider_types = get_unique_values(db, "providers", "Type")
        selected_provider_type = st.selectbox("Provider Type", ["All"] + provider_types)
    
    with col3:
        food_types = get_unique_values(db, "food_listings", "Food_Type")
        selected_food_type = st.selectbox("Food Type", ["All"] + food_types)
    
    with col4:
        meal_types = get_unique_values(db, "food_listings", "Meal_Type")
        selected_meal_type = st.selectbox("Meal Type", ["All"] + meal_types)
    
    # Additional filters
    col1, col2 = st.columns(2)
    with col1:
        min_quantity = st.number_input("Minimum Quantity", min_value=0, value=0)
    with col2:
        search_term = st.text_input("Search food name")
    
    # Build filter dictionary
    filters = {}
    if selected_city != "All":
        filters['city'] = selected_city
    if selected_provider_type != "All":
        filters['provider_type'] = selected_provider_type
    if selected_food_type != "All":
        filters['food_type'] = selected_food_type
    if selected_meal_type != "All":
        filters['meal_type'] = selected_meal_type
    if min_quantity > 0:
        filters['min_quantity'] = min_quantity
    
    # Search button
    if st.button("🔍 Search Food", type="primary"):
        try:
            results_df = search_and_filter_food(db, filters)
            
            # Apply text search if provided
            if search_term and not results_df.empty:
                mask = results_df['Food_Name'].str.contains(search_term, case=False, na=False)
                results_df = results_df[mask]
            
            if not results_df.empty:
                st.success(f"✅ Found {len(results_df)} food items")
                
                # Display results with better formatting
                for idx, row in results_df.iterrows():
                    with st.expander(f"🍽️ {row['Food_Name']} - {row['Provider_Name']}", expanded=False):
                        col1, col2 = st.columns([2, 1])
                        
                        with col1:
                            st.write(f"**Food Type:** {row['Food_Type']}")
                            st.write(f"**Meal Type:** {row['Meal_Type']}")
                            st.write(f"**Quantity Available:** {row['Quantity']} units")
                            st.write(f"**Expiry Date:** {row['Expiry_Date']}")
                            st.write(f"**Location:** {row['Location']}")
                        
                        with col2:
                            st.write(f"**Provider:** {row['Provider_Name']}")
                            st.write(f"**Provider Type:** {row['Provider_Type']}")
                            st.write(f"**Contact:** {row['Contact']}")
                            
                            # Claim button (simulation)
                            if st.button(f"📞 Contact Provider", key=f"contact_{idx}"):
                                st.info(f"Contact {row['Provider_Name']} at {row['Contact']} to claim this food item.")
                
                # Summary statistics
                st.subheader("📊 Search Summary")
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Total Items", len(results_df))
                with col2:
                    st.metric("Total Quantity", results_df['Quantity'].sum())
                with col3:
                    st.metric("Unique Providers", results_df['Provider_Name'].nunique())
                with col4:
                    st.metric("Locations", results_df['Location'].nunique())
                
            else:
                st.warning("⚠️ No food items found matching your criteria")
                
        except Exception as e:
            st.error(f"Error searching food: {str(e)}")

elif directory_type == "Provider Directory":
    st.header("🏪 Provider Directory")
    st.markdown("Browse and contact food providers")
    
    # Filters
    col1, col2 = st.columns(2)
    
    with col1:
        provider_cities = get_unique_values(db, "providers", "City")
        selected_city = st.selectbox("Filter by City", ["All"] + provider_cities)
    
    with col2:
        provider_types = get_unique_values(db, "providers", "Type")
        selected_type = st.selectbox("Filter by Type", ["All"] + provider_types)
    
    # Search
    search_provider = st.text_input("🔍 Search provider name")
    
    try:
        # Build query
        query = "SELECT * FROM providers WHERE 1=1"
        params = []
        
        if selected_city != "All":
            query += " AND City = ?"
            params.append(selected_city)
        
        if selected_type != "All":
            query += " AND Type = ?"
            params.append(selected_type)
        
        if search_provider:
            query += " AND Name LIKE ?"
            params.append(f"%{search_provider}%")
        
        query += " ORDER BY Name"
        
        providers = db.execute_query(query, params if params else None)
        
        if providers:
            st.success(f"✅ Found {len(providers)} providers")
            
            # Display providers
            for provider in providers:
                with st.expander(f"🏪 {provider[1]} - {provider[2]}", expanded=False):
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        st.write(f"**Name:** {provider[1]}")
                        st.write(f"**Type:** {provider[2]}")
                        st.write(f"**Address:** {provider[3]}")
                        st.write(f"**City:** {provider[4]}")
                        st.write(f"**Contact:** {provider[5]}")
                    
                    with col2:
                        # Get provider statistics
                        stats = db.execute_query("""
                            SELECT 
                                COUNT(fl.Food_ID) as total_listings,
                                SUM(fl.Quantity) as total_quantity,
                                COUNT(c.Claim_ID) as total_claims
                            FROM food_listings fl
                            LEFT JOIN claims c ON fl.Food_ID = c.Food_ID
                            WHERE fl.Provider_ID = ?
                        """, (provider[0],))
                        
                        if stats:
                            st.metric("Food Listings", stats[0][0] or 0)
                            st.metric("Total Quantity", stats[0][1] or 0)
                            st.metric("Total Claims", stats[0][2] or 0)
            
            # Summary by type
            st.subheader("📊 Provider Summary")
            summary = db.execute_query("""
                SELECT Type, COUNT(*) as count
                FROM providers
                WHERE 1=1
            """ + (" AND City = ?" if selected_city != "All" else ""), 
            [selected_city] if selected_city != "All" else None)
            
            if summary:
                summary_df = pd.DataFrame(summary, columns=['Type', 'Count'])
                col1, col2 = st.columns([1, 1])
                
                with col1:
                    st.dataframe(summary_df, use_container_width=True)
                
                with col2:
                    import plotly.express as px
                    fig = px.pie(summary_df, values='Count', names='Type', 
                               title='Provider Distribution by Type')
                    st.plotly_chart(fig, use_container_width=True)
        
        else:
            st.warning("⚠️ No providers found matching your criteria")
            
    except Exception as e:
        st.error(f"Error loading providers: {str(e)}")

elif directory_type == "Receiver Directory":
    st.header("👥 Receiver Directory")
    st.markdown("Browse and contact food receivers")
    
    # Filters
    col1, col2 = st.columns(2)
    
    with col1:
        receiver_cities = get_unique_values(db, "receivers", "City")
        selected_city = st.selectbox("Filter by City", ["All"] + receiver_cities)
    
    with col2:
        receiver_types = get_unique_values(db, "receivers", "Type")
        selected_type = st.selectbox("Filter by Type", ["All"] + receiver_types)
    
    # Search
    search_receiver = st.text_input("🔍 Search receiver name")
    
    try:
        # Build query
        query = "SELECT * FROM receivers WHERE 1=1"
        params = []
        
        if selected_city != "All":
            query += " AND City = ?"
            params.append(selected_city)
        
        if selected_type != "All":
            query += " AND Type = ?"
            params.append(selected_type)
        
        if search_receiver:
            query += " AND Name LIKE ?"
            params.append(f"%{search_receiver}%")
        
        query += " ORDER BY Name"
        
        receivers = db.execute_query(query, params if params else None)
        
        if receivers:
            st.success(f"✅ Found {len(receivers)} receivers")
            
            # Display receivers
            for receiver in receivers:
                with st.expander(f"👥 {receiver[1]} - {receiver[2]}", expanded=False):
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        st.write(f"**Name:** {receiver[1]}")
                        st.write(f"**Type:** {receiver[2]}")
                        st.write(f"**City:** {receiver[3]}")
                        st.write(f"**Contact:** {receiver[4]}")
                    
                    with col2:
                        # Get receiver statistics
                        stats = db.execute_query("""
                            SELECT 
                                COUNT(c.Claim_ID) as total_claims,
                                COUNT(CASE WHEN c.Status = 'Completed' THEN 1 END) as completed_claims,
                                COUNT(CASE WHEN c.Status = 'Pending' THEN 1 END) as pending_claims
                            FROM claims c
                            WHERE c.Receiver_ID = ?
                        """, (receiver[0],))
                        
                        if stats:
                            st.metric("Total Claims", stats[0][0] or 0)
                            st.metric("Completed", stats[0][1] or 0)
                            st.metric("Pending", stats[0][2] or 0)
            
            # Summary by type
            st.subheader("📊 Receiver Summary")
            summary = db.execute_query("""
                SELECT Type, COUNT(*) as count
                FROM receivers
                WHERE 1=1
            """ + (" AND City = ?" if selected_city != "All" else ""), 
            [selected_city] if selected_city != "All" else None)
            
            if summary:
                summary_df = pd.DataFrame(summary, columns=['Type', 'Count'])
                col1, col2 = st.columns([1, 1])
                
                with col1:
                    st.dataframe(summary_df, use_container_width=True)
                
                with col2:
                    import plotly.express as px
                    fig = px.pie(summary_df, values='Count', names='Type', 
                               title='Receiver Distribution by Type')
                    st.plotly_chart(fig, use_container_width=True)
        
        else:
            st.warning("⚠️ No receivers found matching your criteria")
            
    except Exception as e:
        st.error(f"Error loading receivers: {str(e)}")

elif directory_type == "Contact Information":
    st.header("📞 Quick Contact Information")
    st.markdown("Get contact details for providers and receivers")
    
    # Quick contact search
    tab1, tab2 = st.tabs(["Provider Contacts", "Receiver Contacts"])
    
    with tab1:
        st.subheader("🏪 Provider Contact Information")
        
        # City filter for providers
        provider_cities = get_unique_values(db, "providers", "City")
        contact_city = st.selectbox("Select City for Provider Contacts", provider_cities)
        
        if contact_city:
            try:
                provider_contacts = db.execute_query("""
                    SELECT Name, Type, Contact, Address
                    FROM providers
                    WHERE City = ?
                    ORDER BY Type, Name
                """, (contact_city,))
                
                if provider_contacts:
                    st.success(f"✅ Found {len(provider_contacts)} providers in {contact_city}")
                    
                    contact_df = pd.DataFrame(provider_contacts, columns=[
                        'Provider Name', 'Type', 'Contact', 'Address'
                    ])
                    
                    st.dataframe(contact_df, use_container_width=True)
                    
                    # Download option
                    csv = contact_df.to_csv(index=False)
                    st.download_button(
                        label="📥 Download Provider Contacts",
                        data=csv,
                        file_name=f"provider_contacts_{contact_city}.csv",
                        mime="text/csv"
                    )
                else:
                    st.info(f"No providers found in {contact_city}")
                    
            except Exception as e:
                st.error(f"Error loading provider contacts: {str(e)}")
    
    with tab2:
        st.subheader("👥 Receiver Contact Information")
        
        # City filter for receivers
        receiver_cities = get_unique_values(db, "receivers", "City")
        contact_city = st.selectbox("Select City for Receiver Contacts", receiver_cities)
        
        if contact_city:
            try:
                receiver_contacts = db.execute_query("""
                    SELECT Name, Type, Contact
                    FROM receivers
                    WHERE City = ?
                    ORDER BY Type, Name
                """, (contact_city,))
                
                if receiver_contacts:
                    st.success(f"✅ Found {len(receiver_contacts)} receivers in {contact_city}")
                    
                    contact_df = pd.DataFrame(receiver_contacts, columns=[
                        'Receiver Name', 'Type', 'Contact'
                    ])
                    
                    st.dataframe(contact_df, use_container_width=True)
                    
                    # Download option
                    csv = contact_df.to_csv(index=False)
                    st.download_button(
                        label="📥 Download Receiver Contacts",
                        data=csv,
                        file_name=f"receiver_contacts_{contact_city}.csv",
                        mime="text/csv"
                    )
                else:
                    st.info(f"No receivers found in {contact_city}")
                    
            except Exception as e:
                st.error(f"Error loading receiver contacts: {str(e)}")

# Emergency contacts section
st.sidebar.markdown("---")
st.sidebar.subheader("🚨 Emergency Food Assistance")
st.sidebar.markdown("""
**Need immediate food assistance?**

Contact these organizations:
- National Hunger Hotline: 1-866-3-HUNGRY
- Local Food Bank Directory
- Emergency Services: 911

**Want to donate food?**
- Use the search function to find local receivers
- Check expiry dates before donating
- Contact receivers directly for coordination
""")

# Statistics sidebar
st.sidebar.markdown("---")
st.sidebar.subheader("📊 Directory Statistics")

try:
    total_providers = db.execute_query("SELECT COUNT(*) FROM providers")[0][0]
    total_receivers = db.execute_query("SELECT COUNT(*) FROM receivers")[0][0]
    available_food = db.execute_query("SELECT COUNT(*) FROM food_listings")[0][0]
    active_claims = db.execute_query("SELECT COUNT(*) FROM claims WHERE Status = 'Pending'")[0][0]
    
    st.sidebar.metric("Total Providers", total_providers)
    st.sidebar.metric("Total Receivers", total_receivers)
    st.sidebar.metric("Available Food Items", available_food)
    st.sidebar.metric("Active Claims", active_claims)
    
except Exception as e:
    st.sidebar.error("Error loading statistics")
