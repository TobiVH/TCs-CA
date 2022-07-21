# -*- coding: utf-8 -*-
import pygmt
from typing import Tuple, List
import numpy as np
import pandas as pd
import os

def vertices(x: float, y: float, radius: float) -> Tuple[float,float]:
    """
    Parameters:
        x (float): point in space in the x axis
        y (float): point in space in the y axis
        radius (float): radius of the hexagon
    Process:
        Finds the vertices of the hexagon given its location and radius
    Return:
        Tuple of the hexagon vertices in the x axis and y axis
    """
    first_vert = (x + radius*np.cos(np.pi/6),y + radius*np.sin(np.pi/6))
    vertices_x = [first_vert[0]]
    vertices_y = [first_vert[1]]
    for i in range(1,6):
        vertice_x = x + radius*np.cos(i*(np.pi/3) + np.pi/6)
        vertice_y =  y + radius*np.sin(i*(np.pi/3) + np.pi/6)
        vertices_x.append(vertice_x)
        vertices_y.append(vertice_y)
    vertices_x.append(first_vert[0])
    vertices_y.append(first_vert[1])
    return vertices_x, vertices_y

def plot_HexGrid(region, x_cent: List[float], y_cent: List[float], r: float, lat, lon, style, projection) -> None:
    """
    Parameters:
        region (List of floats): min/max longitude and latitude coordinates to define the region 
        x_cent (List of floats): All hexagon centers in the x axis
        y_cent (List of floats): All hexagon centers in the y axis
        radius (float): radius of the hexagon
        lat (pd Series): Latitude coordinates of all TCs daily average position
        lon (pd Series): Longitude coordinates of all TCs daily average position
        style (str): Marker and size of the scatter plot of TCs
        projection (str):  projection and size of the ima
        
    Process:
        Graphic representation of the Hexagonal Grid and TCs daily average position. It saves the produced imagen in .png format 
    """
    fig = pygmt.Figure()
    fig.coast(shorelines="0.8p,black", region= region, frame="a", projection = projection, borders=["1/0.8p,black", "2/0.3p,black"] ,land="#efefdb") #, water="skyblue"
    pygmt.makecpt(cmap="red")
    #fig.basemap(map_scale="jBL+w500k+o0.5c/0.5c+f+u") #Map Scale
    fig.plot(x=lon, y=lat, style = style, color="red", pen="black", label="TCs' daily average position")
    for i in range(len(x_cent)):
        V = vertices(x_cent[i], y_cent[i], r)
        fig.plot(
              x = V[0],
              y = V[1],
              pen = "1.15p,black",
          ) #dots "1p,black,."
    fig.legend()
    fig.show(method="external")
    fig.savefig('Hexagonal_Grid_wTCs.png', dpi = 650)
    
def make_figures(df: pd.DataFrame, x_center: float, y_center: float, stations, region, style, projection, savedir) -> None:
    """
    Parameters: 
        df (pd DataFrame): Probabilities of extreme precipitation of all stations due to TCs inside one hexagon
        x_center (float): x axis value of the hexagon center being analyzed
        y_center (float): y axis value of the hexagon center being analyzed
        stations (pd Dataframe): stations locations data
        region (List of floats): min/max longitude and latitude coordinates to define the region that shows the stations
        style (str): Marker and size of the scatter plot for the stations
        projection (str): projection and size of the image for the stations plot
        savedir (str): directory where you wish to save the final image results
        
    Process:
        Create an image of the region selected showing the all probabilities of each station and saves it in .png format
    """
    AlertaVerde = (df.loc[:,'%Green']).to_numpy().flatten()
    AlertaAmarilla = (df.loc[:,'%Yellow']).to_numpy().flatten()
    AlertaRoja = (df.loc[:,'%Red']).to_numpy().flatten()
    Alertas = [AlertaVerde, AlertaAmarilla, AlertaRoja]
    labels = ['Green', 'Yellow', 'Red']
    for alerta in range(3):
        fig = pygmt.Figure()
        fig.coast(shorelines="0.8p,black", region = region, projection = projection, borders=["1/0.8p,black", "2/0.3p,black"], land="#adadad") #[-95, -75, 5, 20] #, water="skyblue"
        fig.basemap(frame="a")
        max_probability = max(Alertas[alerta])
        pygmt.makecpt(cmap="abyss", reverse = True, series=[0, max_probability]) 
        fig.plot(x=(stations['X']), y=stations['Y'], style= style, color=Alertas[alerta], cmap=True, pen="black") #style="c0.125c"
        fig.colorbar(frame=f'af+l"{labels[alerta]} Alert Probability (%)"')
        # fig.show(method="external")
        x_center = round(x_center, 2)
        y_center = round(y_center, 2)
        img_name = f'LON{x_center}_LAT{y_center}_{labels[alerta]}_alert.png'
        savepath = os.path.join(savedir, img_name)
        fig.savefig(savepath, dpi = 650)

    
    