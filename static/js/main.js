/**
 * TileShop Premium - Main JavaScript
 * Handles UI interactions: mobile menu, cart badge, message auto-dismiss
 */

document.addEventListener('DOMContentLoaded', function () {

    // ==========================================
    // Mobile Menu Toggle
    // ==========================================
    const menuBtn = document.getElementById('mobile-menu-btn');
    const mobileMenu = document.getElementById('mobile-menu');

    if (menuBtn && mobileMenu) {
        menuBtn.addEventListener('click', function () {
            const isHidden = mobileMenu.classList.contains('hidden');
            mobileMenu.classList.toggle('hidden', !isHidden);
            menuBtn.setAttribute('aria-expanded', isHidden ? 'true' : 'false');
        });
    }

    // ==========================================
    // Auto-dismiss flash messages after 4 seconds
    // ==========================================
    const messages = document.querySelectorAll('.message-alert');
    messages.forEach(function (msg) {
        setTimeout(function () {
            msg.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
            msg.style.opacity = '0';
            msg.style.transform = 'translateY(-8px)';
            setTimeout(function () { msg.remove(); }, 400);
        }, 4000);
    });

    // ==========================================
    // Active nav link highlighting
    // ==========================================
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('nav a[href]');
    navLinks.forEach(function (link) {
        const href = new URL(link.href, window.location.origin).pathname;
        if (href !== '/' && currentPath.startsWith(href)) {
            link.classList.add('text-tile-gold');
            link.classList.remove('text-gray-300');
        }
    });

    // ==========================================
    // Smooth add-to-cart feedback (cart badge update)
    // ==========================================
    const cartForms = document.querySelectorAll('form[action*="add"]');
    cartForms.forEach(function (form) {
        form.addEventListener('submit', function () {
            const btn = form.querySelector('button[type="submit"]');
            if (btn) {
                const original = btn.innerHTML;
                btn.innerHTML = '<svg class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path></svg> Adding...';
                btn.disabled = true;
            }
        });
    });

    // ==========================================
    // Quantity input: select all on focus
    // ==========================================
    const quantityInputs = document.querySelectorAll('input[name="quantity"]');
    quantityInputs.forEach(function (input) {
        input.addEventListener('focus', function () { this.select(); });
    });

    // ==========================================
    // Lazy loading images
    // ==========================================
    if ('IntersectionObserver' in window) {
        const lazyImages = document.querySelectorAll('img[data-src]');
        const imageObserver = new IntersectionObserver(function (entries) {
            entries.forEach(function (entry) {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    img.src = img.dataset.src;
                    img.removeAttribute('data-src');
                    imageObserver.unobserve(img);
                }
            });
        });
        lazyImages.forEach(function (img) { imageObserver.observe(img); });
    }

    // ==========================================
    // model-viewer: handle loading state
    // ==========================================
    const modelViewers = document.querySelectorAll('model-viewer');
    modelViewers.forEach(function (mv) {
        mv.addEventListener('load', function () {
            mv.style.opacity = '1';
        });
        mv.addEventListener('error', function () {
            console.warn('3D model failed to load for:', mv.getAttribute('src'));
            // Show fallback image if available
            const fallbackImg = mv.nextElementSibling;
            if (fallbackImg && fallbackImg.tagName === 'IMG') {
                mv.style.display = 'none';
                fallbackImg.style.display = 'block';
            }
        });
    });

});
