import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys
import os

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import DatabaseManager
from queries import SQLQueries

st.set_page_config(page_title="SQL Queries", page_icon="🔍", layout="wide")

# Initialize database
@st.cache_resource
def get_database():
    return DatabaseManager()

db = get_database()

st.title("🔍 SQL Queries & Analysis")
st.markdown("Execute the 15 analytical queries specified in the project requirements to gain insights into food waste patterns.")

# Get all queries
queries = SQLQueries.get_all_queries()

# Sidebar for query selection
st.sidebar.title("Query Selection")
query_list = list(queries.keys())
selected_query = st.sidebar.selectbox("Select a query to execute:", query_list)

# Execute all queries button
if st.sidebar.button("🚀 Execute All Queries", type="primary"):
    st.session_state.execute_all = True

# Main content
if selected_query:
    st.header(f"Query: {selected_query}")
    
    query_info = queries[selected_query]
    st.markdown(f"**Description:** {query_info['description']}")
    
    # Show the SQL query
    with st.expander("📝 View SQL Query"):
        # Modify query for SQLite compatibility if needed
        display_query = SQLQueries.get_modified_query_for_sqlite(query_info['query'])
        st.code(display_query, language="sql")
    
    # Execute query
    try:
        # Use modified query for SQLite
        executed_query = SQLQueries.get_modified_query_for_sqlite(query_info['query'])
        results = db.execute_query(executed_query)
        
        if results:
            # Determine column names based on query
            if "Providers and Receivers by City" in selected_query:
                columns = ['City', 'Provider_Count', 'Receiver_Count']
            elif "Provider Type Contributions" in selected_query:
                columns = ['Provider_Type', 'Total_Listings', 'Total_Quantity']
            elif "Provider Contacts by City" in selected_query:
                columns = ['City', 'Name', 'Type', 'Contact']
            elif "Top Claiming Receivers" in selected_query:
                columns = ['Receiver_Name', 'Receiver_Type', 'Total_Claims', 'Completed_Claims']
            elif "Total Food Quantity Available" in selected_query:
                columns = ['Total_Food_Quantity', 'Total_Food_Items', 'Average_Quantity_Per_Item']
            elif "Cities with Most Food Listings" in selected_query:
                columns = ['City', 'Total_Listings', 'Total_Quantity']
            elif "Most Common Food Types" in selected_query:
                columns = ['Food_Type', 'Listing_Count', 'Total_Quantity', 'Percentage']
            elif "Claims per Food Item" in selected_query:
                columns = ['Food_Name', 'Food_Type', 'Available_Quantity', 'Total_Claims', 'Provider_Name']
            elif "Providers with Most Successful Claims" in selected_query:
                columns = ['Provider_Name', 'Provider_Type', 'City', 'Total_Claims', 'Successful_Claims', 'Success_Rate']
            elif "Claim Status Distribution" in selected_query:
                columns = ['Status', 'Count', 'Percentage']
            elif "Average Food Claimed per Receiver" in selected_query:
                columns = ['Receiver_Name', 'Receiver_Type', 'Total_Claims', 'Average_Quantity_Claimed', 'Total_Quantity_Claimed']
            elif "Most Claimed Meal Types" in selected_query:
                columns = ['Meal_Type', 'Total_Claims', 'Completed_Claims', 'Total_Quantity_Claimed']
            elif "Total Food Donated by Provider" in selected_query:
                columns = ['Provider_Name', 'Provider_Type', 'City', 'Total_Food_Items', 'Total_Quantity_Donated', 'Average_Quantity_Per_Item']
            elif "Food Expiry Analysis" in selected_query:
                columns = ['Expiry_Status', 'Item_Count', 'Total_Quantity']
            elif "Monthly Claim Trends" in selected_query:
                columns = ['Month', 'Status', 'Claim_Count']
            else:
                # Generic column names
                columns = [f'Column_{i+1}' for i in range(len(results[0]))]
            
            df = pd.DataFrame(results, columns=columns)
            
            # Display results
            st.success(f"✅ Query executed successfully! Found {len(df)} results.")
            
            # Show summary statistics if applicable
            if len(df) > 0:
                st.subheader("📊 Results")
                
                # Display data with better formatting
                if len(df) > 100:
                    st.warning(f"Displaying first 100 rows of {len(df)} total results")
                    display_df = df.head(100)
                else:
                    display_df = df
                
                st.dataframe(display_df, use_container_width=True)
                
                # Create visualizations for specific queries
                if "Provider Type Contributions" in selected_query and len(df) > 0:
                    st.subheader("📈 Visualization")
                    fig = px.bar(df, x='Provider_Type', y='Total_Quantity', 
                               title='Food Quantity by Provider Type')
                    st.plotly_chart(fig, use_container_width=True)
                
                elif "Cities with Most Food Listings" in selected_query and len(df) > 0:
                    st.subheader("📈 Visualization")
                    top_cities = df.head(15)  # Show top 15 cities
                    fig = px.bar(top_cities, x='City', y='Total_Quantity',
                               title='Top Cities by Food Quantity')
                    fig.update_xaxes(tickangle=45)
                    st.plotly_chart(fig, use_container_width=True)
                
                elif "Most Common Food Types" in selected_query and len(df) > 0:
                    st.subheader("📈 Visualization")
                    col1, col2 = st.columns(2)
                    with col1:
                        fig1 = px.pie(df, values='Listing_Count', names='Food_Type',
                                    title='Food Types by Count')
                        st.plotly_chart(fig1, use_container_width=True)
                    with col2:
                        fig2 = px.bar(df, x='Food_Type', y='Total_Quantity',
                                    title='Food Types by Quantity')
                        st.plotly_chart(fig2, use_container_width=True)
                
                elif "Claim Status Distribution" in selected_query and len(df) > 0:
                    st.subheader("📈 Visualization")
                    fig = px.pie(df, values='Count', names='Status',
                               title='Claim Status Distribution')
                    st.plotly_chart(fig, use_container_width=True)
                
                elif "Most Claimed Meal Types" in selected_query and len(df) > 0:
                    st.subheader("📈 Visualization")
                    fig = px.bar(df, x='Meal_Type', y='Total_Claims',
                               title='Claims by Meal Type')
                    st.plotly_chart(fig, use_container_width=True)
                
                elif "Food Expiry Analysis" in selected_query and len(df) > 0:
                    st.subheader("📈 Visualization")
                    # Order the categories logically
                    order = ['Expired', 'Expiring Soon', 'Expiring This Week', 'Fresh']
                    df_ordered = df.set_index('Expiry_Status').reindex(order).reset_index()
                    df_ordered = df_ordered.dropna()
                    
                    fig = px.bar(df_ordered, x='Expiry_Status', y='Total_Quantity',
                               title='Food Quantity by Expiry Status')
                    st.plotly_chart(fig, use_container_width=True)
                
                # Download option
                st.subheader("💾 Download Results")
                csv = df.to_csv(index=False)
                st.download_button(
                    label="📥 Download as CSV",
                    data=csv,
                    file_name=f"query_results_{selected_query.split('.')[0]}.csv",
                    mime="text/csv"
                )
        else:
            st.warning("⚠️ No results found for this query.")
            
    except Exception as e:
        st.error(f"❌ Error executing query: {str(e)}")
        st.error("Please check the database connection and ensure data is loaded.")

# Execute all queries
if st.session_state.get('execute_all', False):
    st.header("🚀 Executing All Queries")
    
    results_summary = []
    
    for i, (query_name, query_info) in enumerate(queries.items(), 1):
        with st.expander(f"Query {i}: {query_name}", expanded=False):
            try:
                # Use modified query for SQLite
                executed_query = SQLQueries.get_modified_query_for_sqlite(query_info['query'])
                results = db.execute_query(executed_query)
                
                if results:
                    # Generic column names for all queries
                    columns = [f'Column_{j+1}' for j in range(len(results[0]))]
                    df = pd.DataFrame(results, columns=columns)
                    
                    st.success(f"✅ Found {len(df)} results")
                    
                    # Show first few rows
                    st.dataframe(df.head(10), use_container_width=True)
                    
                    if len(df) > 10:
                        st.info(f"Showing first 10 rows of {len(df)} total results")
                    
                    results_summary.append({
                        'Query': query_name,
                        'Status': 'Success',
                        'Results_Count': len(df)
                    })
                else:
                    st.warning("⚠️ No results found")
                    results_summary.append({
                        'Query': query_name,
                        'Status': 'No Results',
                        'Results_Count': 0
                    })
                    
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                results_summary.append({
                    'Query': query_name,
                    'Status': 'Error',
                    'Results_Count': 0
                })
    
    # Summary table
    st.subheader("📋 Execution Summary")
    summary_df = pd.DataFrame(results_summary)
    st.dataframe(summary_df, use_container_width=True)
    
    # Reset the flag
    st.session_state.execute_all = False

# Query insights
st.sidebar.markdown("---")
st.sidebar.subheader("💡 Query Insights")
st.sidebar.markdown("""
**Query Categories:**
- **1-4**: Provider & Receiver Analysis
- **5-7**: Food Availability Analysis  
- **8-10**: Claims Analysis
- **11-13**: Distribution Patterns
- **14-15**: Temporal Analysis
""")

st.sidebar.markdown("---")
st.sidebar.info("💡 **Tip:** Use 'Execute All Queries' to run a comprehensive analysis of the entire system.")
