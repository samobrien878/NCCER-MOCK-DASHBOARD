import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from dataclasses import dataclass
from typing import Dict

# ─── Configuration ───────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Training Impact Dashboard",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ─── Constants ───────────────────────────────────────────────────────────────
PRIMARY = '#1e3a5f'
ACCENT = '#FF6B35'
SUCCESS = '#4CAF50'
INFO = '#2196F3'
WARNING = '#FF9800'
PURPLE = '#9C27B0'
CARD_BG = '#ffffff'
PAGE_BG = '#f5f7fa'

RETENTION_THRESHOLD = 12.0
COST_PER_HIRE = 1750
TRAINING_COST_PER_PERSON = 300

# ─── Custom CSS ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .stApp {
        background-color: #f5f7fa;
    }

    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 0.5rem;
        max-height: 100vh;
        overflow-y: auto;
    }

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    .element-container {
        margin-bottom: 0 !important;
    }

    /* Interactive elements */
    .stSelectbox, .stSlider {
        background: white;
        padding: 0.5rem;
        border-radius: 8px;
        box-shadow: 0 1px 4px rgba(0,0,0,0.06);
    }
</style>
""", unsafe_allow_html=True)

# ─── Data Classes ────────────────────────────────────────────────────────────
@dataclass
class MetricComparison:
    training_value: float
    control_value: float

    @property
    def difference(self) -> float:
        return self.training_value - self.control_value

    @property
    def percent_change(self) -> float:
        return (self.difference / self.control_value * 100) if self.control_value != 0 else 0

# ─── Data Loading ────────────────────────────────────────────────────────────
@st.cache_data
def load_data() -> pd.DataFrame:
    data = {
        'Company': ['Training'] * 30 + ['No Training'] * 30,
        'Months_Retained': (
            [12.0] * 21 + [11.8, 11.5, 10.9, 10.2, 9.8, 9.4, 8.7, 7.6, 6.9] +
            [12.0] * 9 + [11.2, 10.8, 9.5, 8.9, 8.1, 7.4, 6.8, 6.2, 5.5, 4.9,
             4.3, 3.8, 3.2, 2.7, 2.1, 1.8, 7.7, 8.4, 9.1, 10.3, 6.6]
        ),
        'Productivity_Rating': [
            4.7, 4.0, 5.0, 3.8, 4.6, 5.0, 4.0, 4.2, 4.4, 4.2, 3.8, 4.4, 4.0, 4.6, 4.0,
            5.0, 4.1, 4.3, 4.7, 3.9, 4.5, 4.9, 3.8, 4.5, 4.5, 4.7, 3.9, 3.9, 4.6, 4.5,
            3.5, 3.5, 2.9, 3.4, 3.5, 2.9, 4.4, 3.6, 2.6, 3.7, 2.7, 3.8, 4.0, 2.8, 3.9,
            3.5, 3.8, 4.4, 3.2, 2.8, 2.8, 2.8, 3.3, 3.5, 3.5, 3.8, 3.3, 4.2, 3.1, 4.9
        ],
        'Absenteeism_Days': [
            4, 1, 1, 4, 3, 4, 4, 3, 1, 0, 2, 5, 3, 1, 3, 4, 1, 3, 3, 1,
            4, 4, 5, 5, 0, 1, 4, 4, 4, 11,
            12, 14, 13, 12, 8, 13, 6, 9, 8, 10, 19, 2, 12, 3, 8, 14, 10, 5, 7, 12,
            7, 10, 10, 7, 18, 12, 1, 10, 7, 13
        ]
    }
    df = pd.DataFrame(data)
    df['Reached_12mo'] = df['Months_Retained'] >= RETENTION_THRESHOLD
    return df

# ─── Metrics Calculation ─────────────────────────────────────────────────────
def calculate_metrics(df: pd.DataFrame, min_retention: float = 0) -> Dict:
    # Filter by minimum retention if specified
    if min_retention > 0:
        df = df[df['Months_Retained'] >= min_retention]

    training_df = df[df['Company'] == 'Training']
    control_df = df[df['Company'] == 'No Training']

    if len(training_df) == 0 or len(control_df) == 0:
        return None

    retention_training = training_df['Reached_12mo'].sum() / len(training_df) * 100
    retention_control = control_df['Reached_12mo'].sum() / len(control_df) * 100

    training_stayed = int(training_df['Reached_12mo'].sum())
    control_stayed = int(control_df['Reached_12mo'].sum())

    # Cost per hire calculations
    training_total_cost = (len(training_df) * COST_PER_HIRE) + (len(training_df) * TRAINING_COST_PER_PERSON)
    control_total_cost = len(control_df) * COST_PER_HIRE

    # Effective cost per retained employee
    training_cost_per_retained = training_total_cost / training_stayed if training_stayed > 0 else 0
    control_cost_per_retained = control_total_cost / control_stayed if control_stayed > 0 else 0

    return {
        'retention': MetricComparison(retention_training, retention_control),
        'productivity': MetricComparison(
            training_df['Productivity_Rating'].mean(),
            control_df['Productivity_Rating'].mean()
        ),
        'absenteeism': MetricComparison(
            training_df['Absenteeism_Days'].mean(),
            control_df['Absenteeism_Days'].mean()
        ),
        'training_stayed': training_stayed,
        'control_stayed': control_stayed,
        'training_total': len(training_df),
        'control_total': len(control_df),
        'training_cost_per_retained': training_cost_per_retained,
        'control_cost_per_retained': control_cost_per_retained,
    }

# ─── KPI Card Functions ──────────────────────────────────────────────────────
def render_kpi_card(title: str, value: str, delta: str, delta_positive: bool,
                    subtitle: str = "", color: str = "#4CAF50"):
    delta_color = "#4CAF50" if delta_positive else "#f44336"
    delta_icon = "▲" if delta_positive else "▼"

    st.markdown(f"""
    <div style='background: white; padding: 1.5rem; border-radius: 12px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.08);
                border-left: 4px solid {color}; height: 145px;'>
        <div style='color: #666; font-size: 0.8rem; font-weight: 500;
                    text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 0.5rem;'>
            {title}
        </div>
        <div style='font-size: 2rem; font-weight: 700; color: #1a1a1a;
                    margin-bottom: 0.3rem; line-height: 1.2;'>
            {value}
        </div>
        <div style='display: flex; align-items: center; gap: 0.5rem; flex-wrap: wrap;'>
            <span style='color: {delta_color}; font-size: 0.9rem; font-weight: 600;'>
                {delta_icon} {delta}
            </span>
            <span style='color: #999; font-size: 0.8rem;'>
                {subtitle}
            </span>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ─── Chart Functions ─────────────────────────────────────────────────────────
def create_retention_donut(metrics: Dict) -> go.Figure:
    retention = metrics['retention']

    fig = go.Figure(data=[go.Pie(
        labels=['Retained', 'Left'],
        values=[retention.training_value, 100 - retention.training_value],
        hole=0.7,
        marker=dict(colors=[SUCCESS, '#e0e0e0']),
        textinfo='none',
        hovertemplate='<b>%{label}</b><br>%{value:.1f}%<extra></extra>',
        showlegend=True
    )])

    fig.add_annotation(
        text=f"<b>{retention.training_value:.0f}%</b>",
        x=0.5, y=0.5,
        font=dict(size=36, color='#1a1a1a'),
        showarrow=False
    )

    fig.update_layout(
        height=220,
        margin=dict(l=10, r=10, t=10, b=30),
        paper_bgcolor='white',
        plot_bgcolor='white',
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=-0.15,
            xanchor='center',
            x=0.5,
            font=dict(size=10)
        )
    )

    return fig

def create_comparison_chart(title: str, training_val: float, control_val: float,
                           metric_format: str = ".1f", color: str = "#2196F3",
                           y_range: list = None) -> go.Figure:

    fig = go.Figure()

    categories = ['Training', 'Control']
    values = [training_val, control_val]
    colors = [color, '#b0b0b0']

    fig.add_trace(go.Bar(
        x=categories,
        y=values,
        marker=dict(
            color=colors,
            line=dict(width=0)
        ),
        text=[f'{v:{metric_format}}' for v in values],
        textposition='outside',
        textfont=dict(size=16, color='#1a1a1a'),
        hovertemplate='<b>%{x}</b><br>Value: %{y' + f':{metric_format}' + '}<extra></extra>',
        textangle=0
    ))

    max_val = max(values)
    y_max = max_val * 1.25 if y_range is None else y_range[1]

    fig.update_layout(
        title=dict(
            text=title,
            font=dict(size=13, color='#666'),
            x=0,
            xanchor='left'
        ),
        height=220,
        margin=dict(l=15, r=15, t=40, b=15),
        paper_bgcolor='white',
        plot_bgcolor='white',
        xaxis=dict(showgrid=False, showline=False),
        yaxis=dict(
            showgrid=True,
            gridcolor='#f0f0f0',
            showline=False,
            zeroline=False,
            range=[0, y_max]
        ),
        showlegend=False
    )

    return fig

def create_cost_per_hire_chart(metrics: Dict) -> go.Figure:
    training_cost = metrics['training_cost_per_retained']
    control_cost = metrics['control_cost_per_retained']

    fig = go.Figure()

    categories = ['Training\n(+ $300 training)', 'Control\n(no training)']
    values = [training_cost, control_cost]
    colors = [PURPLE, '#b0b0b0']

    fig.add_trace(go.Bar(
        x=categories,
        y=values,
        marker=dict(
            color=colors,
            line=dict(width=0)
        ),
        text=[f'${v:,.0f}' for v in values],
        textposition='outside',
        textfont=dict(size=16, color='#1a1a1a'),
        hovertemplate='<b>%{x}</b><br>Cost per Retained: $%{y:,.0f}<extra></extra>',
        textangle=0
    ))

    max_val = max(values)
    y_max = max_val * 1.25

    fig.update_layout(
        title=dict(
            text='Cost per Retained Employee',
            font=dict(size=13, color='#666'),
            x=0,
            xanchor='left'
        ),
        height=220,
        margin=dict(l=15, r=15, t=40, b=15),
        paper_bgcolor='white',
        plot_bgcolor='white',
        xaxis=dict(showgrid=False, showline=False, tickfont=dict(size=10)),
        yaxis=dict(
            showgrid=True,
            gridcolor='#f0f0f0',
            showline=False,
            zeroline=False,
            range=[0, y_max]
        ),
        showlegend=False
    )

    return fig

def create_interactive_scatter(df: pd.DataFrame, highlight_group: str = None) -> go.Figure:
    fig = go.Figure()

    training_df = df[df['Company'] == 'Training']
    control_df = df[df['Company'] == 'No Training']

    opacity_training = 0.8 if highlight_group in [None, 'Training'] else 0.2
    opacity_control = 0.8 if highlight_group in [None, 'Control'] else 0.2

    fig.add_trace(go.Scatter(
        x=training_df['Productivity_Rating'],
        y=training_df['Months_Retained'],
        mode='markers',
        name='Training Group',
        marker=dict(
            size=10,
            color=INFO,
            opacity=opacity_training,
            line=dict(width=1, color='white')
        ),
        text=[f"Prod: {p:.1f}<br>Months: {r:.1f}<br>Absences: {a}"
              for p, r, a in zip(training_df['Productivity_Rating'],
                                training_df['Months_Retained'],
                                training_df['Absenteeism_Days'])],
        hovertemplate='<b>Training</b><br>%{text}<extra></extra>'
    ))

    fig.add_trace(go.Scatter(
        x=control_df['Productivity_Rating'],
        y=control_df['Months_Retained'],
        mode='markers',
        name='Control Group',
        marker=dict(
            size=10,
            color=ACCENT,
            opacity=opacity_control,
            line=dict(width=1, color='white')
        ),
        text=[f"Prod: {p:.1f}<br>Months: {r:.1f}<br>Absences: {a}"
              for p, r, a in zip(control_df['Productivity_Rating'],
                                control_df['Months_Retained'],
                                control_df['Absenteeism_Days'])],
        hovertemplate='<b>Control</b><br>%{text}<extra></extra>'
    ))

    fig.update_layout(
        title=dict(
            text='Productivity vs Retention (Individual Employees)',
            font=dict(size=14, color='#1a1a1a'),
            x=0,
            xanchor='left'
        ),
        height=280,
        margin=dict(l=15, r=15, t=50, b=15),
        paper_bgcolor='white',
        plot_bgcolor='white',
        xaxis=dict(
            title='Productivity Rating (1-5)',
            showgrid=True,
            gridcolor='#f0f0f0',
            range=[2.5, 5.2]
        ),
        yaxis=dict(
            title='Months Retained',
            showgrid=True,
            gridcolor='#f0f0f0',
            range=[0, 13]
        ),
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='right',
            x=1,
            font=dict(size=11)
        ),
        hovermode='closest'
    )

    return fig

# ─── Main Dashboard ──────────────────────────────────────────────────────────
def main():
    df = load_data()

    # Header
    st.markdown(f"""
    <div style='background: linear-gradient(135deg, {PRIMARY} 0%, #2c5282 100%);
                padding: 1.2rem 2rem; border-radius: 12px; margin-bottom: 1.2rem;
                box-shadow: 0 4px 12px rgba(0,0,0,0.1);'>
        <h1 style='color: white; margin: 0; font-size: 1.6rem; font-weight: 600;'>
            Training Impact Dashboard
        </h1>
        <p style='color: rgba(255,255,255,0.85); margin: 0.25rem 0 0 0; font-size: 0.85rem;'>
            NCCER Early Training Program • 60 Entry-Level Hires • 12-Month Analysis
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Interactive Controls
    col_filter1, col_filter2, col_filter3 = st.columns([2, 2, 2])

    with col_filter1:
        min_months = st.slider(
            "Filter by Minimum Months Retained",
            min_value=0.0,
            max_value=12.0,
            value=0.0,
            step=1.0,
            help="Filter employees who stayed at least this many months"
        )

    with col_filter2:
        highlight_group = st.selectbox(
            "Highlight Group in Scatter Plot",
            options=['Both', 'Training', 'Control'],
            help="Focus on a specific group in the scatter plot"
        )

    with col_filter3:
        show_details = st.checkbox(
            "Show Detailed Metrics",
            value=False,
            help="Display additional performance details"
        )

    metrics = calculate_metrics(df, min_months)

    if metrics is None:
        st.error("No data available for the selected filters.")
        return

    # KPI Cards Row
    col1, col2, col3, col4 = st.columns(4, gap="medium")

    retention = metrics['retention']
    productivity = metrics['productivity']
    absenteeism = metrics['absenteeism']
    extra_retained = metrics['training_stayed'] - metrics['control_stayed']
    total_savings = extra_retained * COST_PER_HIRE

    with col1:
        render_kpi_card(
            "12-MONTH RETENTION",
            f"{retention.training_value:.0f}%",
            f"{retention.difference:+.0f}pp",
            True,
            "vs control group",
            SUCCESS
        )

    with col2:
        render_kpi_card(
            "PRODUCTIVITY RATING",
            f"{productivity.training_value:.2f}",
            f"{productivity.percent_change:+.1f}%",
            True,
            "manager rated (1-5)",
            INFO
        )

    with col3:
        render_kpi_card(
            "ABSENTEEISM",
            f"{absenteeism.training_value:.1f}",
            f"{absenteeism.difference:.1f} days",
            absenteeism.difference < 0,
            "days per year",
            WARNING
        )

    with col4:
        cost_savings = metrics['control_cost_per_retained'] - metrics['training_cost_per_retained']
        render_kpi_card(
            "COST SAVINGS/EMPLOYEE",
            f"${cost_savings:,.0f}",
            f"{(cost_savings/metrics['control_cost_per_retained']*100):.1f}% reduction",
            cost_savings > 0,
            "per retained employee",
            PURPLE
        )

    st.markdown("<div style='margin: 1.2rem 0;'></div>", unsafe_allow_html=True)

    # Charts Row
    col5, col6, col7, col8 = st.columns([1, 1, 1, 1.3], gap="medium")

    with col5:
        st.markdown("""
        <div style='background: white; padding: 1rem; border-radius: 12px;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.08);'>
            <div style='font-size: 0.8rem; font-weight: 500; color: #666;
                        text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 0.5rem;'>
                TRAINING GROUP
            </div>
        """, unsafe_allow_html=True)
        st.plotly_chart(
            create_retention_donut(metrics),
            use_container_width=True,
            config={'displayModeBar': False}
        )
        st.markdown("</div>", unsafe_allow_html=True)

    with col6:
        st.markdown("""
        <div style='background: white; padding: 1rem; border-radius: 12px;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.08);'>
        """, unsafe_allow_html=True)
        st.plotly_chart(
            create_comparison_chart(
                "Productivity Rating",
                metrics['productivity'].training_value,
                metrics['productivity'].control_value,
                ".2f",
                INFO,
                [0, 5]
            ),
            use_container_width=True,
            config={'displayModeBar': False}
        )
        st.markdown("</div>", unsafe_allow_html=True)

    with col7:
        st.markdown("""
        <div style='background: white; padding: 1rem; border-radius: 12px;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.08);'>
        """, unsafe_allow_html=True)
        st.plotly_chart(
            create_cost_per_hire_chart(metrics),
            use_container_width=True,
            config={'displayModeBar': False}
        )
        st.markdown("</div>", unsafe_allow_html=True)

    with col8:
        st.markdown("""
        <div style='background: white; padding: 1rem; border-radius: 12px;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.08);'>
        """, unsafe_allow_html=True)
        highlight = None if highlight_group == 'Both' else highlight_group
        st.plotly_chart(
            create_interactive_scatter(df, highlight),
            use_container_width=True,
            config={'displayModeBar': False}
        )
        st.markdown("</div>", unsafe_allow_html=True)

    # Detailed Metrics Section
    if show_details:
        st.markdown("<div style='margin: 1.2rem 0;'></div>", unsafe_allow_html=True)
        st.markdown("""
        <div style='background: white; padding: 1.5rem; border-radius: 12px;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.08);'>
            <h3 style='margin: 0 0 1rem 0; color: #1a1a1a; font-size: 1.1rem;'>Detailed Performance Metrics</h3>
        """, unsafe_allow_html=True)

        detail_col1, detail_col2, detail_col3 = st.columns(3)

        with detail_col1:
            st.markdown(f"""
            <div style='padding: 1rem; background: {PAGE_BG}; border-radius: 8px;'>
                <h4 style='margin: 0 0 0.5rem 0; color: #666; font-size: 0.9rem;'>TRAINING GROUP</h4>
                <p style='margin: 0.3rem 0; color: #1a1a1a;'><strong>Total:</strong> {metrics['training_total']} employees</p>
                <p style='margin: 0.3rem 0; color: #1a1a1a;'><strong>Retained:</strong> {metrics['training_stayed']} ({retention.training_value:.0f}%)</p>
                <p style='margin: 0.3rem 0; color: #1a1a1a;'><strong>Initial Cost:</strong> ${COST_PER_HIRE + TRAINING_COST_PER_PERSON:,}/person</p>
                <p style='margin: 0.3rem 0; color: #1a1a1a;'><strong>Cost/Retained:</strong> ${metrics['training_cost_per_retained']:,.0f}</p>
            </div>
            """, unsafe_allow_html=True)

        with detail_col2:
            st.markdown(f"""
            <div style='padding: 1rem; background: {PAGE_BG}; border-radius: 8px;'>
                <h4 style='margin: 0 0 0.5rem 0; color: #666; font-size: 0.9rem;'>CONTROL GROUP</h4>
                <p style='margin: 0.3rem 0; color: #1a1a1a;'><strong>Total:</strong> {metrics['control_total']} employees</p>
                <p style='margin: 0.3rem 0; color: #1a1a1a;'><strong>Retained:</strong> {metrics['control_stayed']} ({retention.control_value:.0f}%)</p>
                <p style='margin: 0.3rem 0; color: #1a1a1a;'><strong>Initial Cost:</strong> ${COST_PER_HIRE:,}/person</p>
                <p style='margin: 0.3rem 0; color: #1a1a1a;'><strong>Cost/Retained:</strong> ${metrics['control_cost_per_retained']:,.0f}</p>
            </div>
            """, unsafe_allow_html=True)

        with detail_col3:
            roi_per_employee = metrics['control_cost_per_retained'] - metrics['training_cost_per_retained']
            total_roi = roi_per_employee * metrics['training_stayed']
            st.markdown(f"""
            <div style='padding: 1rem; background: {PAGE_BG}; border-radius: 8px;'>
                <h4 style='margin: 0 0 0.5rem 0; color: #666; font-size: 0.9rem;'>RETURN ON INVESTMENT</h4>
                <p style='margin: 0.3rem 0; color: #1a1a1a;'><strong>Savings/Employee:</strong> ${roi_per_employee:,.0f}</p>
                <p style='margin: 0.3rem 0; color: #1a1a1a;'><strong>Total Savings:</strong> ${total_roi:,.0f}</p>
                <p style='margin: 0.3rem 0; color: #1a1a1a;'><strong>Extra Retained:</strong> +{extra_retained} employees</p>
                <p style='margin: 0.3rem 0; color: {SUCCESS}; font-weight: 600;'><strong>ROI:</strong> {(total_roi/(metrics['training_total']*TRAINING_COST_PER_PERSON)*100):.0f}%</p>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
