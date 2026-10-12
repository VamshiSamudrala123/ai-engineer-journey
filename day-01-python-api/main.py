import requests
import csv
import os

# Base URL for the API
BASE_URL = "https://jsonplaceholder.typicode.com/users"
TIMEOUT = 10  # Timeout for HTTP requests in seconds

def fetch_user_by_id(user_id):
    """Fetch a user by ID from the API."""
    try:
        response = requests.get(f"{BASE_URL}/{user_id}", timeout=TIMEOUT)
        response.raise_for_status()
        user = response.json()
        display_user(user)
    except requests.exceptions.RequestException as e:
        print(f"Error fetching user by ID: {e}")
    except ValueError:
        print("Invalid response from the server.")

def fetch_all_users():
    """Fetch all users from the API."""
    try:
        response = requests.get(BASE_URL, timeout=TIMEOUT)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching all users: {e}")
        return []

def display_user(user):
    """Display user details."""
    print("\nUser Details:")
    print(f"Name: {user.get('name')}")
    print(f"Username: {user.get('username')}")
    print(f"Email: {user.get('email')}")
    print(f"Company: {user.get('company', {}).get('name')}\n")

def search_users_by_name(users, name):
    """Search users by name (case-insensitive, partial match)."""
    results = [user for user in users if name.lower() in user['name'].lower()]
    if results:
        print("\nSearch Results:")
        for user in results:
            display_user(user)
    else:
        print("\nNo users found with that name.")

def export_users_to_csv(users):
    """Export users to a CSV file."""
    os.makedirs("exports", exist_ok=True)
    filepath = "exports/users.csv"
    try:
        with open(filepath, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(["ID", "Name", "Username", "Email", "Company"])
            for user in users:
                writer.writerow([
                    user.get("id"),
                    user.get("name"),
                    user.get("username"),
                    user.get("email"),
                    user.get("company", {}).get("name")
                ])
        print(f"\nUsers exported to {filepath}")
    except IOError as e:
        print(f"Error writing to CSV file: {e}")

def main_menu():
    """Display the main menu and handle user input."""
    while True:
        print("\nMenu:")
        print("1. View user by ID")
        print("2. View all users")
        print("3. Search by name")
        print("4. Export users to CSV")
        print("5. Exit")
        choice = input("Enter your choice: ")

        if choice == "1":
            user_id = input("Enter user ID (1-10): ")
            if user_id.isdigit() and 1 <= int(user_id) <= 10:
                fetch_user_by_id(user_id)
            else:
                print("Invalid user ID. Please enter a number between 1 and 10.")
        elif choice == "2":
            users = fetch_all_users()
            if users:
                for user in users:
                    display_user(user)
        elif choice == "3":
            name = input("Enter name to search: ")
            users = fetch_all_users()
            if users:
                search_users_by_name(users, name)
        elif choice == "4":
            users = fetch_all_users()
            if users:
                export_users_to_csv(users)
        elif choice == "5":
            print("Exiting the program. Goodbye!")
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main_menu()