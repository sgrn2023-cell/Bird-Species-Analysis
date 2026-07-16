
import pandas as pd
import numpy as np
import json
import matplotlib.pyplot as plt  
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

# load_data_from_mysql()
def load_data_from_mysql():
    try:
        connection = get_mysql_connection()
        df_forest = pd.read_sql("SELECT * FROM bird_forest_observations", connection)
        df_grassland = pd.read_sql( "SELECT * FROM bird_grassland_observations", connection)
        df_combined = pd.concat([df_forest, df_grassland], ignore_index=True)
        connection.close()
        return df_combined
    except Exception as error:
        print(f" Error loading data: {error}")
        return None
#  temporal_analysis(df)
def temporal_analysis(df):
    print("\n TEMPORAL ANALYSIS")
    results = {}
    
    try:
        df = df.copy()
        if df.empty:
            print("Dataset is empty")
            return {}
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'], errors='coerce')
            df = df.dropna(subset=['date'])

            df['year'] = df['date'].dt.year
            df['month'] = df['date'].dt.month
            df['day_of_week'] = df['date'].dt.dayofweek
            
            #  YEARLY ANALYSIS
            yearly_counts = df.groupby('year').size().sort_index()
            print("\n1. Observations by Year:",yearly_counts)
            results[ "yearly"]= yearly_counts.to_dict()
            
            #  MONTHLY ANALYSIS 
            monthly_counts = df.groupby('month').size().sort_index()  
            print("\n2. Observations by Month:",monthly_counts)      
            results['monthly'] = monthly_counts.to_dict()
            
            #  SEASONAL ANALYSIS
            def get_season(month):
                if month in [12, 1, 2]:
                    return 'Winter'
                elif month in [3, 4, 5]:
                    return 'Spring'
                elif month in [6, 7, 8]:
                    return 'Summer'
                else:
                    return 'Fall'
            df['season'] = df['month'].apply(get_season)
            seasonal_counts = df.groupby('season').size()
            print("\n3. Observations by Season:",seasonal_counts)
            results['seasonal'] = seasonal_counts.to_dict()
            
            # TREND ANALYSIS
            yearly_trend = df.groupby('year').size()
            print("\n4. Year-over-Year Trend:")
            if len(yearly_trend) > 1:
                yearly_change = yearly_trend.diff()
                print(yearly_change)
            results['trend'] = yearly_trend.to_dict()    
    except Exception as error:
        print(f"Error in temporal analysis: {error}")    
    return results

# spatial_analysis(df)
def spatial_analysis(df):
    print("\nSPATIAL ANALYSIS")
    results = {}
    try:
        df = df.copy()
        if df.empty:
            print("Dataset is empty")
            return {}
        # ADMIN UNIT ANALYSIS
        if 'admin_unit_code' in df.columns:
            admin_counts = df.groupby('admin_unit_code').size().sort_values(ascending=False)
            print("\n1. Observations by Administrative Unit:",admin_counts)
            results['admin_units'] = admin_counts.to_dict()

        # LOCATION TYPE ANALYSIS
        if 'location_type' in df.columns:
            location_counts = df.groupby('location_type').size()
            location_pct = (location_counts / location_counts.sum() * 100).round(2)
            print("\n2. Observations by Location Type:",location_counts)
            print("\nPercentage Distribution:", location_pct)
            results['location_types'] = location_counts.to_dict()
        
        # BIODIVERSITY HOTSPOTS
        if 'scientific_name' in df.columns:
            biodiversity = df.groupby('admin_unit_code')['scientific_name'].nunique().sort_values(ascending=False)
            print("\n3. Species Diversity by Admin Unit (Hotspots):",biodiversity)
            results['hotspots'] = biodiversity.to_dict()
        
        # PLOT ANALYSIS
        if 'plot_name' in df.columns:
            plot_counts = df.groupby('plot_name').size().sort_values(ascending=False).head(10)
            print("\n4. Top 10 Most Visited Plots:",plot_counts)
            results['top_plots'] = plot_counts.to_dict()
        
        # SITE ANALYSIS 
        if 'site_name' in df.columns:
            site_counts = df.groupby('site_name').size().sort_values(ascending=False).head(10)
            print("\n5. Top 10 Most Visited Sites:",site_counts)
            results['top_sites'] = site_counts.to_dict()
    
    except Exception as error:
        print(f" Error in spatial analysis: {error}")
    return results

# species_analysis
def species_analysis(df):
    print("\nSPECIES ANALYSIS")
    results = {}
    try:
        df = df.copy()
        if df.empty:
            print("Dataset is empty")
            return {}
        # DIVERSITY METRICS
        if 'scientific_name' in df.columns:
            results['total_species'] = df['scientific_name'].nunique()
            print(f"\n1. Total Unique Species: {results['total_species']}")
        # TOP 10 MOST OBSERVED SPECIES
        if 'common_name' in df.columns:
            results['top_10_species'] = df.groupby('common_name').size().sort_values(ascending=False).head(10).to_dict()
            print("\n2. Top 10 Most Observed Species:", results['top_10_species'])

        #SPECIES RARITY
        if 'common_name' in df.columns:
            results['rarest_species'] = df.groupby('common_name').size().sort_values(ascending=True).head(10).to_dict()
            print("\n3. Rarest Species:", results['rarest_species'])

        # SEX RATIO ANALYSIS 
        if 'sex' in df.columns:
            sex_ratio = df.groupby('sex').size()
            print("\n4. Sex Ratio:",sex_ratio)
            sex_pct = (sex_ratio / sex_ratio.sum() * 100).round(2)
            print("Percentage:",sex_pct)
            results['sex_ratio'] = sex_ratio.to_dict()

        # AT-RISK SPECIES (PIF WATCHLIST)
        if 'pif_watchlist_status' in df.columns:
            at_risk = df[df['pif_watchlist_status'] == 1]
            at_risk_species = at_risk['common_name'].nunique()
            print(f"\n 5. At-Risk Species (on PIF Watchlist): {at_risk_species}")
            results['at_risk_species'] = at_risk['common_name'].value_counts().head(10).to_dict()
        
        # CONSERVATION PRIORITY 
        if 'regional_stewardship_status' in df.columns:
            conservation = df[df['regional_stewardship_status'] == 1]
            conservation_count = conservation['common_name'].nunique()
            print(f"\n6. Conservation Priority Species: {conservation_count}")
            results['conservation_priority'] = conservation_count
    
    except Exception as error:
        print(f"Error in species analysis: {error}")
    return results

#  environmental_analysis(df)
def environmental_analysis(df):
    results = {}
    try:
        df = df.copy()
        if df.empty:
            print("Dataset is empty")
            return {}
        # TEMPERATURE ANALYSIS
        print("\n1. Temperature Impact:")
        if 'temperature' in df.columns:
            df['temperature'] = pd.to_numeric(df['temperature'], errors='coerce')
            mean_temp = df['temperature'].mean()
            print(f"   Mean Temperature: {mean_temp:.2f}°")
            min_temp = df['temperature'].min()
            max_temp = df['temperature'].max()
            print(f"   Temperature Range: {min_temp:.2f}° to {max_temp:.2f}°")
            df['temp_range'] = pd.cut(df['temperature'], bins=5)
            results['temperature'] = {str(k): v  for k, v in df.groupby('temp_range', observed=False).size().items()}
            print("\n3. Temperature Impact:",results['temperature'])
        
        # HUMIDITY ANALYSIS
        print("\n2. Humidity Impact:")
        if 'humidity' in df.columns:
            df['humidity'] = pd.to_numeric(df['humidity'], errors='coerce')
            mean_humidity = df['humidity'].mean()
            print(f"Mean Humidity: {mean_humidity:.2f}%")
            df['humidity_range'] = pd.cut(df['humidity'], bins=5)
            results['humidity'] = {str(k): v for k, v in df.groupby('humidity_range', observed=False).size().items()}
            print("\n3. Humidity Impact:",results['humidity'])

        #  SKY CONDITION ANALYSIS
        if 'sky' in df.columns:
            results['sky_conditions'] = (df.groupby('sky').size().sort_values(ascending=False).to_dict() )
            print("\n3. Sky Conditions:", results['sky_conditions'])
        
        # WIND ANALYSIS 
        if 'wind' in df.columns:
            results['wind_conditions'] = (df.groupby('wind').size().sort_values(ascending=False).head(5).to_dict())
        #   results['wind_conditions'] = df.groupby('wind').size().sort_values(ascending=False).head(5).to_dict()
            print("\n4. Wind Conditions:", results['wind_conditions'])
        
        # DISTURBANCE EFFECT
        if 'disturbance' in df.columns:
            results['disturbance'] = (df.groupby('disturbance').size().sort_values(ascending=False).to_dict())
            print("\n5. Disturbance Types:", results['disturbance'])

    except Exception as error:
        print(f"Error in environmental analysis: {error}")
    return results

#  behavioral_analysis
def behavioral_analysis(df):
    print("\n BEHAVIORAL ANALYSIS")
    results = {}    
    try:
        df = df.copy()
        if df.empty:
            print("Dataset is empty")
            return {}
        # IDENTIFICATION METHOD 
        if 'id_method' in df.columns: 
            id_method_counts =( df.groupby('id_method').size().sort_values(ascending=False))
            print("\n1. Bird Identification Methods:")
            print(id_method_counts)
            id_method_pct = (id_method_counts / id_method_counts.sum() * 100).round(2)
            print("Percentage:")
            print(id_method_pct)
            results['id_methods'] = id_method_counts.to_dict()
        
        #  DISTANCE DISTRIBUTION 
        if 'distance' in df.columns:
            results['distance'] = (df.groupby('distance').size().sort_values(ascending=False).to_dict())
            print("\n2. Distance Categories:", results['distance'])

        # FLYOVER FREQUENCY
        if 'flyover_observed' in df.columns:
            print("\n3. Flyover Observations:")
            flyover_counts =( df.groupby('flyover_observed').size())
            #print(flyover_counts)       
            flyover_pct = (flyover_counts / flyover_counts.sum() * 100).round(2)
            #print(flyover_pct)
            results['flyover'] = flyover_counts.to_dict()
            print(f"\n  Flyover Observations: {flyover_counts.get(1, 0)} ({flyover_pct.get(1, 0)}%)")
        
        # OBSERVER BIAS
        if 'observer' in df.columns:
            observer_counts = df.groupby('observer').size().sort_values(ascending=False).head(10)
            print("\n4. Top 10 Observers (by observation count):")
            print(observer_counts)
            results['observers'] = observer_counts.to_dict()
            if not observer_counts.empty:
                print(f"\n  Top Observer: {observer_counts.idxmax()} with {observer_counts.max()} observations")

        # VISIT IMPACT 
        if 'visit' in df.columns:
            df['visit'] = pd.to_numeric(df['visit'], errors='coerce')
            visit_counts = df.groupby('visit').size().sort_index()
            print("\n5. Observations by Visit Number:")
            print(visit_counts)        
            results['visits'] = visit_counts.to_dict() 
            if not visit_counts.empty:
                print(f"\n  Most Common Visit Number: {visit_counts.idxmax()} with {visit_counts.max()} observations")
    
    except Exception as error:        
        print(f"Error in behavioral analysis: {error}")    
    return results

# statistical_summary
def statistical_summary(df):
    print("\n STATISTICAL SUMMARY")
    results = {}
    try:
        df = df.copy()
        if df.empty:
            print("Dataset is empty")
            return {}
        # BASIC STATISTICS      
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        # REMOVE IDENTIFIER COLUMNS
        exclude_cols = ['id', 'acceptedtsn']
        numeric_cols = [col for col in numeric_cols if col not in exclude_cols]

        if len(numeric_cols) > 0:
            print("\n1. Numeric Columns Summary:")        
            summary_stats = df[numeric_cols].describe()        
            print(summary_stats)        
            results['numeric_summary'] = summary_stats.to_dict()
        # CORRELATION ANALYSIS
        if len(numeric_cols) > 1:
            correlation_matrix = df[numeric_cols].corr()
            print("\n2. Correlation Matrix:")
            print(correlation_matrix)        
            results['correlations'] = correlation_matrix.to_dict()
        # MISSING VALUES 
        missing = df.isnull().sum()        
        missing_filtered = missing[missing > 0]
        print("\n3. Missing Values:")
        if len(missing_filtered) > 0:
            for col, count in missing_filtered.items():
                pct = (count / len(df)) * 100                
                print(f"{col}: {count} ({pct:.2f}%)")
        else:            
            print(" No missing values found!")       
        results['missing_values'] = missing_filtered.to_dict()
        #DATA QUALITY SCORE
        total_cells = len(df) * len(df.columns)
        if total_cells > 0:
            completeness = (1-(df.isnull().sum().sum() / (len(df) * len(df.columns)))) * 100
            print(f"\n4. Data Completeness: {completeness:.2f}%")
            results['data_quality'] = completeness

    except Exception as error:        
        print(f"Error in statistical summary: {error}") 
    return results

# save_analysis_report
def save_analysis_report(all_results):
    print("\n Saving Analysis Report")
    try:        
        if not os.path.exists('output'):            
            os.makedirs('output')
        output_file = os.path.join('output', 'EDA_Analysis_Report.txt')
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("BIRD SPECIES ANALYSIS - EDA REPORT\n")
            from datetime import datetime
            f.write(f"Report Generated: {datetime.now()}\n\n")
            f.write("OVERALL SUMMARY:\n")
            f.write(f"Total Observations: {all_results['total_obs']}\n")
            f.write(f"Total Species: {all_results['total_species']}\n\n")
            #f.write(str(all_results))
            json.dump(all_results, f,indent=4, default=str)
        print(f"Report saved to: {output_file}")
    except Exception as error:
        print(f" Error saving report: {error}")

# MAIN EXECUTION BLOCK
if __name__ == "__main__":
    print("BIRD SPECIES ANALYSIS - EXPLORATORY DATA ANALYSIS (EDA)")
    df = load_data_from_mysql()
    if df is None:
        print("\nFailed to load data. Exiting...")
        import sys
        sys.exit(1)
    all_results = {}
    all_results['total_obs'] = len(df)
    all_results['total_species'] =(df['scientific_name'].nunique() if 'scientific_name' in df.columns  else 0)
    # HABITAT DISTRIBUTION
    if 'habitat' in df.columns:
        all_results['habitat_distribution'] = (df['habitat'] .value_counts().to_dict())
    all_results['temporal'] = temporal_analysis(df)
    all_results['spatial'] = spatial_analysis(df)
    all_results['species'] = species_analysis(df)
    all_results['environmental'] = environmental_analysis(df)
    all_results['behavioral'] = behavioral_analysis(df)
    all_results['statistics'] = statistical_summary(df)
    save_analysis_report(all_results)
    print(" EXPLORATORY DATA ANALYSIS COMPLETE!")
