"""V1: call the study-time calculator directly, without Gemini."""

from tools import calculate_study_time


def main():
    try:
        minutes = int(input("How many minutes can you study each day? "))
        days = int(input("For how many days? "))
        result = calculate_study_time(minutes, days)
    except (EOFError, KeyboardInterrupt):
        print("\nGoodbye!")
        return 0
    except ValueError as error:
        print(f"Invalid input: {error}")
        return 1
    print(f"You have {result['total_minutes']} minutes ({result['total_hours']:g} hours).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
