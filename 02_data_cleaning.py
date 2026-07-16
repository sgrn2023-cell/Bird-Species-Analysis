
import pandas as pd
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

def load_csv_files():    
    try:
        # Load CSV files
        df_forest = pd.read_csv(r'D:\Bird_Species_Project_2\Bird_Monitoring_Data_FOREST_All_data.csv.csv', dtype=str)
        print(f" Forest data loaded: {len(df_forest)} rows, {len(df_forest.columns)} columns")

        df_grassland = pd.read_csv(r'D:\Bird_Species_Project_2\Bird_Monitoring_Data_GRASSLAND_All_data.csv.csv', dtype=str)
        print(f" Grassland data loaded: {len(df_grassland)} rows, {len(df_grassland.columns)} columns")
        print(f" Total records: {len(df_forest) + len(df_grassland)}")
        return df_forest, df_grassland
    except Exception as error:
        print(f" Error loading CSV files: {error}")
        return None, None
    
# clean_data(df)
def clean_data(df, dataset_name):
    print(f"\n Cleaning {dataset_name} dataset")
    initial_rows = len(df)
    print(f"Initial records: {initial_rows}")
    # Standardize Column Names
    df.columns = (df.columns.str.strip().str.lower().str.replace(' ', '_'))
    # Remove Empty Rows
    df = df.dropna(how='all')
    # Remove Duplicate Rows
    duplicate_count = df.duplicated().sum()
    df = df.drop_duplicates()
    print(f" Removed {duplicate_count} duplicate rows")
    # Handle Missing Values - Text Columns
    text_columns = ['observer','id_method','sex','common_name','scientific_name','sky','wind','disturbance' ]
    for col in text_columns:
        if col in df.columns:
            missing_count = df[col].isna().sum()
            if missing_count > 0:
                df[col] = df[col].fillna('Unknown')
                print(f"{col}: missing values filled")
    # Handle Missing Values - Numeric Columns
    numeric_columns = ['temperature','humidity','initial_three_min_cnt','visit','acceptedtsn','year']
    for col in numeric_columns:
        if col in df.columns:
            df[col] = pd.to_numeric( df[col], errors='coerce' )
            missing_count = df[col].isna().sum()
            if missing_count > 0:
                median_val = df[col].median()
                df[col] = df[col].fillna(median_val)
                print(f" Filled {missing_count} missing values in '{col}' with median: {median_val}")
    # Handle Boolean Columns
    boolean_columns = ['flyover_observed', 'pif_watchlist_status','regional_stewardship_status']
    for col in boolean_columns:
        if col in df.columns:
            missing_count = df[col].isna().sum()
            df[col] = df[col].astype(str).str.upper().map({ 'TRUE': True, 'FALSE': False, '1': True, '0': False }).fillna(False)
            print(f" Filled {missing_count} missing values in '{col}' with False")
    # Add Habitat Column
    df['habitat'] = dataset_name
    final_rows = len(df)
    print(f" Cleaning complete for {dataset_name}")
    print(f" Final rows: {final_rows}")
    print(f" Removed rows: {initial_rows - final_rows}")
    return df
   
# preprocess_dates(df)
def preprocess_dates(df, dataset_name):
    print(f"\n Preprocessing date columns for {dataset_name} dataset")
    # Convert Date Column
    if 'date' in df.columns:
         df['date'] = pd.to_datetime( df['date'], errors='coerce').dt.date
         print(" Date column converted")
    # Convert Start Time
    if 'start_time' in df.columns:
        df['start_time'] = pd.to_datetime( df['start_time'], errors='coerce' ).dt.time
        print(" Start time converted")
    # Convert End Time
    if 'end_time' in df.columns:
        df['end_time'] = pd.to_datetime( df['end_time'], errors='coerce' ).dt.time
        print(" End time converted")
    return df
# preprocess_data_types(df)
def preprocess_data_types(df, dataset_name):
    print(f"\n Preprocessing data types for {dataset_name} dataset")
    # Numeric Columns
    numeric_columns = ['temperature','humidity','initial_three_min_cnt','year','visit', 'acceptedtsn']
    for col in numeric_columns:
        if col in df.columns:
            try:
                df[col] = pd.to_numeric(df[col],errors='coerce')
                print(f" Converted '{col}' to numeric")
            except Exception as e:
                print(f" Error converting '{col}': {e}")
    # Boolean Columns
    boolean_columns = ['flyover_observed', 'pif_watchlist_status','regional_stewardship_status']
    for col in boolean_columns:
        if col in df.columns:
            try:
                df[col] = (df[col].astype(str).str.upper().map({'TRUE': True,'FALSE': False,'1': True,'0': False}))
                print(f" Converted '{col}' to boolean")
            except Exception as e:
                print(f" Error converting '{col}': {e}")
    print(" Data type conversion complete")
    return df

# insert_data_to_mysql
def insert_data_to_mysql(df, table_name, batch_size=100):
    try:
        connection = mysql.connector.connect(
    host='localhost',
    port=3306,
    user='root',
    password='root123',
    database='bird_species_db'
)
        cursor = connection.cursor()
        columns = df.columns.tolist()
        columns_str = ', '.join(columns)
        placeholders = ', '.join(['%s'] * len(columns))
        insert_query = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})"
        # Convert NaN / NaT values to None (important for MySQL)
        df = df.astype(object).where(pd.notnull(df), None)
        data_tuples = [tuple(row) for row in df.itertuples(index=False, name=None)]
        total_records = len(data_tuples)
        total_batches = (total_records + batch_size - 1) // batch_size
        
        print(f"Inserting {total_records} records in {total_batches} batches...")
        
        inserted = 0
        for i in range(0, len(data_tuples), batch_size):
            batch = data_tuples[i:i + batch_size]
            cursor.executemany(insert_query, batch)
            inserted += len(batch)
            current_batch = (i // batch_size) + 1
            print(f"  Batch {current_batch}/{total_batches}: {inserted}/{total_records} records inserted")
        connection.commit()
        
        print(f"All {inserted} records inserted successfully into {table_name}")
        
        cursor.close()
        connection.close()
        return inserted
    except mysql.connector.Error as error:
        print(f"Error inserting data: {error}")
        if connection.is_connected():
            connection.rollback()
        return 0
# save_cleaned_data_to_csv(df_forest, df_grassland)
def save_cleaned_data_to_csv(df_forest, df_grassland):
    try:
        os.makedirs('output', exist_ok=True)
        forest_path = "output/cleaned_forest_data.csv"
        grassland_path = "output/cleaned_grassland_data.csv"
        combined_path = "output/cleaned_combined_data.csv"
        # Save files
        df_forest.to_csv(forest_path, index=False)
        df_grassland.to_csv(grassland_path, index=False)
        pd.concat([df_forest, df_grassland], ignore_index=True ).to_csv(combined_path, index=False)
        print("\n Cleaned CSV files saved successfully!")
    except Exception as error:
        print(f" Error saving files: {error}")

def create_database_and_tables():
    print("Creating database and tables...")
    connection = mysql.connector.connect(host='localhost', user='root', password='root123')
    cursor = connection.cursor()
    cursor.execute("CREATE DATABASE IF NOT EXISTS bird_species_db")
    cursor.execute("USE bird_species_db")
    cursor.execute("""CREATE TABLE IF NOT EXISTS bird_forest_observations (
        id INT AUTO_INCREMENT PRIMARY KEY
    )    """)
    cursor.execute("""  CREATE TABLE IF NOT EXISTS bird_grassland_observations (
        id INT AUTO_INCREMENT PRIMARY KEY
    )   """)
    connection.commit()
    cursor.close()
    connection.close()
    print("Database and tables created successfully")

# MAIN EXECUTION BLOCK
if __name__ == "__main__":
    #  LOAD DATA
    df_forest, df_grassland = load_csv_files()
    if df_forest is None or df_grassland is None:
        print("\nFailed to load CSV files. Exiting...")
        sys.exit(1)
    # CLEAN  DATA
    df_forest = clean_data(df_forest, "Forest")
    df_grassland = clean_data(df_grassland, "Grassland")
     
    #  PREPROCESS DATA
    df_forest = preprocess_dates(df_forest, "Forest")
    df_grassland = preprocess_dates(df_grassland, "Grassland")
    
    df_forest = preprocess_data_types(df_forest, "Forest")
    df_grassland = preprocess_data_types(df_grassland, "Grassland")

    #  SAVE SEPARATE FILES
    os.makedirs("output", exist_ok=True)
    df_forest.to_csv("output/cleaned_forest_data.csv", index=False)
    df_grassland.to_csv("output/cleaned_grassland_data.csv", index=False)

    print("Separate datasets saved successfully!")

    #  SAVE COMBINED DATASET
    final_df = pd.concat([df_forest, df_grassland], ignore_index=True)
    final_df.to_csv("cleaned_bird_dataset.csv", index=False)

    print("Combined dataset saved successfully!")
    
    #  INSERT INTO MYSQL
    forest_inserted = insert_data_to_mysql(df_forest, 'bird_forest_observations')
    grassland_inserted = insert_data_to_mysql(df_grassland, 'bird_grassland_observations')

    #  SAVE CLEANED FILES
    print(" DATA CLEANING AND PREPROCESSING COMPLETE!")
    print(f" Forest records inserted: {forest_inserted}")
    print(f" Grassland records inserted: {grassland_inserted}")
    print(f" Total records processed: {forest_inserted + grassland_inserted}")
