(() => {
  // Configuration
  const config = {
    //apiBaseUrl: "/api/",
    apiBaseUrlHardware: "/hardware/",
    refreshInterval: 30000, // 30 seconds
    maxDataPoints: 200,
  };

  // Global Variables
  let currentData = {};
  let realTimeUpdateInterval;

  // Load Initial Data
  function loadInitialData() {
    console.log("Loading initial data...");
    fetch(`${config.apiBaseUrlHardware}sensor/current`)
      .then((response) => response.json())
      .then((data) => {
        if (data.status === "success") {
          currentData = data.data;

          console.log("Sensor Data:", currentData); // ดูค่าที่ใช้จริง
          updateDashboard();
        } else {
          console.error("Failed to load initial data:", data.message);
        }
      })
      .catch((error) => console.error("Error fetching initial data:", error));
  }

  // Setup Event Listeners
  function setupEventListeners() {
    const refreshButton = document.getElementById("refresh-button");
    if (refreshButton) {
      refreshButton.addEventListener("click", () => {
        loadInitialData();
      });
    }

    // Start real-time updates
    realTimeUpdateInterval = setInterval(() => {
      fetch(`${config.apiBaseUrlHardware}sensor/sensor-data`)
        .then((response) => response.json())
        .then((data) => {
          if (data.status === "success") {
            currentData = data.data;
            updateDashboard();
            console.log("Real-time data updated:", currentData);
          }
        })
        .catch((error) =>
          console.error("Error fetching real-time data:", error)
        );
    }, config.refreshInterval);
  }

  function updateDashboard() {
    console.log("Updating dashboard with current data:", currentData);
    if (!currentData) return;

    const lastUpdatedElement = document.getElementById("last-updated");
    if (lastUpdatedElement) {
      const now = new Date();
      const formattedTime = now.toLocaleString(); // หรือใช้ toLocaleTimeString() เฉพาะเวลา
      lastUpdatedElement.innerText = `Last updated: ${formattedTime}`;
    }
    const humidityElement = document.getElementById("humidity-display");
    const temperatureElement = document.getElementById("temperature-display");
    const tdsElement = document.getElementById("tds-display");
    const phElement = document.getElementById("ph-display");

    if (
      humidityElement &&
      currentData.humidity !== undefined &&
      currentData.humidity !== null
    ) {
      humidityElement.innerText = `${currentData.humidity} %`;
    } else {
      humidityElement.innerText = "-- %"; // fallback
    }
    if (
      temperatureElement &&
      currentData.temperature !== undefined &&
      currentData.temperature !== null
    ) {
      temperatureElement.innerText = `${currentData.temperature.toFixed(1)} °C`;
    } else {
      temperatureElement.innerText = "-- °C"; // fallback
    }
    if (
      tdsElement &&
      currentData.tds !== undefined &&
      currentData.tds !== null
    ) {
      tdsElement.innerText = `${currentData.tds} ppm`;
    } else {
      tdsElement.innerText = "-- ppm"; // fallback
    }
    if (phElement && currentData.ph !== undefined && currentData.ph !== null) {
      phElement.innerText = `${currentData.ph.toFixed(2)}`;
    } else {
      phElement.innerText = "--"; // fallback
    }
  }

  window.controlDevice = async function (device_id, action, channel) {

    console.log(
      `Controlling device ${device_id} to ${action} on channel ${channel}`
    );
    try {
      const response = await fetch(
        `${config.apiBaseUrlHardware}lamp/lampcontrol`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ device_id, action, channel }),
        }
      );

      if (!response.ok) {
        throw new Error(`HTTP error js ! status: ${response.status}`);
      }

      const result = await response.json();
      if (result.status === "success") {
        console.log(`Device ${device_id} turned ${action} channel ${channel}`);
        fetchLampStatus(); // Refresh lamp status
      } else {
        console.error(`Failed to control device: ${result.message}`);
      }
    } catch (error) {
      showAlert(`Error controlling device: ${error.message}`);
      //console.error("Error controlling device:", error);
    }
  };

  function showAlert(message) {
    // ใช้ UI framework ที่มีอยู่ หรือสร้าง alert ง่ายๆ
    alert(message); // หรือใช้ modal ที่สวยงามกว่า
  }

  async function fetchLampStatus() {
    try {
      const response = await fetch(`${config.apiBaseUrlHardware}lamp/status`);
      const result = await response.json();

      if (Array.isArray(result.data)) {
        const container = document.getElementById("lampStatusContainer");
        container.innerHTML = "";

        result.data.forEach((lamp) => {
          const lampDiv = document.createElement("div");
          lampDiv.classList.add("mb-3");
          lampDiv.innerHTML = `
          <h6 class="fw-bold">Lamp ${lamp.id}</h6>
          <div class="d-grid gap-2 d-md-block">
            <button class="btn btn-success me-2" onclick="updateLampStatus(${
              lamp.id
            }, 'on')">
                <i class="bi bi-lightbulb-fill"></i> Turn On
            </button>

            <button class="btn btn-danger" onclick="updateLampStatus(${
              lamp.id
            }, 'off')">
              <i class="bi bi-lightbulb-off"></i> Turn Off
            </button>

            <span class="badge bg-${
              lamp.status === "on" || lamp.status === "1"
                ? "success"
                : "secondary"
            } ms-3">
              ${lamp.status === "on" || lamp.status === "1" ? "On" : "Off"}
            </span>
          </div>
        `;
          container.appendChild(lampDiv);
        });
      } else {
        console.error("Unexpected data format:", result);
      }
    } catch (error) {
      console.error("Error fetching lamp status:", error);
    }
  }

  // ✅ ฟังก์ชันอัพเดทสถานะไปยัง Flask API
  // ✅ ฟังก์ชันอัพเดทสถานะไปยัง Flask API
  async function updateLampStatus(lampId, status) {
    try {
      const response = await fetch(
        `${config.apiBaseUrlHardware}lamp/status/${lampId}`,
        {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ status: status }),
        }
      );

      const result = await response.json();
      if (result.status === "success") {
        console.log(`Lamp ${lampId} updated to ${status}`);
        fetchLampStatus(); // refresh UI
      } else {
        console.error("Update failed:", result.message);
      }
    } catch (error) {
      console.error("Error updating lamp status:", error);
    }
  }

  async function getComport() {
    const comdetails = document.getElementById("comdetails");

    // แสดงสถานะกำลังโหลด
    comdetails.innerHTML = `
        <span style="margin-left: 10px; color: #FFC107;">
            <i class="fas fa-spinner fa-spin"></i> กำลังตรวจสอบการเชื่อมต่อ...
        </span>
    `;

    try {
      const response = await fetch("/hardware/com-status");

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();

      // ดึงข้อมูลการเชื่อมต่อจากโครงสร้าง JSON ที่ให้มา
      const connection = result.connected;

      // กำหนดสไตล์ตามสถานะ
      const statusText = connection.connected
        ? "เชื่อมต่อแล้ว"
        : "ยังไม่เชื่อมต่อ";
      const statusColor = connection.connected ? "#fefffeff" : "#F44336";
      const statusIcon = connection.connected
        ? "fa-check-circle"
        : "fa-times-circle";

      // แสดงผลข้อมูล
      comdetails.innerHTML = `
            <span style="margin-left: 10px;">
                <i class="fas ${statusIcon}" style="color: ${statusColor};"></i>
                <strong>พอร์ต:</strong> ${connection.port || "ไม่ทราบ"} |
                <strong>ความเร็ว:</strong> ${
                  connection.baudrate || "ไม่ทราบ"
                } baud |
                <span style="color: ${statusColor}">${statusText}</span>
            </span>
        `;
    } catch (err) {
      console.error("Error fetching COM status:", err);
      comdetails.innerHTML = `
            <span style="margin-left: 10px; color: #F44336;">
                <i class="fas fa-exclamation-triangle"></i> ไม่สามารถตรวจสอบการเชื่อมต่อ
            </span>
        `;
    }
  }
  // ✅ ทำให้ฟังก์ชันนี้เรียกจาก HTML ได้
  //window.getComport = getComport;
  // ✅ ทำให้เรียกจาก HTML ได้
  window.updateLampStatus = updateLampStatus;
 
  // Run on page load
  document.addEventListener("DOMContentLoaded", () => {
    loadInitialData();
    setupEventListeners();
    fetchLampStatus();
    getComport();
  });
})();
