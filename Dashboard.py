import streamlit as st
import pandas as pd
import geopandas as gpd
import plotly_express as px
import plotly.graph_objs as go
import altair as alt

st.set_page_config(
    page_title="Envirowise Dashboard",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
.block-container {
    padding-top: 1rem;
    padding-bottom: 0rem;
    padding-left: 5rem;
    padding-right: 5rem;
}

[data-testid="stMetric"] {
    background-color: #1b212b;
    padding: 5px 15px;
}
</style>
""", unsafe_allow_html=True)
with st.sidebar:
    st.markdown("""
        <style>
        .block-container {
            padding-top: 1rem;
            padding-bottom: 0rem;
            padding-left: 5rem;
            padding-right: 5rem;
        }
        </style>
        """, unsafe_allow_html=True)
    st.markdown('### Envirowise Dashboard')
    st.markdown("##### Greater Manchester")
    st.divider()
    with st.expander('**About**', expanded=False):
        st.write('''             
            **Sources**
            - **Emissions**: [UK local authority and regional greenhouse gas emissions national statistics, 2005 to 2021](https://www.gov.uk/government/statistics/uk-local-authority-and-regional-greenhouse-gas-emissions-national-statistics-2005-to-2021)
            
            - **Location**: [Local Authority Districts (December 2023) Boundaries UK BFC](https://geoportal.statistics.gov.uk/datasets/127c4bda06314409a1fa0df505f510e6_0/explore?location=53.465754%2C-1.068236%2C6.89)
            
            - **Vehicles**: [Vehicle Statistics](https://www.gov.uk/government/collections/vehicles-statistics)
            
            - **Charging Devices**: [Electric vehicle charging device statistics: October 2023](https://www.gov.uk/government/statistics/electric-vehicle-charging-device-statistics-october-2023/electric-vehicle-charging-device-statistics-october-2023)
            
            
            ''')
        st.divider()
        st.write('''         
            **Metrics**    
                 
            - **Kt CO2e** = *Kiloton of Carbon Dioxide*
            
            - **Per 100k population** = *Based on a population size of 100,000 individuals*

            ''')

def map():
    geo = gpd.read_file(".data/mapdata.geojson")
    geo = geo.set_index("District")

    fig = px.choropleth(geo, geojson=geo['geometry'], 
                        locations=geo.index, 
                        color=geo['Emissions'],
                        color_continuous_scale='mint',
                        height=555,
                        labels={'Emissions': 'Kt CO2e', 'District': 'Region'}
                        )
    
    fig.update_geos(fitbounds="locations", visible=False)
    fig.update_layout(
        margin={"r":0,"t":0,"l":0,"b":0},
        geo_bgcolor='rgba(0,0,0,0)',
        geo=dict(
            center=dict(lat=53.5025, lon=-2.3100),
            scope="europe"
        )
    )
    return fig

def melt():
    heatdata = pd.read_csv(".data/transport.csv")
    heatdata = heatdata.drop(columns={'Unnamed: 0'})
    heatdatamelt = heatdata.melt(id_vars='Year', var_name='Region', value_name='Kt CO2e')
    heatmap = alt.Chart(heatdatamelt).mark_rect().encode(
        x=alt.X('Year:O', title=None), 
        y=alt.Y('Region:O', title=None),
        color=alt.Color('Kt CO2e:Q', scale=alt.Scale(scheme='teals'))
    ).properties(
  
        width=600,
        height=270
    )
    return heatmap

def charging_data(dataset, metric):
    chargers = pd.read_csv(".data/chargers.csv")
    chargers = chargers.rename(columns={'Oct-23':'Charging Devices'})

    if dataset == 'All Chargers' and metric == 'Total':
        chargers = chargers[:10]
    elif dataset == 'All Chargers' and metric == 'Per 100k Population':
        chargers = chargers[20:30]
    elif dataset == 'Rapid Chargers' and metric == 'Total':
        chargers = chargers[10:20]
    else:
        chargers = chargers[30:]
            
    chargers = chargers.sort_values(by='Charging Devices',ascending=False)
    return chargers

def vehicles_data(region):
    cars = pd.read_csv(".data/cars.csv")
    cars['Region Name'] = cars['Region Name'].str.strip()
    df = cars[cars['Region Name'] == region]
    df = df.T
    df.columns=['Diesel', 'Hybrid Electric', 'Other Fuels', 'Petrol']
    df = df[3:]
    df = df [::-1]
    df["EV's"] = df['Hybrid Electric'] + df['Other Fuels']
    df['Diesel/Petrol'] = df['Diesel'] + df['Petrol']
    df['pct'] = (df['Hybrid Electric'] + df['Other Fuels'])/(df['Diesel'] + df['Petrol'])*100
    df["Total"] = df['Hybrid Electric'] + df['Other Fuels'] + df['Diesel'] + df['Petrol']
    
    return df

def bar_chart(region):
    df = vehicles_data(region)
    fig = px.bar(df, x=df.index, y="EV's", title="Electric Vehicles & Hybrids",color_discrete_sequence =['#00ffd9'])
    fig.update_layout(yaxis_title="")
    fig.update_layout(xaxis_title="")
    fig.update_layout(yaxis=dict(side='right'),height=475)
    return fig

col = st.columns((2, 4.5, 1.5), gap='medium')

with col[0]:
    st.markdown(" #### Electric Vehicles")
    st.write("")
    region = st.selectbox(
    'Region',
    ('Bolton', 'Bury', 'Manchester', 'Oldham', 'Rochdale', 'Salford', 'Stockport', 'Tameside', 'Trafford', 'Wigan'))
    df = vehicles_data(region)
    st.divider()
    st.metric(label="Total Cars", value=df['Total'].iloc[-1], delta="")
    st.metric(label="EV's & Hybrids", value=df["EV's"].iloc[-1], delta=f'{round(df["pct"].iloc[-1],2)}% of Total Cars')
    
    st.plotly_chart(bar_chart(region), use_container_width=True)

with col[1]:
    st.markdown(" #### Greater Manchester Transport CO2 Levels")
    st.plotly_chart(map(), use_container_width=True)
    st.altair_chart(melt(), use_container_width=True)

with col[2]:
    st.markdown("#### Charging Points")
    st.write("")
    dataset = st.selectbox(
    'Select a Dataset',
    ('All Chargers', 'Rapid Chargers'))
    st.write("")
    metric = st.radio(
    'Metric',
    ('Total', 'Per 100k Population'))
    
    st.divider()
    st.write("")
    chargers=charging_data(dataset, metric)
    st.dataframe(chargers, use_container_width=True,
        column_order=("Region", "Charging Devices"),
        hide_index=True,
        width=None,
        column_config={
            "Region": st.column_config.TextColumn(
                "Region"),
            "Charging Devices": st.column_config.ProgressColumn(
                "Charging Devices",
                format="%f",
                min_value=0,
                max_value=max(chargers['Charging Devices']),
                     )}
                 )
