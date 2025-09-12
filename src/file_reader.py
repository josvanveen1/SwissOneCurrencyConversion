from datetime import datetime

def parse_stock_data(file_path):
    """
    Reads a tab-separated stock data file and returns each column as a list.
    Handles number formats like 1.000,00 or 1000,00 by normalizing to float.
    
    Args:
        file_path (str): Path to the text file
        
    Returns:
        tuple: (dates, opens, highs, lows, closes, volumes)
            - dates: List of datetime objects
            - opens, highs, lows, closes: Lists of float values
            - volumes: List of integer values
    """
    dates = []
    opens = []
    highs = []
    lows = []
    closes = []
    volumes = []
    
    def normalize_number(number_str):
        """Converts a number string (e.g., '1.000,00' or '1000,00') to float."""
        # Replace period with nothing and comma with period for float conversion
        cleaned = number_str.replace('.', '').replace(',', '.')
        return float(cleaned)
    
    try:
        with open(file_path, 'r') as file:
            for line in file:
                # Skip empty lines
                if not line.strip():
                    continue
                    
                # Split the line by tabs
                columns = line.strip().split('\t')
                
                # Ensure we have the expected number of columns
                if len(columns) != 6:
                    print(f"Warning: Skipping malformed line: {line.strip()}")
                    continue
                
                try:
                    # Parse date (format: DD.MM.YYYY)
                    date = columns[0]
                    
                    # Parse prices using normalize_number
                    open_price = normalize_number(columns[1])
                    high_price = normalize_number(columns[2])
                    low_price = normalize_number(columns[3])
                    close_price = normalize_number(columns[4])
                    
                    # Parse volume (should be an integer, no decimal formatting)
                    volume = int(columns[5])
                    
                    # Append to respective lists
                    dates.append(date)
                    opens.append(open_price)
                    highs.append(high_price)
                    lows.append(low_price)
                    closes.append(close_price)
                    volumes.append(volume)
                    
                except ValueError as e:
                    print(f"Warning: Error parsing line: {line.strip()}. Error: {e}")
                    continue
                    
    except FileNotFoundError:
        print(f"Error: File {file_path} not found")
        return None
    except Exception as e:
        print(f"Error: An unexpected error occurred: {e}")
        return None
        
    return dates, opens, highs, lows, closes, volumes


file_path = "src/stock_data.txt"
dates, opens, highs, lows, closes, volumes = parse_stock_data(file_path)
if dates is not None:
    print("Dates:", dates)
    print("Opens:", opens)
    print("Highs:", highs)
    print("Lows:", lows)
    print("Closes:", closes)
    print("Volumes:", volumes)
