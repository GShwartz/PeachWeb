"use strict";

const yearEl = document.getElementById("current-year");

const year = () => {
  const d = new Date();
  return d.getFullYear();
};

yearEl.textContent = year();
