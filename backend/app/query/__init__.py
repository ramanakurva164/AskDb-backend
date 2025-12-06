# app/query/__init__.py
"""
Query planning & SQL building utilities.
"""

from .builder import build_sql_from_plan

__all__ = ["build_sql_from_plan"]
