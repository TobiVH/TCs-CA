# -*- coding: utf-8 -*-
import pandas as pd
from distfit import distfit
import numpy as np
from typing import Tuple, List
import matplotlib.path as mpltPath
import plot_functions as plot

def create_IRdf(df: pd.DataFrame) -> List[str]:
    """
    Parameters:
        df (pd Dataframe): Dates of TCs activity 'year-month-day'
    
    Return:
        List cotaining dates of TCs activity 'year/month/day'
    """
    IR_dates = []
    for year, month, day, *event in df: 
        date = f'{int(year)}/{int(month)}/{int(day)}'
        IR_dates.append(date)
    return IR_dates

def get_thresholds():
    """
    Process:
        Auxiliar function to load precipitation data and call get_distribution function
    """
    stations = pd.read_csv('precipitation_data.txt', delimiter = "\t", header=None)
    stations = stations[stations > 0.]
    get_distributions(stations) 

def get_distributions(df: pd.DataFrame) -> None:
    """
    Parameters:
        df (pd DataFrame): Historical data of precipitation
        
    Process:
        Compute the thresholds for green, yellow and red alert, and saves it in a .csv file
    """
    station_locations = pd.read_csv('stations_location.txt', delimiter ="\t")
    Resultados = []
    array = df.to_numpy() 
    for i in range(len(df.columns)): 
        station_data = array[:,i]
        print(len(station_data))
        station_data = station_data[~np.isnan(station_data)]
        dist = distfit(distr = 'full')
        dist.fit_transform(station_data)
        *parametros, loc, scale =  dist.model['params']
        dist.plot()
        VNR = dist.model['distr'].ppf([0.6, 0.75, 0.9], *parametros, loc = loc, scale = scale)
        Resultados.append([station_locations.iloc[0]['ID'], dist.model['name'] ,*VNR])
        print(Resultados)
    dataframe = pd.DataFrame(Resultados, columns = ['ID', 'distribution' , 'Green', 'Yellow', 'Red'])
    dataframe.to_csv('thresholds.csv')


def time_correction(df: pd.DataFrame) -> None:
    """
    Parameters:
        df (pd DataFrame): TCs data
        
    Process:
        Modify the day, month, or year according to hour negative values
    """
    days_of_month = {1.: 31, 2.: 28, 3.: 31, 4.: 30, 5.: 31, 6.: 30, 7.: 31, 8.: 31, 9.: 30, 10.: 31, 11.: 30, 12.: 31}
    for i in df.index:
        if df.loc[i, 'hour'] < 0:
            if df.loc[i, 'day'] == 1.0:
                if df.loc[i, 'month'] == 1:
                    df.loc[i, 'month'] = 12.
                    df.loc[i, 'year'] = df.loc[i, 'year'] - 1
                    df.loc[i, 'day'] = days_of_month[12.]
                else:    
                    month = df.loc[i, 'month'] - 1
                    df.loc[i, 'month'] = month
                    df.loc[i, 'day'] = days_of_month[month]
            else:
                df.loc[i, 'day'] -= 1
            df.loc[i, 'hour'] += 24.  

def create_hex_grid(df: pd.DataFrame, region, xpos, ypos, style, projection, ncolumns: int = 4, nrows: int = 5, scale: float = 1.) -> Tuple[List[List[int]], List[float]]:
    """
    Parameters:
        df (pd DataFrame): latitude and longitude of TCs with its induced precipitation 
        region (List of floats): min/max longitude and latitude coordinates to define the region 
        xpos (float): longitude coordinate of the lower left corner hexagon of the grid
        ypos (float): latitude coordinate of the lower left corner hexagon of the grid
        style (str): Marker and size of the scatter plot of TCs
        projection (str):  projection and size of the image for the grid plot
        ncolumns (integer): number of columns of the grid
        nrows (integer): number of rows of the grid
        scale (float): double size of the hexagon apotheme
        
    Process:
        Organization of the hexagonal grid, calls the functions make_grid, create_grid_matrix and plot_HexGrid
        
    Return:
        Tuple with the Matrix (Grid) and its centers
    """
    lat = df['lat']
    lon = df['lon']
    r = scale/np.sqrt(3)
    grid_matrix = [([0]*(ncolumns) ) for i in range(nrows)]
    coord_x, coord_y = make_grid(ncolumns, nrows, scale, xpos, ypos)
    x_cent_aux, y_cent_aux = (coord_x.flat, coord_y.flat)
    x_cent = [i for i in x_cent_aux]
    y_cent = [i for i in y_cent_aux]
    y_cent.reverse()
    coords = list(zip(x_cent,y_cent))  
    Matrix = create_grid_matrix(df, coords, grid_matrix,r)
    plot.plot_HexGrid(region, x_cent, y_cent, r ,lat, lon, style, projection)
    return (Matrix, [x_cent, y_cent]) 

def create_grid_matrix(df: pd.DataFrame,  centers: List[Tuple[float]], Matrix: List[List[int]],r) -> List[List[pd.DataFrame]]:
    """
    Parameters:
        df (pd DataFrame): latitude and longitude of TCs with its induced precipitation 
        centers (List of tuple of floats): List with the hexgonal grids centers 
        Matrix (List of List of integer): Abstract representation of the hexagonal grid

    Process:
        Determines which TCs are inside each hexagon
        
    Return:
        Matrix (List of List of pd DataFrame) with the corresponding TCs inside the hexagons and precipitation
    """
    nrows = len(Matrix[0]) 
    lats, lons = (df['lat'],df['lon'])
    points = list(zip(lons,lats))
    for pos in range(len(centers)):
        V = plot.vertices(centers[pos][0], centers[pos][1], r)
        polygon = list(zip(V[0],V[1]))
        path = mpltPath.Path(polygon)    
        inside = path.contains_points(points)
        Matrix[pos//nrows][pos%nrows] = df[inside]
    return Matrix

def make_grid(ncolumns: int, nrows: int, scale: float, xpos , ypos) -> Tuple[float]:
    """
    Parameters:
        ncolumns (integer): number of columns of the grid
        nrows (integer): number of rows of the grid
        scale (float): double size of the hexagon apotheme
        xpos (float): longitude coordinate of the lower left corner hexagon of the grid
        ypos (float): latitude coordinate of the lower left corner hexagon of the grid
    
    Process:
        Create the centers of all hexagons with the requested size and position
        
    Return:
        Tuple of x_centers and y_centers
    """
    ratio = np.sqrt(3) / 2
    coord_x, coord_y = np.meshgrid(np.arange(0 , ncolumns), np.arange(0 , nrows), sparse=False, indexing='xy')
    coord_y = coord_y * ratio
    coord_x = coord_x.astype(np.float)
    coord_x[1::2, :] -= 0.5
    coord_x *= scale 
    coord_y = coord_y.astype(np.float) * scale
    if nrows%2 == 0:
        coord_x += xpos + scale/2 
    else:
        coord_x += xpos
    coord_y += ypos
    coord_x = coord_x.reshape(-1, 1)
    coord_y = coord_y.reshape(-1, 1)
    return coord_x, coord_y


def get_probabilities(df: pd.DataFrame, Thresholds: pd.DataFrame) -> pd.DataFrame: #df lluvias de ciclones, umbrales 
    """
    Parameters:
        df (pd DataFrame): Induced precipitation data of one hexagon
        Thresholds (pd DataFrame): Thresholds of each stations
        
    Process:
        Finds the best fit for the induced precipitation data and computes extreme precipitation according to the Thresholds
        
    Return:
        pd DataFrame containing probabilities of all stations due to TCs located in a specific hexagon
    """
    Resultados = []
    for i in Thresholds.index:
        array = df.to_numpy()  
        station_data = array[:,i]
        dist = distfit(distr = 'popular',smooth=10)
        dist.fit_transform(station_data)
        *parametros, loc, scale =  dist.model['params']
        dist.plot() #Plot of the empirical and theoretical distributions
        probabilities_VNR = np.round(100*(1-dist.model['distr'].cdf(list(Thresholds.loc[i,['Green','Yellow','Red']]), *parametros, loc = loc, scale = scale)),2)
        Resultados.append([Thresholds['ID'].loc[i], dist.model['name'] ,*probabilities_VNR]) 
    dataframe = pd.DataFrame(Resultados, columns = ['ID', 'distribution' , '%Green', '%Yellow', '%Red'])
    return dataframe  

def Probs_grid(grid: List[List[pd.DataFrame]], centers: List[List[float]], Thresholds: pd.DataFrame, stations, region, style, projection, savedir) -> None:
    """
    Parameters:
        grid (List of List of pd DataFrame): Induced precipitation data of one hexagon
        centers (List of List of floats):  List containing the latitude and longitude coordinate of the hexagon centers in a list
        Thresholds (pd DataFrame): Thresholds data
        stations (pd Dataframe): stations locations data
        region (List of floats): min/max longitude and latitude coordinates to define the region that shows the stations
        style (str): Marker and size of the scatter plot for the stations
        projection (str): projection and size of the image for the stations plot
        savedir (str): directory where you wish to save the final image results
    Process:
        Analayze all hexagons and make a graphical result of probabilities in all stations. Saves the computed probabilities in a .csv file
    """
    x_centers, y_centers = (centers[0],centers[1])
    ncolumns = len(grid[0])
    x_centers_par = x_centers[0:ncolumns]
    x_centers_impar = x_centers[ncolumns:2*ncolumns]
    y_centers = y_centers[0:-1:ncolumns]    
    probs_results = pd.DataFrame(columns = ['Hex_lat', 'Hex_long', 'ID', 'distribution' , '%Green', '%Yellow', '%Red']) 
    for i in range(0,len(grid)): 
        for j in range(0,len(grid[0])): 
            if grid[i][j].shape[0] < 7:
                continue
            else:    
                print(i,j)
                if i%2 == 0:  
                    probabilities_df = get_probabilities(grid[i][j].drop(columns=['lat','lon']), Thresholds)
                    hex_loc_df = pd.DataFrame([[x_centers_par[j], y_centers[i]]],columns = ['Hex_lat', 'Hex_long'])
                    probs_results_aux = pd.concat([hex_loc_df, probabilities_df])
                    probs_results = pd.concat([probs_results, probs_results_aux])
                    plot.make_figures(probabilities_df, x_centers_par[j], y_centers[i], stations, region, style, projection, savedir)
                else:
                    probabilities_df = get_probabilities(grid[i][j].drop(columns=['lat','lon']), Thresholds)
                    hex_loc_df = pd.DataFrame([[x_centers_impar[j], y_centers[i]]],columns = ['Hex_lat', 'Hex_long'])
                    probs_results_aux = pd.concat([hex_loc_df, probabilities_df])
                    probs_results = pd.concat([probs_results, probs_results_aux])
                    plot.make_figures(probabilities_df, x_centers_impar[j], y_centers[i], stations, region, style, projection, savedir)
    probs_results.to_csv('computed_probabilities.csv') 
    
