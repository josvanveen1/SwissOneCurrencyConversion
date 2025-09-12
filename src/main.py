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
    data = DB.read_price_range(date(2024, 10, 24), date.today())
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
      <div class="mb-2 text-center sm:text-left">
        <h1 class="text-3xl sm:text-4xl font-bold text-red-500 tracking-tight mb-2">
          Price Chart
        </h1>
        <p class="text-gray-300 text-sm sm:text-base">
          Chart showing recent closing prices
        </p>
      </div>

      <div class='mb-4 text-center sm:text-left'>
        <div class="flex items-baseline space-x-4">
            <h2 id="mostRecentPrice" class="text-3xl font-semibold">$0.00</h2>
            <h3 id="performanceChange">0%</h3>
        </div>
        <h2 id="mostRecentDate" class="text-sm text-gray-400">2023-01-01</h2>
      </div>

      <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-4">
        <div class="mb-4 text-center sm:text-left">
            <input type="date" id="startDate" min="2024-10-24" class="p-2 rounded-lg bg-gray-800 text-white border border-gray-700 mr-2" />
            <input type="date" id="endDate" class="p-2 rounded-lg bg-gray-800 text-white border border-gray-700 mr-2" />
            <button id="filterButton" class="bg-red-500 hover:bg-red-600 text-white py-1 px-4 rounded-lg transition duration-200">
            Filter
            </button>
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
        let performance = 0;
        let isUSD = true;

        let currentLabels = [...chartData.labels];
        let currentUSD = [...chartData.usd_values];
        let currentEUR = [...chartData.eur_values];

        function calculatePerformance() {
          const initialPrice = isUSD ? currentUSD[0] : currentEUR[0];
          const mostRecentPrice = isUSD ? currentUSD[currentUSD.length - 1] : currentEUR[currentEUR.length - 1];
          performance = ((mostRecentPrice - initialPrice) / initialPrice) * 100;
          
          let symbol = performance >= 0 ? '+' : '';
          const performanceElement = document.getElementById('performanceChange');
          performanceElement.textContent = `${symbol}${performance.toFixed(2)}%`;
          performanceElement.style.color = performance >= 0 ? '#4CAF50' : '#F44336';

        }

        function filterChartData(startDate, endDate) {
          const start = new Date(startDate);
          const end = new Date(endDate);

          const filteredLabels = [];
          const filteredUSD = [];
          const filteredEUR = [];

          chartData.labels.forEach((label, index) => {
              const currentDate = new Date(label);
              if (currentDate >= start && currentDate <= end) {
                  filteredLabels.push(label);
                  filteredUSD.push(chartData.usd_values[index]);
                  filteredEUR.push(chartData.eur_values[index]);
              }
          });

          currentLabels = filteredLabels;
          currentUSD = filteredUSD;
          currentEUR = filteredEUR;

          // Update the chart with the filtered data
          priceChart.data.labels = currentLabels;
          priceChart.data.datasets[0].data = isUSD ? currentUSD : currentEUR;
          priceChart.update();
        }

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
                pointRadius: 1,
                pointHoverRadius: 4,
                pointBackgroundColor: '#3B82F6',
                pointBorderColor: '#fff',
                pointBorderWidth: 1
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

        document.getElementById('mostRecentPrice').textContent = `$${isUSD ? chartData.most_recent_price_usd.toFixed(2) : chartData.most_recent_price_eur.toFixed(2)}`;
        document.getElementById('mostRecentDate').textContent = `${chartData.most_recent_date}`;
        calculatePerformance(); // <-- Calculate and display performance on load

        document.getElementById('filterButton').addEventListener('click', () => {
            const startDate = document.getElementById('startDate').value;
            const endDate = document.getElementById('endDate').value;
            if (startDate && endDate) {
            // Call a function to filter the chart data based on the selected dates
            filterChartData(startDate, endDate);
              calculatePerformance();
            }
        });
          document.getElementById('toggleCurrency').addEventListener('click', () => {
              isUSD = !isUSD;
              const dataset = priceChart.data.datasets[0];

              dataset.data = isUSD ? currentUSD : currentEUR;  // ✅ uses filtered data if available
              dataset.label = isUSD ? 'Closing Price (USD)' : 'Closing Price (EUR)';
              dataset.borderColor = isUSD ? '#F44336' : '#3B82F6';
              dataset.backgroundColor = isUSD ? 'rgba(244, 67, 54, 0.2)' : 'rgba(59, 130, 246, 0.2)';
              priceChart.options.scales.y.title.text = isUSD ? 'Closing Price (USD)' : 'Closing Price (EUR)';
              document.getElementById('toggleCurrency').textContent = isUSD ? 'Switch to EUR' : 'Switch to USD';
              calculatePerformance(); // <-- Update performance on currency switch
              priceChart.update();
          });
      </script>
  </body>
</html>
    """
    # Inject JS to calculate and display performance on load
    injected_js = """
    """
    html = html.replace("<script>\n      const chartData = REPLACE_CHART_DATA_HERE;", injected_js)
    html = html.replace("REPLACE_CHART_DATA_HERE", json.dumps(chart_data))
    return HTMLResponse(content=html)

@scheduler.scheduled_job('cron', hour='11', minute='19')
async def fetch_data_job():
    await populate_database()