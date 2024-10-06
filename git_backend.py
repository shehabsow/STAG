import json
from github import Github
import json
from datetime import datetime, timedelta
import pytz
import pandas as pd
import streamlit as st
# تهيئة المنطقة الزمنية للقاهرة
egypt_tz = pytz.timezone('Africa/Cairo')

def load_data(file_path):
    """تحميل البيانات من ملف JSON"""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        if file_path == "matrils.json":
            return {"matril": []}
        elif file_path == "change log.json":
            return {"logs": []}
    except json.JSONDecodeError:
        return None
if 'df' not in st.session_state:
    data = load_data("matrils.json")  # تحميل البيانات من ملف JSON
    if data:  # إذا تم العثور على بيانات
        # تحويل البيانات إلى DataFrame وحفظها في session_state
        st.session_state['df'] = pd.DataFrame(data["matril"])
    else:
        st.error("لم يتم العثور على بيانات!")
        
def save_data(file_path, data):
    """حفظ البيانات في ملف JSON"""
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def create_checklist_record(item_data):
    """إنشاء سجل جديد في قائمة المواد"""
    data = load_data("matrils.json")
    new_item = {
        "Item Name": item_data.get("Item Name", ""),
        "Actual Quantity": item_data.get("Actual Quantity", 0),
        "Monthly Consumption": item_data.get("Monthly Consumption", 0),
        "Coverage in Month": item_data.get("Coverage in Month", 0)
    }
    data["matril"].append(new_item)
    save_data("matrils.json", data)
    return new_item

def update_checklist_record(item_name, updated_data):
    """تحديث سجل موجود في قائمة المواد"""
    data = load_data("matrils.json")
    for item in data["matril"]:
        if item["Item Name"] == item_name:
            item.update(updated_data)
            save_data("matrils.json", data)
            return item
    return None

def create_change_log_entry(entry_data):
    """إنشاء سجل جديد في سجل التغييرات"""
    data = load_data("change log.json")
    new_entry = {
        "timestamp": datetime.now(egypt_tz).strftime("%Y-%m-%d %H:%M:%S"),
        "Item Name": entry_data.get("Item Name", ""),
        "user": entry_data.get("user", ""),
        "last_quantity": entry_data.get("last_quantity", 0),
        "new_quantity": entry_data.get("new_quantity", 0),
        "operation": entry_data.get("operation", ""),
        "change_amount": entry_data.get("change_amount", 0)
    }
    data["logs"].append(new_entry)
    save_data("change log.json", data)
    return new_entry

def update_quantity(item_name, change_amount, operation, username):
    """تحديث كمية المادة وتسجيل التغيير"""
    data = load_data("matrils.json")
    
    for item in data["matril"]:
        if item["Item Name"] == item_name:
            last_quantity = item["Actual Quantity"]
            
            if operation == "add":
                item["Actual Quantity"] += change_amount
            elif operation == "subtract":
                if item["Actual Quantity"] >= change_amount:
                    item["Actual Quantity"] -= change_amount
                else:
                    return False, "الكمية المطلوبة أكبر من المتوفر"
            
            save_data("matrils.json", data)
            
            # تسجيل التغيير
            log_entry = {
                "Item Name": item_name,
                "user": username,
                "last_quantity": last_quantity,
                "new_quantity": item["Actual Quantity"],
                "operation": operation,
                "change_amount": change_amount
            }
            create_change_log_entry(log_entry)
            
            return True, f"تم تحديث الكمية بنجاح. الكمية الجديدة: {item['Actual Quantity']}"
    
    return False, "المادة غير موجودة"

def check_tab_quantities(tab_name, min_quantity):
    df_tab = st.session_state.df[st.session_state.df['Item Name'] == tab_name]
    tab_alerts = df_tab[df_tab['Actual Quantity'] < min_quantity]['Item Name'].tolist()
   
    return tab_alerts, df_tab

# Function to display each tab
def display_tab(tab_name, min_quantity):
    st.header(f'{tab_name}')
  
    st.dataframe(filtered_df, width=2000)

    if not filtered_df.empty:
        row_number = filtered_df.index[0]
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

def get_low_stock_items():
    """الحصول على قائمة المواد التي تحتاج إلى تجديد المخزون"""
    data = load_data("matrils.json")
    low_stock = []
    
    for item in data["matril"]:
        if item["Actual Quantity"] <= item["Monthly Consumption"]:
            low_stock.append({
                "Item Name": item["Item Name"],
                "Actual Quantity": item["Actual Quantity"],
                "Monthly Consumption": item["Monthly Consumption"]
            })
    
    return low_stock

def get_item_history(item_name):
    """الحصول على سجل التغييرات الخاص بمادة معينة"""
    data = load_data("change log.json")
    history = [entry for entry in data["logs"] if entry["Item Name"] == item_name]
    return history

def export_to_excel(file_path="stock_report.xlsx"):
    """تصدير البيانات إلى ملف Excel"""
    data = load_data("matrils.json")
    df = pd.DataFrame(data["matril"])
    df.to_excel(file_path, index=False)
    return file_path




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
            Large = df_Material[df_Material['Item Name'] == 'Reel Label (Large)'].sort_values(by='Item Name')
            st.dataframe(Large, width=2000)
            col4, col5, col6 = st.columns([2,1,2])
            with col4:
                display_tab('Reel Label (Large)', 60)
        with tab3:
            Ink = df_Material[df_Material['Item Name'] == 'Ink Reels for Label'].sort_values(by='Item Name')
            st.dataframe(Ink, width=2000)
            col4, col5, col6 = st.columns([2,1,2])
            with col4:
                display_tab('Ink Reels for Label', 20)
        with tab4:
            Tape = df_Material[df_Material['Item Name'] == 'Red Tape'].sort_values(by='Item Name')
            st.dataframe(Tape, width=2000)
            col4, col5, col6 = st.columns([2,1,2])
            with col4:
                display_tab('Red Tape', 5)
        with tab5:
            Adhesive = df_Material[df_Material['Item Name'] == 'Adhasive Tape'].sort_values(by='Item Name')
            st.dataframe(Adhesive, width=2000)
            col4, col5, col6 = st.columns([2,2,2])
            with col4:
                display_tab('Adhasive Tape', 100)
        with tab6:
            Cartridges = df_Material[df_Material['Item Name'] == 'Cartridges'].sort_values(by='Item Name')
            st.dataframe(Cartridges, width=2000)
            col4, col5, col6 = st.columns([2,1,2])
            with col4:
                display_tab('Cartridges', 50)
        with tab7:
            MultiPharma = df_Material[df_Material['Item Name'] == 'MultiPharma Cartridge'].sort_values(by='Item Name')
            st.dataframe(MultiPharma, width=2000)
            col4, col5, col6 = st.columns([2,1,2])
            with col4:
                display_tab('MultiPharma Cartridge', 5)

        st.button("Update page")
        csv = df_Material.to_csv(index=False)
        st.download_button(label="Download updated sheet", data=csv, file_name='matril.csv', mime='text/csv')

    if __name__ == '__main__':
        main()
elif page == 'View Logs':
    st.header('User Activity Logs')
    load_logs()  # Load logs when page is changed to 'View Logs'

    if st.session_state.logs:
        logs_df = pd.DataFrame(st.session_state.logs)
        st.dataframe(logs_df, width=1000, height=400)
        csv = logs_df.to_csv(index=False)
        st.download_button(label="Download Logs as CSV", data=csv, file_name='logs.csv', mime='text/csv')
        #if st.button("Clear Logs"):
            #clear_logs()
    else:
        st.write("No logs available.")
