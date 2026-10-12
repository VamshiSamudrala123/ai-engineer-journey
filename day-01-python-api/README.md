# Python API Explorer (V2)

## Overview
This project is a beginner-friendly Python application that interacts with a public API to fetch and display user data. It now includes additional features like viewing all users, searching by name, and exporting data to a CSV file.

## Features
1. View user details by ID (1-10).
2. View all users.
3. Search users by name (case-insensitive, partial match).
4. Export all users to a CSV file (`exports/users.csv`).
5. Graceful error handling for invalid inputs and network issues.

## Requirements
- Python 3.x
- `requests` library

## Installation
1. Clone the repository.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt