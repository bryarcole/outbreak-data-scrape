import requests
from bs4 import BeautifulSoup
import PyPDF2
import io
import pdfplumber
import json
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from flask import Flask, jsonify
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime  # Import the datetime module
import warnings

# Suppress all warnings
warnings.filterwarnings("ignore")

app = Flask(__name__)

def fetch_first_pdf_data(url):
    # Send a GET request to the URL
    response = requests.get(url)
    response.raise_for_status()  # Raise an error for bad responses

    # Parse the HTML content using Beautiful Soup
    soup = BeautifulSoup(response.content, 'html.parser')

    # Find all <a> tags on the page
    links = soup.find_all('a')

    # Iterate through all links and filter for PDFs
    for link in links:
        href = link.get('href')  # Get the href attribute
        if href and href.endswith('.pdf'):  # Check if href ends with .pdf
            #add to index here to go back and get all previous data 
            pdf_link = href if href.startswith('http') else url.rsplit('/', 1)[0] + href  # Construct full URL if needed
            print(f"Found PDF link: {pdf_link}")

            # Download the PDF
            pdf_response = requests.get(pdf_link)
            pdf_response.raise_for_status()  # Raise an error for bad responses

            # Read the PDF content and extract tables
            tables_data = extract_tables_from_pdf(pdf_response.content)
            return tables_data  # Return the extracted tables data

    print("No PDF found on the page.")
    return []

def extract_tables_from_pdf(pdf_content):
    tables_data = []

    with pdfplumber.open(io.BytesIO(pdf_content)) as pdf:
        for page in pdf.pages:
            # Extract the title of the page (assuming it's the first text element)
            title = page.extract_text().split('\n')[0] if page.extract_text() else "Untitled Page"

            # Extract all text from the page
            page_text = page.extract_text().split('\n') if page.extract_text() else []
            tables = page.extract_tables()

            if not tables:
                continue  # Skip the page if no tables are found

            for i, table in enumerate(tables):
                if table and table[0]:
                    # Attempt to find the header text that directly precedes the table
                    header_text = table[0][0]
                    if header_text in page_text:
                        header_index = page_text.index(header_text) - 1
                        table_header = page_text[header_index] if header_index >= 0 else f"Table {i + 1}"
                    else:
                        table_header = f"Table {i + 1}"  # Default if header not found
                else:
                    table_header = f"Table {i + 1}"  # Default if table is empty

                # Prepare the data for the JSON structure
                table_data = {
                    "Title": title,
                    f"Table{i + 1}": table_header,
                    "TableDataHeader": table[0],  # First row as headers
                    "TableData": table[1:]  # Remaining rows as data
                }

                tables_data.append(table_data)

    return tables_data

def save_tables_to_json(tables_data, output_json_path):
    with open(output_json_path, 'w') as json_file:
        json.dump(tables_data, json_file, indent=4)  # Save the tables data to a JSON file


# Function to fetch PDF data and save to JSON
def fetch_and_save_data():
    url = 'https://www.dshs.texas.gov/texas-respiratory-virus-surveillance-report'  # Replace with your target URL
    tables_data = fetch_first_pdf_data(url)  # Call the function from your script

    # Get the current date in the desired format
    current_date = datetime.now().strftime('%-m.%-d.%Y')  # Format: M.D.YYYY

    # Construct the output JSON path with the current date
    pdf_data_tables = f'pdf_data_tables_{current_date}.json'  # Output JSON path
    save_tables_to_json(tables_data, pdf_data_tables)
    print(f"Extracted tables saved to {pdf_data_tables}")

# Set up the scheduler
scheduler = BackgroundScheduler()
fetch_and_save_data()
scheduler.add_job(fetch_and_save_data, 'interval', weeks=1)  # Adjust the interval as needed
scheduler.start()

@app.route('/')
def index():
    return jsonify({"message": "Server is running and will fetch data periodically."})

if __name__ == '__main__':
    try:
        app.run(port=5000)  # Run the Flask server on port 5000
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()  # Shut down the scheduler when exiting