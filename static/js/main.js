(function () {
  "use strict";

  // ---- Mobile navigation -------------------------------------------------
  var toggle = document.querySelector(".nav-toggle");
  var nav = document.getElementById("main-nav");
  if (toggle && nav) {
    toggle.addEventListener("click", function () {
      var open = nav.classList.toggle("is-open");
      toggle.setAttribute("aria-expanded", open ? "true" : "false");
    });
  }

  // ---- Language dropdown -------------------------------------------------
  var lang = document.querySelector(".lang");
  if (lang) {
    var langBtn = lang.querySelector(".lang__current");
    langBtn.addEventListener("click", function (e) {
      e.stopPropagation();
      lang.classList.toggle("is-open");
    });
    document.addEventListener("click", function () { lang.classList.remove("is-open"); });
  }

  // ---- Inquiry modal -----------------------------------------------------
  var modal = document.getElementById("inquiry-modal");
  function openModal(productId) {
    if (!modal) return;
    var field = modal.querySelector('input[name="product_id"]');
    if (productId) {
      if (!field) {
        field = document.createElement("input");
        field.type = "hidden";
        field.name = "product_id";
        modal.querySelector("form").appendChild(field);
      }
      field.value = productId;
    } else if (field) {
      field.value = "";
    }
    modal.hidden = false;
    document.body.style.overflow = "hidden";
    var first = modal.querySelector('input[name="name"]');
    if (first) setTimeout(function () { first.focus(); }, 50);
  }
  function closeModal() {
    if (!modal) return;
    modal.hidden = true;
    document.body.style.overflow = "";
  }
  document.querySelectorAll(".js-open-modal").forEach(function (btn) {
    btn.addEventListener("click", function () { openModal(btn.getAttribute("data-product")); });
  });
  document.querySelectorAll(".js-close-modal").forEach(function (el) {
    el.addEventListener("click", closeModal);
  });
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape") closeModal();
  });

  // ---- Product gallery thumbnails ---------------------------------------
  var mainImg = document.getElementById("product-main-img");
  if (mainImg) {
    document.querySelectorAll(".thumb").forEach(function (thumb) {
      thumb.addEventListener("click", function () {
        mainImg.src = thumb.getAttribute("data-img");
        document.querySelectorAll(".thumb").forEach(function (t) { t.classList.remove("is-active"); });
        thumb.classList.add("is-active");
      });
    });
  }

  // ---- Lightbox for galleries -------------------------------------------
  document.querySelectorAll(".js-gallery .gallery__item").forEach(function (item) {
    item.addEventListener("click", function (e) {
      e.preventDefault();
      var box = document.createElement("div");
      box.className = "lightbox";
      var img = document.createElement("img");
      img.src = item.getAttribute("href");
      box.appendChild(img);
      box.addEventListener("click", function () { box.remove(); });
      document.body.appendChild(box);
    });
  });
})();
