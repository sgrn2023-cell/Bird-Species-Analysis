
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

# visualizations.
#  get_mysql_connection()
def get_mysql_connection():
    connection = mysql.connector.connect(
        host='localhost',           
        user='root',                
        password='root123',            
        database='bird_species_db'  
    )
    return connection

# load_data_from_mysql()
def load_data_from_mysql():
    print("\n[STEP 1] Loading Data from MySQL...")
    try:
        connection = get_mysql_connection()
        forest_query = "SELECT * FROM bird_forest_observations"
        df_forest = pd.read_sql(forest_query, connection)
        df_forest['ecosystem'] = 'forest'

        grassland_query = "SELECT * FROM bird_grassland_observations"
        df_grassland = pd.read_sql(grassland_query, connection)
        df_grassland['ecosystem'] = 'grassland'
        
        df_combined = pd.concat([df_forest, df_grassland], ignore_index=True)
        df_combined.columns = (df_combined.columns.str.strip().str.lower().str.replace(' ', '_'))
        print(df_combined.columns)
        df_combined['date'] = pd.to_datetime(df_combined['date'], errors='coerce')
               
        print(f" Total records loaded: {len(df_combined)}")
        print(f" Total unique species: {df_combined['scientific_name'].nunique()}")
        connection.close()
        return df_combined
    except Exception as error:
        print(f" Error loading data: {error}")
        return None
    
#  TOP 10 SPECIES BAR CHART
def viz_1_top_species(df):
    print("\n[VIZ 1] Creating Top 10 Species Bar Chart...")
    try:
        top_species = df['common_name'].value_counts().head(10).reset_index()
        top_species.columns = ['species', 'count']
    
        fig = px.bar( top_species, x='species', y='count', color='count',title='TOP 10 MOST OBSERVED BIRD SPECIES')
        os.makedirs("output/visualizations", exist_ok=True)
        fig.write_html("output/visualizations/01_top_species.html")
        fig.show()
        
    except Exception as error:
        print(f" Error creating visualization 1: {error}")

# TEMPORAL TRENDS - OBSERVATIONS OVER TIME
def viz_2_temporal_trends(df):
    print("\n[VIZ 2] Creating Temporal Trends ")
    try:
        df = df.dropna(subset=['date'])
        df['year_month'] = df['date'].dt.to_period('M').astype(str)
        temporal = df.groupby(['year_month', 'ecosystem']).size().reset_index(name='observations')
        fig = px.line(temporal, x='year_month', y='observations', color='ecosystem',markers=True,
            title='Bird Observations Over Time (Forest vs Grassland)' )
        fig.update_layout( xaxis_tickangle=-45, height=600)
        os.makedirs("output/visualizations", exist_ok=True)
        fig.write_html('output/visualizations/02_temporal_trends.html')
        fig.show()
    except Exception as error:
        print(f" Error creating visualization 2: {error}")

#ECOSYSTEM COMPARISON
def viz_3_ecosystem_comparison(df):
    print("\n[VIZ 3] Ecosystem Comparison...")
    try:
        data = df.groupby('ecosystem').agg(species=('scientific_name', 'nunique'),observations=('scientific_name', 'count')).reset_index()
        fig = px.bar(data, x='ecosystem', y='species', color='ecosystem',title='Forest vs Grassland: Species & Observation Comparison',labels={'value': 'Count', 'variable': 'Metric'},
            color_discrete_sequence=['green', 'orange'])
        fig.update_layout(height=600)
        os.makedirs("output/visualizations", exist_ok=True)
        fig.write_html('output/visualizations/03_ecosystem_comparison.html')
        fig.show()
    except Exception as error:
        print("Error:", error)

#  LOCATION TYPE COMPARISON (Forest vs Grassland)
def viz_4_location_comparison(df):
    print("\n[VIZ 4] Creating Location Type Comparison Chart...")
    try:
        location_comparison = df.groupby(['location_type','ecosystem']).agg(Observations=('scientific_name', 'count'),Unique_Species=('scientific_name', 'nunique')).reset_index()
        #location_counts = df.groupby(['location_type','ecosystem']).size().reset_index(name='Observations')
        #species_by_location = df.groupby(['location_type','ecosystem'])['scientific_name'].nunique().reset_index(name='Unique_Species')
        #location_comparison = pd.merge(location_counts, species_by_location, on='location_type')
        fig = px.bar(location_comparison, x='location_type', y='Observations',color='ecosystem', hover_data=['Unique_Species'], title='HABITAT COMPARISON: FOREST vs GRASSLAND', barmode='group',  # Side-by-side bars
            color_discrete_map={'Observations': 'steelblue', 'Unique_Species': 'coral'})#labels={'location_type': 'Habitat Type', 'value': 'Count'},
        os.makedirs("output/visualizations", exist_ok=True)
        fig.write_html('output/visualizations/04_location_comparison.html')
        fig.show()
    except Exception as error:
        print(f" Error creating visualization 4: {error}")

#  GEOGRAPHIC ANALYSIS - OBSERVATIONS BY ADMIN UNIT
def viz_5_geographic_analysis(df):
    print("\n[VIZ 5] Creating Geographic Analysis (Admin Units)")
    try:
        admin_counts = df.groupby('admin_unit_code').size().reset_index(name='Observations')     
        fig = px.bar(admin_counts, x='admin_unit_code', y='Observations', title='OBSERVATIONS BY GEOGRAPHIC REGION (ADMIN UNITS)', color='Observations', color_continuous_scale='Blues')  # Blue gradient
        os.makedirs("output/visualizations", exist_ok=True)
        fig.write_html('output/visualizations/05_geographic.html')
        fig.show()
    except Exception as error:
        print(f" Error creating visualization 5: {error}")
# Species Richness by Location
def viz_6_species_richness(df):
    print("\n[VIZ 6] Species Richness by Location")
    try:
        data = df.groupby('admin_unit_code').agg(
            unique_species=('common_name', 'nunique'),
            total_observations=('common_name', 'count')
        ).reset_index()
        fig = px.bar(
            data,
            x='admin_unit_code',
            y='unique_species',
            color='total_observations',
            title='Species Richness by Admin Unit',
            color_continuous_scale='Viridis'
        )

        os.makedirs("output/visualizations", exist_ok=True)
        fig.write_html("output/visualizations/06_species_richness.html")
        fig.show()

    except Exception as error:
        print(f"Error in VIZ 6: {error}")

#  SPECIES ANALYSIS - TOP SPECIES BY LOCATION
def viz_7_species_by_location(df):
    print("\n[VIZ 7] Creating Species by Location Analysis")
    try:
        top_species = df['common_name'].value_counts().head(10).index
        filtered_df = df[df['common_name'].isin(top_species)]

        species_location = (filtered_df.groupby(['common_name', 'location_type']).size().reset_index(name='observations'))
        fig = px.bar(
            species_location, x='common_name', y='observations', color='location_type',barmode='group',
            facet_col='location_type', title='Top 10 Species Distribution Across Habitats (Forest vs Grassland)', labels={'Common_Name': 'Species', 'observations': 'Count'})
        fig.update_layout(height=600,xaxis_tickangle=-45)
        os.makedirs("output/visualizations", exist_ok=True)
        fig.write_html('output/visualizations/07_species_by_location.html')
        fig.show()
    except Exception as error:
        print(f"Error creating visualization 7: {error}")

#  ENVIRONMENTAL IMPACT ON OBSERVATIONS
def viz_8_environmental_heatmap(df):
    print("\n[VIZ 8] Creating Environmental Impact ")
    try:
        df['month'] = df['date'].dt.month
        env = df.groupby(['month', 'sky','ecosystem']).size().reset_index(name='observations')

        fig = px.density_heatmap(env,x='sky',y='month',z='observations',facet_col='ecosystem',
            color_continuous_scale='Viridis',title='Environmental Impact on Bird Observations (Forest vs Grassland)')
        fig.update_layout(height=600)
        os.makedirs("output/visualizations", exist_ok=True)
        fig.write_html('output/visualizations/08_environmental.html')
        fig.show()

    except Exception as error:
        print(f"Error creating visualization 8: {error}")

#  SEX RATIO PIE CHART
def viz_9_sex_ratio(df):
    try:
        sex_df = df[df['sex'].notna()]
        sex_counts = sex_df.groupby(['sex', 'ecosystem']).size().reset_index(name='count')
        fig = px.pie(sex_counts, names='sex', values='count',facet_col='ecosystem',
            title='Sex Ratio Distribution (Forest vs Grassland)',hole=0.4 ) # donut style
        os.makedirs("output/visualizations", exist_ok=True)
        fig.write_html('output/visualizations/09_sex_ratio.html')
        fig.show() 
    except Exception as error:
        print(f"Error creating visualization 9: {error}")

# IDENTIFICATION METHOD DISTRIBUTION
def viz_10_id_methods(df):
    print("\n[VIZ 10] Creating Identification Methods")
    try:
        id_data = df.groupby(['id_method', 'ecosystem']).size().reset_index(name='count')
        fig = px.bar( id_data,x='id_method',y='count',color='ecosystem',barmode='group',
            title='Bird Identification Methods (Forest vs Grassland)',labels={'id_method': 'Identification Method', 'count': 'Observations'})
        fig.update_layout(xaxis_tickangle=-45, height=600 )
        os.makedirs("output/visualizations", exist_ok=True)
        fig.write_html('output/visualizations/10_id_methods.html')
        fig.show()    
    except Exception as error:
        print(f" Error creating visualization 10: {error}")

# Clean Environmental Comparison
def viz_11_environmental_comparison(df):
    print("\n[VIZ 11] Environmental Comparison")

    try:
        df['temperature'] = pd.to_numeric(df['temperature'], errors='coerce')
        df['humidity'] = pd.to_numeric(df['humidity'], errors='coerce')

        env = df.groupby('ecosystem').agg(
            avg_temp=('temperature', 'mean'),
            avg_humidity=('humidity', 'mean'),
            total_observations=('common_name', 'count')
        ).reset_index()

        fig = px.bar(
            env,
            x='ecosystem',
            y=['avg_temp', 'avg_humidity'],
            barmode='group',
            title='Environmental Comparison: Forest vs Grassland'
        )

        os.makedirs("output/visualizations", exist_ok=True)
        fig.write_html("output/visualizations/11_environmental_comparison.html")
        fig.show()

    except Exception as error:
        print(f"Error in VIZ 11: {error}")

# MAIN EXECUTION BLOCK
if __name__ == "__main__":
    print("BIRD SPECIES ANALYSIS - DATA VISUALIZATIONS")
    df = load_data_from_mysql()
    print(df.columns)

    if df is None:
        print("\n Failed to load data. Exiting...")
        import sys
        sys.exit(1)
    print("\n[STEP 2] Creating Visualizations...")    
    viz_1_top_species(df)
    viz_2_temporal_trends(df) 
    viz_3_ecosystem_comparison(df)   
    viz_4_location_comparison(df)    
    viz_5_geographic_analysis(df)
    viz_6_species_richness(df)    
    viz_7_species_by_location(df)
    viz_8_environmental_heatmap(df)
    viz_9_sex_ratio(df)
    viz_10_id_methods(df)
    viz_11_environmental_comparison(df)
    print(" ALL VISUALIZATIONS CREATED SUCCESSFULLY!")
    print(" Charts saved to: output/visualizations/")