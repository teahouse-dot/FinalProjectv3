## from https://docs.streamlit.io/develop/tutorials/databases/mysql
import streamlit as st
## initialize connection
conn=st.connection('mysql', type='sql')

## Create first visualization
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Health & Sleep Dashboard", layout="wide")

st.title("Health & Sleep Analytics Dashboard")

def fetch_data(query):
    return conn.query(query)

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

################ Sleep Disruption causes ######################

st.header("Sleep Interference Factors")

sleep_query = f"""
SELECT sleep_cause, gender, SUM(num_people) AS num_people
FROM (
    SELECT 'stress' AS sleep_cause, g.gender_desc AS gender, 
           CASE WHEN s.stress_sleep_id = 1 THEN 1 ELSE 0 END AS num_people
    FROM sleep_fact s
    JOIN demographics_fact d ON s.fact_id = d.fact_id
    JOIN gender_dim g ON d.gender_id = g.gender_id
    {where_clause}
    UNION ALL
    SELECT 'medication', g.gender_desc, 
           CASE WHEN s.med_sleep_id = 1 THEN 1 ELSE 0 END
    FROM sleep_fact s
    JOIN demographics_fact d ON s.fact_id = d.fact_id
    JOIN gender_dim g ON d.gender_id = g.gender_id
    {where_clause}
    UNION ALL
    SELECT 'pain', g.gender_desc, 
           CASE WHEN s.pain_sleep_id = 1 THEN 1 ELSE 0 END
    FROM sleep_fact s
    JOIN demographics_fact d ON s.fact_id = d.fact_id
    JOIN gender_dim g ON d.gender_id = g.gender_id
    {where_clause}
    UNION ALL
    SELECT 'bathroom', g.gender_desc, 
           CASE WHEN s.bathroom_sleep_id = 1 THEN 1 ELSE 0 END
    FROM sleep_fact s
    JOIN demographics_fact d ON s.fact_id = d.fact_id
    JOIN gender_dim g ON d.gender_id = g.gender_id
    {where_clause}
    UNION ALL
    SELECT 'Unknown', g.gender_desc, 
           CASE WHEN s.unknown_sleep_id = 1 THEN 1 ELSE 0 END
    FROM sleep_fact s
    JOIN demographics_fact d ON s.fact_id = d.fact_id
    JOIN gender_dim g ON d.gender_id = g.gender_id
    {where_clause}
) t
GROUP BY sleep_cause, gender
"""

sleep_df = fetch_data(sleep_query)

# build stacked bar chart
# calculate total number per sleep cause
totals = sleep_df.groupby("sleep_cause")["num_people"].sum().reset_index()

# get the causes in desc order based on total number
cause_order = (totals.sort_values("num_people", ascending=False)["sleep_cause"].tolist())

sleep_df["sleep_cause"] = pd.Categorical(sleep_df["sleep_cause"],
                                         categories=cause_order,
                                         ordered=True)

sorted_sleep_df = sleep_df.sort_values(by=["sleep_cause", "gender"])

col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Sleep Disruption Causes")

    fig = px.bar(sorted_sleep_df, x="sleep_cause", y="num_people",
                 color="gender", category_orders={"sleep_cause": cause_order})

    fig.update_layout(barmode="stack",
                      xaxis_title="Sleep Disruption Cause",
                      yaxis_title="Number of People")
    
    for _, row in totals.iterrows():
        fig.add_annotation(x=row["sleep_cause"],
                           y=row["num_people"],
                           text=str(int(row["num_people"])),
                           showarrow=False,
                           yshift=8)

    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("Data")
    st.dataframe(sorted_sleep_df[["sleep_cause", "gender", "num_people"]])


############## Employment Status vs Doctor Visits ####################

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

######## connection between sleep from stress and mental health (Matt) ######## 
sleephealth = fetch_data("""SELECT sleep_desc, mental_health_id, health_desc, COUNT(*) as count
FROM health_fact JOIN sleep_fact ON health_fact.fact_id = sleep_fact.fact_id
JOIN health_dim ON health_dim.health_id = health_fact.mental_health_id
JOIN sleep_dim ON sleep_dim.sleep_id = sleep_fact.stress_sleep_id
JOIN demographics_fact ON health_fact.fact_id = demographics_fact.fact_id
JOIN gender_dim ON demographics_fact.gender_id = gender_dim.gender_id
WHERE mental_health_id <> -1
GROUP BY sleep_desc, mental_health_id, health_desc
ORDER BY mental_health_id DESC
""")

### https://docs.streamlit.io/develop/api-reference/charts/st.scatter_chart
### from https://plotly.com/python/tick-formatting/
fig= px.line(sleephealth, x="mental_health_id", y="count", color="sleep_desc", title="Is there a connection between sleep from stress and mental health?")

fig.update_layout(
    xaxis = dict(
        tickmode = 'array',
        tickvals = [1, 2, 3, 4, 5],
        ticktext = ['Excellent', 'Very Good', 'Good', 'Fair', 'Poor']
    )
)

st.plotly_chart(fig)

