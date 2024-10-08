import streamlit as st
import pandas as pd
from datetime import datetime
from github import Github
from io import StringIO
import json
egypt_tz = pytz.timezone('Africa/Cairo')
def load_users():
    try:
        with open('users.json', 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {
            "knhp322": {"password": "knhp322", "first_login": True, "name": "Shehab Ayman", "last_password_update": str(datetime.now(egypt_tz))},
            "KFXW551": {"password": "KFXW551", "first_login": True, "name": "Hossameldin Mostafa", "last_password_update": str(datetime.now(egypt_tz))},
            "knvp968": {"password": "knvp968", "first_login": True, "name": "Mohamed Nader", "last_password_update": str(datetime.now(egypt_tz))},
            "kcqw615": {"password": "kcqw615", "first_login": True, "name": "Tareek Mahmoud", "last_password_update": str(datetime.now(egypt_tz))}}


def login(username, password):
    users = load_users()
    if username in users and users[username]['password'] == password:
        st.session_state.logged_in = True
        st.session_state.username = username
    else:
        st.error("Invalid username or password")


def update_quantity(row_index, quantity, operation, username):
    last_month = st.session_state.df.loc[row_index, 'Actual Quantity']
    
    if operation == 'add':
        st.session_state.df.loc[row_index, 'Actual Quantity'] += quantity
    elif operation == 'subtract':
        st.session_state.df.loc[row_index, 'Actual Quantity'] -= quantity
    new_quantity = st.session_state.df.loc[row_index, 'Actual Quantity']
    st.session_state.df.to_csv('matril.csv', index=False)
    update_csv_on_github(st.session_state.df, 'matril.csv', "Updated CSV with new quantity")
    st.success(f"Quantity updated successfully by {username}! New Quantity: {int(new_quantity)}")
    
    log_entry = {
        'user': username,
        'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'item': st.session_state.df.loc[row_index, 'Item Name'],
        'last_month': last_month,
        'new_quantity': new_quantity,
        'operation': operation
    }
    st.session_state.logs.append(log_entry)
    logs_df = pd.DataFrame(st.session_state.logs)
    logs_df.to_csv('logs.csv', index=False)

    update_csv_on_github(logs_df, 'logs.csv', "Updated logs CSV")


    check_quantities()

def update_csv_on_github(df, filename, commit_message):
    g = Github(st.secrets["GITHUB_TOKEN"])
    repo = g.get_repo(st.secrets["REPO_NAME"])
    contents = repo.get_contents(filename)
    csv_buffer = StringIO()
    df.to_csv(csv_buffer, index=False)
    repo.update_file(contents.path, commit_message, csv_buffer.getvalue(), contents.sha, branch="main")



def check_tab_quantities(tab_name, min_quantity):
    df_tab = st.session_state.df[st.session_state.df['Item Name'] == tab_name]
    tab_alerts = df_tab[df_tab['Actual Quantity'] < min_quantity]['Item Name'].tolist()
   
    return tab_alerts, df_tab

def display_tab(tab_name, min_quantity):
    st.header(f'{tab_name}')
    row_number = st.number_input(f'Select row number for {tab_name}:', min_value=0, max_value=len(st.session_state.df)-1, step=1, key=f'{tab_name}_row_number')
    st.markdown(f"""
    <div style='font-size: 20px; color: blue;'>Selected Item: {st.session_state.df.loc[row_number, 'Item Name']}</div>
    <div style='font-size: 20px; color: blue;'>Current Quantity: {int(st.session_state.df.loc[row_number, 'Actual Quantity'])}</div>
    """, unsafe_allow_html=True)
    quantity = st.number_input(f'Enter quantity for {tab_name}:', min_value=1, step=1, key=f'{tab_name}_quantity')
    operation = st.radio(f'Choose operation for {tab_name}:', ('add', 'subtract'), key=f'{tab_name}_operation')
    if st.button('Update Quantity', key=f'{tab_name}_update_button'):
        update_quantity(row_number, quantity, operation, st.session_state.username)

    tab_alerts, df_tab = check_tab_quantities(tab_name, min_quantity)
    if tab_alerts:
        st.error(f"Low stock for items in {tab_name}:")
        st.dataframe(df_tab.style.applymap(lambda x: 'background-color: red' if x < min_quantity else '', subset=['Actual Quantity']))

def clear_logs():
    st.session_state.logs = []
    logs_df = pd.DataFrame(columns=['user', 'time', 'item', 'old_quantity', 'new_quantity', 'operation'])
    logs_df.to_csv('logs.csv', index=False)
    st.success("Logs cleared successfully!")
    
users = load_users()


if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.logs = []

if 'logs' not in st.session_state:
    st.session_state.logs = []

if not st.session_state.logged_in:
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            login(username, password)
else:
    st.markdown(f"<div style='text-align: right; font-size: 20px; color: green;'>Logged in by: {users[st.session_state.username]['name']}</div>", unsafe_allow_html=True)
    
    if 'df' not in st.session_state:
        st.session_state.df = pd.read_csv('matril.csv')
    try:
        logs_df = pd.read_csv('logs.csv')
        st.session_state.logs = logs_df.to_dict('records')
    except FileNotFoundError:
        st.session_state.logs = []

    page = st.sidebar.radio('Select page', ['STG-2024', 'View Logs'])
    
    if page == 'STG-2024':
        
        st.markdown("""
        <style>
            .stProgress > div > div > div {
                background-color: #FFD700;
                border-radius: 50%;
            }
        </style>
        """, unsafe_allow_html=True)
        
        with st.spinner("Data loaded successfully!"):
            import time
            time.sleep(1)
        
        col1, col2 = st.columns([2, 0.75])
        with col1:
            st.markdown("""
                <h2 style='text-align: center; font-size: 40px; color: red;'>
                    Find your parts
                </h2>
            """, unsafe_allow_html=True)
        
        with col2:
            search_keyword = st.session_state.get('search_keyword', '')
            search_keyword = st.text_input("Enter keyword to search:", search_keyword)
            search_button = st.button("Search")
            search_option = 'All Columns'
        
        def search_in_dataframe(df_Material, keyword, option):
            if option == 'All Columns':
                result = df_Material[df_Material.apply(lambda row: row.astype(str).str.contains(keyword, case=False).any(), axis=1)]
            else:
                result = df_Material[df_Material[option].astype(str).str.contains(keyword, case=False)]
            return result
        
        if st.session_state.get('refreshed', False):
            st.session_state.search_keyword = ''
            st.session_state.refreshed = False
        
        if search_button and search_keyword:
            st.session_state.search_keyword = search_keyword
            search_results = search_in_dataframe(st.session_state.df, search_keyword, search_option)
            st.write(f"Search results for '{search_keyword}'in{search_option}:")
            st.dataframe(search_results, width=1000, height=200)
        st.session_state.refreshed = True 
        
        tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
            'Reel Label (Small)', 'Reel Label (Large)',
            'Ink Reels for Label', 'Red Tape', 'Adhasive Tape', 'Cartridges', 'MultiPharma Cartridge'
        ])
        
        with tab1:
            Small = df_Material[df_Material['Item Name'] == 'Reel Label (Small)'].sort_values(by='Item Name')
            st.dataframe(Small, width=2000)
            col4, col5, col6 = st.columns([2,1,2])
            with col4:
                display_tab('Reel Label (Small)', 20)
                    
        with tab2:
            display_tab('Reel Label (Large)', 60)
        with tab3:
            display_tab('Ink Reels for Label', 20)
        with tab4:
            display_tab('Red Tape', 5)
        with tab5:
            display_tab('Adhasive Tape', 100)
        with tab6:
            display_tab('Cartridges', 50)
        with tab7:
            display_tab('MultiPharma Cartridge', 5)

        st.button("Update page")
        csv = st.session_state.df.to_csv(index=False)
        st.download_button(label="Download updated sheet", data=csv, file_name='matril.csv', mime='text/csv')

    elif page == 'View Logs':
        st.header("View Logs")
        logs_df = pd.DataFrame(st.session_state.logs)
        st.dataframe(logs_df)
        if st.button("Clear Logs"):
            clear_logs()
