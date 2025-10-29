/**
 * Search Autocomplete Implementation
 * Provides real-time search suggestions and handles search navigation
 */

(function() {
    'use strict';

    // Configuration
    const CONFIG = {
        searchInput: document.getElementById('search-input'),
        suggestionsBox: document.getElementById('suggestions'),
        searchButton: document.querySelector('.search-box .btn'),
        autocompleteUrl: '/api/search/autocomplete/',
        searchResultsUrl: '/search/',  // Change this to your search results page URL
        debounceDelay: 300,
        minChars: 2,
        maxSuggestions: 5
    };

    let debounceTimer = null;
    let currentFocus = -1;

    /**
     * Initialize search functionality
     */
    function init() {
        if (!CONFIG.searchInput || !CONFIG.suggestionsBox) {
            console.error('Search elements not found');
            return;
        }

        // Event listeners
        CONFIG.searchInput.addEventListener('input', handleInput);
        CONFIG.searchInput.addEventListener('keydown', handleKeydown);
        CONFIG.searchButton.addEventListener('click', performSearch);
        CONFIG.searchInput.addEventListener('focus', handleFocus);

        // Close suggestions when clicking outside
        document.addEventListener('click', function(e) {
            if (!e.target.closest('.search-box')) {
                closeSuggestions();
            }
        });

        // Handle form submission if wrapped in a form
        const form = CONFIG.searchInput.closest('form');
        if (form) {
            form.addEventListener('submit', function(e) {
                e.preventDefault();
                performSearch();
            });
        }
    }

    /**
     * Handle input events with debouncing
     */
    function handleInput(e) {
        const query = e.target.value.trim();

        // Clear existing timer
        clearTimeout(debounceTimer);

        // Close suggestions if query is too short
        if (query.length < CONFIG.minChars) {
            closeSuggestions();
            return;
        }

        // Show loading state
        showLoading();

        // Debounce the API call
        debounceTimer = setTimeout(() => {
            fetchSuggestions(query);
        }, CONFIG.debounceDelay);
    }

    /**
     * Handle keyboard navigation
     */
    function handleKeydown(e) {
        const items = CONFIG.suggestionsBox.querySelectorAll('.suggestion-item');

        if (items.length === 0) return;

        switch(e.key) {
            case 'ArrowDown':
                e.preventDefault();
                currentFocus++;
                if (currentFocus >= items.length) currentFocus = 0;
                setActive(items);
                break;

            case 'ArrowUp':
                e.preventDefault();
                currentFocus--;
                if (currentFocus < 0) currentFocus = items.length - 1;
                setActive(items);
                break;

            case 'Enter':
                e.preventDefault();
                if (currentFocus > -1 && items[currentFocus]) {
                    items[currentFocus].click();
                } else {
                    performSearch();
                }
                break;

            case 'Escape':
                closeSuggestions();
                CONFIG.searchInput.blur();
                break;
        }
    }

    /**
     * Handle input focus
     */
    function handleFocus() {
        const query = CONFIG.searchInput.value.trim();
        if (query.length >= CONFIG.minChars) {
            fetchSuggestions(query);
        }
    }

    /**
     * Set active suggestion item
     */
    function setActive(items) {
        // Remove active class from all items
        items.forEach(item => item.classList.remove('active'));

        // Add active class to current item
        if (currentFocus >= 0 && currentFocus < items.length) {
            items[currentFocus].classList.add('active');
            items[currentFocus].scrollIntoView({ block: 'nearest', behavior: 'smooth' });
        }
    }

    /**
     * Fetch suggestions from API
     */
    async function fetchSuggestions(query) {
        try {
            const url = `${CONFIG.autocompleteUrl}?q=${encodeURIComponent(query)}&size=${CONFIG.maxSuggestions}`;
            const response = await fetch(url);

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();

            if (data.success && data.suggestions) {
                displaySuggestions(data.suggestions, query);
            } else {
                showNoResults();
            }
        } catch (error) {
            console.error('Error fetching suggestions:', error);
            showError();
        }
    }


    // format price
    function formatPrice(amount, currency = "NGN") {
      const hasDecimals = amount % 1 !== 0;

      return new Intl.NumberFormat("en-NG", {
        style: "currency",
        currency: currency,
        minimumFractionDigits: hasDecimals ? 2 : 0,
        maximumFractionDigits: hasDecimals ? 2 : 0
      }).format(amount);
    }


    /**
     * Display suggestions in the dropdown
     */
    function displaySuggestions(suggestions, query) {
        currentFocus = -1;

        if (suggestions.length === 0) {
            showNoResults();
            return;
        }

        let html = '<div class="suggestions-list">';

        suggestions.forEach((suggestion, index) => {
            const product = suggestion.product;
            const highlightedText = highlightMatch(suggestion.text, query);
            const price = product.price ? formatPrice(product.price) : '';
            const discountedPrice = product.discounted_price ? formatPrice(product.discounted_price) : '';
            const imageUrl = (product.product_media?.length && product.product_media[0].image)  || '/static/frontend/assets/images/placeholder.jpg';

            console.log(price)
            console.log(discountedPrice)

            html += `
                <div class="suggestion-item" data-product-id="${product.id}" data-product-slug="${product.slug}" data-query="${escapeHtml(suggestion.text)}">
                    <div class="d-flex align-items-center p-2">
                        <img src="${imageUrl}" alt="${escapeHtml(product.name)}" class="suggestion-image me-3">
                        <div class="flex-grow-1">
                            <div class="suggestion-title">${highlightedText}</div>
                            ${product.category ? `<div class="suggestion-category text-muted small">${escapeHtml(product.category.name)}</div>` : ''}
                        </div>
                        <div class="suggestion-price text-end">
                            ${discountedPrice && discountedPrice !== price ?
                                `<div class="text-danger fw-bold">${discountedPrice}</div>
                                 <div class="text-muted small text-decoration-line-through">${price}</div>` :
                                `<div class="fw-bold">${price}</div>`
                            }
                        </div>
                    </div>
                </div>
            `;
        });

        // Add "View all results" option
        html += `
            <div class="suggestion-item view-all" data-query="${escapeHtml(query)}">
                <div class="p-2 text-center text-primary">
                    <i data-feather="search"></i> View all results for "${escapeHtml(query)}"
                </div>
            </div>
        `;

        html += '</div>';

        CONFIG.suggestionsBox.innerHTML = html;
        CONFIG.suggestionsBox.style.display = 'block';

        // Re-initialize feather icons if using them
        if (typeof feather !== 'undefined') {
            feather.replace();
        }

        // Add click handlers
        attachSuggestionHandlers();
    }

    /**
     * Attach click handlers to suggestion items
     */
    function attachSuggestionHandlers() {
        const items = CONFIG.suggestionsBox.querySelectorAll('.suggestion-item');

        items.forEach(item => {
            item.addEventListener('click', function() {
                const query = this.dataset.query;
                const productId = this.dataset.productId;
                const productSlug = this.dataset.productSlug;

                if (productId) {
                    // Navigate to product detail page
                    window.location.href = `/detail/${productSlug}/`;
                } else {
                    // Navigate to search results page
                    navigateToSearchResults(query);
                }
            });

            // Hover effect
            item.addEventListener('mouseenter', function() {
                const allItems = CONFIG.suggestionsBox.querySelectorAll('.suggestion-item');
                allItems.forEach(el => el.classList.remove('active'));
                this.classList.add('active');
            });
        });
    }

    /**
     * Navigate to search results page
     */
    function navigateToSearchResults(query) {
        const url = `${CONFIG.searchResultsUrl}?q=${encodeURIComponent(query)}`;
        window.location.href = url;
    }

    /**
     * Perform search (when button clicked or Enter pressed)
     */
    function performSearch() {
        const query = CONFIG.searchInput.value.trim();

        if (query.length === 0) {
            CONFIG.searchInput.focus();
            return;
        }

        navigateToSearchResults(query);
    }

    /**
     * Highlight matching text
     */
    function highlightMatch(text, query) {
        const regex = new RegExp(`(${escapeRegex(query)})`, 'gi');
        return escapeHtml(text).replace(regex, '<strong>$1</strong>');
    }



    /**
     * Escape HTML to prevent XSS
     */
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    /**
     * Escape regex special characters
     */
    function escapeRegex(text) {
        return text.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    }

    /**
     * Show loading state
     */
    function showLoading() {
        CONFIG.suggestionsBox.innerHTML = `
            <div class="p-3 text-center text-muted">
                <div class="spinner-border spinner-border-sm me-2" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                Searching...
            </div>
        `;
        CONFIG.suggestionsBox.style.display = 'block';
    }

    /**
     * Show no results message
     */
    function showNoResults() {
        CONFIG.suggestionsBox.innerHTML = `
            <div class="p-3 text-center text-muted">
                <i data-feather="search"></i>
                <div class="mt-2">No results found</div>
            </div>
        `;
        CONFIG.suggestionsBox.style.display = 'block';

        if (typeof feather !== 'undefined') {
            feather.replace();
        }
    }

    /**
     * Show error message
     */
    function showError() {
        CONFIG.suggestionsBox.innerHTML = `
            <div class="p-3 text-center text-danger">
                <i data-feather="alert-circle"></i>
                <div class="mt-2">Something went wrong. Please try again.</div>
            </div>
        `;
        CONFIG.suggestionsBox.style.display = 'block';

        if (typeof feather !== 'undefined') {
            feather.replace();
        }
    }

    /**
     * Close suggestions dropdown
     */
    function closeSuggestions() {
        CONFIG.suggestionsBox.innerHTML = '';
        CONFIG.suggestionsBox.style.display = 'none';
        currentFocus = -1;
    }

    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

})();