import json
from github import Github
import json
from datetime import datetime, timedelta
import pytz
import pandas as pd
import streamlit as st
# تهيئة المنطقة الزمنية للقاهرة
egypt_tz = pytz.timezone('Africa/Cairo')

import streamlit as st
import pandas as pd
from datetime import datetime
from github import Github
from io import StringIO

# تحميل بيانات المستخدمين
def load_users():
    return {
        "admin": {"name": "Admin", "password": "admin123"},
        # يمكنك إضافة المزيد من المستخدمين هنا
    }

# وظيفة تسجيل الدخول
def login(username, password):
    users = load_users()
    if username in users and users[username]['password'] == password:
        st.session_state.logged_in = True
        st.session_state.username = username
    else:
        st.error("Invalid username or password")

# وظيفة تحديث الكمية
def update_quantity(row_index, quantity, operation, username):
    last_month = st.session_state.df.loc[row_index, 'Actual Quantity']
    
    if operation == 'add':
        st.session_state.df.loc[row_index, 'Actual Quantity'] += quantity
    elif operation == 'subtract':
        st.session_state.df.loc[row_index, 'Actual Quantity'] -= quantity
    
    new_quantity = st.session_state.df.loc[row_index, 'Actual Quantity']
    
    # حفظ التعديلات في ملف محلي
    st.session_state.df.to_csv('matril.csv', index=False)
    
    # تحديث الملف على GitHub
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
    
    # حفظ السجلات في CSV محلي
    logs_df = pd.DataFrame(st.session_state.logs)
    logs_df.to_csv('logs.csv', index=False)
    
    # تحديث ملف السجلات على GitHub
    update_csv_on_github(logs_df, 'logs.csv', "Updated logs CSV")

    # تحقق من الكميات لتحديث التنبيهات
    check_quantities()

# وظيفة تحديث ملف CSV على GitHub
def update_csv_on_github(df, filename, commit_message):
    # التوكن الخاص بك (استبدل بـ التوكن الخاص بك)
    g = Github("your_github_token")
    
    # الوصول إلى الريبو والمجلد الذي يحتوي على الملف
    repo = g.get_repo("your_github_username/your_repo_name")
    contents = repo.get_contents(filename)
    
    # تحويل DataFrame إلى نص CSV
    csv_buffer = StringIO()
    df.to_csv(csv_buffer, index=False)
    
    # تحديث الملف على GitHub
    repo.update_file(contents.path, commit_message, csv_buffer.getvalue(), contents.sha, branch="main")

# وظيفة التحقق من الكميات وتحديث التنبيهات
def check_quantities():
    new_alerts = []
    for index, row in st.session_state.df.iterrows():
        if row['Actual Quantity'] < 100:  # غير العتبة حسب الحاجة
            new_alerts.append(row['Item Name'])
            
    st.session_state.alerts = new_alerts

# وظيفة عرض كل تبويب وتحديث الكميات
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

# وظيفة تنظيف السجلات
def clear_logs():
    st.session_state.logs = []
    logs_df = pd.DataFrame(columns=['user', 'time', 'item', 'old_quantity', 'new_quantity', 'operation'])
    logs_df.to_csv('logs.csv', index=False)
    st.success("Logs cleared successfully!")
    
users = load_users()

# واجهة تسجيل الدخول
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
    
    # تحميل البيانات
    if 'df' not in st.session_state:
        st.session_state.df = pd.read_csv('matril.csv')
    try:
        logs_df = pd.read_csv('logs.csv')
        st.session_state.logs = logs_df.to_dict('records')
    except FileNotFoundError:
        st.session_state.logs = []

    page = st.sidebar.radio('Select page', ['STG-2024', 'View Logs'])
    
    if page == 'STG-2024':
        def main():
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
