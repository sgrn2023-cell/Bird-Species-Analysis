import streamlit as st
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
    try:
        connection = mysql.connector.connect(
            host='localhost',           
            user='root',                
            password='root123',            
            database='bird_species_db'  
        )
        
        if connection.is_connected():
            db_info = connection.get_server_info()
            print(f" Successfully connected to MySQL Server version {db_info}")
            print(f" Database: bird_species_db")
        return connection
    except mysql.connector.Error as error:
        print(f" Error connecting to MySQL: {error}")
        return None
    
# create_database_and_tables()
def create_database_and_tables():
    try:
        connection = mysql.connector.connect(
            host='localhost',   
            user='root',       
            password='root123'     
        )
        cursor = connection.cursor()
        cursor.execute("CREATE DATABASE IF NOT EXISTS bird_species_db")
        cursor.execute("USE bird_species_db")
        cursor.execute("""
        CREATE TABLE bird_forest_observations (
            id INT AUTO_INCREMENT PRIMARY KEY,
            Admin_Unit_Code VARCHAR(10), Sub_Unit_Code VARCHAR(10), Site_Name VARCHAR(100),
            Plot_Name VARCHAR(50), Location_Type VARCHAR(50), Year INT, Date DATE,
            Start_Time TIME, End_Time TIME, Observer VARCHAR(100), Visit INT,
            Interval_Length VARCHAR(20), ID_Method VARCHAR(50), Distance VARCHAR(30),
            Flyover_Observed BOOLEAN, Sex VARCHAR(20), Common_Name VARCHAR(100),
            Scientific_Name VARCHAR(100), AcceptedTSN INT, NPSTaxonCode VARCHAR(20),
            AOU_Code VARCHAR(10), PIF_Watchlist_Status BOOLEAN,
            Regional_Stewardship_Status BOOLEAN, Temperature FLOAT, Humidity FLOAT,
            Sky VARCHAR(50), Wind VARCHAR(100), Disturbance VARCHAR(100),
            Initial_Three_Min_Cnt INT,habitat VARCHAR(50)
        )
        """)

        cursor.execute("""
        CREATE TABLE bird_grassland_observations (
            id INT AUTO_INCREMENT PRIMARY KEY,
            Admin_Unit_Code VARCHAR(10), Sub_Unit_Code VARCHAR(10), Site_Name VARCHAR(100),
            Plot_Name VARCHAR(50), Location_Type VARCHAR(50), Year INT, Date DATE,
            Start_Time TIME, End_Time TIME, Observer VARCHAR(100), Visit INT,
            Interval_Length VARCHAR(20), ID_Method VARCHAR(50), Distance VARCHAR(30),
            Flyover_Observed BOOLEAN, Sex VARCHAR(20), Common_Name VARCHAR(100),
            Scientific_Name VARCHAR(100), AcceptedTSN INT, NPSTaxonCode VARCHAR(20),
            AOU_Code VARCHAR(10), PIF_Watchlist_Status BOOLEAN,
            Regional_Stewardship_Status BOOLEAN, Temperature FLOAT, Humidity FLOAT,
            Sky VARCHAR(50), Wind VARCHAR(100), Disturbance VARCHAR(100),
            Initial_Three_Min_Cnt INT ,habitat VARCHAR(50)
        )
        """)
        connection.commit()
        print(" Database and tables created successfully!")
        cursor.close()
        connection.close()
    except mysql.connector.Error as error:
        print(f" Error creating database: {error}")
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


