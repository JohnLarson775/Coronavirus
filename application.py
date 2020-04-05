# Import visualization tools:
import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go
from plotly.subplots import make_subplots
import plotly_express as px

# Import analysis tools
import pandas as pd
import numpy as np

# Import ISO3 mapping tool
from geonamescache.mappers import country

# Import GEOjson data
from urllib.request import urlopen
import json
with urlopen('https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json') as response:
    counties = json.load(response)

# Import timep
from datetime import datetime, timedelta

def serve_layout():
    # Links to time series datasets on github:
    url_confirmed = 'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_confirmed_global.csv'
    url_deaths = 'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_deaths_global.csv'
    # Create dataframes from datasets:
    df_confirmed = pd.read_csv(url_confirmed)
    df_deaths = pd.read_csv(url_deaths)
    # Replace null values with zeroes:
    df_confirmed[df_confirmed.columns[4:]] = df_confirmed[df_confirmed.columns[4:]].fillna(0, downcast = 'infer')
    df_deaths[df_deaths.columns[4:]] = df_deaths[df_deaths.columns[4:]].fillna(0, downcast = 'infer')

    # Try today's date. If not yet updated use yesterday's date for daily reports:
    try:
        date = datetime.now().strftime('%m-%d-%Y')
        url_daily_reports = f'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_daily_reports/{date}.csv'
        df_daily_reports = pd.read_csv(url_daily_reports, dtype = {'FIPS': object})
    except:
        date = (datetime.now() - timedelta(days = 1)).strftime('%m-%d-%Y')
        url_daily_reports = f'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_daily_reports/{date}.csv'
        df_daily_reports = pd.read_csv(url_daily_reports, dtype = {'FIPS': object})

    # Subsets of confirmed cases:
    df_china = df_confirmed[df_confirmed['Country/Region'] == 'China']
    df_other = df_confirmed[df_confirmed['Country/Region'] != 'China']

    # Add ISO3 codes to daily updating df
    mapper = country(from_key = 'name', to_key = 'iso3')

    country_index = {}
    country_index['West Bank and Gaza'] = 'PSE'
    country_index['Taiwan*'] = 'TWN'
    country_index['Timor-Leste'] = 'TLS'
    country_index['Holy See'] = 'VAT'
    country_index['Republic of the Congo'] = 'COG'
    country_index['Congo (Brazzaville)'] = 'COG'
    country_index['Congo (Kinshasa)'] = 'COD'

    df_confirmed['ISO3'] = df_confirmed['Country/Region'].apply(lambda x: country_index.get(x, mapper(x)))

    # Reformat for global choropleth:
    df_global = df_confirmed.groupby(['ISO3','Country/Region']).sum().reset_index()
    # Convert date columns to rows:
    df_global = pd.melt(
        df_global,
        id_vars = ['ISO3', 'Country/Region', 'Lat', 'Long'],
        value_vars = list(df_global.select_dtypes(include = 'int64')),
        var_name = 'Date',
        value_name = 'Confirmed Cases')

    # Setup df containing states with most cases:
    df_us = df_daily_reports[df_daily_reports['Country_Region'] == 'US']
    leading_states = df_us.groupby('Province_State')['Confirmed'].sum().sort_values(ascending = False)[0:10].index
    df_us_leading_states = df_us[df_us['Province_State'].isin(
        leading_states)].groupby(
        'Province_State').sum().sort_values(
        by = ['Confirmed'], ascending = False).reset_index()
    df_us_leading_states['Active'] = df_us_leading_states['Confirmed'] - df_us_leading_states['Recovered'] - df_us_leading_states['Deaths']

    # Setup df containing states with most deaths:
    leading_states_deaths = df_us.groupby('Province_State')['Deaths'].sum().sort_values(ascending = False)[0:10].index
    df_us_leading_states_deaths = df_us[df_us['Province_State'].isin(
        leading_states_deaths)].groupby(
        'Province_State').sum().sort_values(
        by = ['Deaths'], ascending = False).reset_index()

    # Setup df containing countries with most cases:
    leading_countries = df_daily_reports.groupby('Country_Region')['Confirmed'].sum().sort_values(ascending = False)[0:10].index
    df_leading_countries = df_daily_reports[df_daily_reports['Country_Region'].isin(
        leading_countries)].groupby(
        'Country_Region').sum().sort_values(
        by = ['Confirmed'], ascending = False).reset_index()
    df_leading_countries['Active'] = df_leading_countries['Confirmed'] - df_leading_countries['Recovered'] - df_leading_countries['Deaths']

    # Setup df containing countries with most deaths:
    leading_countries_deaths = df_daily_reports.groupby('Country_Region')['Deaths'].sum().sort_values(ascending = False)[0:10].index
    df_leading_countries_deaths = df_daily_reports[df_daily_reports['Country_Region'].isin(
        leading_countries_deaths)].groupby(
        'Country_Region').sum().sort_values(
        by = ['Deaths'], ascending = False).reset_index()

    # df for US choropleth:
    df_us_choro = df_us.groupby('Province_State').sum().reset_index()

    # Add dict for state abbreviations for US choropleth:
    us_state_abbrev = {'Alabama': 'AL', 'Alaska': 'AK', 'Arizona': 'AZ', 'Arkansas': 'AR', 'California': 'CA', 'Colorado': 'CO', 'Connecticut': 'CT',
        'Delaware': 'DE', 'District of Columbia': 'DC', 'Florida': 'FL', 'Georgia': 'GA', 'Hawaii': 'HI', 'Idaho': 'ID', 'Illinois': 'IL', 'Indiana': 'IN',
        'Iowa': 'IA', 'Kansas': 'KS', 'Kentucky': 'KY', 'Louisiana': 'LA', 'Maine': 'ME', 'Maryland': 'MD', 'Massachusetts': 'MA', 'Michigan': 'MI',
        'Minnesota': 'MN', 'Mississippi': 'MS', 'Missouri': 'MO', 'Montana': 'MT', 'Nebraska': 'NE', 'Nevada': 'NV', 'New Hampshire': 'NH',
        'New Jersey': 'NJ', 'New Mexico': 'NM', 'New York': 'NY', 'North Carolina': 'NC', 'North Dakota': 'ND', 'Northern Mariana Islands':'MP',
        'Ohio': 'OH', 'Oklahoma': 'OK', 'Oregon': 'OR', 'Palau': 'PW', 'Pennsylvania': 'PA', 'Puerto Rico': 'PR', 'Rhode Island': 'RI', 'South Carolina': 'SC',
        'South Dakota': 'SD', 'Tennessee': 'TN', 'Texas': 'TX', 'Utah': 'UT', 'Vermont': 'VT', 'Virgin Islands': 'VI', 'Virginia': 'VA', 'Washington': 'WA',
        'West Virginia': 'WV', 'Wisconsin': 'WI', 'Wyoming': 'WY',
    }

    df_us_choro['Abbrev'] = df_us_choro['Province_State'].map(us_state_abbrev).fillna(df_us_choro['Province_State'])
    df_us_choro = df_us_choro[df_us_choro['Abbrev'].apply(lambda x: len(x) < 3)]

    # ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~
    # ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~

    ## TIME SERIES

    fig_time = go.Figure()
    # Confirmed cases in mainland China
    fig_time.add_trace(go.Scatter(
        x = [i[:-3] for i in list(df_other.select_dtypes(include = 'int64'))], 
        y = list(df_china.select_dtypes(include = 'int64').sum()),
        name = 'China',
        line_color = '#7f7f7f'))
    # Confirmed cases for the rest of the world
    fig_time.add_trace(go.Scatter(
        x = [i[:-3] for i in list(df_other.select_dtypes(include = 'int64'))], 
        y = list(df_other.select_dtypes(include = 'int64').sum()),
        name = 'Rest of World',
        line_color = '#ff7f0e'))
    # Worldwide deaths
    fig_time.add_trace(go.Scatter(
        x = [i[:-3] for i in list(df_other.select_dtypes(include = 'int64'))], 
        y = list(df_deaths.select_dtypes(include = 'int64').sum()),
        name = 'Worldwide Deaths',
        line_color = '#d62728'))

    for trace in fig_time.data:
        trace.hovertemplate = '%{x}<br>%{y}'

    fig_time.update_yaxes(hoverformat = ',f')
    fig_time.update_layout(
        title_text = 'Coronavirus over Time',
        legend = {'x': 0.02, 'y': 0.55},
        legend_bgcolor = 'rgba(0,0,0,0.1)',
        height = 350,
        margin = {'r': 10,'t': 50,'l': 10,'b': 70},
        annotations = [
            dict(
                xshift = 10,
                yshift = -10,
                x = 0,
                y = 1.0,
                showarrow = False,
                text = 'Total Cases: ' + f'{sum(df_daily_reports["Confirmed"]):,}' + '<br>Total Deaths: ' + f'{sum(df_daily_reports["Deaths"]):,}',
                xref = 'paper',
                yref = 'paper',
                font = dict(
                    size = 16,
                    color = '#ffffff'
                ),
                align = 'left',
                bordercolor = 'rgba(0,0,0,0.1)',
                borderwidth = 2,
                borderpad = 4,
                bgcolor = '#ff7f0e'
            )
        ])

    ## GLOBAL CHOROPLETH

    fig_global = px.choropleth(
        df_global, 
        locations = 'ISO3',
        color = 'Confirmed Cases',
        hover_name = 'Country/Region',
        hover_data = ['Date'],
        projection = 'natural earth',
        animation_frame = 'Date',
        range_color = (0, df_global['Confirmed Cases'].max()),
        color_continuous_scale = [
            [0, 'rgb(250, 250, 250)'],       #0
            [1/10000, 'rgb(250, 175, 100)'], #10
            [1/1000, 'rgb(250, 125, 0)'],    #100
            [1/100, 'rgb(200, 100, 0)'],     #1000
            [1/10, 'rgb(250, 50, 50)'],      #10000
            [1, 'rgb(100, 0, 0)'],           #100000
        ])

    # Must loop though traces AND frames to format hovertemplate
    for trace in fig_global.data:
        trace.hovertemplate = '<b>%{hovertext}</b> (%{customdata[0]})<br>%{z:,f}'
    for frame in fig_global.frames:
        frame.data[0].hovertemplate = '<b>%{hovertext}</b> (%{customdata[0]})<br>%{z:,f}'
    # Animation speed and slider/button locations
    fig_global.layout.updatemenus[0].buttons[0].args[1]['frame']['duration'] = 50
    fig_global.layout.updatemenus[0].pad = {'l': 10, 't': 0}
    fig_global.layout.sliders[0].pad = {'b':10,'t':-20, 'l':10}
    fig_global.layout.sliders[0].currentvalue = {'prefix': 'Date = '}
    fig_global.layout.coloraxis.colorbar.title.text = 'Confirmed<br>Cases'

    fig_global.update_layout(
        title = 'Global Time Series',
        margin = {'r': 0,'t': 50,'l': 0,'b': 10},
    )

    ## US CHOROPLETH

    fig_us = px.choropleth(
        df_daily_reports,
        geojson = counties, 
        locations = 'FIPS',
        scope = 'usa',
        color = 'Confirmed',
        hover_name = 'Admin2',
        hover_data = ['Province_State'],
        range_color = (0, df_daily_reports[df_daily_reports['Country_Region'] == 'US']['Confirmed'].max()),
        color_continuous_scale = [
            [0, 'rgb(250, 250, 250)'],       #0
            [1/10000, 'rgb(250, 175, 100)'], #10
            [1/1000, 'rgb(250, 125, 0)'],    #100
            [1/100, 'rgb(200, 100, 0)'],     #1000
            [1/10, 'rgb(250, 50, 50)'],      #10000
            [1, 'rgb(100, 0, 0)'],           #100000
        ])

    for trace in fig_us.data:
        trace.hovertemplate = '<b>%{hovertext}</b> (%{customdata[0]})<br>%{z:,f}'

    fig_us.layout.coloraxis.colorbar.title.text = 'Confirmed<br>Cases'

    fig_us.update_traces(marker_line_width = 0.1)

    fig_us.update_layout(
        title = f'US Counties ({date})',
        margin = {'r':0,'t':50,'l':0,'b':30},
    )

    ## MOST AFFECTED

    trace_glob_c = go.Bar(
        x = df_leading_countries['Country_Region'], 
        y = df_leading_countries['Confirmed'],
        marker = {'color' : 'rgb(250, 175, 100)'},
        visible = True)
    trace_glob_d = go.Bar(
        x = df_leading_countries_deaths['Country_Region'], 
        y = df_leading_countries_deaths['Deaths'],
        marker = {'color' : 'rgb(250, 50, 50)'},
        visible = False)
    trace_us_c = go.Bar(
        x = df_us_leading_states['Province_State'], 
        y = df_us_leading_states['Confirmed'],
        marker = {'color' : 'rgb(250, 175, 100)'},
        visible = True)
    trace_us_d = go.Bar(
        x = df_us_leading_states_deaths['Province_State'], 
        y = df_us_leading_states_deaths['Deaths'],
        marker = {'color' : 'rgb(250, 50, 50)'},
        visible = False)

    fig_most_affected = make_subplots(rows = 1, cols = 2)

    fig_most_affected.append_trace(trace_glob_c, 1, 1)
    fig_most_affected.append_trace(trace_glob_d, 1, 1)
    fig_most_affected.append_trace(trace_us_c, 1, 2)
    fig_most_affected.append_trace(trace_us_d, 1, 2)

    for trace in fig_most_affected.data:
        trace.name = ''
        trace.hovertemplate = '%{x}<br>%{y}'
    fig_most_affected.update_yaxes(hoverformat = ',f')

    fig_most_affected.update_layout(
        title = f'Leading Countries and US States ({date})',
        showlegend = False,
        height = 350,
        margin = {'r': 10,'t': 50,'l': 40,'b': 10},
        updatemenus = [dict(
                pad = {'r': 10, 't': 10},
                x = 1.0,
                y = 1.0,
                active = 0,
                buttons = list([
                    dict(label = 'Confirmed',
                        method = 'update',
                        args = [{'visible': [True, False, True, False]}]),
                    dict(label = 'Deaths',
                        method = 'update',
                        args = [{'visible': [False, True, False, True]}]),
                ])
        )]
    )

    # ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~
    # ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~

    return html.Div(children = [
        html.Div([
            html.H3('Coronavirus Dashboard'),
            html.Div([
                html.P(f'Updated: {date}', style = {'font-style': 'italic'}),
            ], style = {'display': 'inline-block'}),
            html.Div([
                dcc.Markdown('''Source: [Johns Hopkins University CSSE](https://github.com/CSSEGISandData/COVID-19)''', style = {'font-style': 'italic'})
            ], style = {'display': 'inline-block', 'float':'right', 'color':'#ff7f0e'}),
        ], style = {'color':'white', 'paddingLeft':'10px', 'background':'linear-gradient(to right, #ff7f0e 25%, 50%, white)'}),
        html.Div(children = [
            html.Div([
                dcc.Graph(
                    figure = fig_time,
                )], style = {'margin': '0'}, className = 'five columns'),
            html.Div([
                dcc.Graph(
                    figure = fig_most_affected,
                )], style = {'margin': '0'}, className = 'seven columns'),
        ], className = 'twelve columns'),
        html.Div(children = [
            html.Div([
                dcc.Graph(
                    figure = fig_us,
                )], style = {'margin': '0'}, className = 'six columns'),
            html.Div([
                dcc.Graph(
                    figure = fig_global,
                )], style = {'margin': '0'}, className = 'six columns')
        ], className = 'twelve columns'),
        html.Div([
            html.Div([
                dcc.Markdown('''If you find this dashboard helpful, please share it and consider donating to a charity on the frontlines 
                of COVID-19, such as [Doctors Without Borders](https://donate.doctorswithoutborders.org/onetime.cfm).  \nCreated 
                and maintained by [John Larson](https://www.linkedin.com/in/johnlarson2016/).'''),
            ], style = {'paddingLeft':'10px', 'paddingTop':'20px'}),
        ], className = 'twelve columns')
    ])

# Launch the application with external stylesheet:
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets = external_stylesheets)
app.title = 'Coronavirus'

app.layout = serve_layout

# AWS deployment
application = app.server
app.scripts.config.serve_locally = True

# Add the server clause:
if __name__ == '__main__':
    app.run_server(port = 8080)