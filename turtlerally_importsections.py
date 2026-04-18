import csv

def processSegments(filestr):
    # Initialize an empty dictionary to store the sections and their segments
    sections = {}

    # Open the CSV file
    with open(filestr, newline='', encoding='utf-8') as csvfile:
        # Create a CSV reader object with the semicolon as the delimiter
        csvreader = csv.reader(csvfile, delimiter=';')

        current_section = None

        # Iterate through each row in the CSV
        for row in csvreader:
            # Skip empty rows or rows with insufficient columns
            if not row or len(row) < 4:
                continue

            # If the first column is not empty, it indicates a new section
            if row[0].strip():  # Checking if row[0] is not empty and not just whitespace
                current_section = row[0]
                sections[current_section] = []
            
            # Ensure we have a valid section before processing
            if current_section and len(row) >= 4:
                try:
                    start = float(row[1].replace(',', '.').strip())
                    end = float(row[2].replace(',', '.').strip())
                    avg_dry = float(row[3].replace(',', '.').strip())
                    avg_wet = float(row[4].replace(',', '.').strip())
                    sections[current_section].append((start, end, avg_dry, avg_wet))
                except ValueError:
                    # Skip rows with conversion issues
                    continue
                    
    sections.pop('Section ')
    
    return sections
