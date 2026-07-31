// ============================================
// DATAINSIGHT
// script.js
// ============================================


// ===============================
// Search Dataset Table
// ===============================

const searchInput = document.getElementById("searchInput");

if (searchInput) {

    searchInput.addEventListener("keyup", function () {

        const value = this.value.toLowerCase();

        document.querySelectorAll("#datasetTable tbody tr").forEach(row => {

            row.style.display =
                row.innerText.toLowerCase().includes(value)
                ? ""
                : "none";

        });

    });

}



// ===============================
// Charts
// ===============================

const overviewCanvas = document.getElementById("overviewChart");
const qualityCanvas = document.getElementById("qualityChart");

if (overviewCanvas && qualityCanvas && typeof UPLOAD_ID !== "undefined") {

    fetch(`/chart-data/${UPLOAD_ID}`)

    .then(response => response.json())

    .then(data => {

        Chart.defaults.color = "#cbd5e1";

        Chart.defaults.font.family = "Poppins";



        // ==========================
        // Bar Chart
        // ==========================

        new Chart(overviewCanvas, {

            type: "bar",

            data: {

                labels: data.labels,

                datasets: [{

                    label: "Dataset Statistics",

                    data: data.values,

                    backgroundColor: [

                        "#3b82f6",

                        "#6366f1",

                        "#8b5cf6",

                        "#06b6d4"

                    ],

                    borderRadius: 10,

                    borderSkipped: false

                }]

            },

            options: {

                maintainAspectRatio: false,

                responsive: true,

                plugins: {

                    legend: {

                        display: false

                    }

                },

                scales: {

                    x: {

                        grid: {

                            display: false

                        }

                    },

                    y: {

                        beginAtZero: true,

                        grid: {

                            color: "rgba(255,255,255,.08)"

                        }

                    }

                }

            }

        });



        // ==========================
        // Doughnut Chart
        // ==========================

        new Chart(qualityCanvas, {

            type: "doughnut",

            data: {

                labels: [

                    "Missing",

                    "Valid"

                ],

                datasets: [{

                    data: [

                        data.missing,

                        data.valid

                    ],

                    backgroundColor: [

                        "#ef4444",

                        "#3b82f6"

                    ],

                    borderWidth: 0

                }]

            },

            options: {

                maintainAspectRatio: false,

                cutout: "65%",

                plugins: {

                    legend: {

                        position: "bottom",

                        labels: {

                            padding: 20

                        }

                    }

                }

            }

        });

    })

    .catch(error => {

        console.log(error);

    });

}