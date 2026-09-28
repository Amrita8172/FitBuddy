document.addEventListener("DOMContentLoaded", () => {
  const form = document.querySelector("#planForm");
  if (form) form.addEventListener("submit", () => {
    const button = form.querySelector("button[type=submit]");
    if (button) { button.disabled = true; button.querySelector("span:first-child").textContent = "Building your plan…"; }
  });
  document.querySelectorAll("textarea").forEach((area) => {
    const limit = area.getAttribute("maxlength"); if (!limit) return;
    const counter = document.createElement("small"); counter.style.cssText = "color:#69736c;font-size:10px;text-align:right";
    area.insertAdjacentElement("afterend", counter);
    const update = () => counter.textContent = `${area.value.length}/${limit}`;
    area.addEventListener("input", update); update();
  });
});
