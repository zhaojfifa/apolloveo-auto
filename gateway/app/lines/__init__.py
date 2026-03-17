"""ApolloVeo 2.0 Production Line Registry.

Each production line is a self-contained business execution unit that targets
a single primary result (final_video). Lines are registered at import time and
can be looked up by line_id or task_kind.

Usage:
    from gateway.app.lines.base import LineRegistry
    line = LineRegistry.get("hot_follow_line")

See RFC-0001 for the full ProductionLine contract specification.
"""
