
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt 
import seaborn as sns    
import plotly.express as px
import mysql.connector
import time
from datetime import datetime
import sys
import os
import warnings
warnings.filterwarnings('ignore')

def get_mysql_connection():
    connection = mysql.connector.connect(
        host='localhost',
        user='root',
        password='root123',
        database='bird_species_db'
    )    
    return connection

# execute_query(query, description)
def execute_query(query, description):
    print(description)
    connection = None
    try:       
        connection = get_mysql_connection()      
        df_results = pd.read_sql(query, connection) 
        if len(df_results) > 0:            
            print(f"\n Query returned {len(df_results)} rows\n")         
            pd.set_option('display.max_columns', None)  # Show all columns
            pd.set_option('display.max_rows', None)     # Show all rows
            pd.set_option('display.width', None)        # Auto-width            
            print(df_results.to_string(index=False))
        else:            
            print("\n No results found for this query\n")      
        connection.close()     
        return df_results  
    except Exception as error:        
        print(f"\n Error executing query: {error}\n")
        return None
    finally:
        if connection and connection.is_connected():
            connection.close()
    
#  save_query_results
def save_query_results(df, filename):
    if df is not None and not df.empty:
        try:          
            os.makedirs('output', exist_ok=True) 
            df.to_csv(os.path.join('output', filename), index=False)
            print(f"\n Results saved to: {filename}\n")
        except Exception as error:
            print(f"Error saving results: {error}\n")

# TOP 10 MOST OBSERVED SPECIES
def query_1_top_species():
    query = """
    SELECT Common_Name,COUNT(*) as Observation_Count
    FROM bird_forest_observations
    WHERE Common_Name IS NOT NULL
    GROUP BY Common_Name
    ORDER BY Observation_Count DESC
    LIMIT 10
    """
    forest_df = execute_query(query, "QUERY 1: TOP 10 MOST OBSERVED SPECIES (FOREST)")
    
    query_grassland = """
    SELECT Common_Name, COUNT(*) as Observation_Count
    FROM bird_grassland_observations
    WHERE Common_Name IS NOT NULL
    GROUP BY Common_Name
    ORDER BY Observation_Count DESC
    LIMIT 10
    """
    grassland_df = execute_query(query_grassland, "QUERY 1: TOP 10 MOST OBSERVED SPECIES (GRASSLAND)")

    forest_df["Habitat"] = "Forest"
    grassland_df["Habitat"] = "Grassland"
    
    final_df = pd.concat([forest_df, grassland_df], ignore_index=True)

    save_query_results(final_df, "01_ TOP 10 MOST OBSERVED SPECIES_combined.csv")

    print("Query 01 completed successfully!")
    return final_df

# SPECIES COUNT BY LOCATION TYPE
def query_2_species_by_location():
    query_forest = """
    SELECT Location_Type, COUNT(DISTINCT Scientific_Name) as Unique_Species_Count, COUNT(*) as Total_Observations
    FROM bird_forest_observations
    GROUP BY Location_Type
    """
    forest_df = execute_query(query_forest, "QUERY 2: SPECIES DIVERSITY BY LOCATION (FOREST)")
      
    query_grassland = """
    SELECT Location_Type, COUNT(DISTINCT Scientific_Name) as Unique_Species_Count, COUNT(*) as Total_Observations
    FROM bird_grassland_observations
    GROUP BY Location_Type
    """
    grassland_df = execute_query(query_grassland, "QUERY 2: SPECIES DIVERSITY BY LOCATION (GRASSLAND)")
 
    forest_df["Habitat"] = "Forest"
    grassland_df["Habitat"] = "Grassland"
    
    final_df = pd.concat([forest_df, grassland_df], ignore_index=True)

    save_query_results(final_df, "02_species_diversity_combined.csv")

    print("Query 02 completed successfully!")
    return final_df

# OBSERVATIONS BY YEAR AND MONTH
def query_3_temporal_distribution():
    query_forest = """
    SELECT  YEAR(Date) as Year, MONTH(Date) as Month, COUNT(*) as Observation_Count, COUNT(DISTINCT Scientific_Name) as Species_Count
    FROM bird_forest_observations
    WHERE Date IS NOT NULL
    GROUP BY YEAR(Date), MONTH(Date)
    ORDER BY Year DESC, Month DESC
    LIMIT 24
    """
    forest_df = execute_query(query_forest, "QUERY 3: OBSERVATIONS BY YEAR & MONTH (FOREST)")
    
    query_grassland = """
    SELECT  YEAR(Date) as Year, MONTH(Date) as Month, COUNT(*) as Observation_Count, COUNT(DISTINCT Scientific_Name) as Species_Count
    FROM bird_grassland_observations
    WHERE Date IS NOT NULL
    GROUP BY YEAR(Date), MONTH(Date)
    ORDER BY Year DESC, Month DESC
    LIMIT 24
    """
    grassland_df = execute_query(query_grassland, "QUERY 3: OBSERVATIONS BY YEAR & MONTH (GRASSLAND)")
  
    forest_df["Habitat"] = "Forest"
    grassland_df["Habitat"] = "Grassland"
    
    final_df = pd.concat([forest_df, grassland_df], ignore_index=True)

    save_query_results(final_df, "03_temporal_distribution_combined.csv")

    print("Query 03 completed successfully!")
    return final_df

#  AT-RISK SPECIES (PIF WATCHLIST)
def query_4_at_risk_species():
    query_forest = """
    SELECT  Common_Name, Scientific_Name, COUNT(*) as Observation_Count, COUNT(DISTINCT Admin_Unit_Code) as Locations_Found, PIF_Watchlist_Status
    FROM bird_forest_observations
    WHERE PIF_Watchlist_Status = 1
    GROUP BY Common_Name, Scientific_Name
    ORDER BY Observation_Count DESC
    """
    forest_df = execute_query(query_forest, "QUERY 4: AT-RISK SPECIES ON PIF WATCHLIST (FOREST)")
        
    query_grassland = """
    SELECT Common_Name, Scientific_Name, COUNT(*) as Observation_Count,COUNT(DISTINCT Admin_Unit_Code) as Locations_Found, PIF_Watchlist_Status
    FROM bird_grassland_observations
    WHERE PIF_Watchlist_Status = 1
    GROUP BY Common_Name, Scientific_Name
    ORDER BY Observation_Count DESC
    """
    grassland_df = execute_query(query_grassland, "QUERY 4: AT-RISK SPECIES ON PIF WATCHLIST (GRASSLAND)")

    forest_df["Habitat"] = "Forest"
    grassland_df["Habitat"] = "Grassland"
    
    final_df = pd.concat([forest_df, grassland_df], ignore_index=True)

    save_query_results(final_df, "04_at_risk_species_combined.csv")

    print("Query 04 completed successfully!")
    return final_df

#  OBSERVER PERFORMANCE & BIAS
def query_5_observer_performance():
    query_forest = """
    SELECT Observer, COUNT(*) as Total_Observations, COUNT(DISTINCT Common_Name) as Unique_Species_Found, COUNT(DISTINCT DATE(Date)) as Days_Active
    FROM bird_forest_observations
    WHERE Observer != 'Unknown'
    GROUP BY Observer
    ORDER BY Total_Observations DESC
    LIMIT 15
    """
    forest_df = execute_query(query_forest, "QUERY 5: OBSERVER PERFORMANCE (FOREST)")
        
    query_grassland = """
    SELECT Observer,  COUNT(*) as Total_Observations, COUNT(DISTINCT Common_Name) as Unique_Species_Found, COUNT(DISTINCT DATE(Date)) as Days_Active
    FROM bird_grassland_observations
    WHERE Observer != 'Unknown'
    GROUP BY Observer
    ORDER BY Total_Observations DESC
    LIMIT 15
    """
    grassland_df = execute_query(query_grassland, "QUERY 5: OBSERVER PERFORMANCE (GRASSLAND)")
    
    forest_df["Habitat"] = "Forest"
    grassland_df["Habitat"] = "Grassland"
    
    final_df = pd.concat([forest_df, grassland_df], ignore_index=True)

    save_query_results(final_df, "05_observer_performance_combined.csv")

    print("Query 05 completed successfully!")
    return final_df
#  ENVIRONMENTAL CONDITIONS IMPACT
def query_6_environmental_conditions():
    query_forest = """
    SELECT  Sky, Wind, COUNT(*) as Observation_Count, ROUND(AVG(Temperature), 2) as Avg_Temperature, ROUND(AVG(Humidity), 2) as Avg_Humidity,COUNT(DISTINCT Common_Name) as Species_Observed
    FROM bird_forest_observations
    WHERE Sky IS NOT NULL AND Wind IS NOT NULL
    GROUP BY Sky, Wind
    ORDER BY Observation_Count DESC
    LIMIT 20
    """
    forest_df = execute_query(query_forest, "QUERY 6: ENVIRONMENTAL CONDITIONS IMPACT (FOREST)")
    
    query_grassland = """
    SELECT  Sky, Wind, COUNT(*) as Observation_Count, ROUND(AVG(Temperature), 2) as Avg_Temperature, ROUND(AVG(Humidity), 2) as Avg_Humidity, COUNT(DISTINCT Common_Name) as Species_Observed
    FROM bird_grassland_observations
    WHERE Sky IS NOT NULL AND Wind IS NOT NULL
    GROUP BY Sky, Wind
    ORDER BY Observation_Count DESC
    LIMIT 20
    """
    grassland_df = execute_query(query_grassland, "QUERY 6: ENVIRONMENTAL CONDITIONS IMPACT (GRASSLAND)")
 
    forest_df["Habitat"] = "Forest"
    grassland_df["Habitat"] = "Grassland"
    
    final_df = pd.concat([forest_df, grassland_df], ignore_index=True)

    save_query_results(final_df, "06_environmental_conditions_combined.csv")

    print("Query 06 completed successfully!")
    return final_df

#  SEX RATIO BY SPECIES
def query_7_sex_ratio():
    query_forest = """
    SELECT Common_Name, Scientific_Name, Sex, COUNT(*) as Count
    FROM bird_forest_observations
    WHERE Sex != 'Unknown'
    GROUP BY Common_Name, Scientific_Name, Sex
    ORDER BY Count DESC, Scientific_Name
    LIMIT 30
    """    
    forest_df = execute_query(query_forest, "QUERY 7: SEX RATIO BY SPECIES (FOREST)")
    #save_query_results(results_forest, "07_sex_ratio_forest.csv")
    
    # GRASSLAND VERSION
    query_grassland = """
    SELECT Common_Name, Scientific_Name, Sex, COUNT(*) as Count
    FROM bird_grassland_observations
    WHERE Sex != 'Unknown'
    GROUP BY Common_Name, Scientific_Name, Sex
    ORDER BY Scientific_Name, Count DESC
    LIMIT 30
    """
    grassland_df = execute_query(query_grassland, "QUERY 7: SEX RATIO BY SPECIES (GRASSLAND)")
  
    forest_df["Habitat"] = "Forest"
    grassland_df["Habitat"] = "Grassland"
    
    final_df = pd.concat([forest_df, grassland_df], ignore_index=True)

    save_query_results(final_df, "07_sex_ratio_combined.csv")

    print("Query 07 completed successfully!")
    return final_df
# DISTANCE ANALYSIS
def query_8_distance_analysis():
    query_forest = """
    SELECT  Distance, COUNT(*) as Observation_Count, ROUND(AVG(Initial_Three_Min_Cnt), 2) as Avg_Species_Count, COUNT(DISTINCT Common_Name) as Unique_Species
    FROM bird_forest_observations
    WHERE Distance IS NOT NULL AND Distance != 'Unknown'
    GROUP BY Distance
    ORDER BY Observation_Count DESC
    """
    forest_df = execute_query(query_forest, "QUERY 8: DISTANCE ANALYSIS (FOREST)")
      
    query_grassland = """
    SELECT Distance, COUNT(*) as Observation_Count, ROUND(AVG(Initial_Three_Min_Cnt), 2) as Avg_Species_Count, COUNT(DISTINCT Common_Name) as Unique_Species
    FROM bird_grassland_observations
    WHERE Distance IS NOT NULL AND Distance != 'Unknown'
    GROUP BY Distance
    ORDER BY Observation_Count DESC
    """
    grassland_df = execute_query(query_grassland, "QUERY 8: DISTANCE ANALYSIS (GRASSLAND)")
  
    forest_df["Habitat"] = "Forest"
    grassland_df["Habitat"] = "Grassland"
    
    final_df = pd.concat([forest_df, grassland_df], ignore_index=True)

    save_query_results(final_df, "08_distance_analysis_combined.csv")

    print("Query 08 completed successfully!")
    return final_df

#  BIODIVERSITY HOTSPOTS
def query_9_biodiversity_hotspots():
    query_forest = """
    SELECT  Admin_Unit_Code, Plot_Name, COUNT(DISTINCT Scientific_Name) as Unique_Species, COUNT(*) as Total_Observations,COUNT(DISTINCT DATE(Date)) as Days_Sampled
    FROM bird_forest_observations
    GROUP BY Admin_Unit_Code, Plot_Name
    ORDER BY Unique_Species DESC
    """
    forest_df = execute_query(query_forest, "QUERY 9: BIODIVERSITY HOTSPOTS (FOREST)")  
     if forest_df is None:
      print("Forest query failed")
      return

    query_grassland = """
    SELECT Admin_Unit_Code, Plot_Name, COUNT(DISTINCT Scientific_Name) as Unique_Species, COUNT(*) as Total_Observations, COUNT(DISTINCT DATE(Date)) as Days_Sampled
    FROM bird_grassland_observations
    GROUP BY Admin_Unit_Code, Plot_Name
    ORDER BY Unique_Species DESC
    """
    grassland_df = execute_query(query_grassland, "QUERY 9: BIODIVERSITY HOTSPOTS (GRASSLAND)")
    if grassland_df is None:
      print("Grassland query failed")
      return

    forest_df["Habitat"] = "Forest"
    grassland_df["Habitat"] = "Grassland"
    
    final_df = pd.concat([forest_df, grassland_df], ignore_index=True)

    save_query_results(final_df, "09_biodiversity_hotspots_combined.csv")

    print("Query 09 completed successfully!")
    return final_df
#  IDENTIFICATION METHOD ANALYSIS
def query_10_identification_methods():
    query_forest = """
    SELECT ID_Method, COUNT(*) as Usage_Count, COUNT(DISTINCT Common_Name) as Species_Identified, ROUND((COUNT(*) * 100 / (SELECT COUNT(*) FROM bird_forest_observations)), 2) as Percentage
    FROM bird_forest_observations
    WHERE ID_Method IS NOT NULL AND ID_Method != 'Unknown'
    GROUP BY ID_Method
    ORDER BY Usage_Count DESC
    """
    forest_df = execute_query(query_forest, "QUERY 10: IDENTIFICATION METHOD ANALYSIS (FOREST)")
       
    query_grassland = """
    SELECT ID_Method, COUNT(*) as Usage_Count, COUNT(DISTINCT Common_Name) as Species_Identified, ROUND((COUNT(*) * 100 / (SELECT COUNT(*) FROM bird_grassland_observations)), 2) as Percentage
    FROM bird_grassland_observations
    WHERE ID_Method IS NOT NULL AND ID_Method != 'Unknown'
    GROUP BY ID_Method
    ORDER BY Usage_Count DESC
    """
    grassland_df = execute_query(query_grassland, "QUERY 10: IDENTIFICATION METHOD ANALYSIS (GRASSLAND)")
 
    forest_df["Habitat"] = "Forest"
    grassland_df["Habitat"] = "Grassland"

    final_df = pd.concat([forest_df, grassland_df], ignore_index=True)

    save_query_results(final_df, "10_identification_methods_combined.csv")

    print("Query 10 completed successfully!")
    return final_df
#  Species Richness by Habitat
def query_11_species_richness():
    query = """
    SELECT 'Forest' AS Habitat, COUNT(*) AS Total_Observations,
        COUNT(DISTINCT Scientific_Name) AS Unique_Species,
        ROUND(COUNT(*) / COUNT(DISTINCT Scientific_Name), 2) AS Avg_Observations_Per_Species
    FROM bird_forest_observations
    UNION ALL
    SELECT 'Grassland' AS Habitat, COUNT(*) AS Total_Observations, COUNT(DISTINCT Scientific_Name) AS Unique_Species,
        ROUND(COUNT(*) / COUNT(DISTINCT Scientific_Name),2) AS Avg_Observations_Per_Species
    FROM bird_grassland_observations  """

    final_df = execute_query(query, "QUERY 11: SPECIES RICHNESS BY HABITAT")
    save_query_results( final_df,"11_species_richness.csv")
    return final_df
 
# Seasonal Species Diversity
def query_12_Seasonal_Species_Diversity():
    query = """
    SELECT 'Forest' AS Habitat, MONTH(Date) AS Month_Number, DATE_FORMAT(Date, '%b') AS Month_Name,
            COUNT(DISTINCT Scientific_Name) AS Unique_Species
    FROM bird_forest_observations
    WHERE Date IS NOT NULL
    GROUP BY MONTH(Date), DATE_FORMAT(Date, '%b')
UNION ALL
SELECT
    'Grassland' AS Habitat, MONTH(Date) AS Month_Number, DATE_FORMAT(Date, '%b') AS Month_Name,
        COUNT(DISTINCT Scientific_Name) AS Unique_Species
    FROM bird_grassland_observations
    WHERE Date IS NOT NULL
    GROUP BY MONTH(Date), DATE_FORMAT(Date, '%b')
    ORDER BY Month_Number, Habitat"""
    
    final_df = execute_query(query, "QUERY 12: SEASONAL SPECIES DIVERSITY")
    save_query_results( final_df,"12_seasonal_species_diversity.csv")
    return final_df
# MAIN EXECUTION BLOCK
if __name__ == "__main__":
    print("BIRD SPECIES ANALYSIS - SQL QUERIES")

    print("\n[EXECUTING] Query 1: Top 10 Most Observed Species")
    query_1_top_species()    
    print("\n[EXECUTING] Query 2: Species by Location Type")
    query_2_species_by_location()
    print("\n[EXECUTING] Query 3: Temporal Distribution (Year & Month)")
    query_3_temporal_distribution()
    print("\n[EXECUTING] Query 4: At-Risk Species (PIF Watchlist)")
    query_4_at_risk_species()
    print("\n[EXECUTING] Query 5: Observer Performance & Bias")
    query_5_observer_performance()
    print("\n[EXECUTING] Query 6: Environmental Conditions Impact")
    query_6_environmental_conditions()
    print("\n[EXECUTING] Query 7: Sex Ratio by Species")
    query_7_sex_ratio()    
    print("\n[EXECUTING] Query 8: Distance Analysis")
    query_8_distance_analysis()    
    print("\n[EXECUTING] Query 9: Biodiversity Hotspots")
    query_9_biodiversity_hotspots()
    print("\n[EXECUTING] Query 10: Identification Methods")
    query_10_identification_methods()
    print("\n[EXECUTING] Query 11: Species Richness by Habitat")
    query_11_species_richness()
    print("\n[EXECUTING] Query 12: Seasonal Species Diversity")
    query_12_Seasonal_Species_Diversity()
    
    print(" ALL SQL QUERIES EXECUTED SUCCESSFULLY!")
    print(" Results saved to output/ folder")

    df1 = query_1_top_species()
    df2 = query_2_species_by_location()
    df3 = query_3_temporal_distribution()
    df4 = query_4_at_risk_species()
    df5 = query_5_observer_performance()
    df6 = query_6_environmental_conditions()    
    df7 = query_7_sex_ratio()
    df8 = query_8_distance_analysis()
    df9 = query_9_biodiversity_hotspots()
    df10 = query_10_identification_methods()
    df11 = query_11_species_richness()
    df12 = query_12_Seasonal_Species_Diversity()

all_sql_results = pd.concat(
    [df1, df2, df3, df4, df5, df6,
     df7, df8, df9, df10, df11, df12],
    ignore_index=True)

all_sql_results.to_csv("output/final_sql_analysis.csv", index=False)
