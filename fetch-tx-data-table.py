import requests
from bs4 import BeautifulSoup
import json

def fetch_table_data():
    # URL of the Texas COVID-19 Surveillance page
    url = 'https://www.dshs.state.tx.us/covid-19-coronavirus-disease/texas-covid-19-surveillance'
    
    # Send a GET request to the URL
    response = requests.get(url)
    response.raise_for_status()  # Raise an error for bad responses

    # Parse the HTML content using Beautiful Soup
    soup = BeautifulSoup(response.content, 'html.parser')

    # Find the table (you may need to adjust the selector based on the actual HTML structure)
    table = soup.find('table')

    # Extract data from the table
    table_data = []
    for row in table.find_all('tr'):
        columns = row.find_all('td')  # Get all data cells
        if not columns:  # Skip header rows or empty rows
            continue
        row_data = [column.get_text(strip=True) for column in columns]
        table_data.append(row_data)

    # Convert the table data to a list of dictionaries for better JSON structure
    json_data = []
    headers = ["Component", "Change from Previous Week", "Current Week", "Previous Week"]  # Adjust headers based on your table
    for row in table_data:
        json_data.append(dict(zip(headers, row)))

    # Save the data to a JSON file
    with open('texas_covid_data.json', 'w') as json_file:
        json.dump(json_data, json_file, indent=4)

    print("Data has been written to texas_covid_data.json")

# Run the function
fetch_table_data()