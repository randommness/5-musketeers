(function () {
  async function submitReview(review) {
    return window.PET_API.request("/api/reviews", {
      method: "POST",
      body: review
    });
  }

  window.PET_REVIEWS_API = { submitReview };
})();
