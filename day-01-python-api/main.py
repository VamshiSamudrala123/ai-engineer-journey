import requests

def get_user_id():
    """Prompt the user for a valid user ID between 1 and 10."""
    while True:
        try:
            user_id = int(input("Enter a user ID (1-10): "))
            if 1 <= user_id <= 10:
                return user_id
            else:
                print("Invalid ID. Please enter a number between 1 and 10.")
        except ValueError:
            print("Invalid input. Please enter a numeric value.")

def fetch_user_data(user_id):
    """Fetch user data from the API using the provided user ID."""
    url = f"https://jsonplaceholder.typicode.com/users/{user_id}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()  # Raise an error for bad responses
        return response.json()  # Return the JSON data
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
    except requests.exceptions.RequestException as req_err:
        print(f"Network error occurred: {req_err}")
    return None

def display_user_info(user_data):
    """Display the user's name, username, email, and company name."""
    if user_data:
        print(f"Name: {user_data['name']}")
        print(f"Username: {user_data['username']}")
        print(f"Email: {user_data['email']}")
        print(f"Company: {user_data['company']['name']}")
    else:
        print("No user data to display.")

def main():
    """Main function to run the API Explorer."""
    user_id = get_user_id()  # Get a valid user ID from the user
    user_data = fetch_user_data(user_id)  # Fetch user data
    display_user_info(user_data)  # Display the user information

if __name__ == "__main__":
    main()  # Run the main function