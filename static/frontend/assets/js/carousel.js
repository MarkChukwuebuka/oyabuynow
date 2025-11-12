// Carousel Configuration
const CAROUSEL_CONFIG = {
    autoplayInterval: 5000,
    transitionDuration: 500,
    apiEndpoint: '/api/banners/' // Update this to your actual endpoint
};

// Fallback banner data
const FALLBACK_BANNERS = {
    main: [
        {
            id: 'fallback-main-1',
            title: 'Stay home & get your orders delivered to your',
            subtitle: 'Doorstep',
            description: 'Best comfy wears to match your style.',
            image: '/static/frontend/assets/images/banners/clothes.jpg',
            discount_title: 'Exclusive offer',
            discount_text: '30% Off',
            order: 0
        }
    ],
    side: [
        {
            id: 'fallback-side-1',
            title: 'Electronics Deals',
            subtitle: null,
            description: 'Upgrade your home with our awesome products',
            image: '/static/frontend/assets/images/banners/appliances.jpg',
            discount_title: 'OFF',
            discount_text: '45%',
            order: 0
        },
        {
            id: 'fallback-side-2',
            title: 'Awoof deals',
            subtitle: 'Jewelry Market',
            description: 'Start your daily shopping with some Jewelry products',
            image: '/static/frontend/assets/images/banners/jewelry.jpg',
            discount_title: null,
            discount_text: null,
            order: 1
        }
    ]
};

class Carousel {
    constructor(containerSelector, type = 'Main') {
        this.container = document.querySelector(containerSelector);
        this.carouselContainer = this.container.querySelector('.carousel-container');
        this.indicatorsContainer = this.container.querySelector('.carousel-indicators');
        this.prevBtn = this.container.querySelector('.prev');
        this.nextBtn = this.container.querySelector('.next');
        this.type = type;
        this.currentIndex = 0;
        this.slides = [];
        this.autoplayTimer = null;
        this.useFallback = false;

        this.init();
    }

    init() {
        this.prevBtn.addEventListener('click', () => this.prev());
        this.nextBtn.addEventListener('click', () => this.next());
    }

    async fetchBanners() {
        try {
            const response = await fetch(`${CAROUSEL_CONFIG.apiEndpoint}?type=${this.type}`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                },
                // Add timeout
                signal: AbortSignal.timeout(5000)
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();

            // Check if data is empty or invalid
            if (!Array.isArray(data) || data.length === 0) {
                console.warn('No banners returned from API, using fallback');
                return this.getFallbackBanners();
            }

            return data;
        } catch (error) {
            console.error('Error fetching banners, using fallback:', error);
            return this.getFallbackBanners();
        }
    }

    getFallbackBanners() {
        this.useFallback = true;
        return FALLBACK_BANNERS[this.type] || [];
    }

    showStaticFallback() {
        // Hide carousel wrapper
        const carouselWrapper = document.getElementById('carouselWrapper');
        if (carouselWrapper) {
            carouselWrapper.style.display = 'none';
        }

        // Show static banners
        const staticBanners = document.getElementById('staticBanners');
        if (staticBanners) {
            staticBanners.style.display = 'flex';
        }
    }

    createSlide(banner, isMain = true) {
        const slide = document.createElement('div');
        slide.className = 'carousel-slide';

        if (isMain) {
            slide.innerHTML = `
                <a href="{% url 'shop' %}">
                    <div class="home-contain h-100">
                        <div class="h-100">
                            <img src="${banner.image}" class="bg-img" alt="${banner.title}" onerror="this.src='/static/frontend/assets/images/banners/clothes.jpg'">
                        </div>
                        <div class="home-detail p-center-left w-75">
                            <div>
                                ${banner.discount_title ? `<h6><span>${banner.discount_text || ''}</span></h6>` : ''}
                                <h1 class="text-uppercase" style="color:black;">${banner.title} ${banner.subtitle ? `<span class="daily">${banner.subtitle}</span>` : ''}</h1>
                                ${banner.description ? `<p class="w-75 d-none d-sm-block">${banner.description}</p>` : ''}

                            </div>
                        </div>
                    </div>
                </a>
            `;
        } else {
            slide.innerHTML = `
                <a href="{% url 'shop' %}">
                    <div class="home-contain">
                        <img src="${banner.image}" class="bg-img" alt="${banner.title}" onerror="this.src='/static/frontend/assets/images/banners/appliances.jpg'">
                        <div class="home-detail p-center-left home-p-sm w-75">
                            <div>
                                ${banner.discount_text ? `<h2 class="mt-0 text-danger">${banner.discount_text} <span class="discount text-title"></span></h2>` : ''}
                                <h3 class="${banner.discount_text ? 'theme-color' : 'mt-0 theme-color fw-bold'}">${banner.title}</h3>
                                ${banner.subtitle ? `<h4 class="text-danger">${banner.subtitle}</h4>` : ''}
                                ${banner.description ? `<p class="organic">${banner.description}</p>` : ''}

                            </div>
                        </div>
                    </div>
                </a>
            `;
        }

        return slide;
    }

    createIndicators() {
        this.indicatorsContainer.innerHTML = '';

        // Only show indicators if there's more than one slide
        if (this.slides.length <= 1) {
            return;
        }

        this.slides.forEach((_, index) => {
            const indicator = document.createElement('div');
            indicator.className = `indicator ${index === 0 ? 'active' : ''}`;
            indicator.addEventListener('click', () => this.goToSlide(index));
            this.indicatorsContainer.appendChild(indicator);
        });
    }

    updateIndicators() {
        const indicators = this.indicatorsContainer.querySelectorAll('.indicator');
        indicators.forEach((indicator, index) => {
            indicator.classList.toggle('active', index === this.currentIndex);
        });
    }

    showControls() {
        // Only show controls if there's more than one slide
        if (this.slides.length > 1) {
            this.prevBtn.style.display = 'flex';
            this.nextBtn.style.display = 'flex';
        }
    }

    goToSlide(index) {
        this.currentIndex = index;
        const offset = -this.currentIndex * 100;
        this.carouselContainer.style.transform = `translateX(${offset}%)`;
        this.updateIndicators();
        this.resetAutoplay();
    }

    next() {
        this.currentIndex = (this.currentIndex + 1) % this.slides.length;
        this.goToSlide(this.currentIndex);
    }

    prev() {
        this.currentIndex = (this.currentIndex - 1 + this.slides.length) % this.slides.length;
        this.goToSlide(this.currentIndex);
    }

    startAutoplay() {
        // Only autoplay if there's more than one slide
        if (this.slides.length <= 1) {
            return;
        }

        this.autoplayTimer = setInterval(() => {
            this.next();
        }, CAROUSEL_CONFIG.autoplayInterval);
    }

    stopAutoplay() {
        if (this.autoplayTimer) {
            clearInterval(this.autoplayTimer);
        }
    }

    resetAutoplay() {
        this.stopAutoplay();
        this.startAutoplay();
    }

    async render() {
        try {
            const banners = await this.fetchBanners();

            if (banners.length === 0) {
                console.warn('No banners available, showing static fallback');
                // Only show static fallback on the main carousel's final render
                if (this.type === 'Main') {
                    this.showStaticFallback();
                }
                return;
            }

            this.carouselContainer.innerHTML = '';
            this.slides = [];

            banners.forEach(banner => {
                const slide = this.createSlide(banner, this.type === 'main');
                this.carouselContainer.appendChild(slide);
                this.slides.push(slide);
            });

            this.createIndicators();
            this.showControls();
            this.startAutoplay();

            // Pause autoplay on hover
            this.container.addEventListener('mouseenter', () => this.stopAutoplay());
            this.container.addEventListener('mouseleave', () => this.startAutoplay());

            // If using fallback data, log it
            if (this.useFallback) {
                console.info(`Using fallback banners for ${this.type} carousel`);
            }

        } catch (error) {
            console.error('Error rendering carousel:', error);
            // Show static fallback on critical error
            if (this.type === 'main') {
                this.showStaticFallback();
            }
        }
    }
}

// Initialize carousels when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    try {
        const mainCarousel = new Carousel('#mainCarousel', 'Main');
        const sideCarousel = new Carousel('#sideCarousel', 'Side');

        // Render both carousels
        Promise.all([
            mainCarousel.render(),
            sideCarousel.render()
        ]).catch(error => {
            console.error('Failed to render carousels:', error);
            // Show static fallback as last resort
            const staticBanners = document.getElementById('staticBanners');
            const carouselWrapper = document.getElementById('carouselWrapper');
            if (staticBanners && carouselWrapper) {
                carouselWrapper.style.display = 'none';
                staticBanners.style.display = 'flex';
            }
        });
    } catch (error) {
        console.error('Failed to initialize carousels:', error);
        // Show static fallback
        const staticBanners = document.getElementById('staticBanners');
        const carouselWrapper = document.getElementById('carouselWrapper');
        if (staticBanners && carouselWrapper) {
            carouselWrapper.style.display = 'none';
            staticBanners.style.display = 'flex';
        }
    }
});