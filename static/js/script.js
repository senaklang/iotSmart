// แสดงปีปัจจุบันใน footer
document.getElementById("current-year").textContent = new Date().getFullYear();


/**
// เพิ่มเอฟเฟกต์เมื่อคลิกการ์ด
document.querySelectorAll(".card").forEach((card) => {
  card.addEventListener("click", function () {
    window.location.href = this.querySelector("a").href;
  });
});
 */