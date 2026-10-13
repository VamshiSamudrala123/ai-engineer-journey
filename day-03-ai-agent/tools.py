"""Small Python tools that can be tested without a model."""


def calculate_study_time(minutes_per_day: int, days: int) -> dict:
    """Calculate available study time from whole minutes and days."""
    for name, value in (("minutes_per_day", minutes_per_day), ("days", days)):
        # bool is a subclass of int, but True is not a useful study duration.
        if type(value) is not int or value <= 0:
            raise ValueError(f"{name} must be a positive whole number.")
    if minutes_per_day > 1440:
        raise ValueError("minutes_per_day cannot exceed 1440.")
    if days > 366:
        raise ValueError("days cannot exceed 366 for this planner.")
    total_minutes = minutes_per_day * days
    return {"total_minutes": total_minutes, "total_hours": total_minutes / 60}
