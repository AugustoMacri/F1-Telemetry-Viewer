import streamlit as st
import fastf1 as ff1
import pandas as pd
import numpy as np
import matplotlib as mpl
import os

import plotly.graph_objects as go
import plotly.subplots as sp
import plotly.express as px

from fastf1 import utils
from fastf1.plotting import team_color
from fastf1 import plotting

from matplotlib import pyplot as plt
from matplotlib.collections import LineCollection
from matplotlib import cm

from PIL import Image

# telemetria com setor junto com pneu, ver onde cada pneu é melhor em cada setor

# Set the URL page configuration
st.set_page_config(
    page_title="F1 Telemetry",
    page_icon="🏎️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Set the cache
cache_folder = os.path.join(os.path.dirname(
    __file__), 'cache_data')  # cache folder path
ff1.Cache.enable_cache(cache_folder)  # enable cache

# ------------------------------------------------------------------------------------------------#
# Passos para a seleção do evento
# ------------------------------------------------------------------------------------------------#
# Setting columns
col1, col2, col3 = st.columns(3)  # 3 columns

# (First Column) Set the season selector
with col1:
    seasons = [2021, 2022, 2023, 2024, 2025]
    # selected_season will store the selected season
    selected_season = st.selectbox(
        "Select a Season", seasons, key='season_data')

# (Second Column) Set the event selector
with col2:
    events_data = ff1.get_event_schedule(selected_season)
    events = events_data['OfficialEventName']
    # select_event will store the selected event
    select_event = st.selectbox("Select a Event", events, key='event_data')

# (Select Session) Set the session
with col3:
    session_names = ['Session1', 'Session2',
                     'Session3', 'Session4', 'Session5']
    # Primeiro é selecionado as informacoes do evento a partir deget_event passando o ano e a pista como parâmetro
    session_data = ff1.get_event(selected_season, select_event)
    # Depois é pego o snomes das sessões nesse evento
    sessions = session_data[session_names]
    # por fim é criado um select box com essa lista de sessoes
    select_session = st.selectbox(
        "Select a session", sessions, key='session_data')

session_mapping = {
    'Practice 1': 1,
    'Practice 2': 2,
    'Practice 3': 3
}

# Creating a session. Vamos carregar os dados em data
try:
    data = ff1.get_session(selected_season, select_event,
                           select_session)  # Carregar os dados em data
    data.load()  # Carregar os dados
except:
    st.error('Sessão Inexistente', icon="🚨")


# Função para pegar as cores dos pilotos automaticamente
def get_driver_colors(data):
    drivers = data.laps.Driver.unique()  # Pega os pilotos únicos
    driver_colors = {}

    for driver in drivers:
        try:
            # Tenta pegar a cor do piloto
            driver_colors[driver] = ff1.plotting.driver_color(driver)
        except KeyError:
            # Se der erro (KeyError), define uma cor padrão
            print(
                f"Cor não encontrada para o piloto {driver}, usando cor padrão.")
            driver_colors[driver] = "#808080"  # Cinza como cor padrão

    return driver_colors


# ------------------------------------------------------------------------------------------------#


# ------------------------------------------------------------------------------------------------#
# Passos para gaveta de abas
# ------------------------------------------------------------------------------------------------#
# Creating tabs (telemetry, Positions, standing)
tabs = st.tabs(['Telemetry', 'Positions', 'Standing'])

# Now we need to create the chart for the first tab
with tabs[0]:
    col1, col2 = st.columns(2)

    # Primeiro faremos a seleção do piloto, que pode ser mais de um, e depois armazená-lo em um dicionário
    with col1:
        # Selecting Driver for Telemetry
        # faz a selecao de todos os pilotos que participaram da corida do data (unique() para pegar os valores únicos)
        drivers = data.laps.Driver.unique()
        # cria um multiselect para selecionar os pilotos
        select_driver = st.multiselect(
            "Select a driver", drivers, key='driver_data')

        driver_dict = {}  # cria um dicionário vazio

        # Agora vamos preencher o dicionário com os pilotos selecionados
        for i, driver in enumerate(select_driver, start=1):
            key = f'driver_{i}'  # generate a key
            driver_dict[key] = driver

    # Agora vamos selecionar a volta
    with col2:
        # Selecting Lap
        available_laps = data.laps.LapNumber.unique()
        # selected_lap é a variavel que vai armazenar a volta analisada
        selected_lap = st.selectbox("Select a Lap", available_laps)

    # Criação da tela de visualização de dados

    # Vão ser criados dois gráficos, um para o caso de ser apenas um piloto escolhido e outro para o caso de ser mais de um
    if (len(select_driver) == 1):
        row_heights = [1, 0.5, 5, 1, 1, 1, 0.5]
    else:
        row_heights = [1, 1, 0.5, 5, 1, 1, 0.5]

    variable_names_driver = ['RPM', 'Gear',
                             'Speed', 'Throttle', 'Brake', 'DRS']
    variable_names_drivers = ['Gap to Ref.', 'RPM',
                              'Gear', 'Speed', 'Throttle', 'Brake', 'DRS']

    # Cria um objeto de subplot de 7 linhas e 1 coluna
    fig = sp.make_subplots(rows=7, cols=1, shared_xaxes=True,
                           vertical_spacing=0.02, row_heights=row_heights)

    # Verify if some driver is selected
    if select_driver and selected_lap is not None:

        if len(select_driver) == 1:
            # Selecionando o primeiro piloto da lista
            driver = select_driver[0]
            # Extraindo as informações da volta do piloto
            laps_driver = data.laps.pick_driver(driver)

            # fastest_driver = laps_driver.pick_fastest() #Extraindo as informações da volta mais rápida do piloto

            colors = []
            driver_lap = laps_driver.pick_lap(selected_lap)

            for driver in select_driver:
                try:
                    team = data.laps.pick_driver(driver).pick_fastest()['Team']
                    team_drive_color = team_color(team)
                    driver_color = ff1.plotting.driver_color(driver)
                    colors.append(driver_color)
                except KeyError:
                    st.warning(f"Color for team {team} not found.")
                    driver_color = 'gray'
                    colors.append(driver_color)

            for i, driver in enumerate(select_driver, start=1):
                laps_driver = data.laps.pick_driver(driver)
                driver_data = laps_driver.pick_lap(selected_lap)

                try:
                    telemetry_driver = driver_data.get_telemetry().add_distance()
                except Exception as e:
                    st.warning(
                        f"We do not have telemetry data for {driver} in this session.")
                    telemetry_driver = None

                if telemetry_driver is not None:

                    fig.add_trace(go.Scatter(x=telemetry_driver['Distance'], y=telemetry_driver['RPM'], mode='lines',
                                  name=f'{driver} - RPM', line=dict(color=colors[i-1]), legendgroup=driver), row=1, col=1)
                    fig.add_trace(go.Scatter(x=telemetry_driver['Distance'], y=telemetry_driver['nGear'], mode='lines',
                                  name=f'{driver} - Gear', line=dict(color=colors[i-1]), legendgroup=driver), row=2, col=1)
                    fig.add_trace(go.Scatter(x=telemetry_driver['Distance'], y=telemetry_driver['Speed'], mode='lines',
                                  name=f'{driver} - Speed', line=dict(color=colors[i-1]), legendgroup=driver), row=3, col=1)
                    fig.add_trace(go.Scatter(x=telemetry_driver['Distance'], y=telemetry_driver['Throttle'], mode='lines',
                                  name=f'{driver} - Throttle', line=dict(color=colors[i-1]), legendgroup=driver), row=4, col=1)
                    fig.add_trace(go.Scatter(x=telemetry_driver['Distance'], y=telemetry_driver['Brake'], mode='lines',
                                  name=f'{driver} - Brake', line=dict(color=colors[i-1]), legendgroup=driver), row=5, col=1)
                    fig.add_trace(go.Scatter(x=telemetry_driver['Distance'], y=telemetry_driver['DRS'], mode='lines',
                                  name=f'{driver} - DRS', line=dict(color=colors[i-1]), legendgroup=driver), row=6, col=1)

                fig.update_layout(
                    title={
                        'text': f'Telemetry Data for {select_session} Lap {selected_lap}',
                        'x': 0.5,
                        'xanchor': 'center',
                        'y': 0.95,
                        'yanchor': 'top',
                        'font': {'size': 36}
                    },
                    showlegend=True,
                    hovermode="x unified",
                    height=700,
                )

                fig.update_yaxes(showticklabels=False)

            for j, variable_name in enumerate(variable_names_driver, start=1):
                fig.update_yaxes(title_text=variable_name, row=j, col=1)

            st.plotly_chart(fig, use_container_width=True)
        else:

            # Criando de novo um veor de cores para armazenar as cores dos pilotos
            colors = []
            # Definindo um piloto como referência para user ele para calcular o gap
            driver_ref = driver_dict['driver_1']
            # carregando os dados das voltas do piloto de referência
            laps_driver_ref = data.laps.pick_driver(driver_ref)
            # fastest_driver_ref = laps_driver_ref.pick_fastest()

            # Extraindo a cor de cada piloto
            for driver in select_driver:
                # extraindo a cor do piloto selecionado
                team = ff1.plotting.driver_color(driver)
                colors.append(team)

            # Extraindo os dados da telemetria de cada piloto selecionado na lista select_drivers
            for i, driver in enumerate(select_driver, start=1):
                # obtendo os dados de cada piloto
                laps_driver = data.laps.pick_driver(driver)
                # obtendo os dados da volta selecionada
                driver_data = laps_driver.pick_lap(selected_lap)

                try:
                    telemetry_driver = driver_data.get_telemetry().add_distance()
                except Exception as e:
                    st.warning(
                        f"We do not have telemetry data for {driver} in this session.")
                    telemetry_driver = None

                if telemetry_driver is not None:
                    delta_time, ref_tel, compare_tel = utils.delta_time(
                        laps_driver_ref, driver_data)

                    fig.add_trace(go.Scatter(x=telemetry_driver['Distance'], y=delta_time, mode='lines',
                                  name=f'{driver} - cap', line=dict(color=colors[i-1]), legendgroup=driver), row=1, col=1)
                    fig.add_trace(go.Scatter(x=telemetry_driver['Distance'], y=telemetry_driver['RPM'], mode='lines',
                                  name=f'{driver} - RPM', line=dict(color=colors[i-1]), legendgroup=driver), row=2, col=1)
                    fig.add_trace(go.Scatter(x=telemetry_driver['Distance'], y=telemetry_driver['nGear'], mode='lines',
                                  name=f'{driver} - Gear', line=dict(color=colors[i-1]), legendgroup=driver), row=3, col=1)
                    fig.add_trace(go.Scatter(x=telemetry_driver['Distance'], y=telemetry_driver['Speed'], mode='lines',
                                  name=f'{driver} - Speed', line=dict(color=colors[i-1]), legendgroup=driver), row=4, col=1)
                    fig.add_trace(go.Scatter(x=telemetry_driver['Distance'], y=telemetry_driver['Throttle'], mode='lines',
                                  name=f'{driver} - Throttle', line=dict(color=colors[i-1]), legendgroup=driver), row=5, col=1)
                    fig.add_trace(go.Scatter(x=telemetry_driver['Distance'], y=telemetry_driver['Brake'], mode='lines',
                                  name=f'{driver} - Brake', line=dict(color=colors[i-1]), legendgroup=driver), row=6, col=1)
                    fig.add_trace(go.Scatter(x=telemetry_driver['Distance'], y=telemetry_driver['DRS'], mode='lines',
                                  name=f'{driver} - DRS', line=dict(color=colors[i-1]), legendgroup=driver), row=7, col=1)

                fig.update_layout(
                    title={
                        'text': f'Telemetry Data for {select_session} Lap {selected_lap}',
                        'x': 0.5,
                        'xanchor': 'center',
                        'y': 0.95,
                        'yanchor': 'top',
                        'font': {'size': 36}
                    },
                    showlegend=True,
                    hovermode="x unified",
                    height=700,
                )

                fig.update_yaxes(showticklabels=False)

            for j, variable_name in enumerate(variable_names_drivers, start=1):
                fig.update_yaxes(title_text=variable_name, row=j, col=1)

            st.plotly_chart(fig, use_container_width=True)


with tabs[1]:
    # Positions changed during race

    # Carregando o tema dark
    ff1.plotting.setup_mpl(mpl_timedelta_support=False,
                           misc_mpl_mods=False, color_scheme='fastf1')

    data.load(telemetry=False, weather=False)

    print(data.laps.head())

    # Obtendo as cores dos pilotos automaticamente
    driver_colors = get_driver_colors(data)

    fig, ax = plt.subplots(figsize=(8.0, 4.9))

    for drv in data.drivers:
        drv_laps = data.laps.pick_driver(drv)

        abb = drv_laps['Driver'].iloc[0]
        color = driver_colors[abb]  # Pega a cor do piloto automaticamente
        ax.plot(drv_laps['LapNumber'],
                drv_laps['Position'], label=abb, color=color)

    ax.set_ylim([20.5, 0.5])
    ax.set_yticks([1, 5, 10, 15, 20])
    ax.set_xlabel('Lap')
    ax.set_ylabel('Position')

    ax.legend(bbox_to_anchor=(1.0, 1.02))
    plt.tight_layout()

    st.pyplot(fig)


with tabs[2]:
    st.header("Standing")
    standings = data.results
    columns_to_display_standings = [
        'Position', 'Abbreviation', 'TeamName', 'Points']
    filtered_standings = standings[columns_to_display_standings]
    st.dataframe(filtered_standings)
