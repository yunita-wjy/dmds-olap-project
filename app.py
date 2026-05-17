import streamlit as st
import pandas as pd

st.set_page_config(page_title="OLAP Analysis", layout="wide")

st.title("Dashboard")

st.sidebar.title("Menu")
tab = st.sidebar.radio(" ", [
    "General Dashboard",
    "1",
    "2",
    "3"
])