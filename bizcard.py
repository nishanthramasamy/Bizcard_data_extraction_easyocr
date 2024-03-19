import easyocr
import streamlit as st
import numpy as np
from PIL import Image
import mysql.connector as sql
import re
import pandas as pd

mydb = sql.connect(host = 'localhost',
                   user = 'root',
                   password = 'nishanth0011',
                   auth_plugin='caching_sha2_password',
                   port=3306
                   )

mycursor = mydb.cursor(buffered=True)

query = """CREATE DATABASE IF NOT EXISTS bizcard"""
mycursor.execute(query)
mydb.commit()
mycursor.execute(""" USE bizcard""")
mydb.commit()
query = """ CREATE TABLE IF NOT EXISTS details (name TEXT,
    designation TEXT,
    email VARCHAR(255),
    company_name TEXT,
    number TEXT,
    address TEXT,
    website VARCHAR(255))"""
mycursor.execute(query)
mydb.commit()

reader = easyocr.Reader(['en'])

def extract_name(details):
    temp = details[0].split()
    name = ''
    if len(temp) > 3:
        name = temp[0]+temp[1]
        del temp[0]
        del temp[0]
        designation = ' '.join(temp)
    else:
        name = temp[0]
        del temp[0]
        designation = ' '.join(temp)

    return name, designation

def extract_mail(details):
    mail = ''
    temp = []
    for i in details:
        if '@' in i:
            temp = i.split()
            if len(temp) > 1:
                for j in temp:
                    if '@' in j:
                        mail = j 
            else:
                mail = temp[0]
    return mail

def extract_number(details):
    temp = []
    temps = []
    ph = ''
    for item in details:
        if (re.search(r'\+\d{3}-\d{3}-\d{4}', item)) or (re.search(r'\d{3}-\d{3}-\d{4}', item)) or (re.search(r'\+\d{2}-\d{3}-\d{4}', item)) or (re.search(r'\+\d{2}-\d{3}-\d{4}', item)):
            if len(item) > 2:
                temp = item.split()
                for i in temp:
                    if (re.search(r'\+\d{3}-\d{3}-\d{4}', i)) or (re.search(r'\d{3}-\d{3}-\d{4}', i)) or (re.search(r'\+\d{2}-\d{3}-\d{4}', i)) or (re.search(r'\+\d{2}-\d{3}-\d{4}', i)):
                        temps.append(i)
                        
                ph = ' '.join(temps)
                return ph 
            else:
                return item
        
def extract_address(details, det):
    addrs = []
    ad = []
    for i in details:
        if 'st' in i.lower():
            temp = i.split()
            for j in temp:
                if j not in det:
                    addrs.append(j)
    
    for x in addrs:
        if re.search(r'WWW', x) or re.search(r'\.com', x):
            continue
        else:
            ad.append(x)
    result = ' '.join(ad)
    return result

def extract_website(details):
    temps = []
    web = []
    webste = ''
    for i in details:
        if 'com' in i.lower() or 'www' in i.lower() or 'WWW' in i or 'wWW' in i:
                temps = i.split()
                st.write(temps)
                st.write(str(temps[0]))
                if len(temps) > 1:
                    for j in temps:
                        if ('com' in j.lower() or 'www' in j.lower() or 'WWW' in j.lower()):
                            if '@' not in j.lower():
                                web.append(j)
                    webste = ' '.join(web)
                else:
                    if '@' not in temps[0]:
                        if ('com' in temps[0] or 'www' in temps[0] or 'WWW' in temps[0]):
                            webste = temps[0]
    return webste

def extract_company(details, details_li):

    for i in details:
        if i not in details_li:
            company = i

    return company

col1, col2, col3 = st.columns([1, 3, 3])

st.title("Bizcard details extraction using EasyOCR")

uploaded_file = st.file_uploader("Choose an image...", type=["jpg", "jpeg", "png"])


if uploaded_file is not None:
    # Display the uploaded image
    image = Image.open(uploaded_file)
    st.image(image, caption='Uploaded Image', use_column_width=True)

    image_np = np.array(image)

    image_f = reader.readtext(image_np, paragraph=True, contrast_ths=0.9)
    details = []
    for words in image_f:
        text = words[1]
        details.append(words[1])

    st.write(details)

    #pattern_matching
    name, designation = extract_name(details)
    email = extract_mail(details)
    number = extract_number(details)
    
    website = extract_website(details)
    det =[name, designation, number, website, email]
    address = extract_address(details, det)
    details_li =[name, designation, number, address, website, email]

    company = extract_company(details, details_li)
    st.write('name',name)
    st.write('designation', designation)
    st.write('email', email)
    st.write('number', number)
    st.write('address',address)
    st.write('website', website)
    st.write('company', company)
    details_list = {'name': name, 'designation': designation, 'email' : email, 'company_name': company, 'number' : number, 'address' : address, 'website' : website}
    
    
    #st.write(f"email= {email}, website = {website}, address = {address}, pincode = {pincode}")
    check = st.button("To upload")
    if check:
        query = """INSERT INTO details VALUES(%s,%s,%s,%s,%s,%s,%s)"""
        mycursor.execute(query, tuple(details_list.values()))
        mydb.commit()


mycursor.execute("""SELECT name FROM details""")
name_li = (mycursor.fetchall())
modified_name_li = [''.join(x for x in name if x.isalpha()) for name in name_li]

st.markdown('***')
st.markdown('***')

st.write("If you wish modify any entry: select the entry by choosing the name below")

selected_name = st.selectbox('Select the name', modified_name_li, index = None, placeholder='Choose the name whose details to be modified',)
if selected_name:
    display_name = ''.join(x for x in selected_name if x.isalpha())
    #st.write("selected name", selected_name)
    selected_name = (selected_name,)
    mycursor.execute("SELECT * FROM details WHERE name = %s", selected_name)
    df = pd.DataFrame(mycursor.fetchall(), columns=mycursor.column_names)
    st.write(df)
    
    mycursor.execute("SHOW COLUMNS FROM details")  
    columns = [column[0] for column in mycursor.fetchall()]

    selected_column = st.selectbox('Select the entry to modify', columns, index = None, placeholder='Choose the value you wish to modify')

    if selected_column:
        text = st.text_input(f'Enter text to update in {selected_column}')
        if text :
            update = st.button("Update")
            if update:
                dict = {
                        'text' : text,
                        'name' : selected_name
                        }
                t = tuple(dict.values())
                text = (text)
                st.write("the text to be inserted", text)
                new_name = ''.join(x for x in selected_name if x.isalpha()) 
                li = [(text, selected_name)]
                query = f" UPDATE details SET {selected_column} = %s WHERE name = %s"
                mycursor.execute(query, (text,new_name))
                mydb.commit()

                mycursor.execute("SELECT * FROM details WHERE name = %s", selected_name)
                df = pd.DataFrame(mycursor.fetchall(), columns=mycursor.column_names)
                st.write(df)

