// Configuration
const config = {
  apiBaseUrl: "/api/",
  refreshInterval: 30000, // 30 seconds
  maxDataPoints: 200,
};

// Global Variables
let mainChart, humidityChart, phChart, tdsChart, ecChart;
let currentData = {};
let realTimeUpdateInterval;

// Initialize Charts
function initializeCharts() {
  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    interaction: {
      mode: "index",
      intersect: false,
    },
    scales: {
      x: {
        type: "time",
        time: {
          unit: "hour",
          tooltipFormat: "HH:mm",
          displayFormats: {
            hour: "HH:mm",
          },
        },
        grid: {
          display: false,
        },
      },
      y: {
        beginAtZero: false,
        grid: {
          color: "rgba(0, 0, 0, 0.05)",
        },
      },
    },
    plugins: {
      legend: {
        position: "top",
      },
      tooltip: {
        callbacks: {
          label: function (context) {
            return `${context.dataset.label}: ${context.parsed.y.toFixed(2)}`;
          },
        },
      },
    },
  };

  // Main Chart
  const mainCtx = document.getElementById("mainChart").getContext("2d");
  mainChart = new Chart(mainCtx, {
    type: "line",
    data: { datasets: [] },
    options: chartOptions,
  });

  // Humidity Chart
  const humidityCtx = document.getElementById("humidityChart").getContext("2d");
  humidityChart = new Chart(humidityCtx, {
    type: "line",
    data: { datasets: [] },
    options: chartOptions,
  });

  // pH Chart
  const phCtx = document.getElementById("phChart").getContext("2d");
  phChart = new Chart(phCtx, {
    type: "line",
    data: { datasets: [] },
    options: chartOptions,
  });

  // tds Chart
  const tdsCtx = document.getElementById("tdsChart").getContext("2d");
  tdsChart = new Chart(tdsCtx, {
    type: "line",
    data: { datasets: [] },
    options: chartOptions,
  });

  // ec Chart
  const ecCtx = document.getElementById("ecChart").getContext("2d");
  ecChart = new Chart(ecCtx, {
    type: "line",
    data: { datasets: [] },
    options: chartOptions,
  });
}

// Load Initial Data
async function loadInitialData() {
  try {
    // Load current values
    const currentResponse = await axios.get(
      `${config.apiBaseUrl}/sensor/current`
    );
    updateCurrentValues(currentResponse.data);

    // Load historical data
    await loadHistoricalData("24h");

    // Start real-time updates
    startRealTimeUpdates();
  } catch (error) {
    console.error("Failed to load initial data:", error);
    showErrorAlert("ไม่สามารถโหลดข้อมูลเริ่มต้นได้");
  }
}

// Update Current Values Display
function updateCurrentValues(data) {
  if (data.status === "success") {
    currentData = data.data;

    document.getElementById(
      "current-temp"
    ).textContent = `${data.data.temperature.toFixed(1)} °C`;
    document.getElementById(
      "current-humidity"
    ).textContent = `${data.data.humidity.toFixed(1)} %`;
    document.getElementById(
      "current-tds"
    ).textContent = `${data.data.tds.toFixed(0)} ppm`;
    document.getElementById("current-ph"
    ).textContent = data.data.ph.toFixed(2);
    document.getElementById(
      "current-ec"
    ).textContent = data.data.ec ? data.data.ec.toFixed(2) : "N/A";
    document.getElementById("current-water-temp").textContent="30.5 °C";
    
    const now = new Date();
    document.getElementById(
      "last-updated"
    ).textContent = `อัปเดตล่าสุด: ${now.toLocaleTimeString("th-TH")}`;

  }
}

// Load Historical Data
async function loadHistoricalData(range) {
  try {
    const response = await axios.get(
      `${config.apiBaseUrl}/sensor/history?range=${range}`
    );
    updateCharts(response.data);
  } catch (error) {
    console.error("Failed to load historical data:", error);
    showErrorAlert("ไม่สามารถโหลดข้อมูลย้อนหลังได้");
  }
}

// Update Charts with New Data
function updateCharts(data) {
  if (data.status === "success") {
    // Process data for Chart.js
    const labels = data.data.map((item) => new Date(item.timestamp));

    // Main Chart (Temperature)
    mainChart.data.labels = labels;
    mainChart.data.datasets = [
      {
        label: "อุณหภูมิ (°C)",
        data: data.data.map((item) => item.temperature),
        borderColor: "rgba(78, 115, 223, 1)",
        backgroundColor: "rgba(78, 115, 223, 0.05)",
        borderWidth: 2,
        tension: 0.1,
      },
    ];
    mainChart.update();

    // Humidity Chart
    humidityChart.data.labels = labels;
    humidityChart.data.datasets = [
      {
        label: "ความชื้น (%)",
        data: data.data.map((item) => item.humidity),
        borderColor: "rgba(28, 200, 138, 1)",
        backgroundColor: "rgba(28, 200, 138, 0.05)",
        borderWidth: 2,
        tension: 0.1,
      },
    ];
    humidityChart.update();

    // pH Chart
    phChart.data.labels = labels;
    phChart.data.datasets = [
      {
        label: "ค่า pH",
        data: data.data.map((item) => item.ph),
        borderColor: "rgba(231, 74, 59, 1)",
        backgroundColor: "rgba(231, 74, 59, 0.05)",
        borderWidth: 2,
        tension: 0.1,
      },
    ];
    phChart.update();

    // tds Chart
    tdsChart.data.labels = labels;
    tdsChart.data.datasets = [
      {
        label: "ค่า TDS",
        data: data.data.map((item) => item.tds),
        borderColor: "rgba(59, 197, 231, 1)",
        backgroundColor: "rgba(59, 119, 231, 0.05)",
        borderWidth: 2,
        tension: 0.1,
      },
    ];
    tdsChart.update();

    // Ec Chart
    ecChart.data.labels = labels;
    ecChart.data.datasets = [
      {
        label: "ค่า EC",
        data: data.data.map((item) => item.ec),
        borderColor: "rgba(59, 197, 231, 1)",
        backgroundColor: "rgba(59, 119, 231, 0.05)",
        borderWidth: 2,
        tension: 0.1,
      },
    ];
    ecChart.update();
  }
}

// Setup Event Listeners
function setupEventListeners() {
  // Time range selector
  document.getElementById("time-range").addEventListener("change", function () {
    loadHistoricalData(this.value);
  });

  // Window visibility change
  document.addEventListener("visibilitychange", function () {
    if (document.hidden) {
      stopRealTimeUpdates();
    } else {
      startRealTimeUpdates();
    }
  });
}

// Real-time Updates
function startRealTimeUpdates() {
  stopRealTimeUpdates();

  realTimeUpdateInterval = setInterval(async () => {
    try {
      const response = await axios.get(`${config.apiBaseUrl}/sensor/current`);
      updateCurrentValues(response.data);
    } catch (error) {
      console.error("Real-time update failed:", error);
    }
  }, config.refreshInterval);
}

function stopRealTimeUpdates() {
  if (realTimeUpdateInterval) {
    clearInterval(realTimeUpdateInterval);
  }
}

// Error Handling
function showErrorAlert(message) {
  // Implement a nice error notification
  console.error("Error:", message);
  alert(message); // In production, replace with toast notification
}


// Before Unload
window.addEventListener("beforeunload", stopRealTimeUpdates);

// DOM Ready
document.addEventListener("DOMContentLoaded", function () {
  initializeCharts();
  loadInitialData();
  setupEventListeners();
  
});
