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

################ Doctor Visits by Race ######################

st.header("Doctor Visits by Race")

race_query = f"""
SELECT 
    r.race_desc AS race, 
    COUNT(*) AS num_people 
FROM health_fact h 
JOIN demographics_fact d ON h.fact_id = d.fact_id 
JOIN race_dim r ON d.race_id = r.race_id 
JOIN gender_dim g ON d.gender_id = g.gender_id 
{where_clause} 
GROUP BY r.race_desc 
ORDER BY num_people DESC;
"""

race_df = fetch_data(race_query)

# Fixed color map for races
race_color_map = {
    "White, Non-Hispanic": "#1f77b4",
    "Black, Non-Hispanic": "#ff7f0e",
    "Other, Non-Hispanic'": "#2ca02c",
    "Hispanic": "#d62728",
    "2+ Races, Non-Hispanic": "#9467bd"
}

col5, col6 = st.columns([2, 1])

with col5:
    st.subheader("Doctor Visits Distribution by Race")
    
    fig = px.pie(
        race_df,
        names="race",
        values="num_people",
        color="race",  # 
        color_discrete_map=race_color_map  # 
    )
    
    fig.update_traces(textinfo='percent+label')
    st.plotly_chart(fig, use_container_width=True)

with col6:
    st.subheader("Data")
    sorted_race_df = race_df.sort_values(by="num_people", ascending=False).reset_index(drop=True)
    st.dataframe(sorted_race_df)

################ Sleep from Stress vs Mental Health ######################

st.header("Sleep from Stress and Mental Health")

sleep_query = f"""
SELECT 
    sleep_desc, 
    mental_health_id, 
    health_desc, 
    COUNT(*) AS count
FROM health_fact
JOIN sleep_fact ON health_fact.fact_id = sleep_fact.fact_id
JOIN health_dim ON health_dim.health_id = health_fact.mental_health_id
JOIN sleep_dim ON sleep_dim.sleep_id = sleep_fact.stress_sleep_id
JOIN demographics_fact d ON health_fact.fact_id = d.fact_id
JOIN gender_dim g ON d.gender_id = g.gender_id
{where_clause}
AND health_fact.mental_health_id <> -1
GROUP BY sleep_desc, mental_health_id, health_desc
ORDER BY mental_health_id DESC
"""

sleephealth_df = fetch_data(sleep_query)

sleephealth_df["total_per_sleep"] = sleephealth_df.groupby("sleep_desc")["count"].transform("sum")
sleephealth_df["percent"] = (sleephealth_df["count"] / sleephealth_df["total_per_sleep"]) * 100

sorted_sleephealth_df = sleephealth_df.sort_values(
    by=["sleep_desc", "mental_health_id"]
).reset_index(drop=True)

col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Mental Health Distribution Within Each Sleep Group (%)")

    fig = px.line(
        sorted_sleephealth_df,
        x="mental_health_id",
        y="percent",
        color="sleep_desc",
        markers=True,
        text=sorted_sleephealth_df["percent"].round(1)
    )

    fig.update_layout(
        xaxis=dict(
            tickmode="array",
            tickvals=[1, 2, 3, 4, 5],
            ticktext=["Excellent", "Very Good", "Good", "Fair", "Poor"]
        ),
        xaxis_title="Mental Health",
        yaxis_title="Percentage (%)",
        legend_title_text="Sleep trouble due to stress"
    )

    fig.update_traces(
        textposition="top center",
        selector=dict(name="No")
    )

    fig.update_traces(
        textposition="bottom center",
        selector=dict(name="Yes")
    )

    fig.update_traces(texttemplate="%{text}%")

    st.plotly_chart(fig, use_container_width=True)


with col2:
    st.subheader("Data")

    display_df = sorted_sleephealth_df.sort_values(
        by=["sleep_desc", "mental_health_id"]
    ).reset_index(drop=True)[[
        "sleep_desc", "health_desc", "count", "percent"
    ]].copy()

    display_df["percent"] = display_df["percent"].round(2)

    st.dataframe(display_df)
