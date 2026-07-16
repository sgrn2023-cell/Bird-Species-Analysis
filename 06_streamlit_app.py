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
    connection = mysql.connector.connect(
        host='localhost',           
        user='root',                
        password='root123',            
        database='bird_species_db'  
    )
    return connection

def chart_key(page, name):
    return f"{page}_{name}"

# STREAMLIT PAGE SETTINGS
st.set_page_config(
    page_title="Bird Species Analysis",
    page_icon="🦅",
    layout="wide",
    initial_sidebar_state="expanded"
)

# load_all_data()
@st.cache_data  
def load_all_data():
    print("Loading data from database...")
    try:
        connection = get_mysql_connection()
        # FOREST DATA
        forest_query = "SELECT * FROM bird_forest_observations"
        df_forest = pd.read_sql(forest_query, connection)
        df_forest['ecosystem'] = 'forest'

        # GRASSLAND DATA
        grassland_query = "SELECT * FROM bird_grassland_observations"
        df_grassland = pd.read_sql(grassland_query, connection)
        df_grassland['ecosystem'] = 'grassland'
        # Combine datasets
        df_combined = pd.concat([df_forest, df_grassland], ignore_index=True)
        # STANDARDIZE COLUMN NAMES
        df_combined.columns = ( df_combined.columns .str.strip() .str.lower() .str.replace(' ', '_'))
        print(df_combined.columns)
         # Date handling
        df_combined['date'] = pd.to_datetime(df_combined['date'], errors='coerce')
         # Time features
        df_combined['year'] = df_combined['date'].dt.year
        df_combined['month'] = df_combined['date'].dt.month
        
        connection.close()
        return df_combined
    except Exception as error:
        st.error(f"Database error: {error}")
        return pd.DataFrame()
    
#  HOME PAGE
def page_home(df):
    st.title("🦅 Bird Species Analysis Dashboard")
    
    st.markdown("""
    ### Welcome to the Bird Species Observation Analysis System
    
    This dashboard provides comprehensive analysis of bird species observations across:
    - **Forest Ecosystems**
    - **Grassland Ecosystems**
    
    Explore patterns in biodiversity, conservation priorities, and ecological insights.
    """)
    def chart_key(page, name):
       return f"{page}_{name}"
    PAGE = "home"
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Observations", f"{len(df):,}")
    col2.metric("Unique Species", df['scientific_name'].nunique())
    col3.metric("Forest Observations",len(df[df['ecosystem'] == 'forest']))
    col4.metric("Grassland Observations",len(df[df['ecosystem'] == 'grassland']))
   
    st.subheader("Top 10 Most Observed Species")
    top_species_names = df['common_name'].value_counts().head(10).index
    top_species = df[df['common_name'].isin(top_species_names)].groupby(['common_name', 'ecosystem']).size().reset_index(name='observations')
    fig = px.bar(top_species, x='observations', y='common_name', color='ecosystem', orientation='h',barmode='group', title='Top 10 Species: Forest vs Grassland')
    fig.update_layout(height=500)

    st.plotly_chart(fig)


# DATA OVERVIEW
def page_data_overview(df):
    st.title("📊 Data Overview")
    tab1, tab2, tab3 = st.tabs(["Raw Data", "Data Quality", "Statistics"])
    
    with tab1:
        st.subheader("Raw Dataset View")
        col1, col2 = st.columns(2)

        with col1:
            ecosystem_filter = st.selectbox("Filter by Ecosystem",["All"] + df['ecosystem'].unique().tolist(),key="overview_ecosystem_filter")

        with col2:
            location_filter = st.selectbox("Filter by Location Type",["All"] + df['location_type'].unique().tolist(),key="overview_location_filter")

        filtered_df = df.copy()
        if ecosystem_filter != "All":
            filtered_df = filtered_df[filtered_df['ecosystem'] == ecosystem_filter]
        if location_filter != "All":
            filtered_df = filtered_df[filtered_df['location_type'] == location_filter]
        
        st.dataframe(filtered_df.sample(min(100, len(filtered_df))), use_container_width=True)
        
        st.info(f"Showing {len(filtered_df):,} records")
    
    # DATA QUALITY
    with tab2:
        st.subheader("Data Quality Report")
        
        completeness = (1 - (df.isnull().sum().sum() / (len(df) * len(df.columns)))) * 100
        
        st.metric("Data Completeness", f"{completeness:.2f}%")
        st.write("Missing Values by Column:")
        missing_values = df.isnull().sum()
        missing_filtered = missing_values[missing_values > 0]
        if len(missing_filtered) > 0:
            missing_df = pd.DataFrame({
                'Column': missing_filtered.index,
                'Missing Count': missing_filtered.values,
                'Percentage': (missing_filtered.values / len(df) * 100).round(2)
            })
            st.dataframe(missing_df, use_container_width=True)
        else:
            st.success(" No missing values found!")
    
    #  STATISTICS
    with tab3:
        st.subheader("Numeric Columns Summary")
        
        numeric_df = df.select_dtypes(include=[np.number])
        
        st.dataframe(numeric_df.describe(), use_container_width=True)

#  SPECIES ANALYSIS
def page_species_analysis(df):
    st.title("🦜 Species Analysis") 
    PAGE = "species"

    #  TOP SPECIES 
    st.subheader("Top 20 Most Observed Species")
    top_20 = (df.groupby(['common_name', 'ecosystem']).size().reset_index(name='observations'))
    top_20 = top_20.sort_values('observations', ascending=False).head(20)
    fig = px.bar(top_20, x='observations', y='common_name', color='ecosystem', orientation='h',barmode='group',title='Top 20 Species Across Ecosystems')
    fig.update_layout(height=700)
    st.plotly_chart(fig, key=chart_key(PAGE, "species_top20_chart"))

    # SPECIES SELECTOR 
    st.subheader("Species Details")
    selected_species = st.selectbox("Select a Species:", sorted(df['common_name'].dropna().unique().tolist()),key='species_selector')
    species_data = df[df['common_name'] == selected_species]

    col1, col2, col3, col4 = st.columns(4)

    scientific_name = (
    species_data['scientific_name'].iloc[0]
    if not species_data.empty
    else "Unknown"
)

    col1.metric("Scientific Name",scientific_name)
    col2.metric("Total Observations",len(species_data))
    col3.metric( "Forest Observations",len(species_data[species_data['ecosystem'] == 'forest']))
    col4.metric("Grassland Observations",len(species_data[species_data['ecosystem'] == 'grassland']))

    #  SEX RATIO 
    st.subheader("Sex Ratio")
    
    sex_counts = species_data['sex'].value_counts().reset_index()
    sex_counts.columns = ['sex', 'count']
    fig2 = px.pie( sex_counts, names='sex', values='count', hole=0.4, title='Sex Ratio Distribution')
    st.plotly_chart(fig2, key=chart_key(PAGE, 'species_sex_ratio'))

    #  LOCATIONS 
    st.subheader("Where This Species is Found")

    location_counts = species_data['admin_unit_code'].value_counts().reset_index()    
    location_counts.columns = ['admin_unit','observations']
    fig3 = px.bar(location_counts,x='observations', y='admin_unit',orientation='h',color='observations', color_continuous_scale='Blues', title=f'Locations Where {selected_species} is Found')
    fig3.update_layout(height=500)
    st.plotly_chart(fig3, use_container_width=True,key=chart_key(PAGE, 'species_locations'))

# TEMPORAL ANALYSIS
def page_temporal_analysis(df):
    st.title("📅 Temporal Analysis")
    PAGE = "temporal"

    # YEAR SELECTION 
    st.subheader("Observations Over Time")    
    years = sorted(df['year'].dropna().unique())
    
    selected_years = st.multiselect("Select Years:", years, default=years) # LINE 355: Default to all years
    year_filtered = df[df['year'].isin(selected_years)]
    ecosystem_filter = st.selectbox("Select Ecosystem",['All'] + list(df['ecosystem'].unique()),key='temporal_ecosystem')
    filtered_df = df[df['year'].isin(selected_years)]
    if ecosystem_filter != 'All':
        filtered_df = filtered_df[filtered_df['ecosystem'] == ecosystem_filter]
    
    # YEARLY TREND 
    st.subheader("Yearly Observation Trend")
    yearly_counts = year_filtered.groupby(['year', 'ecosystem']).size().reset_index(name='observations')
    fig1 = px.line(yearly_counts, x='year', y='observations', color='ecosystem', markers=True,title='Yearly Bird Observations')
    fig1.update_layout(height=500)
    st.plotly_chart(fig1, use_container_width=True,key=chart_key(PAGE,'temporal_yearly_chart'))

    # MONTHLY DISTRIBUTION
    st.subheader("Monthly Distribution")
    month_map = {
        1: 'Jan',
        2: 'Feb',
        3: 'Mar',
        4: 'Apr',
        5: 'May',
        6: 'Jun',
        7: 'Jul',
        8: 'Aug',
        9: 'Sep',
        10: 'Oct',
        11: 'Nov',
        12: 'Dec'
    }
    filtered_df = filtered_df.copy()
    filtered_df['month_name'] = (filtered_df['month'].map(month_map))
    monthly_counts = (filtered_df.groupby(['month_name', 'ecosystem']).size().reset_index(name='observations'))
    month_order = ['Jan', 'Feb', 'Mar', 'Apr','May', 'Jun', 'Jul', 'Aug','Sep', 'Oct', 'Nov', 'Dec']
    fig2 = px.line(monthly_counts,x='month_name',y='observations', color='ecosystem',markers=True,
        category_orders={'month_name': month_order},
        title='Monthly Bird Observation Trends')
    fig2.update_layout(height=500)
    st.plotly_chart(fig2, key=chart_key(PAGE,'temporal_monthly_chart'))

# GEOGRAPHIC ANALYSIS
def page_geographic_analysis(df):
    st.title("🗺️ Geographic Analysis")
    PAGE = "geo"

    ecosystem_filter = st.selectbox("Select Ecosystem",['All'] + list(df['ecosystem'].unique()),key='geographic_ecosystem')
    filtered_df = df.copy()
    if ecosystem_filter != 'All':
        filtered_df = filtered_df[filtered_df['ecosystem'] == ecosystem_filter]
    # ADMIN UNIT ANALYSIS
    st.subheader("Observations by Administrative Unit")
    admin_counts = (filtered_df.groupby( ['admin_unit_code', 'ecosystem']).size().reset_index(name='observations'))
    fig1 = px.bar(admin_counts, x='observations', y='admin_unit_code',color='ecosystem', orientation='h', barmode='group', title='Observations by Geographic Region')
    fig1.update_layout(height=600)
    st.plotly_chart(fig1, use_container_width=True,key=chart_key(PAGE,'geo_admin_chart'))
    # FOREST VS GRASSLAND COMPARISON
    st.subheader("Forest vs Grassland Comparison")
    col1, col2 = st.columns(2)
    # DONUT CHART
    with col1:
        location_counts = (filtered_df['ecosystem'].value_counts().reset_index())
        location_counts.columns = ['ecosystem','observations' ]
        fig2 = px.pie(location_counts, names='ecosystem', values='observations',hole=0.4,title='Observations by Ecosystem' )
        st.plotly_chart(fig2, use_container_width=True,key=chart_key(PAGE,'geo_ecosystem_pie chart'))

    # LOCATION TYPE COMPARISON 
    st.subheader("Biodiversity Comparison by Habitat Type")
    location_counts = df['ecosystem'].value_counts()
    col1, col2 = st.columns(2)
 
    with col1:
        fig1, ax1 = plt.subplots()
        ax1.pie( location_counts.values, labels=location_counts.index, autopct='%1.1f%%', startangle=90)
        ax1.set_title("Observations by Habitat Type")
        ax1.axis('equal')  # Makes pie circular
        st.pyplot(fig1)
    #  BAR CHART 
    with col2:
        biodiversity = filtered_df.groupby('ecosystem')['scientific_name'].nunique().reset_index(name='species_count')
        fig2 = px.bar(biodiversity, x='ecosystem', y='species_count', color='ecosystem', title='Species Diversity by Ecosystem')
        st.plotly_chart(fig2, use_container_width=True,key=chart_key(PAGE,'geo_biodiversity_bar'))

    # BIODIVERSITY HOTSPOTS 
    st.subheader("Top 10 Biodiversity Hotspots")
    hotspots =filtered_df.groupby(['site_name', 'ecosystem'])['scientific_name'].nunique().reset_index(name='species_count')
    hotspots = hotspots.sort_values('species_count', ascending=False ).head(10)
    fig4 = px.bar(hotspots, x='species_count', y='site_name', color='ecosystem', orientation='h',title='Top Biodiversity Hotspots')
    fig4.update_layout(height=600)
    st.plotly_chart(fig4, use_container_width=True,key=chart_key(PAGE,'geo_hotspots_chart'))

# ENVIRONMENTAL ANALYSIS
def page_environmental_analysis(df):
    st.title("🌤️ Environmental Analysis")
    PAGE = "env"

    df_env = df.copy()
    #  TEMPERATURE ANALYSIS 
    st.subheader("Temperature Impact")
    df_env['temperature'] = pd.to_numeric(df_env['temperature'],errors='coerce')
    df_env['temp_range'] = pd.cut(df_env['temperature'],bins=5,labels=[
        'Very Low',
        'Low',
        'Medium',
        'High',
        'Very High'
    ])
    df_env['temp_range'] = df_env['temp_range'].astype(str)

    temp_data = (df_env.groupby(['temp_range', 'ecosystem'], observed=False).size().reset_index(name='observations'))
    fig1 = px.bar(temp_data, x='temp_range', y='observations', color='ecosystem', barmode='group', title='Temperature Impact on Bird Observations')
    st.plotly_chart(fig1, use_container_width=True,key=chart_key(PAGE,'env_temp_chart'))
    
    #  SKY CONDITION ANALYSIS 
    st.subheader("Sky Condition Impact")
    sky_data = (df_env.groupby( ['sky', 'ecosystem']).size().reset_index(name='observations'))
    fig2 = px.bar(sky_data, x='sky', y='observations', color='ecosystem', barmode='group', title='Sky Condition vs Bird Activity')
    st.plotly_chart(fig2, use_container_width=True,key=chart_key(PAGE,'env_sky_chart'))

# IDENTIFICATION METHOD 
    st.subheader("Bird Identification Methods")
    id_method = df_env['id_method'].value_counts().dropna().reset_index()
    id_method.columns = ['method', 'count']
    fig3 = px.pie( id_method, names='method', values='count', hole=0.4, title='Identification Methods Distribution')
    st.plotly_chart(fig3, key=chart_key(PAGE,'env_id_method_chart'))

#  CONSERVATION INSIGHTS
def page_conservation_insights(df):
    st.title("🛡️ Conservation Insights")
    PAGE = "cons"
    
    df_cons = df.copy()
     # SAFETY CLEANUP
    df_cons['pif_watchlist_status'] = df_cons['pif_watchlist_status'].astype(str).str.lower() == 'true'
    df_cons['regional_stewardship_status'] = df_cons['regional_stewardship_status'].astype(str).str.lower() == 'true'

    #  AT-RISK SPECIES
    st.subheader("Species on PIF Watchlist (At Risk)")
    at_risk = df_cons[df_cons['pif_watchlist_status']]
    at_risk_data = (at_risk.groupby(['common_name', 'ecosystem']).size().reset_index(name='observations').sort_values('observations', ascending=False).head(15))
    fig1 = px.bar(at_risk_data, x='observations',y='common_name', color='ecosystem',orientation='h',title='At-Risk Species: Forest vs Grassland')
    st.plotly_chart(fig1, use_container_width=True,key=chart_key(PAGE,'cons_at_risk_chart'))
    
    # CONSERVATION PRIORITY 
    st.subheader("Regional Conservation Priorities")
    priority = df_cons[df_cons['regional_stewardship_status']]
    priority_data = ( priority.groupby(['common_name', 'ecosystem']).size().reset_index(name='observations').sort_values('observations', ascending=False).head(15))
    fig2 = px.bar( priority_data, x='observations', y='common_name', color='ecosystem',orientation='h', title='Conservation Priority Species Distribution' )
    st.plotly_chart(fig2, use_container_width=True,key=chart_key(PAGE,'cons_priority_chart'))
    
    #  KEY STATISTICS 
    st.subheader("Conservation Statistics")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("At-Risk Species", at_risk['scientific_name'].nunique())

    with col2:
        st.metric( "Priority Species", priority['scientific_name'].nunique())

    with col3:
        pct = len(at_risk) / len(df_cons) * 100
        st.metric("At-Risk Observations %", f"{pct:.1f}%" )

#  ADVANCED QUERIES
def page_advanced_queries(df):
    st.title("⚙️ Advanced Queries")
    PAGE = "adv"
    
    df_adv = df.copy()
    # CUSTOM FILTERS 
    st.subheader("Custom Data Filtering")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        selected_species = st.multiselect("Select Species:", sorted(df_adv['common_name'].dropna().unique().tolist()))
    
    with col2:
        selected_locations = st.multiselect( "Admin Units", sorted(df_adv['admin_unit_code'].dropna().unique().tolist()))
    
    with col3:
        selected_years = st.multiselect("Select Years:", sorted(df_adv['year'].dropna().unique().tolist()))
    
    with col4:
        selected_ecosystem = st.multiselect( "ecosystem", sorted(df_adv['ecosystem'].dropna().unique()))
   # APPLY FILTERS    
    if selected_species:
        df_adv = df_adv[df_adv['common_name'].isin(selected_species)]

    if selected_locations:
        df_adv = df_adv[df_adv['admin_unit_code'].isin(selected_locations)]

    if selected_years:
        df_adv = df_adv[df_adv['year'].isin(selected_years)]

    if selected_ecosystem:
        df_adv = df_adv[df_adv['ecosystem'].isin(selected_ecosystem)]
    # SUMMARY METRICS
    st.subheader("Filtered Data Summary")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Records",len(df_adv) )

    with col2:
        st.metric("Unique Species",df_adv['common_name'].nunique())

    with col3:
        st.metric("Ecosystems",df_adv['ecosystem'].nunique())
        
    # ECOSYSTEM COMPARISON CHART
    st.subheader("Ecosystem Distribution")
    eco_data = (df_adv.groupby('ecosystem').size().reset_index(name='observations'))
    fig1 = px.bar(eco_data, x='ecosystem', y='observations',color='ecosystem',title='Observations by Ecosystem')
    st.plotly_chart(fig1, use_container_width=True,key=chart_key(PAGE,'adv_eco_chart'))

    # SPECIES DISTRIBUTION
    st.subheader("Top Species in Filtered Data")
    species_data = ( df_adv['common_name'].value_counts().head(10).reset_index() )
    species_data.columns = ['species', 'count']
    fig2 = px.bar( species_data, x='count',y='species', orientation='h',title='Top 10 Species')
    st.plotly_chart(fig2, use_container_width=True,key=chart_key(PAGE,'adv_top_species_chart'))
    # DATA TABLE
    st.subheader("Filtered Dataset")
    st.dataframe(df_adv.head(500), use_container_width=True)

    # EXPORT DATA
    st.subheader("Export Filtered Data")
    csv = df_adv.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Download Filtered CSV",
        data=csv,
        file_name="filtered_bird_data.csv",
        mime="text/csv"
    )

# MAIN APP LAYOUT
def main():
    st.set_page_config(
        page_title="Bird Species Analysis",
        page_icon="🦅",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    st.markdown("""
    <style>
    .main-title {
        text-align: center;
        color: #1f77b4;
    }
    </style>
    """, unsafe_allow_html=True)
    
    df = load_all_data()
    if df.empty:
        st.error("Error: Could not load data from database")
        st.stop()

    # SIDEBAR FILTERS
    ecosystem_filter = st.sidebar.selectbox(
        "Select Ecosystem",
        ["All"] + sorted(df['ecosystem'].dropna().unique().tolist()),
        key="sidebar_ecosystem"
    )
    if ecosystem_filter != "All":
        df = df[df['ecosystem'] == ecosystem_filter]

# SIDEBAR NAVIGATION 
    page = st.sidebar.radio(
    "Navigate",
    [
        "🏠 Home",                    
        "📊 Data Overview",
        "🦜 Species Analysis",
        "📅 Temporal Analysis",
        "🗺️ Geographic Analysis",
        "🌤️ Environmental Analysis",
        "🛡️ Conservation Insights",
        "⚙️ Advanced Queries"
    ]
) 
    st.sidebar.markdown("---")
    st.sidebar.info("""
    **Bird Species Analysis Dashboard**
    
    Comprehensive analysis of bird observations across forest and grassland ecosystems.
    
    **Features:**
    - Data overview and quality metrics
    - Species distribution analysis
    - Temporal trends
    - Geographic hotspots
    - Environmental conditions
    - Conservation priorities
    - Advanced filtering
    """)
    
    #PAGE ROUTING 
    if page == "🏠 Home":
        page_home(df)
    
    elif page == "📊 Data Overview":
        page_data_overview(df)
    
    elif page == "🦜 Species Analysis":
        page_species_analysis(df)
    
    elif page == "📅 Temporal Analysis":
        page_temporal_analysis(df)
    
    elif page == "🗺️ Geographic Analysis":
        page_geographic_analysis(df)
    
    elif page == "🌤️ Environmental Analysis":
        page_environmental_analysis(df)
    
    elif page == "🛡️ Conservation Insights":
        page_conservation_insights(df)
    
    elif page == "⚙️ Advanced Queries":
        page_advanced_queries(df)
# SCRIPT ENTRY POINT
if __name__ == "__main__":
    main()
