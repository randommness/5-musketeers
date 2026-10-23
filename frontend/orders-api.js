(function () {
  async function getOrders(customerId) {
    if (!customerId) throw new Error("A customer ID is required to load orders");
    return window.PET_API.request("/api/orders", {
      query: { customer_id: customerId }
    });
  }

  async function createOrder(order) {
    return window.PET_API.request("/api/orders", {
      method: "POST",
      body: order
    });
  }

  async function cancelOrder(orderId) {
    if (!orderId) throw new Error("An order ID is required to cancel an order");
    return window.PET_API.request(
      `/api/orders/${encodeURIComponent(orderId)}/cancel`,
      { method: "PATCH" }
    );
  }

  async function requestRefund(orderId) {
    if (!orderId) throw new Error("An order ID is required to request a refund");
    return window.PET_API.request(
      `/api/orders/${encodeURIComponent(orderId)}/refund`,
      { method: "PATCH" }
    );
  }

  window.PET_ORDERS_API = { getOrders, createOrder, cancelOrder, requestRefund };
})();
