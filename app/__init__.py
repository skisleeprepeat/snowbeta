# dependencies
# from flask import Flask, render_template, request, url_for
from flask import Flask, render_template, url_for, request
from datetime import datetime as dt, timedelta
import pytz
import json
import plotly
import folium
import requests

#-----------------------------------------------------------------------------
# App initialization

app = Flask(__name__)

#-----------------------------------------------------------------------------
# Local modules
import data_utils
import plot_utils


#-----------------------------------------------------------------------------
# Program Data
''' various datasets needed for app functionality '''

# Load snotel site data
with open('station_json_array.txt', 'r') as f:
    site_obj_str = f.read()
site_data_list = list(eval(site_obj_str))


#-----------------------------------------------------------------------------
# VIEWS

@app.route('/')
def index():

    # build URLS for the USFS Avalanche Center and CAIC Weather Model iframes
    now_MST = dt.now(pytz.timezone("America/Denver"))
    if now_MST.hour >= 6:
        caic_url_date_str = f'{now_MST.date()}-0600'
    else:
        caic_url_date_str = f'{(now_MST - timedelta(1)).date()}-0600'
    caic_wrf_url = f'https://looper.avalanche.state.co.us/weather/fcst/looper.php?date={caic_url_date_str}&model=wrf&domain=0&inc=1&var=S007&wlvl=SFC'

    return render_template('index.html', site_data_list = site_data_list, caic_wrf_url=caic_wrf_url)

@app.route('/about')
def about():

    return render_template('about.html')


def update_database_cb():

    ''' this view will check to see when the last time the daily and the hourly 
    databases were updated. If no updates are needed, the site proceeds normally; if the 
    latest timestamps are not within the set criteria for either of the datasets,
    an api call to snotel will be made to gather the additional data and put the most
    recent rows in the database.

    It is asynchronously called from the javascrip during page laod so that the site can
    load while this task occurs in the background. If it is taking too long or times out,
    the viewer should still be able to just make plots with whatever the last version of the
    database was. 

    There are approximately 900 snotel sites, 
    So a daily row for the season Oct 1 - Jun 30 will be 900 sites * 9 months * 30 days = 243,000 rows
    An hourly obs for the season will be 900 * 9 months * 30 days * 24 hours = 5,832,000 rows;
    If only keep the last seven days in the daily database, then 900 sites * 7 days * 24 hours = 151,000 rows
    
    '''
    pass


# REGIONAL PLOTS
@app.route('/build_regional_plots_cb')
def region_plots_cb():

    ''' take the state and region information to build regional plots, return as a plotly json object 
    to be displayed on the page'''

    zone = request.args.get('zone')
    print(f'zone is: {zone}')

    try:

        # filter the site list
        plot_site_list = list(filter(lambda d: (zone in d['stationZone']) and (d['stationZone'] != ''), site_data_list))

        # create a site info dataframe (pandas is loaded in data utils, so send it there...)
        plot_site_df = data_utils.build_plot_site_df(plot_site_list) 

        # data calls to USGS webservice
        data_hourly = data_utils.get_hourly_data(site_list=plot_site_list)
        data_daily = data_utils.get_daily_data(site_list=plot_site_list)

        # calculate various metrics for recent snowfall (24 change, 3 day change, 7 day change, etc)
        snow_df = data_utils.build_summary_df(dfh=data_hourly.drop(['Wdir_avg','Wvel_avg','Wvel_max'], axis=1), dfd=data_daily)
        print("\nSnow summary dataframe successfully built...\n")

    except Exception as e:
        print(f"Unexpected {e}, {type(e)}")
        print('Snow dataframe build unsucessful')
        data_hourly = None
        data_daily = None
        snow_df = None


    try:
        new_snow_plot_JSON = plot_utils.build_recent_snow_barplot(
            snow_df=snow_df, 
            site_df=plot_site_df
            )
    except Exception as e:
        print(f"Unexpected {e}, {type(e)}")
        new_snow_plot_JSON = f"Error building new snow plots, try again later or try another site"

    try:
        current_temp_plot_JSON = plot_utils.build_current_temperature_plot(
            snow_df=snow_df[['Site_Id', 'Site_Name', 'T_Obs']], 
            site_df=plot_site_df[['Site_Id', 'Elev']]
            )
    except Exception as e:
        print(f"Unexpected {e}, {type(e)}")
        current_temp_plot_JSON = f"Error building current temp plots"
    
    try:
        depth_plot_JSON = plot_utils.build_current_depths_plot(
            snow_df=snow_df[['Site_Id', 'Site_Name', 'Depth']], 
            site_df=plot_site_df[['Site_Id', 'Elev']]
            )
    except Exception as e:
        print(f"Unexpected {e}, {type(e)}")
        depth_plot_JSON = f"Error building current depth plots"
    
    try:
        seasonal_accum_plot_JSON = plot_utils.build_snow_accumulation_plot(
            daily_df=data_daily, 
            site_df=plot_site_df
            )
    except Exception as e:
        print(f"Unexpected {e}, {type(e)}")
        seasonal_accum_plot_JSON = f"Error building seasonal accumulation plot"


    return json.dumps({
        "new-snow-plot": new_snow_plot_JSON,
        "depth-plot": depth_plot_JSON,
        "temp-plot": current_temp_plot_JSON,
        "season-plot":seasonal_accum_plot_JSON
        },
        cls=plotly.utils.PlotlyJSONEncoder)


# INDIVIDUAL SITE PLOTS
@app.route('/build_site_plots_cb')
def build_site_plots_cb():

    ''' take the individual SNOTEL site id to build a set of site plots, return as a plotly json object 
    to be displayed on the page'''
    # pass

    # NOTE: This may need to be split into individual plot callbacks to be more robust in case one plot fails
    site = request.args.get('site')
    print(f'SNOTEL plotting site is: {site}')

    try:
        # filter the site list; it will be a list of one
        # plot_site_list = list(filter(lambda d: d['stationID'] == int(site), site_data_list))
        plot_site_list = list(filter(lambda d: d['stationName'] == site, site_data_list))
        # print(f'\The plot site information list is: {plot_site_list}')

        # build 1 row dataframe of plot site metadata (will be one row in this case), convert it to a dict
        plot_site_df = data_utils.build_plot_site_df(plot_site_list) # function expects a list
        plot_site_dict = plot_site_df.iloc[0].to_dict()

        # formatted hourly dataframe of snow depth, temp, wind, etc.
        data_hourly = data_utils.get_hourly_data(site_list=plot_site_list)
        # formatted hourly dataframe of snow depth, temp, wind, etc.
        data_daily = data_utils.get_daily_data(site_list=plot_site_list)

    except Exception as e:
        print(f"Unexpected {e}, {type(e)}")
        plot_site_dict=None
        data_hourly = None
        data_daily = None

    try:
        seasonal_meteogram_JSON = plot_utils.build_seasonal_meteogram(
            daily_df=data_daily, 
            site_dict=plot_site_dict
            )
    except Exception as e:
        print(f"Unexpected {e}, {type(e)}")
        seasonal_meteogram_JSON = "Error building snow meteogram plot"
    
    try:
        seasonal_temperature_JSON = plot_utils.build_seasonal_temperature_plot(
            plot_df=data_daily[["Date", "Site_Name", "T_Max", "T_Min"]], 
            site_dict=plot_site_dict
            )
    except Exception as e:
        print(f"Unexpected {e}, {type(e)}")
        seasonal_temperature_JSON = "Error building temperature plot"
    
    # check if there is wind data at this station, if there is then build a wind plot, if not return a message
    if data_hourly['Wvel_avg'].notnull().sum() > 0:
        try:
            wind_history_JSON = plot_utils.build_wind_plot(
                plot_df=data_hourly[["DateTime", "Site_Name", "Wdir_avg", "Wvel_avg", "Wvel_max"]], 
                site_dict=plot_site_dict
                )
        except Exception as e:
            print(f"Unexpected {e}, {type(e)}")
            wind_history_JSON = f"Error building wind plot for {site}"
    else:
        wind_history_JSON = "No wind data available at this site"
    

    # pack Plotly plot objects into a JSON object and return to the javascript callback function
    return json.dumps({
        'seasonal_meteogram_plot': seasonal_meteogram_JSON,
        'seasonal_temperature_plot': seasonal_temperature_JSON,
        'wind_history_plot': wind_history_JSON,
        },
        cls=plotly.utils.PlotlyJSONEncoder
        )


@app.route('/build_SWE_regime_cb')
def build_SWE_plot():

    ''' take the individual SNOTEL site id to build a set of site plots, return as a plotly json object 
    to be displayed on the page'''
    # pass

    # NOTE: This may need to be split into individual plot callbacks to be more robust in case one plot fails
    site = request.args.get('site')
    print(f'SNOTEL plotting site for SWE regime plot is: {site}')

    
    try:
        # filter the site list; it will be a list of one
        plot_site_list = list(filter(lambda d: d['stationName'] == site, site_data_list))

        # build 1 row dataframe of plot site metadata (will be one row in this case), convert it to a dict
        plot_site_df = data_utils.build_plot_site_df(plot_site_list) # function expects a list
        plot_site_dict = plot_site_df.iloc[0].to_dict()

        # formatted hourly dataframe of snow depth, temp, wind, etc.
        data_POR = data_utils.get_POR_data(site_list=plot_site_list)

        # estimate the daily percentileb breaks of SWE for the 30 year period
        df_doy = data_utils.build_doy_df(data_POR)

        # extract just the current water year's data
        if dt.today().month < 10:
            this_wy = dt.today().year
        else:
            this_wy = dt.today().year-1
        current_wy_df = data_POR[data_POR.WY==this_wy]

        plot_df = data_utils.add_plotting_variables(df_doy, current_wy_df)
        ts_data = data_POR[['Date','SWE']]

    except Exception as e:
        print(f"Unexpected {e}, {type(e)}")
        plot_site_dict=None
        data_POR = None
    
    try:
        SWE_regime_plot_JSON = plot_utils.build_SWE_regime_plot(
            plot_df=plot_df, 
            ts_df=ts_data,
            site_dict=plot_site_dict
            )

    except Exception as e:
        print(f"Unexpected {e}, {type(e)}")
        SWE_regime_plot_JSON = "Error building SWE regime plot"
    
    # pack Plotly plot objects into a JSON object and return to the javascript callback function
    return json.dumps({
        'SWE_regime_plot_JSON': SWE_regime_plot_JSON
        },
        cls=plotly.utils.PlotlyJSONEncoder
        )


@app.route('/build_fx_map')
def build_map():

    '''
    Use the python folium library (leaflet wrapper) to build an interactive avalanche forecast map.  This function
    calls for a geojson file of the current avy hazard by zone from the natioanl forest service avalanche center, then
    plots that and inserts the plot html into the webpage as an iframe.  accepts: nothing, returns: html representation 
    of a folium map object.    
    '''

    # National Avy Map API docs:  https://github.com/NationalAvalancheCenter/Avalanche.org-Public-API-Docs
    url = 'https://api.avalanche.org/v2/public/products/map-layer'

    try:
        r = requests.get(url, headers={'Accept': 'application/json'})
        print(f"Status Code: {r.status_code}")
    except Exception as e:
        r = None
        raise e     
    
    if r is None:
        return 'Avalanche forecast map currently unavailable'

    avy_json = r.json()
    
    # build an additional key/value into the avy center geojson features that has html strings for formatted popups 
    # and tooltops

    def make_popups(feature):
        zone_name = feature['properties']['name']
        danger = feature['properties']['danger']
        danger_col = feature['properties']['color']
        advice = feature['properties']['travel_advice']
        fx_link = feature['properties']['link']
        center_name = feature['properties']['center']
        center_link = feature['properties']['center_link']
        start_time = feature['properties']['start_date']
        end_time = feature['properties']['end_date']
    
        try:
            html = f"""
            <div class="card">
                <div class="card-header">
                    <em>Forecast zone</em><nbsp><nbsp> | <nbsp><nbsp><a class="link-primary" href={fx_link} target="_blank">{zone_name}</a>
                </div>
                <div class="card-body">
                <div style="background-color:{danger_col}; padding:1px; margin:0px; text-align:center;">
                    <h5 class="card-title" style="color:black;">Current rating: <b>{danger.title()}</b></h5>
                </div>
                <p class="card-text" style="padding:2px; margin:0px;">{advice}</p>
                <p style="padding:2px; margin:0px;"><em>Issued at {start_time}, valid until {end_time}</em></p>
                <a href="{center_link}" class="link-primary" target="_blank" style="padding:2px; margin:0px;">Go to {center_name}</a>
                </div>
            </div>
            """
            return html
        except:
            return feature['name']


    def make_tooltips(feature):
        zone_name = feature['properties']['name']
        danger = feature['properties']['danger']
        center_state = feature['properties']['state']
        
        try:
            html = f"""
            <h6 style="padding:1px; margin:0px;"><b>Zone:<nbsp><nbsp></b>  {zone_name.title()}, {center_state}</h6>
            <p style="padding:1px; margin:0px;"><b>Current danger:<nbsp><nbsp></b>  {danger.title()}</p>
            <p style="font-size: 0.9rem; margin-bottom:0px; padding-bottom:1px;">(Click for info)</p>
            """
            return html
        except:
            return feature['name']


    for feature in avy_json["features"]:
        feature["properties"]["popups"]=make_popups(feature)

    for feature in avy_json["features"]:
        feature["properties"]["tooltips"]=make_tooltips(feature)

    # create the map object, use an esri topo mapset for base tiles
    tileset_url = 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}'
    tileset_attr = 'Tiles &copy; Esri &mdash; Esri, DeLorme, NAVTEQ, TomTom, Intermap, iPC, USGS, FAO, NPS, NRCAN, GeoBase, Kadaster NL, Ordnance Survey, Esri Japan, METI, Esri China (Hong Kong), and the GIS User Community'
    fx_map = folium.Map(
        location=[42, -115],
        zoom_start=5,
        tiles=tileset_url, attr=tileset_attr
    )

    # add the forecast data to the map and style it
    folium.GeoJson(avy_json, name="geojson",
               tooltip=folium.features.GeoJsonTooltip(fields=['tooltips'], labels=False),
               popup=folium.features.GeoJsonPopup(
                fields=['popups'],
                labels=False,
                style=("background-color: white; color: #333333; font-family: arial; font-size: 11px; ")
                ),
               style_function=lambda feature: {
                   'fillColor': feature['properties']['color'],
                   'color' : feature['properties']['stroke'],
                   'weight' : 1,
                   'fillOpacity' : 0.5,
                   }
               ).add_to(fx_map)
    
    # with open('folium_map.html', 'w') as f:
    #     f.write(fx_map._repr_html_())

    return fx_map._repr_html_()
    

#-----------------------------------------------------------------------------

# if using the package style format for a flask app, this code is
# called in 'app.py' at the root level of the project and this file is renamed
# to __init__.py

# if __name__ == '__main__':
#     app.run(debug=True)

