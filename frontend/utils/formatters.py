"""
Data formatting utilities
"""

import pandas as pd


def format_currency(value: float, decimals: int = 2) -> str:
    """Format value as currency"""
    return f"₹{value:,.{decimals}f}"


def format_percentage(value: float, decimals: int = 2) -> str:
    """Format value as percentage"""
    return f"{value*100:.{decimals}f}%"


def format_number(value: float, decimals: int = 2) -> str:
    """Format number with commas"""
    return f"{value:,.{decimals}f}"


def truncate_text(text: str, max_length: int = 50) -> str:
    """Truncate long text"""
    return text[:max_length] + "..." if len(text) > max_length else text


def format_date(date_str: str, format: str = "%Y-%m-%d") -> str:
    """Format date string"""
    try:
        date_obj = pd.to_datetime(date_str)
        return date_obj.strftime(format)
    except:
        return date_str
