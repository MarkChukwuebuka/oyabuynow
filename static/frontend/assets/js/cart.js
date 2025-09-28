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

    // Close button handler
    toast.querySelector(".close-button").addEventListener("click", () => {
        toast.remove();
    });

    // Auto remove after 5s
    setTimeout(() => {
        toast.remove();
    }, 5000);

    container.appendChild(toast);
}


function updateCartCounter(newCount) {
    const counter = document.getElementById("cart-counter");
    if (counter) {
        counter.textContent = newCount;
    }
}

document.addEventListener("DOMContentLoaded", function () {
    const btns = document.querySelectorAll(".addcart-button");

    btns.forEach(btn => {
        btn.addEventListener("click", function () {
            const productId = this.dataset.productId;
            const addUrl = this.dataset.url;
            const removeUrl = this.dataset.removeUrl;
            const isAdded = this.classList.contains("in-cart"); // check if already in cart

            const url = isAdded ? removeUrl : addUrl;

            fetch(url, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": csrfToken,  // make sure csrfToken is defined in template
                },
                body: JSON.stringify({ product_id: productId })
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error("Network response was not ok: " + response.status);
                }
                return response.json();
            })
            .then(data => {
                console.log("Server response:", data);

                if (data.success) {
                    if (isAdded) {
                        this.innerHTML = `Add <span class="add-icon bg-light-gray"><i class="fa-solid fa-plus"></i></span>`;
                        this.classList.remove("in-cart");
                    } else {
                        this.innerHTML = `Remove from Cart`;
                        this.classList.add("in-cart");
                    }
                    if (data.success) {
                        if (isAdded) {
                            this.innerHTML = `Add <span class="add-icon bg-light-gray"><i class="fa-solid fa-plus"></i></span>`;
                            this.classList.remove("in-cart");
                            showToast(data.message, "error");
                        } else {
                            this.innerHTML = `Remove from Cart`;
                            this.classList.add("in-cart");
                            showToast(data.message, "success");

                        }

                        if (data.cart_count !== undefined) {
                            updateCartCounter(data.cart_count);
                        }

                    } else {
                        showToast(data.message, "error");
                    }
                } else {
                    alert("Error: " + data.message);
                }
            })
            .catch(err => {
                console.error("Fetch error:", err);
                alert("Something went wrong. Please try again.");
            });
        });








    });
});
