import pandas as pd
import streamlit as st
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go

def load_data(file_path):
    """Load data from CSV file"""
    try:
        df = pd.read_csv(file_path)
        return df
    except Exception as e:
        st.error(f"Error loading data from {file_path}: {str(e)}")
        return None

def get_summary_stats(db):
    """Get summary statistics for the dashboard"""
    try:
        providers_count = db.execute_query("SELECT COUNT(*) FROM providers")[0][0]
        receivers_count = db.execute_query("SELECT COUNT(*) FROM receivers")[0][0]
        food_listings_count = db.execute_query("SELECT COUNT(*) FROM food_listings")[0][0]
        claims_count = db.execute_query("SELECT COUNT(*) FROM claims")[0][0]
        
        return {
            'total_providers': providers_count,
            'total_receivers': receivers_count,
            'total_food_listings': food_listings_count,
            'total_claims': claims_count
        }
    except Exception as e:
        st.error(f"Error getting summary statistics: {str(e)}")
        return {
            'total_providers': 0,
            'total_receivers': 0,
            'total_food_listings': 0,
            'total_claims': 0
        }

def format_dataframe(df, max_rows=100):
    """Format dataframe for display"""
    if df is None or df.empty:
        return df
    
    # Limit number of rows for display
    if len(df) > max_rows:
        st.warning(f"Displaying first {max_rows} rows of {len(df)} total rows")
        df = df.head(max_rows)
    
    return df

def validate_form_data(data, required_fields):
    """Validate form data"""
    errors = []
    for field in required_fields:
        if field not in data or not data[field] or str(data[field]).strip() == "":
            errors.append(f"{field} is required")
    return errors

def get_unique_values(db, table, column):
    """Get unique values from a table column"""
    try:
        query = f"SELECT DISTINCT {column} FROM {table} WHERE {column} IS NOT NULL ORDER BY {column}"
        results = db.execute_query(query)
        return [row[0] for row in results]
    except Exception as e:
        st.error(f"Error getting unique values: {str(e)}")
        return []

def create_claim_status_chart(db):
    """Create claim status distribution chart"""
    try:
        query = "SELECT Status, COUNT(*) as count FROM claims GROUP BY Status"
        results = db.execute_query(query)
        
        if results:
            df = pd.DataFrame(results, columns=['Status', 'Count'])
            fig = px.pie(df, values='Count', names='Status', title='Claim Status Distribution')
            return fig
        else:
            return None
    except Exception as e:
        st.error(f"Error creating claim status chart: {str(e)}")
        return None

def create_food_type_chart(db):
    """Create food type distribution chart"""
    try:
        query = "SELECT Food_Type, COUNT(*) as count FROM food_listings GROUP BY Food_Type"
        results = db.execute_query(query)
        
        if results:
            df = pd.DataFrame(results, columns=['Food_Type', 'Count'])
            fig = px.bar(df, x='Food_Type', y='Count', title='Food Types Distribution')
            return fig
        else:
            return None
    except Exception as e:
        st.error(f"Error creating food type chart: {str(e)}")
        return None

def create_provider_type_chart(db):
    """Create provider type distribution chart"""
    try:
        query = """
            SELECT p.Type, COUNT(fl.Food_ID) as food_count, SUM(fl.Quantity) as total_quantity
            FROM providers p
            LEFT JOIN food_listings fl ON p.Provider_ID = fl.Provider_ID
            GROUP BY p.Type
        """
        results = db.execute_query(query)
        
        if results:
            df = pd.DataFrame(results, columns=['Provider_Type', 'Food_Count', 'Total_Quantity'])
            fig = px.bar(df, x='Provider_Type', y='Total_Quantity', 
                        title='Total Food Quantity by Provider Type')
            return fig
        else:
            return None
    except Exception as e:
        st.error(f"Error creating provider type chart: {str(e)}")
        return None

def create_city_distribution_chart(db):
    """Create city-wise distribution chart"""
    try:
        query = """
            SELECT Location as City, COUNT(*) as food_listings, SUM(Quantity) as total_quantity
            FROM food_listings
            GROUP BY Location
            ORDER BY total_quantity DESC
            LIMIT 15
        """
        results = db.execute_query(query)
        
        if results:
            df = pd.DataFrame(results, columns=['City', 'Food_Listings', 'Total_Quantity'])
            fig = px.bar(df, x='City', y='Total_Quantity', 
                        title='Top 15 Cities by Food Quantity Available')
            fig.update_xaxes(tickangle=45)
            return fig
        else:
            return None
    except Exception as e:
        st.error(f"Error creating city distribution chart: {str(e)}")
        return None

def create_meal_type_chart(db):
    """Create meal type distribution chart"""
    try:
        query = """
            SELECT Meal_Type, COUNT(*) as count, SUM(Quantity) as total_quantity
            FROM food_listings
            GROUP BY Meal_Type
        """
        results = db.execute_query(query)
        
        if results:
            df = pd.DataFrame(results, columns=['Meal_Type', 'Count', 'Total_Quantity'])
            
            # Create subplot with two y-axes
            fig = go.Figure()
            
            fig.add_trace(go.Bar(
                name='Count of Listings',
                x=df['Meal_Type'],
                y=df['Count'],
                yaxis='y',
                offsetgroup=1
            ))
            
            fig.add_trace(go.Bar(
                name='Total Quantity',
                x=df['Meal_Type'],
                y=df['Total_Quantity'],
                yaxis='y2',
                offsetgroup=2
            ))
            
            fig.update_layout(
                title='Meal Type Distribution: Count vs Quantity',
                xaxis=dict(title='Meal Type'),
                yaxis=dict(title='Count of Listings', side='left'),
                yaxis2=dict(title='Total Quantity', side='right', overlaying='y'),
                barmode='group'
            )
            
            return fig
        else:
            return None
    except Exception as e:
        st.error(f"Error creating meal type chart: {str(e)}")
        return None

def search_and_filter_food(db, filters):
    """Search and filter food listings based on criteria"""
    try:
        query = """
            SELECT fl.Food_ID, fl.Food_Name, fl.Quantity, fl.Expiry_Date, 
                   fl.Food_Type, fl.Meal_Type, fl.Location,
                   p.Name as Provider_Name, p.Type as Provider_Type, p.Contact
            FROM food_listings fl
            JOIN providers p ON fl.Provider_ID = p.Provider_ID
            WHERE 1=1
        """
        params = []
        
        if filters.get('city'):
            query += " AND fl.Location = ?"
            params.append(filters['city'])
        
        if filters.get('provider_type'):
            query += " AND p.Type = ?"
            params.append(filters['provider_type'])
        
        if filters.get('food_type'):
            query += " AND fl.Food_Type = ?"
            params.append(filters['food_type'])
        
        if filters.get('meal_type'):
            query += " AND fl.Meal_Type = ?"
            params.append(filters['meal_type'])
        
        if filters.get('min_quantity'):
            query += " AND fl.Quantity >= ?"
            params.append(filters['min_quantity'])
        
        query += " ORDER BY fl.Food_ID DESC"
        
        results = db.execute_query(query, params if params else None)
        
        if results:
            columns = ['Food_ID', 'Food_Name', 'Quantity', 'Expiry_Date', 
                      'Food_Type', 'Meal_Type', 'Location', 'Provider_Name', 
                      'Provider_Type', 'Contact']
            return pd.DataFrame(results, columns=columns)
        else:
            return pd.DataFrame()
            
    except Exception as e:
        st.error(f"Error searching food listings: {str(e)}")
        return pd.DataFrame()

def get_expiry_analysis(db):
    """Get food expiry analysis"""
    try:
        query = """
            SELECT 
                CASE 
                    WHEN date(Expiry_Date) < date('now') THEN 'Expired'
                    WHEN date(Expiry_Date) <= date('now', '+3 days') THEN 'Expiring Soon'
                    WHEN date(Expiry_Date) <= date('now', '+7 days') THEN 'Expiring This Week'
                    ELSE 'Fresh'
                END as Expiry_Status,
                COUNT(Food_ID) as Item_Count,
                SUM(Quantity) as Total_Quantity
            FROM food_listings
            GROUP BY Expiry_Status
        """
        results = db.execute_query(query)
        
        if results:
            return pd.DataFrame(results, columns=['Expiry_Status', 'Item_Count', 'Total_Quantity'])
        else:
            return pd.DataFrame()
            
    except Exception as e:
        st.error(f"Error getting expiry analysis: {str(e)}")
        return pd.DataFrame()
