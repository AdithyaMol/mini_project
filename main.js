document.addEventListener("DOMContentLoaded", () => {
    const searchForm = document.querySelector(".search-box");
    const searchInput = document.getElementById("searchInput");

    searchForm.addEventListener("submit", (e) => {
        const query = searchInput.value.trim();

        if (query === "") {
            e.preventDefault();
            alert("Please enter a product name to compare.");
        }
        // else: allow form submission (Flask will handle it)
    });
});
