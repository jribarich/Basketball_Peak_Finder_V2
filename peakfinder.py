from telnetlib import SB
from matplotlib.pyplot import xticks
import pandas as pd
import streamlit as st
import requests
from bs4 import BeautifulSoup
import numpy as np
import altair as alt
import ast
import ssl
ssl._create_default_https_context = ssl._create_unverified_context


class Player():
    def __init__(self, name = None, ext = None, 
        nicknames = None, position = None, height = None, 
        hand = None, college = None, reg_season = None, 
        playoff = None, adv_data = None):
        self.name = name
        self.ext = ext  
        self.nicknames = nicknames  # list
        self.position = position
        self.height = height
        self.hand = hand 
        self.college = college  
        self.reg_season = reg_season  # panda DataFrame
        self.playoff = playoff  # panda DataFrame

    def __repr__(self):
        return(f"""Nicknames: {self.nicknames}\nPosition: {self.position}
                    Height: {self.height}\nShoots: {self.hand}\nCollege: {self.college}\n
                    Regular Season Stats:\n{self.reg_season}\n
                    Playoff Stats:\n{self.playoff}\n""")


def create_sidebar():
    sb = st.sidebar
    sb.title("Basketball Peak Finder V2")
    name = sb.text_input("Enter a player's name:", value="").strip().lower()
    option = sb.selectbox("Select an option:", ["Regular Season", "Playoffs"])

    return sb, name, option


def get_player(player, name):
    with open('player_database.txt') as f:
        player_dict = ast.literal_eval(f.read())
    
    player.name = name
    
    try:
        player.ext = player_dict[player.name]  # search players.py dict

    except: 
            return None

def display_pic(pic):
    col1, col2, col3 = st.columns(3)
   
    if pic == './bball_logo.png':
        col2.image(pic, width=200)

    else:
        col2.image(pic)
    
    st.markdown('---')


def get_pic(soup):
    pic = soup.select("img[src^=http]")[1]['src']
    
    if '.jpg' in pic:
        display_pic(pic)
        st.session_state['pic_url'] = pic

    else:
        default = './bball_logo.png'
        display_pic(default)
        st.session_state['pic_url'] = default
    


def player_info(player, soup):
    position_dict = {'Point Guard': 'PG', 'Shooting Guard': 'SG', 
                    'Small Forward': 'SF', 'Power Forward': 'PF',
                    'Center': 'C'}
    height_flag = 0
    nickname_flag = 0

    st.subheader('Player Info')
    col1, col2, col3 = st.columns(3)

    info = soup.find('div', attrs={'id': 'meta'})
    paragraphs = info.find_all('p')
    
    for item in paragraphs:
        # get nicknames
        if '(' in item.text and nickname_flag == 0:
            nickname_flag = 1
            
            if  height_flag == 0:
                player.nicknames = item.text.replace('(', '').replace(')', '').split(',')


            col1.write("***Nickname(s):***")
            
            if player.nicknames == None:
                    col1.write("None")
            else:    
                count = 0
                for name in player.nicknames:
                
                    col1.write(name)
                    count += 1

                    if count == 3:
                        break

        # get height
        if height_flag == 1:
            col3.write('***Height:***')
            player.height = item.text.split(",")[0]
            col3.write(player.height)
            height_flag = 0
        
        # get positions
        if 'Position:' in item.text:
            height_flag = 1
            col2.write("***Position(s):***")
            for p in position_dict.keys():
                if p in item.text:
                    player.position = position_dict[p]
                    
                    col2.write(player.position)

    st.markdown('---')


def player_data(player, player_url):
    response = requests.get(player_url)
    soup = BeautifulSoup(response.text, 'html.parser')

    get_pic(soup)
    player_info(player, soup)
    st.session_state['soup'] = soup


def player_tables(player, url):
    drop_list = ['Age','Tm', 'Lg', 'Pos', 'G', 'MP']

    per_game = pd.read_html(url, attrs = {"id" : "per_game"})[0]
    adv = pd.read_html(url, attrs = {"id" : "advanced"})[0]

    # Drop rows that don't match 'YEAR-YEAR' format such as 'Career' or Did Not Play
    per_game = per_game[per_game['Season'].str.contains('-', na=False)]
    per_game = per_game[pd.to_numeric(per_game['G'], errors='coerce').notnull()]
    adv = adv[adv['Season'].str.contains('-', na=False)]
    adv = adv[pd.to_numeric(adv['G'], errors='coerce').notnull()]

    # Drop duplicate columns then merge
    per_game.drop(drop_list, axis=1, inplace=True)
    player.reg_season = pd.merge(per_game, adv, how='outer', on='Season')

    #pl is playoffs
    try:
        pl_per_game = pd.read_html(url, attrs = {"id" : "playoffs_per_game"})[0]
        pl_adv = pd.read_html(url, attrs = {"id" : "playoffs_advanced"})[0]

        # Drop rows that don't match 'YEAR-YEAR' format such as 'Career' or Did Not Play
        pl_per_game = pl_per_game[pl_per_game['Season'].str.contains('-', na=False)]
        pl_per_game = pl_per_game[pd.to_numeric(pl_per_game['G'], errors='coerce').notnull()]
        pl_adv = pl_adv[pl_adv['Season'].str.contains('-', na=False)]
        pl_adv = pl_adv[pd.to_numeric(pl_adv['G'], errors='coerce').notnull()]

        pl_per_game.drop(drop_list, axis=1, inplace=True)

        player.playoff = pd.merge(pl_per_game, pl_adv, how='outer', on='Season')

    except:
        pl_per_game = None
        pl_adv = None


def peak_calculation(df):
    scalar = 2.5
    flt = lambda x: x.astype(float)  # changes data into floats

    PER = scalar*flt(df['PER'])/flt(df['PER']).max()
    WS = scalar*flt(df['WS'])/flt(df['WS']).max()

    calc = PER + WS

    return calc


def determine_peak_season(player): 
    peak_data = [None, None]
    peak_list = None
    seasons = None
    seas_sum = None
    ppg = None 
    apg = None
    rpg  = None
    reg = player.reg_season 
    plof = player.playoff

    reg['sum'] = peak_calculation(reg)
    idx = reg['sum'].idxmax()  # max season index

    peak_list = [reg.loc[idx, 'Season'], reg.loc[idx, 'Tm'], reg.loc[idx, 'PER'], 
                reg.loc[idx, 'WS'], reg.loc[idx, 'FG%'], reg.loc[idx, 'PTS'], 
                reg.loc[idx, 'AST'], reg.loc[idx, 'TRB']]
    
    seasons = reg['Season'].tolist()
    seas_sum = reg['sum'].tolist()

    ppg = [float(i) for i in reg['PTS'].tolist()]
    apg = [float(i) for i in reg['AST'].tolist()]
    rpg = [float(i) for i in reg['TRB'].tolist()]
    
    peak_data[0] = [peak_list, seasons, seas_sum, ppg, apg, rpg]

    if not isinstance(plof, type(None)):  # playoffs
        plof['sum'] = peak_calculation(plof)
        idx = plof['sum'].idxmax()
        
        peak_list = [plof.loc[idx, 'Season'], plof.loc[idx, 'Tm'], plof.loc[idx, 'PER'], 
                    plof.loc[idx, 'WS'], plof.loc[idx, 'FG%'], plof.loc[idx, 'PTS'], 
                    plof.loc[idx, 'AST'], plof.loc[idx, 'TRB']]

        seasons = plof['Season'].tolist()
        seas_sum = plof['sum'].tolist()
        ppg = [float(i) for i in plof['PTS'].tolist()]
        apg = [float(i) for i in plof['AST'].tolist()]
        rpg = [float(i) for i in plof['TRB'].tolist()]

        peak_data[1] = [peak_list, seasons, seas_sum, ppg, apg, rpg]

    return peak_data


def graph(peak, seasons, seas_sum, ppg, apg, rpg):
    # idx = np.arange(len(peak[1]))  # turns season into a list of indices
    # peak_sum = peak[2]
    # max_idx = peak[2].index(max(peak[2]))
    st.subheader('Peak Season Stats')
    mid_c1, mid_c2 = st.columns(2)
    col1, col2, col3 = st.columns(3)
    
    mid_c1.write("***Season:***")
    mid_c1.write(peak[0])
    mid_c2.write("***Team:***")
    mid_c2.write(peak[1])
    col1.write("***Player Efficiency Rating:***")
    col1.write(float(peak[2]))
    col2.write("***Win Shares:***")
    col2.write(float(peak[3]))
    col3.write("***Field Goal %:***")
    col3.write(round(100*float(peak[4]), 1))
    col1.write("***Points:***")
    col1.write(float(peak[5]))
    col2.write("***Assists:***")
    col2.write(float(peak[6]))
    col3.write("***Rebounds:***")
    col3.write(float(peak[7]))
    st.markdown("---")
    
    st.subheader('Peak Index')

    df = pd.DataFrame(index=seasons, columns=['Peak'])
    df['Peak'] = seas_sum
    df.reset_index(inplace=True)

    graph1 = alt.Chart(df).mark_line().encode(
        x=alt.X('index', title='Seasons', axis=alt.Axis(labelAngle=-45)),
        y=alt.Y('Peak', title='Peak Score'),
        tooltip=['index', 'Peak'],    
    )

    st.altair_chart(graph1, use_container_width=True)

    st.markdown('---')

    st.subheader("Per Game Stats")
    
    stats = pd.DataFrame(index=seasons, columns=['PTS', 'AST', 'REB'])
    stats['PTS'] = ppg
    stats['AST'] = apg
    stats['REB'] = rpg

    data = stats.reset_index().melt('index')


    graph = alt.Chart(data).mark_line().encode(
    x=alt.X('index', title='Seasons', axis=alt.Axis(labelAngle=-45)),
    y=alt.Y('value', title='Stats'),
    color=alt.Color('variable', title='Category'),
    tooltip=['index', 'value'],    
    ).interactive()

    st.altair_chart(graph, use_container_width=True)


def display_graphs(peak_data, option):
    if option == 'Regular Season':
        peak_list = peak_data[0][0]
        seasons = peak_data[0][1]
        seas_sum = peak_data[0][2]
        ppg = peak_data[0][3]
        apg = peak_data[0][4]
        rpg = peak_data[0][5]
        graph(peak_list, seasons, seas_sum, ppg, apg, rpg)
    
    else:
        if len(peak_data) == 2:
            peak_list = peak_data[1][0]
            seasons = peak_data[1][1]
            seas_sum = peak_data[1][2]
            ppg = peak_data[1][3]
            apg = peak_data[1][4]
            rpg = peak_data[1][5]
            graph(peak_list, seasons, seas_sum, ppg, apg, rpg)
    

def player_stats(player, option):
    url = 'https://www.basketball-reference.com/players/'
    end = '.html'

    player_url = url + player.ext[0] + '/' + player.ext + end


    if player.name != st.session_state['name']:
        player_data(player, player_url)
        player_tables(player, player_url)
        peak_data = determine_peak_season(player)

        st.session_state['name'] = player.name
        st.session_state['peak_data'] = peak_data
        
    
    else:
        display_pic(st.session_state['pic_url'])
        

    display_graphs(st.session_state['peak_data'], option)


def main():
    sb, name, option = create_sidebar()
    
    if name != '':
        player = Player() # instantiates player object
        player.name = name

        get_player(player, name) # retrieves player URL

        if player.ext == None:
            sb.error("Player not found. Please check spelling and try again.")

        else:
            st.subheader(player.name.upper())
            player_stats(player, option)


if __name__ == "__main__":
    main()

# initialize session state variables stored in the browser to speed up computation time
if 'name' not in st.session_state:
    st.session_state['name'] = None

if 'peak_data' not in st.session_state:
    st.session_state['peak_data'] = None

if 'pic_url' not in st.session_state:
    st.session_state['pic_url'] = None 