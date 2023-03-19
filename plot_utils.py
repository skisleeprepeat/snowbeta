import matplotlib.pyplot as plt
from datetime import datetime as dt, timedelta
import pytz
import plotly
from plotly.subplots import make_subplots
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

#----------------------------------------------------------------------------------------
# PLOT 1: RECENT SNOWFALL BARPLOT FOR MULTIPLE SITES IN SINGLE ZONE

def build_recent_snow_barplot(snow_df, site_df):

    #TODO: Need to create the site_df somewhere back in the main views script or in data_utils...
    # needs to have 3 columns 
    #  site_df = pd.DataFrame(columns=['Site_Id', 'Site_Name', 'Elev'], data=site_data)

    ''' build a bar plot showing recent snow totals for multiple SNOTEL
    sites in a single zone.
    
    accepts the recent snow dataframe and returns a plotly figure'''

    print('\nBuilding new snow barplot...\n')

    now_MST = dt.now(pytz.timezone('US/Mountain'))

    site_df['Site_Id'] = site_df['Site_Id'].astype('string')
    plot_df = snow_df.set_index('Site_Id').join(site_df[["Site_Id", "Elev"]].set_index('Site_Id'))

    plot_df.sort_values('Elev', ascending=True, inplace=True)

    # plot_df.to_csv("recent_snow_calcs.csv")

    # Note: McCoy park has erroneous data peaks, need to figure out a better filter for those data issues, 
    # for now, just remove it before plotting, no one careas about McCoy
    plot_df = plot_df[plot_df['Site_Name'] != "Mccoy Park"]



    # make the x axis label an interactive link that sends you to the snotel site page...
    link_text = f'https://wcc.sc.egov.usda.gov/nwcc/site?sitenum='
    plot_df.reset_index(inplace=True)
    plot_df['Site_Name'] = f"<a href=\'{link_text}" + plot_df['Site_Id'] + "\'>" + plot_df['Site_Name'] + "</a>, <em style='font-size:0.7rem'>"+ plot_df['Elev'].astype('string') + "\'</em>"

    # plot calls...
    fig = go.Figure(
        data=[
            go.Bar(
                name="Last 24 hrs",
                x=plot_df['Site_Name'],
                y=plot_df["Last_24"],
                offsetgroup=0,
                marker=dict(color="blue"),
                width=0.23
            ),
            go.Bar(
                name="Since 4pm yestrdy",
                x=plot_df['Site_Name'],
                y=plot_df["Since_4pm"],
                offsetgroup=0,
                marker=dict(
                    color="#6666ff",
                    line=dict(
                        color="#fff",
                        width=1,
                        ),
                    ),
                width=0.235,
            ),
            go.Bar(
            name="Since 6am today",
            x=plot_df['Site_Name'],
            y=plot_df["Since_6am"],
            offsetgroup=0,
            marker=dict(
                    color="#bfe6ff",
                    line=dict(
                        color="#fff",
                        width=1,
                        ),
                    ),
                width=0.235,
            ),
            go.Bar(
            name="Last 3 days",
            x=plot_df["Site_Name"],
            y=plot_df["New_Snow_3d"],
            offsetgroup=1,
            marker=dict(color="#3acadf", opacity=0.6),
            width=.18
            ),
            go.Bar(
            name="Last 7 days",
            x=plot_df["Site_Name"],
            y=plot_df["New_Snow_7d"],
            offsetgroup=2,
            marker=dict(color="#9300ff", opacity=0.6),
            width=.18
            ),
        ],
        layout=go.Layout(
            title=f"Recent Snowfall, current at {now_MST.ctime()}",
            yaxis_title="Inches",
            # xaxis_title="Location",
            xaxis_title=None,
            xaxis_type="category",
            paper_bgcolor='rgba(255,255,255,1)',
            plot_bgcolor='rgba(255,255,255,1)',
            xaxis = dict(
                linecolor='black',
                linewidth=2,
                mirror=True,
                ticks='outside',
                showline=True,
            ),
            yaxis = dict(
                linecolor='black',
                linewidth=2,
                mirror=True,
                ticks='outside',
                showline=True,
            )

        )

    )
    # fig.show()
    return fig


#----------------------------------------------------------------------------------------
# PLOT 2: SEASONAL SNOWFALL ACCUMULATION SPAGHETTI PLOT FOR MULTIPLE SITES

def build_snow_accumulation_plot(daily_df, site_df):

    print('\nBuilding seeasonal snowfall accumulation spaghetti plot\n')
    # Merge the DFs, keeping date as index for plotting
    plot_df = daily_df.set_index('Date')
    plot_df['Date'] = plot_df.index
    plot_df['Site_Id'] = plot_df['Site_Id'].astype('str')
    site_df['Site_Id'] = site_df['Site_Id'].astype('str')
    plot_df = pd.merge(plot_df, site_df[['Site_Id', 'Elev']], on='Site_Id', how='left').set_index('Date')
    # print(plot_df.head())

    # Note: McCoy park has erroneous data peaks, need to figure out a filter for those data issues, 
    # for now, just remove before plotting if that zone is chosen
    # plot_df = plot_df[plot_df['Site_Name'] != "Mccoy Park"]

    # sort stations before plotting to control legend order
    plot_df = plot_df.sort_values(by='Date')

    # TODO: change this eventually to just use graph objects instead of plotly express?
    fig = px.line(
        plot_df, 
        x=plot_df.index, 
        y="Depth", 
        color="Site_Name"
        )

    # TODO: Add some tooltip formatting

    fig.update_layout(
        xaxis=dict(
        tickformat='%m/%d',
        tick0 = dt.strptime('2022-10-01', '%Y-%m-%d'),  # will need to change this after year 1; just find the first date in the dataframe
        # dtick=86400000*7,
        dtick='M1',
    ), 
    legend=dict(
        title=None,
        yanchor="top",
        y=0.99,
        xanchor="left",
        x=0.01)
    )

    fig.update_layout(
        title="Seasonal Snow History",
        xaxis_title=None,
        yaxis_title="Depth  HS  (in)",
        font=dict(
            family="Tahoma",
            size=12,
        ),
        # Format plot area to be blank/white with thin black lines on all for sides
        paper_bgcolor='rgba(255,255,255,1)',
        plot_bgcolor='rgba(255,255,255,1)',
        xaxis = dict(
            linecolor='black',
            linewidth=1,
            mirror=True,
            ticks='outside',
            showline=True,
        ),
        yaxis = dict(
            linecolor='black',
            linewidth=1,
            mirror=True,
            ticks='outside',
            showline=True,
        )
    )
    # fig.show()
    return fig


#----------------------------------------------------------------------------------------
# PLOT 3: CURRENT TEMPERATURE vs ELEVATION FOR ZONE

def build_current_temperature_plot(snow_df, site_df):

    print('\nbuilding zone temperature plot\n')

    #merge with sites to use elevation for plotting
    plot_df = pd.merge(snow_df, site_df[['Site_Id', 'Elev']], on='Site_Id', how='left')
    plot_df.sort_values('Elev', ascending=False, inplace=True)
    # print(plot_df.info())
    # print(plot_df.head())

    plot_df['Site_Name'] = plot_df['Site_Name'] + '  <em style="font-size:0.7rem">'+ plot_df['Elev'].astype(str) + "'</em>"
    plot_df.sort_values('Elev', ascending=False, inplace=True)
    fig = go.Figure(
        data=[
            go.Scatter(
            name="Temperatures",
            y=plot_df["Site_Name"],
            x=plot_df["T_Obs"],
            mode="markers",
            marker=dict(size=10, 
                        color="orange")
            )
            ],
        layout=go.Layout(
            title="Current Temperatures",
            yaxis_title="Site",
            xaxis_title="Temp (F)",
            yaxis_type="category",
            paper_bgcolor='rgba(255,255,255,1)',
            plot_bgcolor='rgba(255,255,255,1)',
            xaxis = dict(
                linecolor='black',
                linewidth=2,
                mirror=True,
                ticks='outside',
                showline=True,
            ),
            yaxis = dict(
                linecolor='black',
                linewidth=2,
                mirror=True,
                ticks='outside',
                showline=True,
            ),
            xaxis_range=[min(0,min(plot_df['T_Obs'])-5), max(40, max(plot_df['T_Obs'])+5)]

        )

    )
    # add a reference line at 32 degrees
    fig.add_vline(x=32, line_width=2, line_dash="dash", line_color="blue" )

    fig.update_yaxes(autorange="reversed")
    fig.update_layout(width=800)

    return fig


#----------------------------------------------------------------------------------------
# PLOT 4 CURRENT SNOW DEPTHS AT MULTI SITES

def build_current_depths_plot(snow_df, site_df):

    print('\nBuilding current snow depths plot\n')

    plot_df = pd.merge(snow_df, site_df, on='Site_Id', how='left')
    plot_df['Site_Name'] = plot_df['Site_Name'] + '  <em style="font-size:0.7rem">'+ plot_df['Elev'].astype(str) + "'</em>"
    plot_df = plot_df[['Site_Name', 'Depth', 'Elev']]
    plot_df.sort_values('Elev', ascending=True, inplace=True)
    # print(plot_df.info())
    # print(plot_df.head())

    # Note: McCoy park has erroneous data peaks, need to figure out a filter for those data issues, 
    # for now, just remove before plotting
    # plot_df = plot_df[plot_df['Site_Name'] != "Mccoy Park"]

    fig = go.Figure(
        data=[
            go.Bar(
                # name="Current snow depths",
                # x=plot_df.index,
                x=plot_df['Site_Name'],
                y=plot_df['Depth']
            )
        ],
        layout=go.Layout(
            title="Current Settled Snow Depths",
            yaxis_title="Depth  HS  (in)",
            xaxis_type="category",
            paper_bgcolor='rgba(255,255,255,1)',
            plot_bgcolor='rgba(255,255,255,1)',
            xaxis = dict(
                linecolor='black',
                linewidth=2,
                mirror=True,
                ticks='outside',
                showline=True,
            ),
            yaxis = dict(
                linecolor='black',
                linewidth=2,
                mirror=True,
                ticks='outside',
                showline=True,
            )
        )
    )

    return fig


#----------------------------------------------------------------------------------------
#      INDIVIDUAL SITE PLOT FUNCTIONS
#----------------------------------------------------------------------------------------

#----------------------------------------------------------------------------------------
# PLOT 5 FULL SEASONAL SNOWFALL HISTORY (BASIC METEOGRAM) FOR 1 SITE

def build_seasonal_meteogram(daily_df, site_dict):

    '''Build a seasonal snowfall meteogram for a single SNOTEL site'''

    site_name = site_dict['Site_Name']
    site_id = site_dict['Site_Id']

    plot_df = daily_df.set_index('Date')
    tot_season = str(int(plot_df["New_Snow"].sum()))

    print(f'\nBuilding snowfall meteogram plot for {site_name}\n')

    # Create figure with secondary y-axis
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # Add traces
    
    fig.add_trace(
        go.Bar(
            name="New Snowfall (HN24)",
            x=plot_df.index,
            # y=plot_df[plot_df['Site_Name'] == site_name]["New_Snow"],
            y=plot_df["New_Snow"],
            customdata=plot_df.index.date,
            hovertemplate = '%{customdata}<br>New Snow: %{y} in<extra></extra>',
            ),
        secondary_y=False,
    )

    fig.add_trace(
        go.Bar(
            name="Settlement or Loss",
            x=plot_df.index,
            y=plot_df[plot_df['Site_Name'] == site_name]["Settlement"],
            customdata=plot_df.index.date,
            hovertemplate = '%{customdata}<br>Settlement: %{y} in<extra></extra>',  # ADD change SWE or density! to this?
            ),
        secondary_y=False,
    )

    fig.add_trace(
        go.Line(
            name="Current Base Depth (HS)",
            x=plot_df.index,
            y=plot_df[plot_df['Site_Name'] == site_name]["Depth"],
            customdata=plot_df.index.date,
            hovertemplate = '%{customdata}<br>HS: %{y} in<extra></extra>',
            ),
        secondary_y=True,
    )

    fig.add_trace(
        go.Line(
            name="SWE",
            x=plot_df.index,
            y=plot_df["SWE"],
            line=dict(dash = 'dot', width= 2,),
            customdata=plot_df.index.date,
            hovertemplate = '%{customdata}<br>SWE: %{y} in<extra></extra>',
            ),
        secondary_y=True,
    )

    #Layout options

    # make background and paper white and add a border around entire plot
    fig.update_layout(
            paper_bgcolor='rgba(255,255,255,1)',
            plot_bgcolor='rgba(255,255,255,1)',
            xaxis = dict(
                linecolor='black',
                linewidth=1,
                mirror=True,
                ticks='outside',
                showline=True,
            ),
            yaxis = dict(
                linecolor='black',
                linewidth=1,
                mirror=True,
                ticks='outside',
                showline=True,
            )
    )

    # Add figure title
    fig.update_layout(
        # title_text=f"Season Snowfall History for {site_name}",
        title_text=f'Season Snowfall History for {site_name}<br><br><sup>Total recorded snowfall since season start: {tot_season}"<sup>',
    
        yaxis2 = dict(matches='y')
    )

    # Set y-axes titles
    fig.update_yaxes(title_text="Depth (HS) and daily Δ (HN24) +/- (in)", secondary_y=False)
    fig.update_yaxes(title_text="SWE (in)", secondary_y=True)
    # fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='#989898')

    fig.update_yaxes(zeroline=True, zerolinecolor="#989898", secondary_y=True)

    # legend location
    fig.update_layout(
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01
            )
        )

    fig.update_layout(
        xaxis=dict(
            tick0 = dt.strptime('2021-10-01', '%Y-%m-%d'),
            # dtick='D7',
            dtick = 7*24*60*60*1000, # format number of days using milliseconds
            tickformat="%d\n%b"
        )
    )
    # fig.show()

    return fig


#----------------------------------------------------------------------------------------
# PLOT 6 SEASONAL TEMPERATURE HISTORY FOR 1 SITE

def build_seasonal_temperature_plot(plot_df, site_dict):

    '''Build a ribbon plot of min/max daily temperatures for a SNOTEL site'''

    site_name = site_dict['Site_Name']
    site_id = site_dict['Site_Id']

    plot_df.set_index('Date', inplace=True)

    print(f'\nBuilding temperature plot for {site_name}\n')

    # print(plot_df.tail())

    fig = go.Figure(
        data=[
            go.Line(
            name="High",
            x=plot_df.index,
            y=plot_df[plot_df['Site_Name'] == site_name]["T_Max"],
            line=dict(color="#00008b"),
            hovertemplate = '%{y} °F<extra></extra>'
            ),
            go.Line(
            name="Low",
            x=plot_df.index,
            y=plot_df[plot_df['Site_Name'] == site_name]["T_Min"],
            line=dict(color="#A5F2F3"),
            hovertemplate = '%{y} °F<extra></extra>'
            )
        ]
    )
    fig.add_hline(y=32, line_width=2, line_dash="dash", line_color="orange", opacity=0.5 )
    fig.update_layout(
        hovermode='x',
        title=f"Season temperature history for {site_name}",
        yaxis_title="Temp (F)",
        font=dict(
            family="Tahoma",
            size=12,
            color="black"
        ),
        paper_bgcolor='rgba(255,255,255,1)',
        plot_bgcolor='rgba(255,255,255,1)',
        xaxis = dict(
            linecolor='black',
            linewidth=1,
            mirror=True,
            ticks='outside',
            showline=True,
        ),
        yaxis = dict(
            linecolor='black',
            linewidth=1,
            mirror=True,
            ticks='outside',
            showline=True,
        )
    )

    # legend location
    fig.update_layout(
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.90
            )
        )
    # fig.show()

    return fig


#----------------------------------------------------------------------------------------
# PLOT 7 SEASONAL TEMPERATURE HISTORY FOR 1 SITE

# Build a wind timeseries plot with traces for average speed, max speed, and direction

def build_wind_plot(plot_df, site_dict):

    '''Build a wind history plot for an individual site'''

    plot_df = plot_df.set_index('DateTime')
    # print(plot_df.info())
    # print(plot_df.tail())

    site_name = site_dict['Site_Name']
    site_id = site_dict['Site_Id']

    print(f'\nBuilding wind plot for {site_name}\n')

    # plot_df = plot_df.set_index('Date')

    fig = go.Figure()
    
    # average wind speed
    fig.add_trace(
        go.Scatter(
            name="Avg. Wind Speed",
            mode="lines",
            x=plot_df.index,
            y=plot_df["Wvel_avg"],
            customdata=plot_df.index.date,
            hovertemplate = 'Avg Speed: %{y} mph<extra></extra>'
        )
    )

    # gusts
    fig.add_trace(
        go.Scatter(
            mode="markers",
            name="Gust",
            x=plot_df.index,
            y=plot_df["Wvel_max"],
            customdata=plot_df.index.date,
            hovertemplate = 'Gust: %{y} mph<extra></extra>',  # ADD change SWE or density! to this?
            )
    )

    # wind direction arrows on top of graph
    fig.add_trace(
        go.Scatter(
                name='Direction',
                mode="markers",
                x=plot_df.index,
                y=pd.Series( [plot_df['Wvel_max'].max() * 1.1 ]*len(plot_df.index) ),
                marker=dict(
                    size=14, 
                    symbol="arrow-up", 
                    angle= plot_df.Wdir_avg - 180, 
                    line=dict(width=0.5, color="DarkSlateGrey"), 
                    opacity=0.8
                ),
                text = plot_df['Wdir_avg'].values,
                hoverinfo = 'x+text',
                hovertemplate = "Direction: %{text}&deg;<extra></extra>"
            )
    )

    fig.update_layout({
        'plot_bgcolor': 'rgba(0,0,0,0)',
        # 'paper_bgcolor': 'rgba(0,0,0,0)'
    })

    # get max date and 7 days before, set initial plot axis on last 7 days
    max_date = plot_df.index.max() 
    prior_3days = plot_df.index.max() - timedelta(3)

    fig.update_layout(
        title=f"{site_name} wind history",
        yaxis_title="Wind speed, mph",
        hovermode="x",
        xaxis_range=[prior_3days, max_date],
        showlegend=False
    )

    # Add range slider and range buttons
    fig.update_layout(
        xaxis=dict(
            rangeselector=dict(
                buttons=list([
                    dict(count=3,
                        label="3d",
                        step="day",
                        stepmode="backward"),
                    # dict(count=7,
                    #     label="7d",
                    #     step="day",
                    #     stepmode="backward"),
                    # dict(count=1,
                    #     label="1m",
                    #     step="month",
                    #     stepmode="backward"),
                    dict(label="All",step="all"),  
                ])
            ),
            rangeslider=dict(
                visible=True
            ),
            type="date"
        )
    )
    
    # fig.show()
    return fig


#----------------------------------------------------------------------------------------
# PLOT 8 SWE REGIME PLOT (PERCENTILES PLOT) FOR 1 SITE

def build_SWE_regime_plot(plot_df, ts_df, site_dict):

    '''Build a SWE regime plot (daily value percentile plot) for a single SNOTEL site for the
    available POR. Use the aggregated day of year dataframe, the full POR daily timesries, and build the flow regime plot.
    Takes in several dataframes and metadata variables (site_dict and returns a plotly plot 
    '''
    # plot_df = plot_df.set_index('Date')
    site_name = site_dict['Site_Name']
    site_id = site_dict['Site_Id']
    start_yr_str = str(min(ts_df.Date).year)
    end_yr_str = str(max(ts_df.Date).year)  

    print(f'building SWE regime percentile plot for {site_name} {site_id} {start_yr_str}-{end_yr_str}')

    # Create figure 

    # remove leap dates
    plot_df = plot_df[~((plot_df['Date'].dt.month == 2) & (plot_df['Date'].dt.day == 29))]
    plot_df = plot_df[~(plot_df['doy']== 366) ]

    # sort by date to ensure plotting order is correct
    plot_df = plot_df.sort_values(by=['Date'])

    # calc a water year column
    ts_df['WY'] = ts_df.Date.dt.to_period('A-Sep').astype(str).astype(int)
    year_list = ts_df['WY'].unique()

    # TODO: account for whether or not you are in the correct water year for the the 'this year' statement
    # create another fake dates column to trick the plot for plotting on
    # julian dates but using this year's dates as the x axis
    this_year = dt.today().year
    # date_range = pd.date_range(start=f'1/1/{this_year}', end=f'12/31/{this_year}')
    date_range = pd.date_range(start=f'10/1/{this_year-1}', end=f'09/30/{this_year}')
    # print(date_range)
    fake_dates = pd.DataFrame({'plot_date':date_range})
    fake_dates['doy'] = fake_dates['plot_date'].dt.dayofyear

    # get the date of peak median to plot
    median_peak_date = plot_df['doy'].loc[plot_df['median'].idxmax()]
    print(f'median peak date: {median_peak_date}')
    median_peak_date = pd.to_datetime(this_year*1000 + median_peak_date, format="%Y%j")
    median_peak_SWE = plot_df['median'].max()
    print(plot_df.tail())
    yesterday = dt.now().date() - timedelta(1)
    current_SWE_perc = int(plot_df.loc[plot_df['Date'].dt.date==yesterday]['SWE'].values[0] / median_peak_SWE * 100)
    
    #draw the figure with some initial formatting settings
    fig = go.Figure(
            layout=go.Layout(
                title=go.layout.Title(text=f"Mean Daily SWE Percentiles, {start_yr_str}-{end_yr_str}<br>{site_name} ({site_id})<br><sup>Current SWE is {current_SWE_perc}% of annual median peak SWE.</sup>"),
                plot_bgcolor='#fff',
                legend_title_text='SWE<br>Percentiles',
                xaxis = dict(title = None, showline=True, linewidth=0.5, linecolor='black', mirror=True, tickformat='%b-%d',dtick="M1",),
                yaxis = dict(title = 'Mean daily flow (cfs)', showline=True, linewidth=0.5, linecolor='black',mirror=True,),
                height= 500,
            )
        )

    fig.update_layout(
      legend=dict(
          bordercolor="Black",
          borderwidth=1
      )
    )

    # View the current hovertool settings in case you want to try and modify:
    fig.update_traces(hovertemplate="%{y:,.3r}")
    fig.update_layout(hovermode="x unified")
    fig.update_layout(legend_traceorder='normal')

    # Add traces: shaded percentile areas, median, current, and all yiears

    # Max (no line, just a boundary for fill shading and for hoverinfo)
    fig.add_trace(go.Scatter(x=plot_df['Date'],
                            y=plot_df['max'],
                            mode='lines',
                            line=dict(color='#D9D9FC', width=1),
                            showlegend=False,
                            name='Max'
                            )
    )

    # 90th percentile (shade here to 100th/max )
    fig.add_trace(go.Scatter(x=plot_df['Date'],
                            y=plot_df['q90'],
                            mode='lines',
                            line=dict(width =0),
                            name='90th-Max',
                            hoverinfo='skip',
                            fill='tonexty',
                            fillcolor='#D9D9FC', # light purple
                            )
    )

    # 75th percentile (shade here to 90th)
    fig.add_trace(go.Scatter(x=plot_df['Date'],
                            y=plot_df['q75'],
                            mode='lines',
                            line=dict(width =0),
                            fill='tonexty',
                            fillcolor='#D9FCFC', #light blue
                            name='75th-90th',
                            hoverinfo='skip'
                            )
    )

    # 25th percentile (shade here to 75th)
    fig.add_trace(go.Scatter(x=plot_df['Date'],
                            y=plot_df['q25'],
                            mode='lines',
                            line=dict(width =0),
                            name='25th-75th',
                            fill='tonexty',
                            fillcolor='#EAFCEA', #light green
                            hoverinfo='skip'
                            )
    )

    # 10th percentile (shade here to 25th)
    fig.add_trace(go.Scatter(x=plot_df['Date'],
                            y=plot_df['q10'],
                            mode='lines',
                            line=dict(width =0),
                            name='10th-25th',
                            fill='tonexty',
                            fillcolor='#FCFCD9', #light yellow
                            hoverinfo='skip'
                            )
    )

    # Min / 0th (shade here to 10th)
    fig.add_trace(go.Scatter(x=plot_df['Date'],
                            y=plot_df['min'],
                            mode='lines',
                            line=dict(width=0),
                            name='Min-10th',
                            fill='tonexty',
                            fillcolor='#FCD9D9', #light red/orange
                            hoverinfo='skip'
                            )
    )

    # Median (overplot a dark dotted line)
    fig.add_trace(go.Scatter(x=plot_df['Date'],
                            y=plot_df['median'],
                            mode='lines',
                            line=dict(color='darkblue', width =1, dash='dot'),
                            name='Median'
                            )
    )

    # Min (no line, just a trace to show in the hoverinfo tooltip)
    fig.add_trace(go.Scatter(x=plot_df['Date'],
                            y=plot_df['min'],
                            mode='lines',
                            line=dict(color='#FCD9D9', width=1),
                            showlegend=False,
                            name='Min'
                            )
    )

    # Current Year
    fig.add_trace(go.Scatter(x= plot_df['Date'],
                            y= plot_df['SWE'],
                            mode='lines',
                            line=dict(color='rgb(0,0,140)', width =2),
                            name='Current Yr',
                            text=plot_df['perc_of_median'].round(),
                            hovertemplate = 'Current: %{y:.1f}"<extra></extra><br>(%{text}% of median<br>for this date)'
                            )
    )

    # Add in all the rest of the years, but make them not visible
    # unless clicked on in the legend

    

    # Median Peak day marker (overplot a dark X character)
    fig.add_trace(go.Scatter(x=pd.Series(median_peak_date),
                            y=pd.Series(median_peak_SWE),
                            mode='markers',
                            marker=dict(color='darkblue'),
                            hoverinfo='skip',
                            showlegend=False,
                            )
    )


    for year in reversed(year_list[0:-1]):

        # subset the year of interest
        year_data = ts_df[ts_df['WY']==year]
        # remove leap dates
        year_data = year_data[~((year_data['Date'].dt.month == 2) & (year_data['Date'].dt.day == 29))]


        # merge on the fake date column
        year_data['doy'] = year_data['Date'].dt.dayofyear
        year_data = year_data.merge(fake_dates, on ='doy', how='left')
        # remove the last row, which will have Nan on 12/31 in a leap years
        year_data = year_data[:-1]
        year_data = year_data[~(year_data['doy'] == 366)]

        # sort by date to ensure plotting order is correct
        year_data = year_data.sort_values(by=['Date'])

        # plot each year as a different random color
        fig.add_trace(go.Scatter(x= year_data['plot_date'],
                                y= year_data['SWE'],
                                mode='lines',
                                line=dict(width=1.5),
                                name=str(year),
                                visible='legendonly'
                                )
        )

    # fig.update_traces(hovertemplate="%{y:,.3r}")
    print("plotly express hovertemplate:", fig.data[0].hovertemplate)

    # hovertemplate formatting options
    fig.update_layout(
        hoverlabel=dict(
            bgcolor="white",
            font_size=12,
            font_family="Tahoma"
        )
    )

    # fig.show()
    return fig





















#
