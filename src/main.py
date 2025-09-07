from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from database_client import DatabaseClient
import json
import os
from dotenv import load_dotenv
from utility import main as get_historical_data
from utility import get_dates_from, serialize_chart_data
from datetime import date
from datetime import timedelta

app = FastAPI()

@app.get("/", response_class=HTMLResponse)
async def root():
    load_dotenv()
    one_month_ago = date.today() - timedelta(days=30)
    dates = get_dates_from(one_month_ago)

    DB = DatabaseClient(
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT")),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD")
    )
    DB.connect()

    # Get historical data
    data = DB.read_price_range(one_month_ago, date.today())
    values = [float(v[1]) for v in data]
    dates = [str(v[0]) for v in data]
    DB.disconnect()

    # Prepare data for JSON
    chart_data = {
        "labels": dates,
        "values": values
    }


    html = f"""
    <!DOCTYPE html>
    <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Price in USD</title>
            <script src="https://cdn.tailwindcss.com"></script>
            <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
            <style>
                body {{
                    font-family: 'Roboto', sans-serif;
                    background-color: #121212;
                    color: white;
                }}
                .container {{
                    max-width: 1200px;
                    margin: 0 auto;
                    padding: 2rem;
                }}
                .chart-container {{
                    background-color: #1a1a1a;
                    padding: 1.5rem;
                    border-radius: 0.5rem;
                    height: 500px;
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
                }}
                h1 {{
                    font-size: 26px;
                    font-weight: bold;
                    color: #DC3545;
                    text-align: left;
                    margin-bottom: 2rem;
                }}
                canvas {{
                    max-width: 100%;
                    height: 100%;
                }}
                @media (max-width: 640px) {{
                    h1 {{
                        font-size: 1.5rem;
                    }}
                    .container {{
                        padding: 1rem;
                    }}
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="chart-container">
                    <canvas id="priceChart"></canvas>
                </div>
            </div>
            <script>
                const chartData = {json.dumps(chart_data)};
                const ctx = document.getElementById('priceChart').getContext('2d');
                new Chart(ctx, {{
                    type: 'line',
                    data: {{
                        labels: chartData.labels,
                        datasets: [{{
                            label: 'Closing Price (USD)',
                            data: chartData.values,
                            borderColor: '#00A3FF',
                            backgroundColor: 'rgba(0, 163, 255, 0.2)',
                            fill: true,
                            tension: 0.4,
                            pointRadius: 5,
                            pointHoverRadius: 8
                        }}]
                    }},
                    options: {{
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {{
                            legend: {{
                                labels: {{
                                    color: 'white'
                                }}
                            }},
                            tooltip: {{
                                backgroundColor: '#1a1a1a',
                                titleColor: 'white',
                                bodyColor: 'white',
                                borderColor: '#FFD700',
                                borderWidth: 1
                            }}
                        }},
                        scales: {{
                            x: {{
                                title: {{
                                    display: true,
                                    text: 'Date',
                                    color: 'white'
                                }},
                                ticks: {{
                                    color: 'white'
                                }}
                            }},
                            y: {{
                                title: {{
                                    display: true,
                                    text: 'Closing Price (USD)',
                                    color: 'white'
                                }},
                                ticks: {{
                                    color: 'white'
                                }},
                                grid: {{
                                    color: 'gray'
                                }}
                            }}
                        }}
                    }}
                }});
            </script>
        </body>
    </html>
    """
    return HTMLResponse(content=html)