import pandas as pd
import dash
from dash import html, dcc
from dash.dependencies import Input, Output
import plotly.express as px

# Load the SpaceX launch data from a CSV file into a pandas DataFrame
# This DataFrame will be used throughout the app to generate charts
spacex_df = pd.read_csv("spacex_launch_dash.csv")

# Find the maximum and minimum payload values in the dataset
# These will be used to set the boundaries of the payload slider
max_payload = spacex_df['Payload Mass (kg)'].max()
min_payload = spacex_df['Payload Mass (kg)'].min()

# Create the Dash app instance
# This is the core object that runs the web application
app = dash.Dash(__name__)

# ---------------------------------------------------------------------------
# LAYOUT
# The layout defines what the user sees on the page.
# html.Div is like a <div> in HTML — a container for grouping elements.
# We nest components inside it to build the page structure.
# ---------------------------------------------------------------------------
app.layout = html.Div(children=[

    # Page title displayed at the top of the dashboard
    html.H1('SpaceX Launch Records Dashboard',
            style={'textAlign': 'center', 'color': '#503D36', 'font-size': 40}),

    # -------------------------------------------------------------------------
    # TASK 1: Dropdown menu for selecting a launch site
    # dcc.Dropdown creates an interactive dropdown list
    # - id: a unique name used to link this component to a callback function
    # - options: the list of choices shown in the dropdown
    #     * First option is 'ALL' to show data for every site
    #     * The rest are generated from the unique launch sites in the dataset
    # - value: the default selected value when the page loads
    # - placeholder: the grey hint text shown before a selection is made
    # - searchable: allows the user to type to filter options
    # -------------------------------------------------------------------------
    dcc.Dropdown(
        id='site-dropdown',
        options=[{'label': 'All Sites', 'value': 'ALL'}] +
                [{'label': site, 'value': site} for site in spacex_df['Launch Site'].unique()],
        value='ALL',
        placeholder='Select a Launch Site here',
        searchable=True
    ),
    html.Br(),  # Adds a blank line (line break) for spacing

    # Placeholder for the pie chart — it will be filled in by the callback (Task 2)
    html.Div(dcc.Graph(id='success-pie-chart')),
    html.Br(),

    html.P("Payload range (Kg):"),  # Label text above the slider

    # -------------------------------------------------------------------------
    # TASK 3: Range slider to filter launches by payload mass
    # dcc.RangeSlider creates a slider with two handles (low and high)
    # - id: used to connect this slider to the scatter chart callback (Task 4)
    # - min / max: the overall range of the slider (0 to 10,000 kg)
    # - step: how much the value changes with each tick (1,000 kg increments)
    # - marks: labels shown at specific points along the slider
    # - value: the default selected range when the page loads
    #     (set to the actual min and max payload in the dataset)
    # -------------------------------------------------------------------------
    dcc.RangeSlider(
        id='payload-slider',
        min=0,
        max=10000,
        step=1000,
        marks={i: str(i) for i in range(0, 10001, 2500)},
        value=[min_payload, max_payload]
    ),

    # Placeholder for the scatter chart — filled in by the callback (Task 4)
    html.Div(dcc.Graph(id='success-payload-scatter-chart')),
])


# ---------------------------------------------------------------------------
# CALLBACKS
# Callbacks are functions that run automatically when a user interacts with
# a component (e.g. selects a dropdown option or moves the slider).
#
# @app.callback connects:
#   - Output: the component that will be UPDATED (e.g. a chart)
#   - Input:  the component that TRIGGERS the update (e.g. a dropdown)
#
# When the Input changes, Dash calls the function below automatically
# and passes the new value as an argument.
# ---------------------------------------------------------------------------

# TASK 2: Update the pie chart when the user selects a launch site
@app.callback(
    Output(component_id='success-pie-chart', component_property='figure'),
    Input(component_id='site-dropdown', component_property='value')
)
def get_pie_chart(entered_site):
    # 'entered_site' is whatever the user selected in the dropdown

    if entered_site == 'ALL':
        # Show total successful launches (class=1) across all sites
        # Each slice of the pie represents one launch site
        fig = px.pie(
            spacex_df,
            values='class',        # 1 = success, 0 = failure; sum per site
            names='Launch Site',   # One slice per launch site
            title='Total Successful Launches by Site'
        )
    else:
        # Filter the data to only include rows for the selected site
        filtered_df = spacex_df[spacex_df['Launch Site'] == entered_site]

        # Count how many successes (1) and failures (0) there are
        site_counts = filtered_df['class'].value_counts().reset_index()
        site_counts.columns = ['class', 'count']

        # Replace 0/1 with readable labels for the chart legend
        site_counts['outcome'] = site_counts['class'].map({1: 'Success', 0: 'Failure'})

        # Show a pie chart of Success vs Failure for this specific site
        fig = px.pie(
            site_counts,
            values='count',
            names='outcome',
            title=f'Success vs Failure for {entered_site}'
        )

    return fig  # Dash sends this figure to the 'success-pie-chart' Graph component


# TASK 4: Update the scatter chart when the user changes the site or payload slider
@app.callback(
    Output(component_id='success-payload-scatter-chart', component_property='figure'),
    [Input(component_id='site-dropdown', component_property='value'),
     Input(component_id='payload-slider', component_property='value')]
    # Two inputs this time — both trigger the function when changed
)
def get_scatter_chart(entered_site, payload_range):
    # 'payload_range' is a list [low, high] from the range slider
    low, high = payload_range

    # Filter the dataset to only include launches within the selected payload range
    filtered_df = spacex_df[
        (spacex_df['Payload Mass (kg)'] >= low) &
        (spacex_df['Payload Mass (kg)'] <= high)
    ]

    # If a specific site is selected, filter further to that site only
    if entered_site != 'ALL':
        filtered_df = filtered_df[filtered_df['Launch Site'] == entered_site]

    # Create a scatter plot:
    # - x axis: payload mass
    # - y axis: outcome (1 = success, 0 = failure)
    # - colour: booster version, so you can spot patterns by rocket type
    fig = px.scatter(
        filtered_df,
        x='Payload Mass (kg)',
        y='class',
        color='Booster Version Category',
        title='Payload vs Launch Outcome',
        labels={'class': 'Launch Outcome (1=Success, 0=Failure)'}
    )

    return fig  # Dash sends this figure to the 'success-payload-scatter-chart' Graph component


# ---------------------------------------------------------------------------
# Run the app
# This starts the local web server. Open http://127.0.0.1:8050/ in your browser.
# The 'if __name__ == "__main__"' guard ensures this only runs when you
# execute the file directly (not when it's imported by another script).
# ---------------------------------------------------------------------------
if __name__ == '__main__':
    app.run()
    
    
# =============================================================================
# DASHBOARD ANALYSIS FINDINGS
# =============================================================================

# 1. Which site has the largest successful launches?
#    Answer: KSC LC-39A (41.7%) has the largest number of successful launches based on the pie chart.

# 2. Which site has the highest launch success rate?
#    Answer: KSC LC-39A has the highest launch success rate at 76.9%.

# 3. Which payload range(s) has the highest launch success rate?
#    Answer: Payloads between 2,000–4,000 kg show the highest success rate.

# 4. Which payload range(s) has the lowest launch success rate?
#    Answer: Payloads above 6,000 kg show more failures.

# 5. Which F9 Booster version has the highest launch success rate?
#    Answer: FT booster version shows the highest success rate.