## from https://docs.streamlit.io/develop/tutorials/databases/mysql
import streamlit as st
## initialize connection
conn=st.connection('mysql', type='sql')

## Create first visualization
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Health & Sleep Dashboard", layout="wide")

st.title("Health & Sleep Analytics Dashboard")

#### Retrieve filter values from the database
@st.cache_data
def get_filter_options():
    query = """
        SELECT DISTINCT g.gender_desc
        FROM demographics_fact d
        JOIN gender_dim g ON d.gender_id = g.gender_id
        WHERE g.gender_desc IS NOT NULL
        ORDER BY g.gender_desc
    """
    df = fetch_data(query)
    if not df.empty:
        return df.iloc[:, 0].tolist()
    return []

#### set up the filters
st.sidebar.header("Filters")

gender_options = get_filter_options()

# add filter option "All" 
gender_filter = st.sidebar.selectbox("Gender", ["All"] + gender_options)

conditions = []
if gender_filter != "All":
    conditions.append(f"g.gender_desc = '{gender_filter}'")

where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""

#### Sleep Disruption causes
st.header("Sleep Interference Factors")

sleep_query = f"""
SELECT 'stress' AS sleep_cause, SUM(stress_sleep_id = 1) AS num_people
FROM sleep_fact s
JOIN demographics_fact d ON s.fact_id = d.fact_id
JOIN gender_dim g ON d.gender_id = g.gender_id
{where_clause}
UNION ALL
SELECT 'medication', SUM(med_sleep_id = 1)
FROM sleep_fact s
JOIN demographics_fact d ON s.fact_id = d.fact_id
JOIN gender_dim g ON d.gender_id = g.gender_id
{where_clause}
UNION ALL
SELECT 'pain', SUM(pain_sleep_id = 1)
FROM sleep_fact s
JOIN demographics_fact d ON s.fact_id = d.fact_id
JOIN gender_dim g ON d.gender_id = g.gender_id
{where_clause}
UNION ALL
SELECT 'bathroom', SUM(bathroom_sleep_id = 1)
FROM sleep_fact s
JOIN demographics_fact d ON s.fact_id = d.fact_id
JOIN gender_dim g ON d.gender_id = g.gender_id
{where_clause}
UNION ALL
SELECT 'Unknown', SUM(unknown_sleep_id = 1)
FROM sleep_fact s
JOIN demographics_fact d ON s.fact_id = d.fact_id
JOIN gender_dim g ON d.gender_id = g.gender_id
{where_clause}
"""

sleep_df = fetch_data(sleep_query)

# build pie chart
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Sleep Disruption Causes")

    sorted_sleep_df = sleep_df.sort_values(by="num_people", ascending=False)

    fig = px.bar(sorted_sleep_df, x="sleep_cause", y="num_people", text="num_people")

    fig.update_traces(textposition="outside")

    fig.update_layout(xaxis_title="Sleep Disruption Cause", 
                      yaxis_title="Number of People")

    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("Data")
    st.dataframe(sorted_sleep_df)


#### 2. Employment Status vs Doctor Visits

st.header("Employment Status vs Doctor Visits")

visit_query = f"""
SELECT 
    e.employment_desc AS employment_status, 
    dv.doctor_visit_desc AS doctor_visits,
    COUNT(*) AS num_people
FROM health_fact h
JOIN demographics_fact d ON h.fact_id = d.fact_id
JOIN employment_dim e ON d.employment_id = e.employment_id
JOIN doctor_visit_dim dv ON h.doctor_visit_id = dv.doctor_visit_id
JOIN gender_dim g ON d.gender_id = g.gender_id
{where_clause}
GROUP BY e.employment_desc, dv.doctor_visit_desc
ORDER BY e.employment_desc, num_people DESC;
"""

visit_df = fetch_data(visit_query)

#build bar chart
col3, col4 = st.columns([2, 1])

with col3:
    st.subheader("Doctor Visits by Employment Status")

    fig = px.bar(visit_df, x="employment_status", y="num_people", 
                 color="doctor_visits", barmode="group", text="num_people")
    
    fig.update_traces(texttemplate='%{y}', textposition='outside')
    
    fig.update_layout(xaxis_title="Employment Status",
                      yaxis_title="Number of People",
                      legend_title="Doctor Visits")

    fig.update_xaxes(tickangle=0)  # horizontal labels

    st.plotly_chart(fig, use_container_width=True)


with col4:
    st.subheader("Data")

    sorted_visit_df = visit_df.sort_values(
    by=["employment_status", "doctor_visits"],
    ascending=[True, True]).reset_index(drop=True)

    st.dataframe(sorted_visit_df)
