// Fills the km/kWh bars once, when the results list first comes into view.
(function () {
  var list = document.querySelector(".results");
  if (!list) return;
  if (!("IntersectionObserver" in window)) { list.classList.add("seen"); return; }
  var io = new IntersectionObserver(function (entries) {
    entries.forEach(function (e) {
      if (e.isIntersecting) { list.classList.add("seen"); io.disconnect(); }
    });
  }, { threshold: 0.25 });
  io.observe(list);
})();
