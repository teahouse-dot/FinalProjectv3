## from https://docs.streamlit.io/develop/tutorials/databases/mysql
import streamlit as st
## initialize connection
conn=st.connection('mysql', type='sql')
