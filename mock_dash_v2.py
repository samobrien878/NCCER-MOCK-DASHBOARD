import pandas as pd
import plotly.graph_objects as go
from dash import Dash, html, dcc, Input, Output, callback, callback_context
import numpy as np

# NCCER Color Scheme
NCCER_NAVY = '#172535'
NCCER_ORANGE = '#FD6A3C'
NCCER_LIGHT_BLUE = '#A1C5D3'
NCCER_DARK_GRAY = '#32373c'
NCCER_WHITE = '#FFFFFF'
NCCER_LIGHT_GRAY = '#EEEEEE'

# Load data
df = pd.read_csv('FAKE_NCCER_DATAV2.csv')

# Rename Control to No Training
df['Company'] = df['Company'].replace('Control', 'No Training')

# Adjust retention data to be normally distributed around 12 months for training group
np.random.seed(42)
training_indices = df[df['Company'] == 'Training'].index
df.loc[training_indices, 'Months_Retained'] = np.random.normal(12, 1.5, len(training_indices))
df.loc[training_indices, 'Months_Retained'] = df.loc[training_indices, 'Months_Retained'].clip(0, 12)

# Generate cost per hire data (realistic construction industry costs)
training_cost_per_hire = np.random.normal(3500, 400, len(df[df['Company'] == 'Training']))
no_training_cost_per_hire = np.random.normal(4800, 500, len(df[df['Company'] == 'No Training']))

df.loc[df['Company'] == 'Training', 'Cost_Per_Hire'] = training_cost_per_hire
df.loc[df['Company'] == 'No Training', 'Cost_Per_Hire'] = no_training_cost_per_hire

# Calculate metrics by group
training_group = df[df['Company'] == 'Training']
control_group = df[df['Company'] == 'No Training']

# Average months retained
training_retention = training_group['Months_Retained'].mean()
control_retention = control_group['Months_Retained'].mean()
retention_diff = training_retention - control_retention

# Average productivity
training_productivity = training_group['Productivity_Rating'].mean()
control_productivity = control_group['Productivity_Rating'].mean()
productivity_diff = ((training_productivity - control_productivity) / control_productivity) * 100

# Average cost per hire
training_cost = training_group['Cost_Per_Hire'].mean()
control_cost = control_group['Cost_Per_Hire'].mean()
cost_diff = ((control_cost - training_cost) / control_cost) * 100  # Positive = savings

# Initialize Dash app
app = Dash(__name__)
server = app.server  # Expose the server for deployment

# Custom CSS
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <style>
            body {
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
                margin: 0;
                padding: 0;
                background-color: #f5f5f5;
            }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

# Layout
app.layout = html.Div([
    # Header
    html.Div([
        html.H1('NCCER Early Training Effects Dashboard',
                style={
                    'textAlign': 'center',
                    'color': NCCER_WHITE,
                    'padding': '30px',
                    'margin': '0',
                    'fontSize': '42px',
                    'fontWeight': '600'
                })
    ], style={'backgroundColor': NCCER_NAVY}),

    # Metric Buttons Container
    html.Div([
        # Retention Button
        html.Div([
            html.Button([
                html.Div([
                    html.Div(f'+{retention_diff:.1f} months',
                             style={'fontSize': '48px', 'fontWeight': 'bold', 'color': NCCER_WHITE, 'marginBottom': '10px'}),
                    html.Div('Longer Average Retention',
                             style={'fontSize': '18px', 'color': NCCER_LIGHT_GRAY, 'marginBottom': '5px'}),
                    html.Div(f'Training: {training_retention:.1f} months vs No Training: {control_retention:.1f} months',
                             style={'fontSize': '14px', 'color': NCCER_LIGHT_BLUE})
                ])
            ], id='retention-btn', n_clicks=0, style={
                'width': '100%',
                'padding': '30px',
                'backgroundColor': NCCER_ORANGE,
                'border': 'none',
                'borderRadius': '12px',
                'cursor': 'pointer',
                'transition': 'all 0.3s ease',
                'boxShadow': '0 4px 6px rgba(0,0,0,0.1)'
            })
        ], style={'flex': '1', 'margin': '0 10px'}),

        # Productivity Button
        html.Div([
            html.Button([
                html.Div([
                    html.Div(f'+{productivity_diff:.1f}%',
                             style={'fontSize': '48px', 'fontWeight': 'bold', 'color': NCCER_WHITE, 'marginBottom': '10px'}),
                    html.Div('Higher Productivity Rating',
                             style={'fontSize': '18px', 'color': NCCER_LIGHT_GRAY, 'marginBottom': '5px'}),
                    html.Div(f'Training: {training_productivity:.2f} vs No Training: {control_productivity:.2f}',
                             style={'fontSize': '14px', 'color': NCCER_LIGHT_BLUE})
                ])
            ], id='productivity-btn', n_clicks=0, style={
                'width': '100%',
                'padding': '30px',
                'backgroundColor': NCCER_DARK_GRAY,
                'border': 'none',
                'borderRadius': '12px',
                'cursor': 'pointer',
                'transition': 'all 0.3s ease',
                'boxShadow': '0 4px 6px rgba(0,0,0,0.1)'
            })
        ], style={'flex': '1', 'margin': '0 10px'}),

        # Cost Per Hire Button
        html.Div([
            html.Button([
                html.Div([
                    html.Div(f'-${control_cost - training_cost:.0f}',
                             style={'fontSize': '48px', 'fontWeight': 'bold', 'color': NCCER_WHITE, 'marginBottom': '10px'}),
                    html.Div('Lower Average Cost Per Hire',
                             style={'fontSize': '18px', 'color': NCCER_LIGHT_GRAY, 'marginBottom': '5px'}),
                    html.Div(f'Training: ${training_cost:.0f} vs No Training: ${control_cost:.0f}',
                             style={'fontSize': '14px', 'color': NCCER_LIGHT_BLUE})
                ])
            ], id='cost-btn', n_clicks=0, style={
                'width': '100%',
                'padding': '30px',
                'backgroundColor': NCCER_NAVY,
                'border': 'none',
                'borderRadius': '12px',
                'cursor': 'pointer',
                'transition': 'all 0.3s ease',
                'boxShadow': '0 4px 6px rgba(0,0,0,0.1)'
            })
        ], style={'flex': '1', 'margin': '0 10px'}),

    ], style={
        'display': 'flex',
        'justifyContent': 'space-around',
        'padding': '40px 20px',
        'maxWidth': '1400px',
        'margin': '0 auto'
    }),

    # Graphs Container
    html.Div([
        # Bar Chart
        html.Div([
            dcc.Graph(id='bar-chart', style={'height': '500px'})
        ], style={'flex': '1', 'margin': '0 10px', 'backgroundColor': NCCER_WHITE, 'borderRadius': '12px', 'padding': '20px', 'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'}),

        # Line Chart
        html.Div([
            dcc.Graph(id='line-chart', style={'height': '500px'})
        ], style={'flex': '1', 'margin': '0 10px', 'backgroundColor': NCCER_WHITE, 'borderRadius': '12px', 'padding': '20px', 'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'}),

    ], style={
        'display': 'flex',
        'padding': '20px',
        'maxWidth': '1400px',
        'margin': '0 auto'
    }),

    # Store for tracking active metric
    dcc.Store(id='active-metric', data='retention')

], style={'backgroundColor': '#f5f5f5', 'minHeight': '100vh'})

# Callback to update graphs based on button clicks
@callback(
    [Output('bar-chart', 'figure'),
     Output('line-chart', 'figure'),
     Output('active-metric', 'data'),
     Output('retention-btn', 'style'),
     Output('productivity-btn', 'style'),
     Output('cost-btn', 'style')],
    [Input('retention-btn', 'n_clicks'),
     Input('productivity-btn', 'n_clicks'),
     Input('cost-btn', 'n_clicks')],
    prevent_initial_call=False
)
def update_graphs(retention_clicks, productivity_clicks, cost_clicks):
    # Determine which button was clicked
    ctx = callback_context
    if not ctx.triggered:
        active_metric = 'retention'
    else:
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
        if button_id == 'retention-btn':
            active_metric = 'retention'
        elif button_id == 'productivity-btn':
            active_metric = 'productivity'
        elif button_id == 'cost-btn':
            active_metric = 'cost'
        else:
            active_metric = 'retention'

    # Define metric configurations
    metrics = {
        'retention': {
            'column': 'Months_Retained',
            'title': 'Average Retention Duration by Company',
            'y_label': 'Average Months Retained',
            'aggregation': 'mean',
            'multiply': 1,
            'format': '.1f'
        },
        'productivity': {
            'column': 'Productivity_Rating',
            'title': 'Average Productivity Rating by Company',
            'y_label': 'Productivity Rating',
            'aggregation': 'mean',
            'multiply': 1,
            'format': '.2f'
        },
        'cost': {
            'column': 'Cost_Per_Hire',
            'title': 'Average Cost Per Hire by Company',
            'y_label': 'Cost Per Hire ($)',
            'aggregation': 'mean',
            'multiply': 1,
            'format': ',.0f'
        }
    }

    metric_config = metrics[active_metric]

    # Calculate data by company
    company_data = df.groupby('Company')[metric_config['column']].mean() * metric_config['multiply']

    # Create bar chart
    bar_fig = go.Figure()

    colors = [NCCER_ORANGE if company == 'Training' else NCCER_NAVY for company in company_data.index]

    bar_fig.add_trace(go.Bar(
        x=company_data.index,
        y=company_data.values,
        marker_color=colors,
        text=[f"{val:{metric_config['format']}}" for val in company_data.values],
        textposition='outside',
        textfont=dict(size=16, color=NCCER_NAVY)
    ))

    bar_fig.update_layout(
        title=dict(text=metric_config['title'], font=dict(size=20, color=NCCER_NAVY)),
        xaxis_title='Company',
        yaxis_title=metric_config['y_label'],
        plot_bgcolor=NCCER_WHITE,
        paper_bgcolor=NCCER_WHITE,
        font=dict(size=14, color=NCCER_NAVY),
        showlegend=False,
        margin=dict(t=80, b=60, l=60, r=40),
        xaxis=dict(showgrid=False),
        yaxis=dict(
            gridcolor=NCCER_LIGHT_GRAY,
            range=[0, max(company_data.values) * 1.15]
        )
    )

    # Create distribution chart (violin plot)
    line_fig = go.Figure()

    for company in ['Training', 'No Training']:
        company_df = df[df['Company'] == company]
        values = company_df[metric_config['column']].values * metric_config['multiply']

        line_fig.add_trace(go.Violin(
            y=values,
            name=company,
            box_visible=False,
            meanline_visible=False,
            points=False,
            fillcolor=NCCER_ORANGE if company == 'Training' else NCCER_LIGHT_BLUE,
            opacity=0.7,
            line_color=NCCER_ORANGE if company == 'Training' else NCCER_NAVY
        ))

    line_fig.update_layout(
        title=dict(text=f'{metric_config["title"].replace("by Company", "")}Distribution', font=dict(size=20, color=NCCER_NAVY)),
        yaxis_title=metric_config['y_label'],
        plot_bgcolor=NCCER_WHITE,
        paper_bgcolor=NCCER_WHITE,
        font=dict(size=14, color=NCCER_NAVY),
        showlegend=True,
        margin=dict(t=80, b=60, l=60, r=40),
        xaxis=dict(showgrid=False),
        yaxis=dict(gridcolor=NCCER_LIGHT_GRAY),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )

    # Update button styles
    base_style = {
        'width': '100%',
        'padding': '30px',
        'border': 'none',
        'borderRadius': '12px',
        'cursor': 'pointer',
        'transition': 'all 0.3s ease',
        'boxShadow': '0 4px 6px rgba(0,0,0,0.1)'
    }

    retention_style = {**base_style, 'backgroundColor': NCCER_ORANGE if active_metric == 'retention' else NCCER_DARK_GRAY}
    productivity_style = {**base_style, 'backgroundColor': NCCER_ORANGE if active_metric == 'productivity' else NCCER_DARK_GRAY}
    cost_style = {**base_style, 'backgroundColor': NCCER_ORANGE if active_metric == 'cost' else NCCER_DARK_GRAY}

    return bar_fig, line_fig, active_metric, retention_style, productivity_style, cost_style

if __name__ == '__main__':
    app.run_server(debug=True, port=8050)
