import auxiliar_functions as aux
import pandas as pd
import pygmt

def demo(region, projection = "M17.5c", style = "c0.125c"):
    """
    Parameters:
        region (List of floats): min/max longitude and latitude coordinates to define the region
        projection (str): projection and size of the map
        style (str): style and size of the scatter plot in the map
    """
    station_locations = pd.read_csv('stations_location.txt', delimiter ="\t")
    fig = pygmt.Figure()
    fig.coast(shorelines="0.8p,black", region= region, frame="a", projection=projection, borders=["1/0.8p,black", "2/0.3p,black"] ,land="#efefdb") #, water="skyblue"
    # fig.basemap(map_scale="jBL+w500k+o0.5c/0.5c+f+u") #Map Scale
    fig.plot(x = station_locations['X'], y = station_locations['Y'], style= style, color= "red", pen="black", label="stations")
    fig.legend()
    fig.show(method="external")
    
##############################################################################################################################################


def main(compute_probs, period, grid_region, stations_region, location, cols, rows, apt_size, hour_correction = 0, style_grid = "c0.075c", style_stations = "c0.15c", projection_grid = "M17.5c", projection_stations = "M15c", img_save = 'Images'):
    """
    Paramteres: 
        
        compute_probs (boolean): if True the script will compute the probabilities, if false the program will end showing the hexgonal grid, without computing probabilities. (This is used to find the appropriate hexagonal grid)
        period (List of str): start and end dates 'day/month/year'
        grid_region (List of floats): min/max longitude and latitude coordinates to define the region of that shows the grid and TCs
        stations_region (List of floats): min/max longitude and latitude coordinates to define the region that shows the stations
        location (List of floats): Contains the center of the lower left corner hexagon of the grid
        cols (int): number of columns of the grid
        rows (int): numbers of rows of the grid
        apt_size (float): double of the hexagon apotheme size in degrees
        hour_correction (int): hours necessary to match TCs data to the precipitation data time zone
        style_grid (str): Marker and size of the scatter plot for TCs daily average position
        style_stations (str): Marker and size of the scatter plot for the stations
        projection_grid (str): projection and size of the image for the grid plot
        projection_stations (str): projection and size of the image for the stations plot
        img_save (str): directory where you wish to save the final images results
        
    Process:
        Makes the hexagonal grid and computing of probabilities starting from raw data
    """
    #load precipitation data, stations location data, TCs data and Thresholds
    prepc_data = pd.read_csv('precipitation_data.txt', delimiter = "\t", header=None)
    station_locations = pd.read_csv('stations_location.txt', delimiter ="\t")
    Thresholds = pd.read_csv('thresholds.csv', delimiter = ",")
    TCs = pd.read_csv('TCs_data.txt', delimiter = "\t", header = None, skiprows=1)
    
    #set the dates of precipitation events
    fechas = pd.date_range(start=period[0], end=period[1])
    prepc_data = prepc_data.set_index(fechas) 
    
    #setting the header and dropping the data that wont be used
    TCs.columns = ['event', 'day', 'month', 'year', 'lat', 'lon', 'hour', 'windkph', 'press', 'typemax']
    TCs = TCs.drop(columns = ['windkph', 'press', 'typemax'])
    TCs = TCs.reset_index(drop=True)
    
    TCs = TCs.replace(',','.', regex=True)
    TCs = TCs.astype({'lat': float, 'lon': float})
    
    #matching the timezone of the TCs data and precipitation data 
    if hour_correction != 0:
        TCs['hour'] -= hour_correction
        aux.time_correction(TCs)
    TCs = TCs.drop(columns = ['hour'])
    
    # Computing the daily average position and extracting its latitude and longitude coordinates
    TCs_means = TCs.groupby(['year', 'month', 'day','event']).mean()      
    
    #Setting the index of TCs data with the pd.series format to match the precipitation data index
    IR_dates_event = TCs_means.index
    IR_dates = aux.create_IRdf(IR_dates_event) #dates with precipitation index
    IR_datesdf_aux = pd.Series(IR_dates) #converting IR_dates to pd.Series
    IR_datesdf = pd.to_datetime(IR_datesdf_aux) #pd.series to pd.datetime, same as the precipitation data
    TCs_means = TCs_means.set_index(IR_datesdf) #setting the pd.datetime as index for the TCs daily average position
    
    #Induced precipitation of TCs
    IR_data = prepc_data.loc[IR_dates,:] #precipitation data that matches the day of TCs events
    
    #Concate TCs data with IR_data
    TCs_IR_JOIN = pd.concat([TCs_means, IR_data], axis=1) 
    
    
    scale = apt_size #double of the hexagon apotheme size in degrees
    
    #Creating the Hexagonal Grid 
    HexGrid, centers = aux.create_hex_grid(TCs_IR_JOIN, grid_region, location[0], location[1], style_grid, projection_grid, cols, rows, scale = scale) 
    
    #Computing the probabilities
    if compute_probs:
        aux.Probs_grid(HexGrid, centers, Thresholds, station_locations, stations_region, style_stations, projection_stations, img_save)
        
    return HexGrid

#Grid = main(False, ['1/1/1981','31/12/2020'], [115, 145, 0, 35], [-85,-75, 5, 10], (127.5, 15), 3, 2, 2)
