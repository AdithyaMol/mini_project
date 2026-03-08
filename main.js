document.addEventListener("DOMContentLoaded", () => {

    /* ================= SEARCH VALIDATION ================= */

    const searchForm = document.querySelector(".search-box form");
    const searchInput = document.querySelector(".search-box input[name='q']");

    if (searchForm && searchInput) {
        searchForm.addEventListener("submit", (e) => {

            const query = searchInput.value.trim();

            if (query === "") {
                e.preventDefault();
                alert("Please enter a product name to search.");
            }
        });
    }


    /* ================= PRODUCT CARD CLICK FIX ================= */

    const productLinks = document.querySelectorAll(".product-link");

    productLinks.forEach(link => {
        link.addEventListener("click", () => {
            link.style.opacity = "0.8";
        });
    });


    /* ================= WISHLIST BUTTON ANIMATION ================= */

    const wishlistButtons = document.querySelectorAll(".btn-wishlist");

    wishlistButtons.forEach(btn => {
        btn.addEventListener("click", () => {

            btn.style.transform = "scale(1.2)";
            btn.style.color = "#7c3aed";

            setTimeout(() => {
                btn.style.transform = "scale(1)";
            }, 200);
        });
    });

});
