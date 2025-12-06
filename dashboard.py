import streamlit as st
import pandas as pd

st.set_page_config(page_title="Youth Job Application Tracker", layout="centered")

st.title("Youth Job Application Tracker (SDG 8)")
st.caption("Submit applicant details and view job listings. Data is stored locally for now.")

# Applicant form
with st.form("applicant_form"):
    st.subheader("Applicant Information")
    name = st.text_input("Full Name")
    age = st.selectbox("Age Group", ["15-19", "20-24", "25-30"])
    region = st.selectbox("Region", ["Western Visayas", "National"])
    job_interest = st.text_input("Preferred Job Role")
    submit = st.form_submit_button("Submit Application")

if submit:
    st.success(f"Application submitted for {name} — interested in {job_interest}")
