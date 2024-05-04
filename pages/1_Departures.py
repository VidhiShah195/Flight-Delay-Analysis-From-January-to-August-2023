import streamlit as st
import pandas as pd
import plotly.express as px
import base64
import plotly.graph_objects as go

st.set_page_config(
    page_title="Departure Analysis",
    page_icon='✈️'
    )


# added cache to ensure that the data doesn't have to be reloaded everytime the file runs.
@st.cache_data
def load_data(csv):
    return pd.read_csv(csv)

flights_data = load_data("Flight_delay.csv/flights_sample_3m.csv")

with open("Flight_delay.csv/take-off.gif", "rb") as f:
    gif_data = f.read()
gif_base64 = base64.b64encode(gif_data).decode()

# creates a centrerd layout with the gif and tile being in the same line and there being 10 pixels of space between the gif and title.
st.markdown(
    f"""
    <div style="display: flex; justify-content: center; align-items: center;">
        <img src="data:image/gif;base64,{gif_base64}" alt="gif" width="100">
        <h1 style="margin-left: 10px;"> Departure Analysis</h1>
    </div>
    """,
    unsafe_allow_html=True
)
# making a gray horizontal line under my title for a visual division.
st.markdown("<hr style='border: 1px solid #f0f0f0;'>", unsafe_allow_html=True)



# Display select boxes
selected_airport_dep = st.selectbox('Select Departure Airport', sorted(flights_data['ORIGIN'].unique()))
# Filter airlines based on selected airport
filtered_airlines = flights_data[flights_data['ORIGIN'] == selected_airport_dep]['AIRLINE'].unique()
selected_airline_dep = st.selectbox('Select Airline', sorted(filtered_airlines))



# BUSIEST DEPARTURE TIMES
st.subheader(f'Overall Busiest Departure Times at {selected_airport_dep} with {selected_airline_dep}')

# converting departure time to datetime forma and then extracting hour from departure time.
flights_data['CRS_DEP_TIME'] = pd.to_datetime(flights_data['CRS_DEP_TIME'], format='%H%M', errors='coerce')
flights_data['DepHour'] = flights_data['CRS_DEP_TIME'].dt.hour

# filtering data based on user's selected airport and airline.
filtered_data_dep = flights_data[(flights_data['ORIGIN'] == selected_airport_dep) & (flights_data['AIRLINE'] == selected_airline_dep)]

# counting occurrences of each departure hour.
departure_counts = filtered_data_dep['DepHour'].value_counts().sort_index()

# Define the hours and initialize departure counts for all hours
hours = [(f'{h % 12 if h % 12 != 0 else 12} {"AM" if h < 12 else "PM"}') for h in range(24)]
departure_counts_all_hours = {hour: 0 for hour in range(24)}

# Count occurrences of each departure hour
for hour, count in departure_counts.items():
    departure_counts_all_hours[hour] = count

# Make the bar chart
fig1 = px.bar(x=hours, y=[departure_counts_all_hours[hour] for hour in range(24)],
              labels={'x': 'Departure Hour', 'y': 'Number of Flights'},
              title=f'Busiest Departure Times from {selected_airport_dep} with {selected_airline_dep}')

# Formatting x-axis to display in AM/PM format
fig1.update_xaxes(tickmode='array')

# Adding a tooltip
fig1.update_traces(hovertemplate='<b>Departure Hour:</b> %{x}<br><b>Number of Flights:</b> %{y}<extra></extra>', marker_color='#048092')
st.plotly_chart(fig1)



st.subheader("Flight Status Distribution")

# renaming my columns so that I can use it later to make sure its easy for my users 
filtered_data_dep.rename(columns={'DELAY_DUE_CARRIER': 'Carrier Delay','DELAY_DUE_WEATHER': 'Weather Delay',
                              'DELAY_DUE_NAS': 'NAS Delay','DELAY_DUE_SECURITY': 'Security Delay',
                              'DELAY_DUE_LATE_AIRCRAFT': 'Late Aircraft Delay'}, inplace=True)

# calculating flight count for cancelled, delayed and or diverted flights.
flight_status_counts = {
    "Cancelled": filtered_data_dep['CANCELLED'].sum(),
    "Delayed": filtered_data_dep[filtered_data_dep['DEP_DELAY'] > 0].shape[0],
    "On time": filtered_data_dep[(filtered_data_dep['CANCELLED'] == 0) & (filtered_data_dep['DEP_DELAY'] <= 0)].shape[0]
}

if all(count == 0 for count in flight_status_counts.values()):
    st.write("No flights were delayed, cancelled, or diverted.")
else:
    st.write(f"The donut chart below shows the percent of flights departing from {selected_airport_dep} airport on {selected_airline_dep} that were on time, or experienced delays and/or cancellations.")
    # making the bigger pie chart with flight overall status.
    fig3 = go.Figure()

    fig3.add_trace(go.Pie(
        labels=list(flight_status_counts.keys()),
        values=list(flight_status_counts.values()),
        textinfo='label+percent', 
        hole=0.5,
        hovertemplate='<b>Flight Status:</b> %{label}<br>' + '<b>Value:</b> %{value}<br>' + '<b>Percent of Total:</b> %{percent}'))
    fig3.update_layout(
        title_text="Flight Status Distribution")
    st.plotly_chart(fig3, use_container_width=True, center=True)



    st.subheader("Average Dalay caused by Each Delay Type")
    st.write(f"The donut chart below shows the the percent of flights departing from {selected_airport_dep} airport on {selected_airline_dep} that experienced delays due to specific delay types. Hover over the chart to view the average delay time (in minutes) caused by each delay type.")
    st.markdown("<b>Note:</b> A flight can be delayed due to more than one reason and in a few cases, the reason for delay was not reported so some discrepencies are viable.", unsafe_allow_html=True)
    
    fig4 = go.Figure()

    # Filter the data to include only rows where DEP_DELAY is positive
    pos_delay = filtered_data_dep[filtered_data_dep['DEP_DELAY'] > 0]

    # Count delay types where DEP_DELAY is positive
    delay_counts = pos_delay[['Carrier Delay', 'Weather Delay', 'NAS Delay', 'Security Delay', 'Late Aircraft Delay']].apply(lambda x: (x > 0).sum())

    # Calculate average delay times for each delay category
    avg_delay_times = pos_delay[['Carrier Delay', 'Weather Delay', 'NAS Delay', 'Security Delay', 'Late Aircraft Delay']].mean()

    fig4.add_trace(go.Pie(
        labels=delay_counts.index,
        values=delay_counts.values,
        textinfo='label+percent', 
        hole=0.5,
        hovertemplate='<b>Cause of Delay:</b> %{label}<br>' + '<b>Average Delay Time:</b> ' + avg_delay_times.round(2).astype(str) + ' minutes <br>' + '<b>Percent of Total:</b> %{percent}',        
        marker=dict(colors=['#FF2B2B', '#7DEFA1', '#29B09D', '#FFD16A','#FF8700'])))
    fig4.update_layout(
        title_text="Average Delay Times by Delay Type")
    st.plotly_chart(fig4, use_container_width=True, center=True) 