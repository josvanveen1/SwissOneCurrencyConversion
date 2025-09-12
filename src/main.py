from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from database_client import DatabaseClient
import json
import os
from dotenv import load_dotenv
from utility import get_dates_from, populate_database 
from datetime import date
from datetime import timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from pytz import utc
from contextlib import asynccontextmanager

scheduler = AsyncIOScheduler(timezone=utc)

@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler.start()
    yield
    scheduler.shutdown()

app = FastAPI(lifespan=lifespan)

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
        password=os.getenv("DB_PASSWORD"),
        sslmode=os.getenv("DB_SSLMODE", "allow")
    )
    DB.connect()

    # Get historical data
    data = DB.read_price_range(one_month_ago, date.today())
    dates = [str(v[0]) for v in data]
    price_usd = [float(v[1]) for v in data]
    price_eur = [float(v[2]) for v in data]

    DB.disconnect()

    # Prepare data for JSON
    chart_data = {
        "labels": dates,
        "usd_values": price_usd,
        "eur_values": price_eur,
        "most_recent_date": str(dates[-1]),
        "most_recent_price_usd": price_usd[-1],
        "most_recent_price_eur": price_eur[-1]
    }

    html = """
    <!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Price Chart</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
      body {
        font-family: 'Roboto', sans-serif;
        background: linear-gradient(135deg, #0f0f0f, #1e1e1e);
        color: white;
      }
      canvas {
        max-width: 100%;
        height: 100%;
      }
    </style>
  </head>
  <body>
    <div class="container mx-auto px-4 py-8 max-w-5xl">
      <!-- Heading Section -->
      <div class="mb-6 text-center sm:text-left">
        <h1 class="text-3xl sm:text-4xl font-bold text-red-500 tracking-tight mb-2">
          Price Chart
        </h1>
        <p class="text-gray-300 text-sm sm:text-base">
          Chart showing recent closing prices
        </p>
      </div>

      <!-- Button Section -->
      <div class="mb-4 text-center sm:text-left">
        <button
          id="toggleCurrency"
          class="bg-transparent border-2 border-red-500 hover:bg-red-500 text-white py-1 px-2 rounded-lg transition duration-200"
        >
          Switch to EUR
        </button>
      </div>

      <!-- Chart Card -->
      <div
        class="bg-[#1a1a1a] p-6 rounded-2xl shadow-xl h-[500px] flex items-center justify-center"
      >
        <canvas id="priceChart"></canvas>
      </div>
    </div>

    <script>
      const chartData = REPLACE_CHART_DATA_HERE;
      const ctx = document.getElementById('priceChart').getContext('2d');
      let isUSD = true;

      const chartConfig = {
        type: 'line',
        data: {
          labels: chartData.labels,
          datasets: [
            {
              label: 'Closing Price (USD)',
              data: chartData.usd_values,
              borderColor: '#F44336',
              backgroundColor: 'rgba(244, 67, 54, 0.2)',
              fill: true,
              tension: 0,
              pointRadius: 4,
              pointHoverRadius: 7,
              pointBackgroundColor: '#3B82F6',
              pointBorderColor: '#fff',
              pointBorderWidth: 2
            }
          ]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            tooltip: {
              backgroundColor: '#111827',
              titleColor: '#facc15',
              bodyColor: '#f5f5f5',
              borderColor: '#3B82F6',
              borderWidth: 1,
              padding: 10
            }
          },
          scales: {
            x: {
              title: {
                display: true,
                text: 'Date',
                color: '#f5f5f5',
                font: {
                  weight: 'bold'
                }
              },
              ticks: {
                color: '#d1d5db'
              },
              grid: {
                color: 'rgba(255,255,255,0.05)'
              }
            },
            y: {
              title: {
                display: true,
                text: 'Closing Price (USD)',
                color: '#f5f5f5',
                font: {
                  weight: 'bold'
                }
              },
              ticks: {
                color: '#d1d5db'
              },
              grid: {
                color: 'rgba(255,255,255,0.1)'
              }
            }
          }
        }
      };

      const priceChart = new Chart(ctx, chartConfig);

      document.getElementById('toggleCurrency').addEventListener('click', () => {
        isUSD = !isUSD;
        const dataset = priceChart.data.datasets[0];
        dataset.data = isUSD ? chartData.usd_values : chartData.eur_values;
        dataset.label = isUSD ? 'Closing Price (USD)' : 'Closing Price (EUR)';
        dataset.borderColor = isUSD ? '#F44336' : '#3B82F6';
        dataset.backgroundColor = isUSD ? 'rgba(244, 67, 54, 0.2)' : 'rgba(59, 130, 246, 0.2)';
        priceChart.options.scales.y.title.text = isUSD ? 'Closing Price (USD)' : 'Closing Price (EUR)';
        document.getElementById('toggleCurrency').textContent = isUSD ? 'Switch to EUR' : 'Switch to USD';
        priceChart.update();
      });
    </script>
  </body>
</html>
    """
    html = html.replace("REPLACE_CHART_DATA_HERE", json.dumps(chart_data))
    return HTMLResponse(content=html)

@scheduler.scheduled_job('cron', hour='11', minute='19')
async def fetch_data_job():
    await populate_database()