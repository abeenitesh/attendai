import streamlit as st
from src.components.header import header_dashboard
from src.ui.base_layout import style_background_dashboard, style_base_layout
from src.db.db import check_teacher_exists, create_teacher, teacher_login


def student_screen():
    
    style_background_dashboard()
    style_base_layout() 
    
    
    c1, c2 = st.columns(2, vertical_alignment="center", gap="small")

    with c1:
        header_dashboard()
        
    with c2:
        if st.button("Go Back to Home", type="secondary", key="loginbackbtn", shortcut="control+backspace"):
            st.session_state["login_type"] = None
            st.rerun()
    st.header("Login using FaceID", text_alignment="center")
    st.space()    
    st.camera_input("Position your face in the center")