import sqlite3
import pandas as pd
import streamlit as st
from datetime import datetime
import os

class DatabaseManager:
    def __init__(self, db_path="food_waste.db"):
        """Initialize the database manager"""
        self.db_path = db_path
        self.init_database()
    
    def get_connection(self):
        """Get database connection"""
        return sqlite3.connect(self.db_path)
    
    def init_database(self):
        """Initialize database with required tables"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Create providers table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS providers (
                Provider_ID INTEGER PRIMARY KEY,
                Name TEXT NOT NULL,
                Type TEXT NOT NULL,
                Address TEXT,
                City TEXT NOT NULL,
                Contact TEXT
            )
        """)
        
        # Create receivers table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS receivers (
                Receiver_ID INTEGER PRIMARY KEY,
                Name TEXT NOT NULL,
                Type TEXT NOT NULL,
                City TEXT NOT NULL,
                Contact TEXT
            )
        """)
        
        # Create food_listings table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS food_listings (
                Food_ID INTEGER PRIMARY KEY,
                Food_Name TEXT NOT NULL,
                Quantity INTEGER NOT NULL,
                Expiry_Date TEXT,
                Provider_ID INTEGER,
                Provider_Type TEXT,
                Location TEXT,
                Food_Type TEXT,
                Meal_Type TEXT,
                FOREIGN KEY (Provider_ID) REFERENCES providers (Provider_ID)
            )
        """)
        
        # Create claims table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS claims (
                Claim_ID INTEGER PRIMARY KEY,
                Food_ID INTEGER,
                Receiver_ID INTEGER,
                Status TEXT NOT NULL,
                Timestamp TEXT,
                FOREIGN KEY (Food_ID) REFERENCES food_listings (Food_ID),
                FOREIGN KEY (Receiver_ID) REFERENCES receivers (Receiver_ID)
            )
        """)
        
        conn.commit()
        conn.close()
    
    def load_data(self, providers_df, receivers_df, food_listings_df, claims_df):
        """Load data from CSV files into the database"""
        conn = self.get_connection()
        
        try:
            # Clear existing data
            cursor = conn.cursor()
            cursor.execute("DELETE FROM claims")
            cursor.execute("DELETE FROM food_listings")
            cursor.execute("DELETE FROM providers")
            cursor.execute("DELETE FROM receivers")
            
            # Load data into tables
            providers_df.to_sql('providers', conn, if_exists='append', index=False)
            receivers_df.to_sql('receivers', conn, if_exists='append', index=False)
            food_listings_df.to_sql('food_listings', conn, if_exists='append', index=False)
            claims_df.to_sql('claims', conn, if_exists='append', index=False)
            
            conn.commit()
            print("Data loaded successfully!")
            
        except Exception as e:
            conn.rollback()
            print(f"Error loading data: {str(e)}")
            raise e
        finally:
            conn.close()
    
    def execute_query(self, query, params=None):
        """Execute a SELECT query and return results"""
        conn = self.get_connection()
        try:
            if params:
                cursor = conn.cursor()
                cursor.execute(query, params)
                results = cursor.fetchall()
            else:
                cursor = conn.cursor()
                cursor.execute(query)
                results = cursor.fetchall()
            return results
        except Exception as e:
            print(f"Error executing query: {str(e)}")
            return []
        finally:
            conn.close()
    
    def execute_update(self, query, params=None):
        """Execute an INSERT, UPDATE, or DELETE query"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            conn.commit()
            return cursor.rowcount
        except Exception as e:
            conn.rollback()
            print(f"Error executing update: {str(e)}")
            raise e
        finally:
            conn.close()
    
    def get_table_data(self, table_name, limit=None):
        """Get all data from a specific table"""
        query = f"SELECT * FROM {table_name}"
        if limit:
            query += f" LIMIT {limit}"
        return self.execute_query(query)
    
    def insert_provider(self, name, type_, address, city, contact):
        """Insert a new provider"""
        query = """
            INSERT INTO providers (Name, Type, Address, City, Contact)
            VALUES (?, ?, ?, ?, ?)
        """
        return self.execute_update(query, (name, type_, address, city, contact))
    
    def insert_receiver(self, name, type_, city, contact):
        """Insert a new receiver"""
        query = """
            INSERT INTO receivers (Name, Type, City, Contact)
            VALUES (?, ?, ?, ?)
        """
        return self.execute_update(query, (name, type_, city, contact))
    
    def insert_food_listing(self, food_name, quantity, expiry_date, provider_id, provider_type, location, food_type, meal_type):
        """Insert a new food listing"""
        query = """
            INSERT INTO food_listings (Food_Name, Quantity, Expiry_Date, Provider_ID, Provider_Type, Location, Food_Type, Meal_Type)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        return self.execute_update(query, (food_name, quantity, expiry_date, provider_id, provider_type, location, food_type, meal_type))
    
    def insert_claim(self, food_id, receiver_id, status, timestamp):
        """Insert a new claim"""
        query = """
            INSERT INTO claims (Food_ID, Receiver_ID, Status, Timestamp)
            VALUES (?, ?, ?, ?)
        """
        return self.execute_update(query, (food_id, receiver_id, status, timestamp))
    
    def update_provider(self, provider_id, name, type_, address, city, contact):
        """Update an existing provider"""
        query = """
            UPDATE providers 
            SET Name=?, Type=?, Address=?, City=?, Contact=?
            WHERE Provider_ID=?
        """
        return self.execute_update(query, (name, type_, address, city, contact, provider_id))
    
    def update_receiver(self, receiver_id, name, type_, city, contact):
        """Update an existing receiver"""
        query = """
            UPDATE receivers 
            SET Name=?, Type=?, City=?, Contact=?
            WHERE Receiver_ID=?
        """
        return self.execute_update(query, (name, type_, city, contact, receiver_id))
    
    def update_food_listing(self, food_id, food_name, quantity, expiry_date, provider_id, provider_type, location, food_type, meal_type):
        """Update an existing food listing"""
        query = """
            UPDATE food_listings 
            SET Food_Name=?, Quantity=?, Expiry_Date=?, Provider_ID=?, Provider_Type=?, Location=?, Food_Type=?, Meal_Type=?
            WHERE Food_ID=?
        """
        return self.execute_update(query, (food_name, quantity, expiry_date, provider_id, provider_type, location, food_type, meal_type, food_id))
    
    def update_claim_status(self, claim_id, status):
        """Update claim status"""
        query = "UPDATE claims SET Status=? WHERE Claim_ID=?"
        return self.execute_update(query, (status, claim_id))
    
    def delete_record(self, table_name, id_column, record_id):
        """Delete a record from any table"""
        query = f"DELETE FROM {table_name} WHERE {id_column}=?"
        return self.execute_update(query, (record_id,))
    
    def get_providers_by_city(self, city):
        """Get providers in a specific city"""
        query = "SELECT * FROM providers WHERE City=?"
        return self.execute_query(query, (city,))
    
    def get_food_by_type(self, food_type):
        """Get food listings by type"""
        query = "SELECT * FROM food_listings WHERE Food_Type=?"
        return self.execute_query(query, (food_type,))
    
    def search_food(self, city=None, provider_type=None, food_type=None, meal_type=None):
        """Search food listings with filters"""
        query = """
            SELECT fl.*, p.Name as Provider_Name, p.Contact as Provider_Contact
            FROM food_listings fl
            JOIN providers p ON fl.Provider_ID = p.Provider_ID
            WHERE 1=1
        """
        params = []
        
        if city:
            query += " AND fl.Location=?"
            params.append(city)
        if provider_type:
            query += " AND fl.Provider_Type=?"
            params.append(provider_type)
        if food_type:
            query += " AND fl.Food_Type=?"
            params.append(food_type)
        if meal_type:
            query += " AND fl.Meal_Type=?"
            params.append(meal_type)
        
        return self.execute_query(query, params if params else None)
