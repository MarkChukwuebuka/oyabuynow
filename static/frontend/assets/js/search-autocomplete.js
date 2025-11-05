/**
 * Search Autocomplete Implementation (Multi-input version)
 * Provides real-time search suggestions for multiple search fields on the same page.
 */

(function() {
    'use strict';

    // Configuration
    const CONFIG = {
        autocompleteUrl: '/api/search/autocomplete/',
        searchResultsUrl: '/search/',
        debounceDelay: 500,
        minChars: 2,
        maxSuggestions: 5
    };

    let debounceTimer = null;
    let currentFocus = -1;
    let activeContext = null; // Tracks which search box is currently active

    /**
     * Initialize all search inputs on page
     */
    function init() {
        const searchInputs = document.querySelectorAll('input[type="search"], .search-type');
        if (!searchInputs.length) {
            console.error('No search inputs found');
            return;
        }

        searchInputs.forEach(input => {
            const searchBox = input.closest('.search-box, .rightside-box');
            if (!searchBox) return;

            const suggestionsBox = searchBox.querySelector('#suggestions') ||
                createSuggestionsBox(searchBox);

            const searchButton = searchBox.querySelector('button, .close-search');

            // Bind listeners for this input
            input.addEventListener('input', e => handleInput(e, input, suggestionsBox));
            input.addEventListener('keydown', e => handleKeydown(e, input, suggestionsBox));
            input.addEventListener('focus', () => handleFocus(input, suggestionsBox));
            if (searchButton) {
                searchButton.addEventListener('click', () => performSearch(input));
            }

            // If wrapped in a form
            const form = input.closest('form');
            if (form) {
                form.addEventListener('submit', function(e) {
                    e.preventDefault();
                    performSearch(input);
                });
            }
        });

        // Close suggestions when clicking outside any search box
        document.addEventListener('click', function(e) {
            if (!e.target.closest('.search-box, .rightside-box')) {
                closeSuggestions();
            }
        });
    }

    /** Create a suggestions box dynamically if not present */
    function createSuggestionsBox(container) {
        const box = document.createElement('div');
        box.className = 'position-absolute w-100 bg-white border rounded shadow mt-1';
        box.id = 'suggestions';
        container.appendChild(box);
        return box;
    }

    /** Handle input with debounce */
    function handleInput(e, input, suggestionsBox) {
        const query = e.target.value.trim();
        activeContext = { input, suggestionsBox };

        clearTimeout(debounceTimer);

        if (query.length < CONFIG.minChars) {
            closeSuggestions();
            return;
        }

        showLoading(suggestionsBox);
        debounceTimer = setTimeout(() => {
            fetchSuggestions(query, suggestionsBox);
        }, CONFIG.debounceDelay);
    }

    /** Handle keyboard navigation */
    function handleKeydown(e, input, suggestionsBox) {
        const items = suggestionsBox.querySelectorAll('.suggestion-item');
        if (items.length === 0) return;

        switch (e.key) {
            case 'ArrowDown':
                e.preventDefault();
                currentFocus = (currentFocus + 1) % items.length;
                setActive(items);
                break;
            case 'ArrowUp':
                e.preventDefault();
                currentFocus = (currentFocus - 1 + items.length) % items.length;
                setActive(items);
                break;
            case 'Enter':
                e.preventDefault();
                if (currentFocus > -1 && items[currentFocus]) {
                    items[currentFocus].click();
                } else {
                    performSearch(input);
                }
                break;
            case 'Escape':
                closeSuggestions();
                input.blur();
                break;
        }
    }

    /** Handle focus to refetch suggestions */
    function handleFocus(input, suggestionsBox) {
        const query = input.value.trim();
        activeContext = { input, suggestionsBox };
        if (query.length >= CONFIG.minChars) {
            fetchSuggestions(query, suggestionsBox);
        }
    }

    /** Set active suggestion visually */
    function setActive(items) {
        items.forEach(item => item.classList.remove('active'));
        if (currentFocus >= 0 && currentFocus < items.length) {
            items[currentFocus].classList.add('active');
            items[currentFocus].scrollIntoView({ block: 'nearest', behavior: 'smooth' });
        }
    }

    /** Fetch suggestions from API */
    async function fetchSuggestions(query, suggestionsBox) {
        try {
            const url = `${CONFIG.autocompleteUrl}?q=${encodeURIComponent(query)}&size=${CONFIG.maxSuggestions}`;
            const response = await fetch(url);
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            const data = await response.json();
            if (data.success && data.suggestions) {
                displaySuggestions(data.suggestions, query, suggestionsBox);
            } else {
                showNoResults(suggestionsBox);
            }
        } catch (error) {
            console.error('Error fetching suggestions:', error);
            showError(suggestionsBox);
        }
    }

    /** Format price */
    function formatPrice(amount, currency = "NGN") {
        const hasDecimals = amount % 1 !== 0;
        return new Intl.NumberFormat("en-NG", {
            style: "currency",
            currency,
            minimumFractionDigits: hasDecimals ? 2 : 0,
            maximumFractionDigits: hasDecimals ? 2 : 0
        }).format(amount);
    }

    /** Display suggestions */
    function displaySuggestions(suggestions, query, suggestionsBox) {
        currentFocus = -1;
        if (!suggestions.length) {
            showNoResults(suggestionsBox);
            return;
        }

        let html = '<div class="suggestions-list">';
        suggestions.forEach(suggestion => {
            const product = suggestion.product;
            const highlighted = highlightMatch(suggestion.text, query);
            const price = product.price ? formatPrice(product.price) : '';
            const discounted = product.discounted_price ? formatPrice(product.discounted_price) : '';
            const imageUrl = (product.product_media?.length && product.product_media[0].image)
                || '/static/frontend/assets/images/placeholder.jpg';

            html += `
                <div class="suggestion-item" data-product-slug="${product.slug}" data-query="${escapeHtml(suggestion.text)}">
                    <div class="d-flex align-items-center p-2">
                        <img src="${imageUrl}" alt="${escapeHtml(product.name)}" class="suggestion-image me-3">
                        <div class="flex-grow-1">
                            <div class="suggestion-title">${highlighted}</div>
                            ${product.category ? `<div class="text-muted small">${escapeHtml(product.category.name)}</div>` : ''}
                        </div>
                        <div class="suggestion-price text-end">
                            ${discounted && discounted !== price ?
                                `<div class="text-danger fw-bold">${discounted}</div>
                                 <div class="text-muted small text-decoration-line-through">${price}</div>` :
                                `<div class="fw-bold">${price}</div>`
                            }
                        </div>
                    </div>
                </div>`;
        });

        html += `
            <div class="suggestion-item view-all" data-query="${escapeHtml(query)}">
                <div class="p-2 text-center text-primary">
                    <i data-feather="search"></i> View all results for "${escapeHtml(query)}"
                </div>
            </div>
        </div>`;

        suggestionsBox.innerHTML = html;
        suggestionsBox.style.display = 'block';
        if (typeof feather !== 'undefined') feather.replace();
        attachSuggestionHandlers(suggestionsBox);
    }

    /** Attach click handlers */
    function attachSuggestionHandlers(suggestionsBox) {
        suggestionsBox.querySelectorAll('.suggestion-item').forEach(item => {
            item.addEventListener('click', function() {
                const query = this.dataset.query;
                const slug = this.dataset.productSlug;
                if (slug) {
                    window.location.href = `/detail/${slug}/`;
                } else {
                    navigateToSearchResults(query);
                }
            });
        });
    }

    /** Navigate to results */
    function navigateToSearchResults(query) {
        window.location.href = `${CONFIG.searchResultsUrl}?q=${encodeURIComponent(query)}`;
    }

    /** Perform search */
    function performSearch(input) {
        const query = input.value.trim();
        if (query.length === 0) return input.focus();
        navigateToSearchResults(query);
    }

    /** Highlight matched text */
    function highlightMatch(text, query) {
        const regex = new RegExp(`(${escapeRegex(query)})`, 'gi');
        return escapeHtml(text).replace(regex, '<strong>$1</strong>');
    }

    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    function escapeRegex(text) {
        return text.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    }

    /** Feedback states */
    function showLoading(suggestionsBox) {
        suggestionsBox.innerHTML = `
            <div class="p-3 text-center text-muted">
                <div class="spinner-border spinner-border-sm me-2" role="status"></div> Searching...
            </div>`;
        suggestionsBox.style.display = 'block';
    }

    function showNoResults(suggestionsBox) {
        suggestionsBox.innerHTML = `<div class="p-3 text-center text-muted"><i data-feather="search"></i> No results found</div>`;
        suggestionsBox.style.display = 'block';
        if (typeof feather !== 'undefined') feather.replace();
    }

    function showError(suggestionsBox) {
        suggestionsBox.innerHTML = `<div class="p-3 text-center text-danger"><i data-feather="alert-circle"></i> Something went wrong.</div>`;
        suggestionsBox.style.display = 'block';
        if (typeof feather !== 'undefined') feather.replace();
    }

    /** Close all suggestion boxes */
    function closeSuggestions() {
        document.querySelectorAll('#suggestions').forEach(box => {
            box.innerHTML = '';
            box.style.display = 'none';
        });
        currentFocus = -1;
    }

    // Initialize on DOM ready
    document.readyState === 'loading'
        ? document.addEventListener('DOMContentLoaded', init)
        : init();

})();




















///**
// * Search Autocomplete Implementation
// * Provides real-time search suggestions and handles search navigation
// */
//
//(function() {
//    'use strict';
//
//    // Configuration
//    const CONFIG = {
//        searchInput: document.getElementById('search-input'),
//        suggestionsBox: document.getElementById('suggestions'),
//        searchButton: document.querySelector('.search-box .btn'),
//        autocompleteUrl: '/api/search/autocomplete/',
//        searchResultsUrl: '/search/',  // Change this to your search results page URL
//        debounceDelay: 500,
//        minChars: 2,
//        maxSuggestions: 5
//    };
//
//    let debounceTimer = null;
//    let currentFocus = -1;
//
//    /**
//     * Initialize search functionality
//     */
//    function init() {
//        if (!CONFIG.searchInput || !CONFIG.suggestionsBox) {
//            console.error('Search elements not found');
//            return;
//        }
//
//        // Event listeners
//        CONFIG.searchInput.addEventListener('input', handleInput);
//        CONFIG.searchInput.addEventListener('keydown', handleKeydown);
//        CONFIG.searchButton.addEventListener('click', performSearch);
//        CONFIG.searchInput.addEventListener('focus', handleFocus);
//
//        // Close suggestions when clicking outside
//        document.addEventListener('click', function(e) {
//            if (!e.target.closest('.search-box')) {
//                closeSuggestions();
//            }
//        });
//
//        // Handle form submission if wrapped in a form
//        const form = CONFIG.searchInput.closest('form');
//        if (form) {
//            form.addEventListener('submit', function(e) {
//                e.preventDefault();
//                performSearch();
//            });
//        }
//    }
//
//    /**
//     * Handle input events with debouncing
//     */
//    function handleInput(e) {
//        const query = e.target.value.trim();
//
//        // Clear existing timer
//        clearTimeout(debounceTimer);
//
//        // Close suggestions if query is too short
//        if (query.length < CONFIG.minChars) {
//            closeSuggestions();
//            return;
//        }
//
//        // Show loading state
//        showLoading();
//
//        // Debounce the API call
//        debounceTimer = setTimeout(() => {
//            fetchSuggestions(query);
//        }, CONFIG.debounceDelay);
//    }
//
//    /**
//     * Handle keyboard navigation
//     */
//    function handleKeydown(e) {
//        const items = CONFIG.suggestionsBox.querySelectorAll('.suggestion-item');
//
//        if (items.length === 0) return;
//
//        switch(e.key) {
//            case 'ArrowDown':
//                e.preventDefault();
//                currentFocus++;
//                if (currentFocus >= items.length) currentFocus = 0;
//                setActive(items);
//                break;
//
//            case 'ArrowUp':
//                e.preventDefault();
//                currentFocus--;
//                if (currentFocus < 0) currentFocus = items.length - 1;
//                setActive(items);
//                break;
//
//            case 'Enter':
//                e.preventDefault();
//                if (currentFocus > -1 && items[currentFocus]) {
//                    items[currentFocus].click();
//                } else {
//                    performSearch();
//                }
//                break;
//
//            case 'Escape':
//                closeSuggestions();
//                CONFIG.searchInput.blur();
//                break;
//        }
//    }
//
//    /**
//     * Handle input focus
//     */
//    function handleFocus() {
//        const query = CONFIG.searchInput.value.trim();
//        if (query.length >= CONFIG.minChars) {
//            fetchSuggestions(query);
//        }
//    }
//
//    /**
//     * Set active suggestion item
//     */
//    function setActive(items) {
//        // Remove active class from all items
//        items.forEach(item => item.classList.remove('active'));
//
//        // Add active class to current item
//        if (currentFocus >= 0 && currentFocus < items.length) {
//            items[currentFocus].classList.add('active');
//            items[currentFocus].scrollIntoView({ block: 'nearest', behavior: 'smooth' });
//        }
//    }
//
//    /**
//     * Fetch suggestions from API
//     */
//    async function fetchSuggestions(query) {
//        try {
//            const url = `${CONFIG.autocompleteUrl}?q=${encodeURIComponent(query)}&size=${CONFIG.maxSuggestions}`;
//            const response = await fetch(url);
//
//            if (!response.ok) {
//                throw new Error(`HTTP error! status: ${response.status}`);
//            }
//
//            const data = await response.json();
//
//            if (data.success && data.suggestions) {
//                displaySuggestions(data.suggestions, query);
//            } else {
//                showNoResults();
//            }
//        } catch (error) {
//            console.error('Error fetching suggestions:', error);
//            showError();
//        }
//    }
//
//
//    // format price
//    function formatPrice(amount, currency = "NGN") {
//      const hasDecimals = amount % 1 !== 0;
//
//      return new Intl.NumberFormat("en-NG", {
//        style: "currency",
//        currency: currency,
//        minimumFractionDigits: hasDecimals ? 2 : 0,
//        maximumFractionDigits: hasDecimals ? 2 : 0
//      }).format(amount);
//    }
//
//
//    /**
//     * Display suggestions in the dropdown
//     */
//    function displaySuggestions(suggestions, query) {
//        currentFocus = -1;
//
//        if (suggestions.length === 0) {
//            showNoResults();
//            return;
//        }
//
//        let html = '<div class="suggestions-list">';
//
//        suggestions.forEach((suggestion, index) => {
//            const product = suggestion.product;
//            const highlightedText = highlightMatch(suggestion.text, query);
//            const price = product.price ? formatPrice(product.price) : '';
//            const discountedPrice = product.discounted_price ? formatPrice(product.discounted_price) : '';
//            const imageUrl = (product.product_media?.length && product.product_media[0].image)  || '/static/frontend/assets/images/placeholder.jpg';
//
//            console.log(price)
//            console.log(discountedPrice)
//
//            html += `
//                <div class="suggestion-item" data-product-id="${product.id}" data-product-slug="${product.slug}" data-query="${escapeHtml(suggestion.text)}">
//                    <div class="d-flex align-items-center p-2">
//                        <img src="${imageUrl}" alt="${escapeHtml(product.name)}" class="suggestion-image me-3">
//                        <div class="flex-grow-1">
//                            <div class="suggestion-title">${highlightedText}</div>
//                            ${product.category ? `<div class="suggestion-category text-muted small">${escapeHtml(product.category.name)}</div>` : ''}
//                        </div>
//                        <div class="suggestion-price text-end">
//                            ${discountedPrice && discountedPrice !== price ?
//                                `<div class="text-danger fw-bold">${discountedPrice}</div>
//                                 <div class="text-muted small text-decoration-line-through">${price}</div>` :
//                                `<div class="fw-bold">${price}</div>`
//                            }
//                        </div>
//                    </div>
//                </div>
//            `;
//        });
//
//        // Add "View all results" option
//        html += `
//            <div class="suggestion-item view-all" data-query="${escapeHtml(query)}">
//                <div class="p-2 text-center text-primary">
//                    <i data-feather="search"></i> View all results for "${escapeHtml(query)}"
//                </div>
//            </div>
//        `;
//
//        html += '</div>';
//
//        CONFIG.suggestionsBox.innerHTML = html;
//        CONFIG.suggestionsBox.style.display = 'block';
//
//        // Re-initialize feather icons if using them
//        if (typeof feather !== 'undefined') {
//            feather.replace();
//        }
//
//        // Add click handlers
//        attachSuggestionHandlers();
//    }
//
//    /**
//     * Attach click handlers to suggestion items
//     */
//    function attachSuggestionHandlers() {
//        const items = CONFIG.suggestionsBox.querySelectorAll('.suggestion-item');
//
//        items.forEach(item => {
//            item.addEventListener('click', function() {
//                const query = this.dataset.query;
//                const productId = this.dataset.productId;
//                const productSlug = this.dataset.productSlug;
//
//                if (productId) {
//                    // Navigate to product detail page
//                    window.location.href = `/detail/${productSlug}/`;
//                } else {
//                    // Navigate to search results page
//                    navigateToSearchResults(query);
//                }
//            });
//
//            // Hover effect
//            item.addEventListener('mouseenter', function() {
//                const allItems = CONFIG.suggestionsBox.querySelectorAll('.suggestion-item');
//                allItems.forEach(el => el.classList.remove('active'));
//                this.classList.add('active');
//            });
//        });
//    }
//
//    /**
//     * Navigate to search results page
//     */
//    function navigateToSearchResults(query) {
//        const url = `${CONFIG.searchResultsUrl}?q=${encodeURIComponent(query)}`;
//        window.location.href = url;
//    }
//
//    /**
//     * Perform search (when button clicked or Enter pressed)
//     */
//    function performSearch() {
//        const query = CONFIG.searchInput.value.trim();
//
//        if (query.length === 0) {
//            CONFIG.searchInput.focus();
//            return;
//        }
//
//        navigateToSearchResults(query);
//    }
//
//    /**
//     * Highlight matching text
//     */
//    function highlightMatch(text, query) {
//        const regex = new RegExp(`(${escapeRegex(query)})`, 'gi');
//        return escapeHtml(text).replace(regex, '<strong>$1</strong>');
//    }
//
//
//
//    /**
//     * Escape HTML to prevent XSS
//     */
//    function escapeHtml(text) {
//        const div = document.createElement('div');
//        div.textContent = text;
//        return div.innerHTML;
//    }
//
//    /**
//     * Escape regex special characters
//     */
//    function escapeRegex(text) {
//        return text.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
//    }
//
//    /**
//     * Show loading state
//     */
//    function showLoading() {
//        CONFIG.suggestionsBox.innerHTML = `
//            <div class="p-3 text-center text-muted">
//                <div class="spinner-border spinner-border-sm me-2" role="status">
//                    <span class="visually-hidden">Loading...</span>
//                </div>
//                Searching...
//            </div>
//        `;
//        CONFIG.suggestionsBox.style.display = 'block';
//    }
//
//    /**
//     * Show no results message
//     */
//    function showNoResults() {
//        CONFIG.suggestionsBox.innerHTML = `
//            <div class="p-3 text-center text-muted">
//                <i data-feather="search"></i>
//                <div class="mt-2">No results found</div>
//            </div>
//        `;
//        CONFIG.suggestionsBox.style.display = 'block';
//
//        if (typeof feather !== 'undefined') {
//            feather.replace();
//        }
//    }
//
//    /**
//     * Show error message
//     */
//    function showError() {
//        CONFIG.suggestionsBox.innerHTML = `
//            <div class="p-3 text-center text-danger">
//                <i data-feather="alert-circle"></i>
//                <div class="mt-2">Something went wrong. Please try again.</div>
//            </div>
//        `;
//        CONFIG.suggestionsBox.style.display = 'block';
//
//        if (typeof feather !== 'undefined') {
//            feather.replace();
//        }
//    }
//
//    /**
//     * Close suggestions dropdown
//     */
//    function closeSuggestions() {
//        CONFIG.suggestionsBox.innerHTML = '';
//        CONFIG.suggestionsBox.style.display = 'none';
//        currentFocus = -1;
//    }
//
//    // Initialize when DOM is ready
//    if (document.readyState === 'loading') {
//        document.addEventListener('DOMContentLoaded', init);
//    } else {
//        init();
//    }
//
//})();