import streamlit as st
import pandas as pd
from datetime import datetime, date
import sys
import os

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import DatabaseManager
from utils import get_unique_values, validate_form_data

st.set_page_config(page_title="Data Management", page_icon="📊", layout="wide")

# Initialize database
@st.cache_resource
def get_database():
    return DatabaseManager()

db = get_database()

st.title("📊 Data Management - CRUD Operations")
st.markdown("Add, update, view, and delete records from the food waste management system.")

# Sidebar for selecting operation
st.sidebar.title("Select Operation")
operation = st.sidebar.selectbox(
    "Choose what you want to do:",
    ["View Data", "Add Records", "Update Records", "Delete Records"]
)

if operation == "View Data":
    st.header("👀 View Data")
    
    # Select table to view
    table = st.selectbox(
        "Select table to view:",
        ["providers", "receivers", "food_listings", "claims"]
    )
    
    try:
        # Get data from selected table
        if table == "providers":
            data = db.execute_query("SELECT * FROM providers ORDER BY Provider_ID")
            columns = ["Provider_ID", "Name", "Type", "Address", "City", "Contact"]
        elif table == "receivers":
            data = db.execute_query("SELECT * FROM receivers ORDER BY Receiver_ID")
            columns = ["Receiver_ID", "Name", "Type", "City", "Contact"]
        elif table == "food_listings":
            data = db.execute_query("""
                SELECT fl.*, p.Name as Provider_Name 
                FROM food_listings fl 
                LEFT JOIN providers p ON fl.Provider_ID = p.Provider_ID 
                ORDER BY fl.Food_ID
            """)
            columns = ["Food_ID", "Food_Name", "Quantity", "Expiry_Date", "Provider_ID", 
                      "Provider_Type", "Location", "Food_Type", "Meal_Type", "Provider_Name"]
        else:  # claims
            data = db.execute_query("""
                SELECT c.*, fl.Food_Name, r.Name as Receiver_Name 
                FROM claims c 
                LEFT JOIN food_listings fl ON c.Food_ID = fl.Food_ID 
                LEFT JOIN receivers r ON c.Receiver_ID = r.Receiver_ID 
                ORDER BY c.Claim_ID
            """)
            columns = ["Claim_ID", "Food_ID", "Receiver_ID", "Status", "Timestamp", 
                      "Food_Name", "Receiver_Name"]
        
        if data:
            df = pd.DataFrame(data, columns=columns)
            st.success(f"Found {len(df)} records in {table}")
            
            # Add search functionality
            if len(df) > 0:
                search_term = st.text_input("🔍 Search records:")
                if search_term:
                    # Search in all string columns
                    mask = df.astype(str).apply(lambda x: x.str.contains(search_term, case=False, na=False)).any(axis=1)
                    df = df[mask]
                    st.info(f"Found {len(df)} records matching '{search_term}'")
            
            # Display with pagination
            if len(df) > 100:
                st.warning(f"Displaying first 100 rows of {len(df)} total rows")
                df = df.head(100)
            
            st.dataframe(df, use_container_width=True)
        else:
            st.info(f"No data found in {table} table")
            
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")

elif operation == "Add Records":
    st.header("➕ Add New Records")
    
    # Select record type to add
    record_type = st.selectbox(
        "Select record type to add:",
        ["Provider", "Receiver", "Food Listing", "Claim"]
    )
    
    if record_type == "Provider":
        st.subheader("Add New Provider")
        
        with st.form("add_provider"):
            name = st.text_input("Provider Name*", max_chars=100)
            type_ = st.selectbox("Provider Type*", ["Restaurant", "Grocery Store", "Supermarket", "Catering Service"])
            address = st.text_area("Address")
            city = st.text_input("City*", max_chars=50)
            contact = st.text_input("Contact Information", max_chars=50)
            
            submitted = st.form_submit_button("Add Provider")
            
            if submitted:
                errors = validate_form_data(
                    {"name": name, "type": type_, "city": city},
                    ["name", "type", "city"]
                )
                
                if errors:
                    for error in errors:
                        st.error(error)
                else:
                    try:
                        db.insert_provider(name, type_, address, city, contact)
                        st.success("✅ Provider added successfully!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error adding provider: {str(e)}")
    
    elif record_type == "Receiver":
        st.subheader("Add New Receiver")
        
        with st.form("add_receiver"):
            name = st.text_input("Receiver Name*", max_chars=100)
            type_ = st.selectbox("Receiver Type*", ["NGO", "Shelter", "Charity", "Individual"])
            city = st.text_input("City*", max_chars=50)
            contact = st.text_input("Contact Information", max_chars=50)
            
            submitted = st.form_submit_button("Add Receiver")
            
            if submitted:
                errors = validate_form_data(
                    {"name": name, "type": type_, "city": city},
                    ["name", "type", "city"]
                )
                
                if errors:
                    for error in errors:
                        st.error(error)
                else:
                    try:
                        db.insert_receiver(name, type_, city, contact)
                        st.success("✅ Receiver added successfully!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error adding receiver: {str(e)}")
    
    elif record_type == "Food Listing":
        st.subheader("Add New Food Listing")
        
        # Get providers for dropdown
        providers = db.execute_query("SELECT Provider_ID, Name, Type FROM providers ORDER BY Name")
        provider_options = {f"{row[1]} ({row[2]})": row[0] for row in providers}
        
        with st.form("add_food_listing"):
            food_name = st.text_input("Food Name*", max_chars=100)
            quantity = st.number_input("Quantity*", min_value=1, max_value=1000, value=1)
            expiry_date = st.date_input("Expiry Date*", min_value=date.today())
            
            if provider_options:
                provider_display = st.selectbox("Provider*", list(provider_options.keys()))
                provider_id = provider_options[provider_display]
                # Get provider type for the selected provider
                provider_info = next((row for row in providers if row[0] == provider_id), None)
                provider_type = provider_info[2] if provider_info else ""
            else:
                st.error("No providers found. Please add providers first.")
                provider_id = None
                provider_type = ""
            
            location = st.text_input("Location*", max_chars=100)
            food_type = st.selectbox("Food Type*", ["Vegetarian", "Non-Vegetarian", "Vegan"])
            meal_type = st.selectbox("Meal Type*", ["Breakfast", "Lunch", "Dinner", "Snacks"])
            
            submitted = st.form_submit_button("Add Food Listing")
            
            if submitted:
                if not provider_id:
                    st.error("Please select a provider")
                else:
                    errors = validate_form_data(
                        {"food_name": food_name, "location": location},
                        ["food_name", "location"]
                    )
                    
                    if errors:
                        for error in errors:
                            st.error(error)
                    else:
                        try:
                            db.insert_food_listing(
                                food_name, quantity, str(expiry_date), provider_id, 
                                provider_type, location, food_type, meal_type
                            )
                            st.success("✅ Food listing added successfully!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Error adding food listing: {str(e)}")
    
    elif record_type == "Claim":
        st.subheader("Add New Claim")
        
        # Get food listings and receivers for dropdowns
        food_listings = db.execute_query("SELECT Food_ID, Food_Name, Quantity FROM food_listings ORDER BY Food_Name")
        food_options = {f"{row[1]} (Qty: {row[2]})": row[0] for row in food_listings}
        
        receivers = db.execute_query("SELECT Receiver_ID, Name, Type FROM receivers ORDER BY Name")
        receiver_options = {f"{row[1]} ({row[2]})": row[0] for row in receivers}
        
        with st.form("add_claim"):
            if food_options:
                food_display = st.selectbox("Food Item*", list(food_options.keys()))
                food_id = food_options[food_display]
            else:
                st.error("No food listings found. Please add food listings first.")
                food_id = None
            
            if receiver_options:
                receiver_display = st.selectbox("Receiver*", list(receiver_options.keys()))
                receiver_id = receiver_options[receiver_display]
            else:
                st.error("No receivers found. Please add receivers first.")
                receiver_id = None
            
            status = st.selectbox("Status*", ["Pending", "Completed", "Cancelled"])
            timestamp = st.datetime_input("Timestamp*", value=datetime.now())
            
            submitted = st.form_submit_button("Add Claim")
            
            if submitted:
                if not food_id or not receiver_id:
                    st.error("Please select both food item and receiver")
                else:
                    try:
                        db.insert_claim(food_id, receiver_id, status, str(timestamp))
                        st.success("✅ Claim added successfully!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error adding claim: {str(e)}")

elif operation == "Update Records":
    st.header("✏️ Update Records")
    
    # Select record type to update
    record_type = st.selectbox(
        "Select record type to update:",
        ["Provider", "Receiver", "Food Listing", "Claim Status"]
    )
    
    if record_type == "Provider":
        st.subheader("Update Provider")
        
        # Get providers for selection
        providers = db.execute_query("SELECT Provider_ID, Name, Type, Address, City, Contact FROM providers ORDER BY Name")
        
        if providers:
            provider_options = {f"{row[1]} - {row[4]}": row for row in providers}
            selected_provider = st.selectbox("Select Provider to Update:", list(provider_options.keys()))
            
            if selected_provider:
                current_data = provider_options[selected_provider]
                
                with st.form("update_provider"):
                    st.write(f"**Current Provider ID:** {current_data[0]}")
                    name = st.text_input("Provider Name*", value=current_data[1], max_chars=100)
                    type_ = st.selectbox("Provider Type*", 
                                       ["Restaurant", "Grocery Store", "Supermarket", "Catering Service"],
                                       index=["Restaurant", "Grocery Store", "Supermarket", "Catering Service"].index(current_data[2]) if current_data[2] in ["Restaurant", "Grocery Store", "Supermarket", "Catering Service"] else 0)
                    address = st.text_area("Address", value=current_data[3] or "")
                    city = st.text_input("City*", value=current_data[4], max_chars=50)
                    contact = st.text_input("Contact Information", value=current_data[5] or "", max_chars=50)
                    
                    submitted = st.form_submit_button("Update Provider")
                    
                    if submitted:
                        try:
                            db.update_provider(current_data[0], name, type_, address, city, contact)
                            st.success("✅ Provider updated successfully!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Error updating provider: {str(e)}")
        else:
            st.info("No providers found to update.")
    
    elif record_type == "Claim Status":
        st.subheader("Update Claim Status")
        
        # Get claims for selection
        claims = db.execute_query("""
            SELECT c.Claim_ID, c.Status, fl.Food_Name, r.Name as Receiver_Name 
            FROM claims c 
            LEFT JOIN food_listings fl ON c.Food_ID = fl.Food_ID 
            LEFT JOIN receivers r ON c.Receiver_ID = r.Receiver_ID 
            ORDER BY c.Claim_ID DESC
        """)
        
        if claims:
            claim_options = {f"Claim #{row[0]} - {row[2]} for {row[3]} (Current: {row[1]})": row for row in claims}
            selected_claim = st.selectbox("Select Claim to Update:", list(claim_options.keys()))
            
            if selected_claim:
                current_data = claim_options[selected_claim]
                
                with st.form("update_claim"):
                    st.write(f"**Claim ID:** {current_data[0]}")
                    st.write(f"**Food Item:** {current_data[2]}")
                    st.write(f"**Receiver:** {current_data[3]}")
                    st.write(f"**Current Status:** {current_data[1]}")
                    
                    new_status = st.selectbox("New Status*", 
                                            ["Pending", "Completed", "Cancelled"],
                                            index=["Pending", "Completed", "Cancelled"].index(current_data[1]) if current_data[1] in ["Pending", "Completed", "Cancelled"] else 0)
                    
                    submitted = st.form_submit_button("Update Status")
                    
                    if submitted:
                        try:
                            db.update_claim_status(current_data[0], new_status)
                            st.success("✅ Claim status updated successfully!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Error updating claim status: {str(e)}")
        else:
            st.info("No claims found to update.")

elif operation == "Delete Records":
    st.header("🗑️ Delete Records")
    st.warning("⚠️ Deletion is permanent and cannot be undone!")
    
    # Select record type to delete
    record_type = st.selectbox(
        "Select record type to delete:",
        ["Provider", "Receiver", "Food Listing", "Claim"]
    )
    
    if record_type == "Provider":
        st.subheader("Delete Provider")
        
        providers = db.execute_query("SELECT Provider_ID, Name, Type, City FROM providers ORDER BY Name")
        
        if providers:
            provider_options = {f"{row[1]} ({row[2]}) - {row[3]}": row[0] for row in providers}
            selected_provider = st.selectbox("Select Provider to Delete:", list(provider_options.keys()))
            
            if selected_provider:
                provider_id = provider_options[selected_provider]
                
                # Check for dependencies
                food_count = db.execute_query("SELECT COUNT(*) FROM food_listings WHERE Provider_ID = ?", (provider_id,))[0][0]
                
                if food_count > 0:
                    st.error(f"❌ Cannot delete provider. There are {food_count} food listings associated with this provider.")
                else:
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("🗑️ Delete Provider", type="primary"):
                            try:
                                db.delete_record("providers", "Provider_ID", provider_id)
                                st.success("✅ Provider deleted successfully!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ Error deleting provider: {str(e)}")
                    with col2:
                        st.info("This action cannot be undone!")
        else:
            st.info("No providers found to delete.")
    
    elif record_type == "Claim":
        st.subheader("Delete Claim")
        
        claims = db.execute_query("""
            SELECT c.Claim_ID, c.Status, fl.Food_Name, r.Name as Receiver_Name 
            FROM claims c 
            LEFT JOIN food_listings fl ON c.Food_ID = fl.Food_ID 
            LEFT JOIN receivers r ON c.Receiver_ID = r.Receiver_ID 
            ORDER BY c.Claim_ID DESC
        """)
        
        if claims:
            claim_options = {f"Claim #{row[0]} - {row[2]} for {row[3]} ({row[1]})": row[0] for row in claims}
            selected_claim = st.selectbox("Select Claim to Delete:", list(claim_options.keys()))
            
            if selected_claim:
                claim_id = claim_options[selected_claim]
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("🗑️ Delete Claim", type="primary"):
                        try:
                            db.delete_record("claims", "Claim_ID", claim_id)
                            st.success("✅ Claim deleted successfully!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Error deleting claim: {str(e)}")
                with col2:
                    st.info("This action cannot be undone!")
        else:
            st.info("No claims found to delete.")

# Display current counts
st.sidebar.markdown("---")
st.sidebar.subheader("📈 Current Counts")
try:
    providers_count = db.execute_query("SELECT COUNT(*) FROM providers")[0][0]
    receivers_count = db.execute_query("SELECT COUNT(*) FROM receivers")[0][0]
    food_count = db.execute_query("SELECT COUNT(*) FROM food_listings")[0][0]
    claims_count = db.execute_query("SELECT COUNT(*) FROM claims")[0][0]
    
    st.sidebar.metric("Providers", providers_count)
    st.sidebar.metric("Receivers", receivers_count)
    st.sidebar.metric("Food Listings", food_count)
    st.sidebar.metric("Claims", claims_count)
except Exception as e:
    st.sidebar.error("Error loading counts")
