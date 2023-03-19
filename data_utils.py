# utility functions for updating the daily data and the hourly data.

# dependencies
# from asyncio.windows_events import NULL
from datetime import datetime as dt, timedelta
import pytz
import os.path
import numpy as np
import pandas as pd

import pytz

#-------------------------------------------------------------------------------------------------------------
# future buildout will include database functionality

# def get_db_update_time(which_database):

#     '''get the timestamp of the most recent observation from the update_time.json file and check it against the current time
#     in the appropriate timezone, if it is current, return TRUE, if it is out of date, return FALSE
 
#     Parameters
#     ------------
#         which_database: text
#             a switch argument to direct the check to the daily or hourly timestamp key in the update_time.json file
        
#     Return
#     -----------
#         update_time : a python datetime object 
#             the date and time the database of interest was last updated

#     '''
#     pass


# def update_daily_database(last_update_date):
#     '''Call the SNOTEL API and get the multi-station values between the last update time and the current time,
#     format them to match the data model add them as new rows. no value is returned.'''
#     pass


# def update_hourly_database(last_update_datetime):
#     '''Call the SNOTEL API and get the multi-station values between the last update time and the current time,
#     format them to match the data model add them as new rows. no value is returned.'''
#     pass

#---------------------------------------------------------------------------------------------------------------

def build_plot_site_df(site_list):
    site_df = pd.DataFrame.from_dict(site_list)
    site_df.columns=('Site_Name', 'Site_Id', 'State', 'Zone', 'Latitude', 'Longitude', 'Elev')
    # define column datatypes if needed...
    site_df = site_df.astype({'Elev':'int'})
    return site_df


def build_site_list_str(site_list):
    ''' receive the rows or dict list from the master site list that have pertinent metadata to build the URL string 
    for the api call, this includes the site ID, the site state, '''
    site_str_list = []
    for site_dict in site_list:
        site_str = f"{site_dict['stationID']}:{site_dict['stationState']}:SNTL%7C"
        site_str_list.append(site_str)
    return  ''.join(site_str_list)



def format_hourly_SNOTEL_dataframe(df):

    ''' Perform a variety of smoothing and filtering operations on the data frame so that
    plotting functions will produce nice looking plots and not get confused by missing data etc.
    Accepts a dataframe and returns a dataframe.'''

    # Fill missing values in 'Depth' with the previous reported value (forward fill)
    df['Depth']= df.groupby(['Site_Id'])["Depth"].fillna(method='ffill')

    # Smooth out any minor fluctuations from the snotel sensor by taking the max value across a 4 hour window
    df['Depth']=df['Depth'].rolling(window=4, min_periods=1).max()

    # Find the change in Depth and change in SWE over each row
    df["d_Depth"] = df.groupby(["Site_Id"])["Depth"].diff().fillna(0)

    return df


def format_daily_SNOTEL_dataframe(df):
    
    ''' Perform a variety of smoothing and filtering operations on the data frame so that
    plotting functions will produce nice looking plots and not get confused by missing data etc.
    Accepts a dataframe and returns a dataframe.'''

    # Fill missing values in 'Depth' with the nearest value, for continuous plotting
    df['Depth'] = df.groupby(['Site_Id'])["Depth"].fillna(method='ffill')

    # Find the change in Depth and change in SWE over each row
    df["d_Depth"] = df.groupby("Site_Id")["Depth"].diff().fillna(0)
    df["d_SWE"] = df.groupby("Site_Id")["SWE"].diff().fillna(0)

    # Assign positive changes in depth to 'new snow' and negative changes to 'settlement'
    df["New_Snow"] = df["d_Depth"][df["d_Depth"] > 0]
    df["New_Snow"].fillna(0, inplace=True)
    df["Settlement"] = df["d_Depth"][df["d_Depth"] < 0]
    df["Settlement"].fillna(0, inplace=True)

    # Fill missing values in 'Depth' with the last logged value, for continuous plotting
    df['Depth'] = df.groupby(['Site_Id'])["Depth"].fillna(method='ffill')

    return df


def format_POR_SNOTEL_dataframe(df):
    
    ''' Perform a variety of smoothing and filtering operations on the data frame so that
    plotting functions will produce nice looking plots and not get confused by missing data etc.
    Accepts a dataframe and returns a dataframe.'''

    # Fill missing values in 'SWE' with the nearest value, for continuous plotting
    df['SWE'] = df["SWE"].fillna(method='ffill')    

    # add some grouping columns for dataframe summaries
    df["Year"] = df['Date'].dt.year
    df["Month"] = df['Date'].dt.month
    df["doy"] = df['Date'].dt.dayofyear

    # add a water year column; pandas period object, A-Sep means 'annual' period ends in Sep?
    df['WY'] = df.Date.dt.to_period('A-Sep').astype(str).astype(int) # WYyear ends on sep

    # subset only snowpack months to help plot focus just on snowpack periods of the year
    df = df[df.Month.isin([10,11,12,1,2,3,4,5,6,7])]


    return df

def build_doy_df(df):

    ''' build a day-of-year (julian date) percentile data frame using the period of record dataframe'''
        
    # calculate day-of-year percentiles

    # 90th Percentile
    def q90(x):
        return x.quantile(0.9)

    # 75th Percentile
    def q75(x):
        return x.quantile(0.75)

    # 25th Percentile
    def q25(x):
        return x.quantile(0.25)

    # 10th Percentile
    def q10(x):
        return x.quantile(0.1)


    df_doy = df[['SWE', 'doy']].groupby(["doy"]).agg(
            {'SWE': ['max', q90, q75, 'median', q25, q10, 'min']}).reset_index()

    df_doy.columns = df_doy.columns.droplevel(0)
    df_doy.rename(columns={ df_doy.columns[0]: "doy" }, inplace = True)

    # print(df_doy.head())
    return df_doy


def add_plotting_variables(df_doy, current_wy_df):

  '''
  create a fake date column for plotting and merge it to the doy dataframe,
  this allows an actual date axis instead of doy
  '''

  #get the current  water year
  if dt.today().month < 10:
    this_wy = dt.today().year
  else:
    this_wy = dt.today().year-1
  # print(this_wy) 

  # date_range = pd.date_range(start=f'10/1/{this_wy}', end=f'12/31/{dt.today().year}')
  date_range = pd.date_range(start=f'10/1/{this_wy-1}', end=f'09/30/{dt.today().year}')
  fake_dates = pd.DataFrame({'Date':date_range})
  fake_dates['doy'] = fake_dates['Date'].dt.dayofyear
  df_doy = df_doy.merge(fake_dates, on='doy')

  df_doy = df_doy.merge(current_wy_df[['SWE','doy']], on='doy', how='left')
  df_doy['perc_of_median'] = round(df_doy['SWE'] / df_doy['median'],2) * 100
  df_doy['perc_of_median'] = df_doy['perc_of_median'].fillna(0)

  return df_doy


# TODO: refactor all the data fetching functions into a single function that just takes arguments for the 
# timestep and which site parameters should be returned; then make a separate formatting function for 
# each type of dataset returned (hourly for 7 days, daily for the current season, full POR)

def get_hourly_data(site_list):

    ''' Call SNOTEL webservice and return a csv file for a multi-station report'''

    if os.path.exists('dev/dev_data_hourly_fake_file.csv'):

        print('\nGetting file locally from development data\n')
        df = pd.read_csv('dev/dev_data_hourly.csv')
        # the datetime datatype gets lost in the csv conversion, which messes up the 
        # snow_df creation later, make sure datatypes correct
        df["DateTime"] = pd.to_datetime(df['DateTime'])

    else:

        print(f'\nGetting hourly data for {site_list} from SNOTEL Webservic\ne')

        # set starting and ending date parameters
        # todo: make this time-zone agnostic; or get the timezone of the user's system time...
        now_date = dt.now(pytz.timezone('US/Mountain')) 
        # now_date_str = now_date.strftime('%Y-%m-%d')
        n_days = 7
        start_date_str = (now_date - timedelta(n_days) ).strftime('%Y-%m-%d')
        time_step = 'hourly'
        
        # snotel site parameter string
        multi_site_str = build_site_list_str(site_list)
        
        # Parameters for hourly data are: Snow Depth, SWE, Current Temperature, Wind speed, Wind direction, Wind gust
        # hourly_param_str = f'SNWD::value,WTEQ::value,TOBS::value,WDIRV::value,WSPDV::value,WSPDX::value'
        hourly_param_str = f'SNWD::value,WTEQ::value,PREC::value,TOBS::value,WDIRV::value,WSPDV::value,WSPDX::value'
        

        base_url = 'https://wcc.sc.egov.usda.gov/reportGenerator/view_csv/customMultipleStationReport/'
        full_param_str = f'{time_step}/start_of_period/{multi_site_str}id=%22%22%7Cname/{start_date_str},0/{hourly_param_str}'

        url = base_url + full_param_str
        print(f'\n{url}\n')

        try:
            df = pd.read_csv(url, comment="#", index_col=None, parse_dates=['Date'], sep=',')
        except Exception as e:
            print(e)
            # TODO: perhaps save the last successful data call locally, and if an updated call is not available, just
            # read in yesterdays data and plot it to allow the site to always work during interim periods
        
        print(f'\nHourly dataframe info:\n')
        print(df.info())
        print(df.tail())
        print(f'dataframe columns: {df.columns}')

        if df.shape[1] == 10:
            df.columns = ["DateTime", "Site_Id", "Site_Name", "Depth", "SWE", "Prec_Accum", "T_Obs", "Wdir_avg","Wvel_avg","Wvel_max"]
            print('updated columns: ')
            print(df.info())
        else:
            df.columns = ["DateTime", "Depth", "SWE", "Prec_Accum", "T_Obs", "Wdir_avg", "Wvel_avg", "Wvel_max"]
            df['Site_Id']=site_list[0]['stationID']
            df['Site_Name']=site_list[0]['stationName']
            print('updated columns')
            print(df.info())
            df = df[ ["DateTime", "Site_Id", "Site_Name", "Depth", "SWE", "Prec_Accum", "T_Obs", "Wdir_avg", "Wvel_avg", "Wvel_max"] ]

        df["DateTime"] = pd.to_datetime(df['DateTime'])

        # during development, write the file to a csv to be called locally
        df.to_csv('dev/dev_data_hourly.csv', index=False, sep=',', mode='a')
    
    df = format_hourly_SNOTEL_dataframe(df)

    return df


def get_daily_data(site_list):

    '''
    Call the snotel service and for a daily dataset, return a dataframe
    '''

    if os.path.exists('dev/dev_data_daily_fake_file.csv'):

        print('\nGetting file locally from development data\n')
        df = pd.read_csv('dev/dev_data_daily.csv')
        # the datetime datatype gets lost in the csv conversion, which may messes up the 
        # creation of some other dfs later, make sure datatype is correct
        df["Date"] = pd.to_datetime(df['Date'])
    
    else:

        print("\nGetting daily dataframe from SNOTEL webservice\n")

        # create some timestep strings to use in the url
        time_step='daily'
        now_MST = dt.now(pytz.timezone('US/Mountain'))
        now_month = now_MST.month
        now_year = now_MST.year
        start_date_str = ( now_MST - timedelta(7) ).strftime('%Y-%m-%d') 

        # start date parameter string begins at most recent Water Year
        if now_month in [10, 11, 12]:
            start_date_str = f'{now_year}-10-01'
        else: 
            start_date_str = f'{now_year-1}-10-01'
        print(f'start date is {start_date_str}')

        # snotel site parameter string
        multi_site_str = build_site_list_str(site_list)
        print(f'building daily dataframe for sites: {multi_site_str}')

        # parameters to return for daily are: Depth, SWE, Accumulated Precip, Current Temp, Max Temp, Min Temp
        # see 'https://wcc.sc.egov.usda.gov/reportGenerator/' for help
        daily_param_str = f'SNWD::value,WTEQ::value,PREC::value,TOBS::value,TMAX::value,TMIN::value'
        
        base_url = 'https://wcc.sc.egov.usda.gov/reportGenerator/view_csv/customMultipleStationReport/'
        full_param_str = f'{time_step}/end_of_period/{multi_site_str}id=%22%22%7Cname/{start_date_str},0/{daily_param_str}'
        url = base_url + full_param_str
        print(f'\nDaily values URL: {url}\n')

        try:
            df = pd.read_csv(url, comment="#", index_col=None, sep=',')
        except Exception as e:
            print(e)
            # TODO: perhaps save the last successful data call locally, and if an updated call is not available, just
            # read in yesterdays data and plot it to allow the site to always work during interim periods
        
        print('\nDaily dataframe info:\n')
        print(df.tail())
        print(df.info())

        # If making a multi-site URL call, colums for ID and Name will be returned. If not, need to manually add those in
        # for use in later plotting functions
        # print(df.columns)

        if df.shape[1] == 9:
            df.columns = ["Date", "Site_Id", "Site_Name", "Depth", "SWE", "Prec_Accum", "T_Obs", "T_Max", "T_Min"]
        else:
            df.columns = ["Date", "Depth", "SWE", "Prec_Accum", "T_Obs", "T_Max", "T_Min"]
            df['Site_Id']=site_list[0]['stationID']
            df['Site_Name']=site_list[0]['stationName']
            # print(df.columns)
            df = df[ ["Date", "Site_Id", "Site_Name", "Depth", "SWE", "Prec_Accum", "T_Obs", "T_Max", "T_Min"] ]

        df["Date"] = pd.to_datetime(df['Date'])

        # during developement, write the file to a csv to be called locally
        df.to_csv('dev/dev_data_daily.csv', index=False, sep=',', mode='a')

    df = format_daily_SNOTEL_dataframe(df)

    return df


def get_POR_data(site_list):
    
    '''
    Call the snotel service and get a dataframe of daily data for the period of record
    '''

    if os.path.exists('dev/dev_POR_daily_fake_file.csv'):

        print('\nGetting file locally from development data\n')
        df = pd.read_csv('dev/dev_data_POR.csv')
        # the datetime datatype gets lost in the csv conversion, which may messes up the 
        # creation of some other dfs later, make sure datatype is correct
        df["Date"] = pd.to_datetime(df['Date'])
    
    else:

        print("\nGetting POR dataframe from SNOTEL webservice\n")

        # create some timestep strings to use in the url
        time_step='daily'
        start_year = dt.now(pytz.timezone('US/Mountain')).year - 30
        start_date_str = f'{start_year}-10-01'

        # snotel site parameter string
        multi_site_str = build_site_list_str(site_list)
        print(f'building daily dataframe for sites: {multi_site_str}')

        # parameters to return for POR data are: SWE (snow depth generally only available in last 10 yrs...)
        # see 'https://wcc.sc.egov.usda.gov/reportGenerator/' for help
        daily_param_str = f'WTEQ::value'
        
        base_url = 'https://wcc.sc.egov.usda.gov/reportGenerator/view_csv/customMultipleStationReport/'
        full_param_str = f'{time_step}/end_of_period/{multi_site_str}id=%22%22%7Cname/{start_date_str},0/{daily_param_str}'
        url = base_url + full_param_str
        print(f'\nDaily SWE values for POR URL: {url}\n')

        try:
            df = pd.read_csv(url, comment="#", index_col=None, sep=',')
        except Exception as e:
            print(e)
            # TODO: perhaps save the last successful data call locally, and if an updated call is not available, just
            # read in yesterdays data and plot it to allow the site to always work during interim periods
        
        print('\nDaily SWE dataframe info:\n')
        print(df.tail())
        print(df.info())

        # If making a multi-site URL call, colums for ID and Name will be returned. If not, need to manually add those in
        # for use in later plotting functions
        # print(df.columns)

        if df.shape[1] == 4:
            df.columns = ["Date", "Site_Id", "Site_Name", "SWE"]
        else:
            df.columns = ["Date", "SWE"]
            df['Site_Id']=site_list[0]['stationID']
            df['Site_Name']=site_list[0]['stationName']
            # print(df.columns)
            df = df[ ["Date", "Site_Id", "Site_Name","SWE"] ]

        df["Date"] = pd.to_datetime(df['Date'])

        # during developement, write the file to a csv to be called locally
        df.to_csv('dev/dev_data_POR.csv', index=False, sep=',', mode='a')

    df = format_POR_SNOTEL_dataframe(df)
    print(df.info())
    print(df.head())

    return df


def build_summary_df(dfh, dfd):

    ''' Use the daily and hourly dataframes to create a summary dataframe that will be used in most of the plotting
    codes '''

    # 1) create some date/time stamps to help get specific data points from the hourly and daily dataframes
    print("\nChecking time indices...")
    now_MST = dt.now(pytz.timezone('US/Mountain'))
    print(f'\nCurrent time MST is {now_MST}')
    now_str = now_MST.strftime('%Y-%m-%d')
    this_morning = f"{now_str} 06:00"
    this_morning = pd.to_datetime(this_morning, format='%Y-%m-%d %H:%M')
    print(f'This morning time was {this_morning}')
    midnight = f"{now_str} 00:00"
    midnight = pd.to_datetime(midnight, format='%Y-%m-%d %H:%M')
    yesterday = (dt.today()-timedelta(1)).strftime("%Y-%m-%d")
    yesterday = pd.to_datetime(f"{yesterday} 16:00", format='%Y-%m-%d %H:%M')
    print(f'\nyesterdays times were {midnight} and {yesterday}\n')

    # 2) find a the values of interest

    # today's most current values
    print(dfh.head())
    print(dfh.info())
    most_recent_df = dfh.loc[dfh.groupby(['Site_Id'])['DateTime'].idxmax()].set_index('Site_Id')

    # TODO: do i need to keep the Site_id column here for any reason later on?....
    most_recent_df = most_recent_df[[ 'Site_Name', 'DateTime','T_Obs', 'Depth', 'SWE']]

    # get values from 6am today, 4pm yesterday, and 24 hours from current time and 
    # put together into a list of dataframes to be joined

    df_list = []

    # 6am today reading (Need to only run if today's current time is later than 6am)
    if now_MST.hour > 5:
        print('\ngetting values for 6am')
        today_6am = dfh[ dfh['DateTime'] == this_morning][['Site_Id', 'Depth']]
        today_6am = today_6am.rename({'Depth':'Depth_6am'}, axis=1).set_index("Site_Id")
        print(today_6am)
    else:
        # make an empty dataframe as a placeholder for creating the html chart later
        today_6am = pd.DataFrame(list(zip(most_recent_df.index,[])), columns =['Site_Id', 'Depth_6am']).set_index("Site_Id")
    
    df_list.append(today_6am)

    # 12am today reading (closing time)
    today_12am = dfh[ dfh['DateTime'] == midnight][['Site_Id', 'Depth']]
    today_12am = today_12am.rename({'Depth':'Depth_12am'}, axis=1).set_index("Site_Id")
    df_list.append(today_12am)

    # 4pm yesterday reading (closing time)
    yesterday_4pm = dfh[ dfh['DateTime'] == yesterday][['Site_Id', 'Depth']]
    yesterday_4pm = yesterday_4pm.rename({'Depth':'Depth_4pm'}, axis=1).set_index("Site_Id")
    df_list.append(yesterday_4pm)

    # 24 hours ago reading
    now_MST = dt.now(pytz.timezone('US/Mountain'))
    hr24_ago = dt.strptime( dt.strftime(now_MST - timedelta(1), '%Y-%m-%d %H:%M' ), '%Y-%m-%d %H:%M')
    # hr24_ago = hr24_ago.replace(second=0, microsecond=0, minute=0, hour=hr24_ago.hour)
    hr24_ago = hr24_ago.replace(second=0, microsecond=0, minute=0, hour=hr24_ago.hour).strftime("%Y-%m-%d %H:%M:%S")
    last_24 = dfh[ dfh['DateTime'] == hr24_ago][['Site_Id', 'Depth', 'SWE']]
    last_24 = last_24.rename({'Depth':'Depth_24hr', 'SWE':'SWE_24'}, axis=1).set_index("Site_Id")
    df_list.append(last_24)

    # Get last week's data for joining to the station summary dataframe
    # last week (7 days ago)
    today = now_MST.replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=None)
    # date_range = pd.date_range(end=today, periods=7, freq='24H')
    date_range = pd.date_range(end=today, periods=7, freq='24H').astype('str')  # use string because the date column is not a date type anymore
    last_week_df = dfd[ dfd['Date'].isin(date_range)]
    # print(last_week_df.head())
    last_week_summary = last_week_df.groupby('Site_Id')[['New_Snow','Settlement']].sum()
    last_week_summary.columns = ['New_Snow_7d', 'Settlement_7d']
    df_list.append(last_week_summary)
    # print(last_week_summary)

    # 72 hours ago
    # date_range = pd.date_range(end=today, periods=3, freq='24H')
    date_range = pd.date_range(end=today, periods=3, freq='24H').astype('str') # use string because the date column is not a date type anymore
    three_days_df = dfd[ dfd['Date'].isin(date_range)]
    three_days_summary = three_days_df.groupby('Site_Id')[['New_Snow','Settlement']].sum()
    three_days_summary.columns = ['New_Snow_3d', 'Settlement_3d']
    df_list.append(three_days_summary)

    # Join all the recent depth values together
    snow_df = most_recent_df.join(df_list, how="outer")

    # calculate the change in snow metrics over various time periods, 
    snow_df["Since_6am"] = snow_df["Depth"] - snow_df["Depth_6am"]
    snow_df["Since_4pm"] = snow_df["Depth"] - snow_df["Depth_4pm"]
    snow_df["Since_12am"] = snow_df["Depth"] - snow_df["Depth_12am"]
    snow_df["Last_24"] =snow_df["Depth"] - snow_df["Depth_24hr"]
    snow_df["dSWE_24"] = snow_df["SWE"] - snow_df["SWE_24"]

    #if any values are negative (settlement), just set them to zero
    snow_df.Since_6am = np.where(snow_df.Since_6am < 0, 0, snow_df.Since_6am)
    snow_df.Since_12am = np.where(snow_df.Since_12am < 0, 0, snow_df.Since_12am)
    snow_df.Since_4pm = np.where(snow_df.Since_4pm < 0, 0, snow_df.Since_4pm)
    snow_df.Last_24 = np.where(snow_df.Last_24 < 0, 0, snow_df.Last_24)
    snow_df.dSWE_24 = np.where(snow_df.dSWE_24 < 0, 0, snow_df.dSWE_24)

    # If any shorter time period snowfall in last 24 is greater than 'last_24', assign that to 'last_24'
    snow_df["Last_24"] = snow_df[["Last_24", "Since_6am", "Since_4pm", "Since_12am"]].max(axis=1)
    # If any shorter time period in last 3 days

    # Add the snow from today between 6am and now into the 7d and 3d totals 
    # (totals to this point in the code are based off of start-of-day values, so don't include last few hours since midnight)
    snow_df['New_Snow_7d'] = snow_df['New_Snow_7d'] + snow_df['Since_12am'] 
    snow_df['New_Snow_3d'] = snow_df['New_Snow_3d'] + snow_df['Since_12am'] 

    # house cleaning for plotting
    snow_df = snow_df.reset_index()
    snow_df["Site_Id"] = snow_df["Site_Id"].astype("string")

    return snow_df


#----------------------------------------------------------------------------------------------------------------------------
# FUTURE FUNCTION IDEAS STO FETCH DATA FROM REGULARLY UPDATED LOCAL DATABASE RATHER THAN DIRECT FROM API

def check_last_update_time():
    pass


def update_hourly_data():
    # calls the snotel api and gets a new hourly 7 day dataset.
    pass


def update_daily_data():
    pass



#---------------------------------------------------------------------------------------------------
# Plot building functions
# TODO: move this to another separate module called 'plot_utils.py' or something like that?


def build_regional_plotset(site_list):

    ''' this function is a flow control that utilizes the other functinons above to call the 
    snotel api (or later, the local database) and build plot objects to return to the main page view'''

    # May not use this function in favor of calling individual plots from the View function with a try-except block...
    # or could put the try-except blocks in here;  which would greatly clean up / shorten the view functions for readability

    pass

    # snotel_data_hour = get_hourly_data(site_list)
    # data_day = get_daily_data(site_list)

    # # build the regional plotset

    # return region_plot_JSON


def build_site_plots(site):
    ''' this function is a flow control that utilizes the other functinons above to call the 
    snotel api (or later, the local database) and build plot objects to return to the main page view'''

    snotel_data_hour = get_hourly_data(site)
    data_day = get_daily_data(site)

    pass


