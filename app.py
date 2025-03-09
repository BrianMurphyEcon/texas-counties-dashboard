import dash
from dash import html, dcc
from dash.dependencies import Input, Output
import plotly.express as px
import pandas as pd
import geopandas as gpd
import json
import os

# Data loading function
def load_data():
    # Use relative paths for data files in the 'data' directory
    # This will work both locally and when deployed
    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
    
    # Load geospatial data (saved as GeoJSON)
    counties_path = os.path.join(data_dir, 'county_shapes.geojson')
    texas_counties = gpd.read_file(counties_path)
    
    # Load business data (saved as CSV)
    business_path = os.path.join(data_dir, 'minority_business.csv')
    mb_df = pd.read_csv(business_path)
    
    # Prepare and merge data
    texas_counties['Geo_ID_5'] = texas_counties['Geo_ID_5'].astype(str)
    mb_df['GeoID'] = mb_df['GeoID'].astype(str)
    
    # Merge the datasets
    merged_df = texas_counties.merge(
        mb_df, 
        left_on='Geo_ID_5', 
        right_on='GeoID', 
        how='left'
    )
    
    return merged_df

# Load the data
merged_df = load_data()

# Create the Dash app
app = dash.Dash(__name__)

# This is needed for deployment platforms like Heroku
server = app.server

# Available measures for the dropdown
measure_options = [
    {"label": "Number of Establishments", "value": "Number of establishments"},
    # Add more measures here as needed
]

# App layout
app.layout = html.Div([
    html.H1("Texas Counties Interactive Dashboard"),
    html.P("Select a measure to display on the map:"),
    dcc.Dropdown(
        id="measure-dropdown",
        options=measure_options,
        value="Number of establishments"
    ),
    dcc.Graph(id="map-graph")
])

# Callback to update the map
@app.callback(
    Output("map-graph", "figure"),
    Input("measure-dropdown", "value")
)
def update_map(selected_measure):
    # Create a GeoJSON-like object from the GeoDataFrame
    geojson = merged_df.__geo_interface__
    
    fig = px.choropleth_mapbox(
        merged_df,
        geojson=geojson,
        locations=merged_df.index,
        color=selected_measure,
        featureidkey="id",
        center={"lat": 31.0, "lon": -99.0},
        mapbox_style="carto-positron",
        zoom=5,
        color_continuous_scale="OrRd",
        labels={selected_measure: selected_measure.replace('_', ' ')}
    )
    
    fig.update_layout(
        margin={"r": 0, "t": 40, "l": 0, "b": 0},
        title=f"{selected_measure.replace('_', ' ')} by County in Texas (2022)"
    )
    
    return fig

# Run the app
if __name__ == '__main__':
    # Use environment variable for port if available (for cloud deployment)
    port = int(os.environ.get("PORT", 8051))
    app.run_server(debug=False, host='0.0.0.0', port=port)
