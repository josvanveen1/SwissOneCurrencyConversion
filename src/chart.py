import matplotlib.pyplot as plt
from datetime import datetime

def plot_historical_prices(dates, values):
    """
    Displays a line chart of the historical closing prices of a financial security.

    Parameters:
    dates (list): List of date strings in 'DD.MM.YYYY' format.
    values (list): List of closing prices corresponding to the dates.

    The date at index 0 corresponds to the value at index 0.
    """
    # Convert date strings to datetime objects
    dates_dt = [datetime.strptime(date, '%d.%m.%Y') for date in dates]
    
    # Create the plot
    plt.figure(figsize=(10, 5))
    plt.plot(dates_dt, values, marker='o', linestyle='-')
    plt.title('Historical Closing Prices')
    plt.xlabel('Date')
    plt.ylabel('Closing Price')
    plt.grid(True)
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    # Display the plot
    plt.show()
