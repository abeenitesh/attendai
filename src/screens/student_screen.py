import time
from PIL import Image
import streamlit as st
import hashlib
import numpy as np
from src.components.dialog_enroll import enroll_dialog
from src.components.subject_card import subject_card
from src.pipelines.voice_pipeline import get_voice_embedding
from src.pipelines.face_pipeline import get_face_embeddings, predict_attendance, train_classifier
from src.components.header import header_dashboard
from src.ui.base_layout import style_background_dashboard, style_base_layout
from src.db.db import create_student, get_all_students, get_student_attendance, get_student_subjects, unenroll_student_to_subject


def student_dashboard():
    student_data = st.session_state.student_data
    student_id = student_data["student_id"]
    c1, c2 = st.columns(2, vertical_alignment="center", gap="small")

    with c1:
        header_dashboard()
        
    with c2:
        st.subheader(f"""
                Welcome, {student_data["name"]}
        """)
        if st.button("Logout", type="secondary", key="loginbackbtn", shortcut="control+backspace"):
            st.session_state["is_logged_in"] = False
            del st.session_state.student_data 
            st.rerun()

    st.space()
    
    c1, c2 = st.columns(2)
    with c1:
        st.header("Your Enrolled Subjects")

    with c2:
        if st.button("Enroll in Subject", type="primary", width="stretch"):
            enroll_dialog()
    
    st.divider()

    with st.spinner("Loading your enrolled subjects..."):
        subjects = get_student_subjects(student_id)
        logs = get_student_attendance(student_id)
    
    stats_map = {}

    for log in logs:
        sid = log["subject_id"]
        
        if sid not in stats_map:
            stats_map[sid] = {"total": 0, "attended": 0}

        stats_map[sid]["total"] += 1

        if log.get("is_present"):
            stats_map[sid]["attended"] += 1

    cols = st.columns(2)
    for i, sub in enumerate(subjects):
        sid = sub["subject_id"]

        stats = stats_map.get(sid, {"total": 0, "attended": 0})
        def unenroll_button():
            if st.button("Unenroll from this course", type="tertiary", width="stretch", icon=":material/delete_forever:"):
                unenroll_student_to_subject(student_id, sid)
                st.toast(f"Unenrolled from this {sub['name']} sucessfully!")
                st.rerun()
            
        with cols[i % 2]:
            subject_card(
                name = sub["name"],
                code = sub["subject_code"],
                section = sub["section"],
                stats = [
                    ("🗓️", "Total", stats["total"]),
                    ("✅", "Attended", stats["attended"]),
                ],
                footer_callback=unenroll_button
            )
    
def get_photo_hash(photo_source):
    if photo_source is None:
        return None

    data = photo_source.getvalue()
    return hashlib.md5(data).hexdigest()


def authenticate_student(photo_source):
    if photo_source is None:
        return

    current_hash = get_photo_hash(photo_source)

    # Same image -> don't scan again
    if st.session_state.last_photo_hash == current_hash:
        registration_form(
            photo_source,
            st.session_state.show_registration
        )
        return

    st.session_state.last_photo_hash = current_hash
    st.session_state.detected_student = None

    result = detect_student(photo_source)

    st.session_state.show_registration = False

    if result["status"] == "noface":
        st.warning("Face not found!")
        return

    if result["status"] == "multiple":
        st.warning("Multiple faces found!")
        return

    if result["status"] == "success":

        student = result["student"]

        st.session_state.detected_student = student

        st.session_state.is_logged_in = True
        st.session_state.user_role = "student"
        st.session_state.student_data = student

        st.toast(f"Welcome Back! {student['name']}")

        time.sleep(1)
        st.rerun()

    st.info("Face not recognized! You might be a new student!")

    st.session_state.show_registration = True

    registration_form(photo_source, True)


def detect_student(photo_source):
    img = np.array(Image.open(photo_source))

    with st.spinner("AI is scanning..."):
        detected, _, num_faces = predict_attendance(img)

    if num_faces == 0:
        return {"status": "noface"}

    if num_faces > 1:
        return {"status": "multiple"}

    if detected:
        student_id = list(detected.keys())[0]

        students = get_all_students()

        student = next(
            (s for s in students if s["student_id"] == student_id),
            None
        )

        if student:
            return {
                "status": "success",
                "student": student
            }

    return {"status": "new"}

def registration_form(photo_source, show=False):
    if not show:
        return
    with st.container(border=True):
        st.header("Register New Profile")
        new_name = st.text_input("Enter your name", placeholder="E.g. Kumar")
        
        st.subheader("Optional: Voice Enrollment")
        st.info("Enroll your for voice only attendance")


        audio_data = None
        
        try:
            audio_data = st.audio_input("Record a short phrase like I am present, My name is Kumar.")
        except Exception as e:
            st.error("Audio data failed!")

        if st.button("Create Account", type="primary"):
            if new_name:
                with st.spinner("Creating profile..."):
                    img = np.array(Image.open(photo_source))
                    encodings = get_face_embeddings(img)
                    if encodings:
                        face_emb = encodings[0].tolist()
                        voice_emb = None

                        if audio_data:
                            voice_emb = get_voice_embedding(audio_data.read())

                        response_data = create_student(new_name, face_embedding=face_emb, voice_embedding=voice_emb)

                        if response_data:
                            # print(type(response_data))
                            # print(response_data)
                            train_classifier()
                            st.session_state.is_logged_in = True
                            st.session_state.user_role = "student"
                            st.session_state.student_data = response_data
                            st.toast(f"Profile Created! Hi {new_name}!")
                            time.sleep(1)
                            st.session_state.image_source = None
                            st.session_state.last_photo_hash = None
                            st.session_state.show_registration = False
                            st.session_state.detected_student = None
                            st.rerun()
                            
                    else:
                        st.error("Could not capture your facial features for registration")
            else:
                st.warning("Please enter your name!")


def student_screen():
    
    style_background_dashboard()
    style_base_layout() 
    
    defaults = {
        "image_source": None,
        "last_photo_hash": None,
        "show_registration": False,
        "detected_student": None,
    }

    for key, value in defaults.items():
        st.session_state.setdefault(key, value)
    
    
    if "student_data" in st.session_state:
        student_dashboard()
        return
    
    c1, c2 = st.columns(2, vertical_alignment="center", gap="small")

    with c1:
        header_dashboard()
        
    with c2:
        if st.button("Go Back to Home", type="secondary", key="loginbackbtn", shortcut="control+backspace"):
            st.session_state.login_type = None
            st.session_state.image_source = None
            st.session_state.last_photo_hash = None
            st.session_state.show_registration = False
            st.session_state.detected_student = None
            st.rerun()
    st.header("Login using FaceID", text_alignment="center")
    st.space()
    

    # Selection Screen
    if st.session_state.image_source is None:

        left, spacer, right = st.columns([1, 0.2, 1])

        with left:
            if st.button("📷 Open Camera", use_container_width=True):
                st.session_state.image_source = "camera"
                st.rerun()

        with right:
            if st.button("🖼 Upload Image", use_container_width=True):
                st.session_state.image_source = "upload"
                st.rerun()

    # Camera Screen
    elif st.session_state.image_source == "camera":

        col1, col2 = st.columns([1, 5])

        with col1:
            if st.button("← Back"):
                st.session_state.image_source = None
                st.session_state.last_photo_hash = None
                st.session_state.show_registration = False
                st.session_state.detected_student = None
                st.rerun()

        st.divider()
        

        photo_source = st.camera_input("Position your face in the center")
        authenticate_student(photo_source)

    # Upload Screen
    elif st.session_state.image_source == "upload":

        col1, col2 = st.columns([1, 5])

        with col1:
            if st.button("← Back"):
                st.session_state.image_source = None
                st.session_state.last_photo_hash = None
                st.session_state.show_registration = False
                st.session_state.detected_student = None
                st.rerun()

        st.divider()

        photo_source = st.file_uploader(
            "Upload your face image",
            type=["jpg", "jpeg", "png"]
        )
        if photo_source:
            preview_left, preview_center, preview_right = st.columns([1, 2, 1])
            with preview_center:
                st.image(photo_source, caption="Image Preview", width=300)
    
        authenticate_student(photo_source)
