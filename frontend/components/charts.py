"""
Reusable chart components
"""

import plotly.graph_objects as go
import pandas as pd


def create_time_series_chart(df: pd.DataFrame, title: str = "Time Series"):
    """Create a time series line chart"""
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=df['date'],
        y=df['value'],
        mode='lines',
        name=title,
        line=dict(color='blue', width=2)
    ))
    
    fig.update_layout(
        title=title,
        xaxis_title="Date",
        yaxis_title="Value",
        height=400,
        hovermode='x unified'
    )
    
    return fig


def create_bar_chart(data: dict, title: str = "Bar Chart"):
    """Create a bar chart"""
    
    fig = go.Figure(data=[
        go.Bar(
            x=list(data.keys()),
            y=list(data.values()),
            marker_color='lightblue'
        )
    ])
    
    fig.update_layout(
        title=title,
        height=400
    )
    
    return fig


def create_pie_chart(labels: list, values: list, title: str = "Distribution"):
    """Create a pie chart"""
    
    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=.3
    )])
    
    fig.update_layout(
        title=title,
        height=400
    )
    
    return fig
