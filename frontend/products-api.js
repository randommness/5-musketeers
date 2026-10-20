(function () {
  const BASE_URL = "https://5-musketeers-production.up.railway.app/";
  const ENDPOINT = "/api/products";
  const PET_TYPES = new Set(["dog", "cat", "fish", "rabbit"]);

  function normalizeProduct(product) {
    if (!product || product.product_id == null || !product.product_name) {
      throw new Error("A product is missing its ID or name");
    }

    const category = String(product.pet_type ?? "").trim().toLowerCase();
    if (!PET_TYPES.has(category)) {
      return null;
    }

    const price = Number(product.unit_price);
    if (!Number.isFinite(price)) {
      throw new Error(`Product ${product.product_id} has invalid price data`);
    }

    const oldPriceValue = product.old_price ?? product.oldPrice;
    const oldPrice = oldPriceValue == null ? null : Number(oldPriceValue);

    return {
      id: String(product.product_id),
      category,
      productType: String(product.product_category ?? "").trim().toLowerCase(),
      brand: String(product.brand ?? ""),
      name: String(product.product_name),
      price,
      rating: Number(product.product_rating) || 0,
      reviewCount: Number(product.number_of_reviews) || 0,
      oldPrice: Number.isFinite(oldPrice) ? oldPrice : null,
      isOnSale: Boolean(product.is_on_sale ?? product.isOnSale) ||
        (Number.isFinite(oldPrice) && oldPrice > price),
      isNewArrival: Boolean(product.is_new_arrival ?? product.isNewArrival)
    };
  }

  async function loadProducts() {
    const url = new URL(ENDPOINT, BASE_URL.trim());
    const response = await fetch(url);

    if (!response.ok) {
      throw new Error(`HTTP ${response.status} for ${url}`);
    }

    const result = await response.json();
    const products = Array.isArray(result) ? result : result?.products;
    if (!Array.isArray(products)) {
      throw new Error("Unexpected products response format");
    }

    const supportedProducts = products.map(normalizeProduct).filter(Boolean);
    if (supportedProducts.length === 0) {
      throw new Error("No products found for the supported pet types");
    }
    return supportedProducts;
  }

  window.PET_PRODUCTS_API = { loadProducts };
})();
