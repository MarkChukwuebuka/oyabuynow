function showToast(message, type = "info") {
    const container = document.querySelector(".message-container");
    if (!container) return;

    const toast = document.createElement("div");
    toast.className = `message-toast ${type}`;
    toast.setAttribute("role", "alert");

    toast.innerHTML = `
        <div class="message-body">${message}</div>
        <button type="button" class="close-button" aria-label="Close" title="Close">×</button>
    `;

    toast.querySelector(".close-button").addEventListener("click", () => {
        toast.remove();
    });

    setTimeout(() => {
        toast.remove();
    }, 5000);

    container.appendChild(toast);
}

document.addEventListener("DOMContentLoaded", function () {
    const btns = document.querySelectorAll(".wishlist-button");

    btns.forEach(btn => {
        btn.addEventListener("click", function () {
            const productId = this.getAttribute('data-product-id');
            const url = this.getAttribute('data-url');
            const isInWishlist = this.classList.contains("in-wishlist");

            fetch(url, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": csrfToken,
                },
                body: JSON.stringify({ product_id: productId }),
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error("Network response was not ok: " + response.status);
                }
                return response.json();
            })
            .then(data => {
                if (data.success) {
                    if (this.classList.contains("in-wishlist")) {
                        // ✅ Currently in wishlist → remove
                        this.classList.remove("in-wishlist");
                        this.innerHTML = `<i data-feather="heart"></i> <span>Add to Wishlist</span>`;
                        showToast(data.message || "Removed from wishlist", "error");
                    } else {
                        // ✅ Not in wishlist → add
                        this.classList.add("in-wishlist");
                        this.innerHTML = `<i data-feather="heart"></i> <span>Remove from Wishlist</span>`;
                        showToast(data.message || "Added to wishlist", "success");
                    }

                    // ✅ Re-render feather icons if you’re using them
                    if (typeof feather !== "undefined") {
                        feather.replace();
                    }

                } else {
                    showToast(data.message || "Something went wrong.", "error");
                }
            })

            .catch(err => {
                console.error("Fetch error:", err);
                showToast("Something went wrong. Please try again.", "error");
            });
        });
    });
});
