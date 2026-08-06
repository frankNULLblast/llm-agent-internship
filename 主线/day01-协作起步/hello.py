import sys
from datetime import date


def main() -> None:
    print("LLM Agent Internship")
    print(f"Date: {date.today().isoformat()}")
    print(f"Python: {sys.version.split()[0]}")
    print("Environment: OK")


if __name__ == "__main__":
    main()