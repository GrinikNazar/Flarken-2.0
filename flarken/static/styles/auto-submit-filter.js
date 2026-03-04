document.addEventListener("DOMContentLoaded", function () {

    const filterForm = document.querySelector(".form-inline");

    if (!filterForm) return;

    // Авто-сабміт для select
    document.querySelectorAll(".admin-filter select").forEach(function (el) {
        el.addEventListener("change", function () {
            filterForm.submit();
        });
    });

    // Авто-сабміт для чекбоксів
    document.querySelectorAll(".admin-filter input[type=checkbox]").forEach(function (el) {
        el.addEventListener("change", function () {
            filterForm.submit();
        });
    });

});