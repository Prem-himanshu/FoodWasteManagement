"""
SQL Queries for Food Waste Management System
Implements the 15 analytical queries specified in the PRD
"""

class SQLQueries:
    
    @staticmethod
    def get_all_queries():
        """Return all 15 SQL queries as specified in the PRD"""
        return {
            "1. Providers and Receivers by City": {
                "description": "How many food providers and receivers are there in each city?",
                "query": """
                    SELECT 
                        COALESCE(p.City, r.City) as City,
                        COUNT(DISTINCT p.Provider_ID) as Provider_Count,
                        COUNT(DISTINCT r.Receiver_ID) as Receiver_Count
                    FROM providers p
                    FULL OUTER JOIN receivers r ON p.City = r.City
                    GROUP BY COALESCE(p.City, r.City)
                    ORDER BY Provider_Count DESC, Receiver_Count DESC
                """
            },
            
            "2. Provider Type Contributions": {
                "description": "Which type of food provider contributes the most food?",
                "query": """
                    SELECT 
                        p.Type as Provider_Type,
                        COUNT(fl.Food_ID) as Total_Listings,
                        SUM(fl.Quantity) as Total_Quantity
                    FROM providers p
                    LEFT JOIN food_listings fl ON p.Provider_ID = fl.Provider_ID
                    GROUP BY p.Type
                    ORDER BY Total_Quantity DESC
                """
            },
            
            "3. Provider Contacts by City": {
                "description": "Contact information of food providers in each city",
                "query": """
                    SELECT 
                        City,
                        Name,
                        Type,
                        Contact
                    FROM providers
                    ORDER BY City, Name
                """
            },
            
            "4. Top Claiming Receivers": {
                "description": "Which receivers have claimed the most food?",
                "query": """
                    SELECT 
                        r.Name as Receiver_Name,
                        r.Type as Receiver_Type,
                        COUNT(c.Claim_ID) as Total_Claims,
                        COUNT(CASE WHEN c.Status = 'Completed' THEN 1 END) as Completed_Claims
                    FROM receivers r
                    LEFT JOIN claims c ON r.Receiver_ID = c.Receiver_ID
                    GROUP BY r.Receiver_ID, r.Name, r.Type
                    ORDER BY Total_Claims DESC
                    LIMIT 20
                """
            },
            
            "5. Total Food Quantity Available": {
                "description": "Total quantity of food available from all providers",
                "query": """
                    SELECT 
                        SUM(Quantity) as Total_Food_Quantity,
                        COUNT(Food_ID) as Total_Food_Items,
                        AVG(Quantity) as Average_Quantity_Per_Item
                    FROM food_listings
                """
            },
            
            "6. Cities with Most Food Listings": {
                "description": "Which city has the highest number of food listings?",
                "query": """
                    SELECT 
                        Location as City,
                        COUNT(Food_ID) as Total_Listings,
                        SUM(Quantity) as Total_Quantity
                    FROM food_listings
                    GROUP BY Location
                    ORDER BY Total_Listings DESC
                """
            },
            
            "7. Most Common Food Types": {
                "description": "Most commonly available food types",
                "query": """
                    SELECT 
                        Food_Type,
                        COUNT(Food_ID) as Listing_Count,
                        SUM(Quantity) as Total_Quantity,
                        ROUND(COUNT(Food_ID) * 100.0 / (SELECT COUNT(*) FROM food_listings), 2) as Percentage
                    FROM food_listings
                    GROUP BY Food_Type
                    ORDER BY Listing_Count DESC
                """
            },
            
            "8. Claims per Food Item": {
                "description": "How many food claims have been made for each food item?",
                "query": """
                    SELECT 
                        fl.Food_Name,
                        fl.Food_Type,
                        fl.Quantity as Available_Quantity,
                        COUNT(c.Claim_ID) as Total_Claims,
                        p.Name as Provider_Name
                    FROM food_listings fl
                    LEFT JOIN claims c ON fl.Food_ID = c.Food_ID
                    JOIN providers p ON fl.Provider_ID = p.Provider_ID
                    GROUP BY fl.Food_ID, fl.Food_Name, fl.Food_Type, fl.Quantity, p.Name
                    ORDER BY Total_Claims DESC
                """
            },
            
            "9. Providers with Most Successful Claims": {
                "description": "Which provider has had the highest number of successful food claims?",
                "query": """
                    SELECT 
                        p.Name as Provider_Name,
                        p.Type as Provider_Type,
                        p.City,
                        COUNT(c.Claim_ID) as Total_Claims,
                        COUNT(CASE WHEN c.Status = 'Completed' THEN 1 END) as Successful_Claims,
                        ROUND(COUNT(CASE WHEN c.Status = 'Completed' THEN 1 END) * 100.0 / COUNT(c.Claim_ID), 2) as Success_Rate
                    FROM providers p
                    JOIN food_listings fl ON p.Provider_ID = fl.Provider_ID
                    LEFT JOIN claims c ON fl.Food_ID = c.Food_ID
                    GROUP BY p.Provider_ID, p.Name, p.Type, p.City
                    HAVING COUNT(c.Claim_ID) > 0
                    ORDER BY Successful_Claims DESC
                """
            },
            
            "10. Claim Status Distribution": {
                "description": "Percentage of food claims completed vs pending vs canceled",
                "query": """
                    SELECT 
                        Status,
                        COUNT(*) as Count,
                        ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM claims), 2) as Percentage
                    FROM claims
                    GROUP BY Status
                    ORDER BY Count DESC
                """
            },
            
            "11. Average Food Claimed per Receiver": {
                "description": "Average quantity of food claimed per receiver",
                "query": """
                    SELECT 
                        r.Name as Receiver_Name,
                        r.Type as Receiver_Type,
                        COUNT(c.Claim_ID) as Total_Claims,
                        AVG(fl.Quantity) as Average_Quantity_Claimed,
                        SUM(fl.Quantity) as Total_Quantity_Claimed
                    FROM receivers r
                    JOIN claims c ON r.Receiver_ID = c.Receiver_ID
                    JOIN food_listings fl ON c.Food_ID = fl.Food_ID
                    WHERE c.Status = 'Completed'
                    GROUP BY r.Receiver_ID, r.Name, r.Type
                    ORDER BY Total_Quantity_Claimed DESC
                """
            },
            
            "12. Most Claimed Meal Types": {
                "description": "Which meal type is claimed the most?",
                "query": """
                    SELECT 
                        fl.Meal_Type,
                        COUNT(c.Claim_ID) as Total_Claims,
                        COUNT(CASE WHEN c.Status = 'Completed' THEN 1 END) as Completed_Claims,
                        SUM(fl.Quantity) as Total_Quantity_Claimed
                    FROM food_listings fl
                    LEFT JOIN claims c ON fl.Food_ID = c.Food_ID
                    GROUP BY fl.Meal_Type
                    ORDER BY Total_Claims DESC
                """
            },
            
            "13. Total Food Donated by Provider": {
                "description": "Total quantity of food donated by each provider",
                "query": """
                    SELECT 
                        p.Name as Provider_Name,
                        p.Type as Provider_Type,
                        p.City,
                        COUNT(fl.Food_ID) as Total_Food_Items,
                        SUM(fl.Quantity) as Total_Quantity_Donated,
                        AVG(fl.Quantity) as Average_Quantity_Per_Item
                    FROM providers p
                    LEFT JOIN food_listings fl ON p.Provider_ID = fl.Provider_ID
                    GROUP BY p.Provider_ID, p.Name, p.Type, p.City
                    ORDER BY Total_Quantity_Donated DESC
                """
            },
            
            "14. Food Expiry Analysis": {
                "description": "Analysis of food items by expiry dates",
                "query": """
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
                    ORDER BY 
                        CASE Expiry_Status
                            WHEN 'Expired' THEN 1
                            WHEN 'Expiring Soon' THEN 2
                            WHEN 'Expiring This Week' THEN 3
                            ELSE 4
                        END
                """
            },
            
            "15. Monthly Claim Trends": {
                "description": "Food claims trends by month and status",
                "query": """
                    SELECT 
                        strftime('%Y-%m', Timestamp) as Month,
                        Status,
                        COUNT(*) as Claim_Count
                    FROM claims
                    WHERE Timestamp IS NOT NULL
                    GROUP BY strftime('%Y-%m', Timestamp), Status
                    ORDER BY Month, Status
                """
            }
        }
    
    @staticmethod
    def get_query_by_number(query_number):
        """Get a specific query by its number (1-15)"""
        queries = SQLQueries.get_all_queries()
        query_keys = list(queries.keys())
        
        if 1 <= query_number <= len(query_keys):
            key = query_keys[query_number - 1]
            return key, queries[key]
        else:
            return None, None
    
    @staticmethod
    def get_modified_query_for_sqlite(original_query):
        """Modify queries to work with SQLite (handle FULL OUTER JOIN)"""
        # Replace FULL OUTER JOIN with UNION for SQLite compatibility
        if "FULL OUTER JOIN" in original_query:
            # For the providers and receivers by city query
            return """
                SELECT 
                    City,
                    SUM(Provider_Count) as Provider_Count,
                    SUM(Receiver_Count) as Receiver_Count
                FROM (
                    SELECT City, COUNT(*) as Provider_Count, 0 as Receiver_Count 
                    FROM providers 
                    GROUP BY City
                    UNION ALL
                    SELECT City, 0 as Provider_Count, COUNT(*) as Receiver_Count 
                    FROM receivers 
                    GROUP BY City
                )
                GROUP BY City
                ORDER BY Provider_Count DESC, Receiver_Count DESC
            """
        return original_query
