# Python API Explorer

This project is a simple Python application that allows users to explore user data from a public API. It prompts the user for an ID between 1 and 10 and retrieves information about the user, including their name, username, email, and company name.

## Features

- Prompts the user for a valid ID.
- Fetches user data from the API: `https://jsonplaceholder.typicode.com/users/{id}`.
- Displays the user's name, username, email, and company name.
- Handles invalid user IDs and network errors gracefully.
- Sets a timeout for requests to ensure the application remains responsive.

## Requirements

- Python 3.x
- requests library

## Installation

1. Clone the repository or download the project files.
2. Navigate to the project directory.
3. Install the required dependencies by running:

```
pip install -r requirements.txt
```

## Usage

To run the application, execute the following command in your terminal:

```
python main.py
```

Follow the prompts to enter a user ID between 1 and 10, and the application will display the corresponding user information.

## License

This project is open-source and available for anyone to use and modify.