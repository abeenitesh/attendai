import psycopg
import streamlit as st

def get_connection():
    return psycopg.connect(st.secrets["DATABASE_URL"])

# def get_connection():
#     return psycopg.connect(
#         host=st.secrets["DB_HOST"],
#         port=st.secrets["DB_PORT"],
#         dbname=st.secrets["DB_NAME"],
#         user=st.secrets["DB_USER"],
#         password=st.secrets["DB_PASSWORD"],
#     )