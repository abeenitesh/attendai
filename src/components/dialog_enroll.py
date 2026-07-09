from src.db.db import enroll_student_to_subject, join_subject
import time
import streamlit as st


@st.dialog("Enroll in Subject")
def enroll_dialog():
    st.write("Enter the subject code provided by your teacher to enroll")
    join_code = st.text_input("Subject Code", placeholder="Eg. CS101")

    if st.button("Enroll Now", type="primary", width="stretch"):
        if join_code:
            result = join_subject(
                st.session_state.student_data["student_id"],
                join_code
            )

            if result == "not_found":
                st.error("Invalid join code.")
            elif result == "already_enrolled":
                st.warning("You are already enrolled in this program.")
            else:
                st.success("Successfully enrolled!")
                time.sleep(1)
                st.rerun()
        else:
            st.warning("Please enter a sujbect code")