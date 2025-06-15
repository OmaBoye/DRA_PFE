function initSampleChart() {
    const ctx = document.getElementById('sampleChart').getContext('2d');
    const chart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: ['Lun', 'Mar', 'Mer', 'Jeu', 'Ven', 'Sam', 'Dim'],
            datasets: [
                {
                    label: 'Échantillons Collectés',
                    data: [12, 19, 15, 24, 18, 10, 5],
                    backgroundColor: 'rgba(70, 128, 255, 0.1)',
                    borderColor: 'rgba(70, 128, 255, 1)',
                    borderWidth: 2,
                    tension: 0.3,
                    fill: true
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    mode: 'index',
                    intersect: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: {
                        drawBorder: false,
                        color: 'rgba(0, 0, 0, 0.05)'
                    }
                },
                x: {
                    grid: {
                        display: false
                    }
                }
            },
            interaction: {
                mode: 'nearest',
                axis: 'x',
                intersect: false
            }
        }
    });
}

function initStatusChart() {
    const ctx = document.getElementById('statusChart').getContext('2d');
    const chart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['En Attente', 'En Cours', 'Complété', 'Rejeté'],
            datasets: [{
                data: [8, 12, 24, 3],
                backgroundColor: [
                    'rgba(108, 117, 125, 0.8)',
                    'rgba(255, 186, 87, 0.8)',
                    'rgba(40, 167, 69, 0.8)',
                    'rgba(255, 82, 82, 0.8)'
                ],
                borderWidth: 0,
                hoverOffset: 5
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '70%',
            plugins: {
                legend: {
                    display: false
                }
            }
        }
    });
}
function initStatusChart() {
    const ctx = document.getElementById('statusChart').getContext('2d');
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['Lun', 'Mar', 'Mer', 'Jeu', 'Ven', 'Sam', 'Dim'],
            datasets: [
                {
                    label: 'Collectés',
                    data: [12, 19, 15, 24, 18, 10, 5],
                    backgroundColor: 'rgba(70, 128, 255, 0.8)'
                },
                {
                    label: 'Analysés',
                    data: [8, 12, 10, 15, 12, 5, 2],
                    backgroundColor: 'rgba(40, 167, 69, 0.8)'
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    grid: {
                        drawBorder: false,
                        color: 'rgba(0, 0, 0, 0.05)'
                    }
                },
                x: {
                    grid: {
                        display: false
                    }
                }
            },
            plugins: {
                legend: {
                    position: 'bottom'
                }
            }
        }
    });
}