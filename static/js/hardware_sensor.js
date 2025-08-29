// hardware_sensors.js

const refreshInterval = 60000; // 1 นาที
let countdownTime = refreshInterval / 1000;
let refreshTimer;
let countdownTimer;

function updateLastUpdatedTime() {
  const now = new Date();
  const timeString = now.toLocaleTimeString("th-TH", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });

  const lastUpdatedEl = document.getElementById("lastUpdated");
  if (lastUpdatedEl) {
    lastUpdatedEl.innerHTML = `<i class="fas fa-sync-alt"></i> อัปเดตล่าสุด: ${timeString}`;
  }
}

function startCountdown() {
  const countdownEl = document.getElementById("countdown");
  if (!countdownEl) return;

  countdownTime = refreshInterval / 1000;
  countdownEl.textContent = countdownTime;

  clearInterval(countdownTimer); // ป้องกัน timer ซ้อน
  countdownTimer = setInterval(() => {
    countdownTime--;
    countdownEl.textContent = countdownTime;

    if (countdownTime <= 0) {
      clearInterval(countdownTimer);
    }
  }, 1000);
}

function manualRefresh() {
  clearInterval(refreshTimer);
  updateLastUpdatedTime();
  startAutoRefresh();
  window.location.reload();
}

function startAutoRefresh() {
  refreshTimer = setInterval(() => {
    fetch("/hardware_sensors").then(() => {
      window.location.reload();
    });
  }, refreshInterval);

  startCountdown();
}

// รอให้ DOM โหลดก่อนค่อยเริ่มทำงาน
document.addEventListener("DOMContentLoaded", () => {
  updateLastUpdatedTime();
  startAutoRefresh();
});

// ป้องกัน memory leak
window.addEventListener("beforeunload", () => {
  clearInterval(refreshTimer);
  clearInterval(countdownTimer);
});
