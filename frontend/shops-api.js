(function () {
  async function loadShops() {
    return window.PET_API.request("/api/shops");
  }

  async function loadPromotions() {
    return window.PET_API.request("/api/promotions");
  }

  window.PET_SHOPS_API = { loadShops, loadPromotions };
})();
