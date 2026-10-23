(function () {
  function parsePrice(product) {
    const value = product.unit_price ?? product.price_per_unit;
    if (typeof value === "number") {
      return { price: value, currency: product.currency || "SGD" };
    }

    const match = String(value ?? "").trim().match(/^([\d,.]+)\s*([A-Z]{3})?$/);
    if (!match) {
      throw new Error(`Product ${product.product_id} has invalid price data`);
    }

    return {
      price: Number(match[1].replace(/,/g, "")),
      currency: product.currency || match[2] || "SGD"
    };
  }

  function parseWeight(product) {
    if (product.product_weight != null) {
      return {
        weight: String(product.product_weight),
        weightUnit: String(product.weight_unit || "")
      };
    }

    const match = String(product.weight_per_unit || "").trim().match(/^([\d.]+)\s*(.*)$/);
    return match
      ? { weight: match[1], weightUnit: match[2] }
      : { weight: "", weightUnit: "" };
  }

  function normalizeProduct(product) {
    if (!product || product.product_id == null || !product.product_name) {
      throw new Error("A product is missing its ID or name");
    }

    const category = String(product.pet_type ?? "").trim().toLowerCase();
    if (!category) {
      throw new Error(`Product ${product.product_id} is missing its pet type`);
    }

    const { price, currency } = parsePrice(product);
    if (!Number.isFinite(price)) {
      throw new Error(`Product ${product.product_id} has invalid price data`);
    }

    const oldPriceValue = product.old_price ?? product.oldPrice;
    const oldPrice = oldPriceValue == null ? null : Number(oldPriceValue);
    const { weight, weightUnit } = parseWeight(product);

    return {
      id: String(product.product_id),
      category,
      productType: String(product.product_category ?? "").trim().toLowerCase(),
      brand: String(product.brand ?? ""),
      name: String(product.product_name),
      description: String(product.product_description ?? ""),
      price,
      currency,
      weight,
      weightUnit,
      size: String(product.product_size ?? ""),
      packagingType: String(product.packaging_type ?? ""),
      rating: Number(product.product_rating) || 0,
      reviewCount: Number(product.number_of_reviews) || 0,
      oldPrice: Number.isFinite(oldPrice) ? oldPrice : null,
      isOnSale: Boolean(product.is_on_sale ?? product.isOnSale) ||
        (Number.isFinite(oldPrice) && oldPrice > price),
      isNewArrival: Boolean(product.is_new_arrival ?? product.isNewArrival),
      subscriptionAvailable: Boolean(product.subscription_availability)
    };
  }

  function normalizeList(result, label) {
    const values = Array.isArray(result) ? result : result?.[label];
    if (!Array.isArray(values)) {
      throw new Error(`Unexpected ${label} response format`);
    }
    return values;
  }

  async function loadProducts(filters = {}) {
    const query = {
      product_category: filters.productCategory,
      pet_type: filters.petType,
      brand: filters.brand
    };
    const result = await window.PET_API.request("/api/products", { query });
    const products = normalizeList(result, "products");
    if (products.length === 0) return [];
    return products.map(normalizeProduct);
  }

  async function loadAllProducts() {
    const result = await window.PET_API.request("/products/all");
    return normalizeList(result, "products").map(normalizeProduct);
  }

  async function loadCategories() {
    return normalizeList(
      await window.PET_API.request("/api/categories"),
      "categories"
    );
  }

  async function loadBrands() {
    return normalizeList(
      await window.PET_API.request("/api/brands"),
      "brands"
    );
  }

  async function loadPetTypes() {
    return normalizeList(
      await window.PET_API.request("/api/pet_types"),
      "pet_types"
    );
  }

  window.PET_PRODUCTS_API = {
    loadProducts,
    loadAllProducts,
    loadCategories,
    loadBrands,
    loadPetTypes
  };
})();
