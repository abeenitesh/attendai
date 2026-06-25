import streamlit as st
from pathlib import Path

def header_home():
    
    logo_url = "https://i.ibb.co/KpQTDMpg/logo.png"
    
    st.markdown(f"""
                <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; margin-vertical: 30px;">
                    <img src='{logo_url}' style='height:200px;' />
                    <h1 style='text-align: center; color: #E0E3FF'>
                        Attend<br />AI
                    </h1>
                </div>
                """, 
                unsafe_allow_html=True
            )