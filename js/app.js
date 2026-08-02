document.addEventListener('DOMContentLoaded', async () => {
    try {
        const [scRes, hnRes, cfRes, steamRes] = await Promise.all([
            fetch('data/statcounter.json').catch(() => null),
            fetch('data/hackernews.json').catch(() => null),
            fetch('data/cloudflare.json').catch(() => null),
            fetch('data/steam.json').catch(() => null)
        ]);
        
        let scData, hnData, cfData, steamData;
        
        if (scRes && scRes.ok) scData = await scRes.json();
        if (hnRes && hnRes.ok) hnData = await hnRes.json();
        if (cfRes && cfRes.ok) cfData = await cfRes.json();
        if (steamRes && steamRes.ok) steamData = await steamRes.json();

        if (scData) initStatCounterChart(scData);
        if (hnData) initHackerNewsChart(hnData);
        
        if (cfData) {
            initCloudflareChart(cfData);
        } else {
            const cfContainer = document.getElementById('cf-loader');
            if(cfContainer) {
                cfContainer.parentElement.innerHTML = '<div style="padding: 20px; text-align: center; color: var(--text-secondary);">Cloudflare API Token required to fetch data.</div>';
            }
        }
        
        if (steamData) {
            initSteamChart(steamData);
        }
        
    } catch (error) {
        console.error('Error initializing dashboard:', error);
        document.querySelectorAll('.loader').forEach(l => {
            l.style.borderTopColor = '#ef4444';
            l.style.animation = 'none';
        });
    }
});

// Common Chart.js defaults for our aesthetic
Chart.defaults.color = '#94a3b8';
Chart.defaults.font.family = "'Inter', system-ui, sans-serif";
Chart.defaults.plugins.tooltip.backgroundColor = 'rgba(15, 17, 26, 0.9)';
Chart.defaults.plugins.tooltip.titleColor = '#fff';
Chart.defaults.plugins.tooltip.bodyColor = '#e2e8f0';
Chart.defaults.plugins.tooltip.borderColor = 'rgba(255,255,255,0.1)';
Chart.defaults.plugins.tooltip.borderWidth = 1;
Chart.defaults.plugins.tooltip.padding = 12;
Chart.defaults.plugins.tooltip.cornerRadius = 8;
Chart.defaults.plugins.tooltip.displayColors = false;

function initStatCounterChart(data) {
    document.getElementById('sc-loader').style.display = 'none';
    
    // Process data to filter down points if needed, or just show all
    // Since 2009 it's ~180 points.
    
    const labels = data.map(d => d.date);
    const shares = data.map(d => d.linux_share);
    
    // Update summary stat
    const currentShare = shares[shares.length - 1];
    const prevShare = shares[shares.length - 13] || shares[shares.length - 2]; // YoY or MoM
    const diff = (currentShare - prevShare).toFixed(2);
    const trendEl = document.getElementById('sc-trend');
    
    document.getElementById('sc-current').textContent = currentShare.toFixed(2);
    
    if (diff > 0) {
        trendEl.innerHTML = `<i class="fa-solid fa-arrow-trend-up"></i> +${diff}% YoY`;
        trendEl.style.color = 'var(--success-color)';
    } else {
        trendEl.innerHTML = `<i class="fa-solid fa-arrow-trend-down"></i> ${diff}% YoY`;
        trendEl.style.color = '#ef4444';
        trendEl.style.background = 'rgba(239, 68, 68, 0.1)';
    }

    const ctx = document.getElementById('scChart').getContext('2d');
    
    // Create gradient
    const gradient = ctx.createLinearGradient(0, 0, 0, 400);
    gradient.addColorStop(0, 'rgba(240, 80, 51, 0.5)');
    gradient.addColorStop(1, 'rgba(240, 80, 51, 0.0)');

    new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Linux Desktop Share (%)',
                data: shares,
                borderColor: '#f05033',
                backgroundColor: gradient,
                borderWidth: 2,
                pointRadius: 0,
                pointHitRadius: 10,
                fill: true,
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false,
            },
            plugins: {
                legend: { display: false }
            },
            scales: {
                x: {
                    grid: { display: false },
                    ticks: { maxTicksLimit: 10 }
                },
                y: {
                    grid: { color: 'rgba(255,255,255,0.05)' },
                    beginAtZero: true
                }
            }
        }
    });
}

function initHackerNewsChart(data) {
    document.getElementById('hn-loader').style.display = 'none';
    
    const labels = data.map(d => d.year);
    const mentions = data.map(d => d.mentions);
    const maxMentions = Math.max(...mentions);

    // Summary
    const currentYearMentions = mentions[mentions.length - 1];
    const prevYearMentions = mentions[mentions.length - 2];
    
    const trendEl = document.getElementById('hn-trend');
    document.getElementById('hn-current').textContent = currentYearMentions;
    
    if (prevYearMentions) {
        const diff = currentYearMentions - prevYearMentions;
        if (diff > 0) {
            trendEl.innerHTML = `<i class="fa-solid fa-arrow-trend-up"></i> +${diff} vs last year`;
        } else {
            trendEl.innerHTML = `<i class="fa-solid fa-arrow-trend-down"></i> ${diff} vs last year`;
            trendEl.style.color = '#ef4444';
            trendEl.style.background = 'rgba(239, 68, 68, 0.1)';
        }
    } else {
        trendEl.style.display = 'none';
    }

    const ctx = document.getElementById('hnChart').getContext('2d');

    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Mentions',
                data: mentions,
                backgroundColor: mentions.map(m => m === maxMentions ? 'rgba(240, 80, 51, 0.9)' : 'rgba(240, 80, 51, 0.3)'),
                borderColor: 'rgba(240, 80, 51, 0.8)',
                borderWidth: 1,
                borderRadius: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return ` ${context.parsed.y} mentions`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: { display: false }
                },
                y: {
                    grid: { color: 'rgba(255,255,255,0.05)' },
                    beginAtZero: true
                }
            }
        }
    });
}

function initCloudflareChart(data) {
    const loader = document.getElementById('cf-loader');
    if (loader) loader.style.display = 'none';

    if (!data || !Array.isArray(data)) return;

    const labels = data.map(d => {
        const date = new Date(d.date);
        return date.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
    });

    const linuxData = data.map(d => d.linux_share);

    const ctx = document.getElementById('cfChart').getContext('2d');
    
    const gradient = ctx.createLinearGradient(0, 0, 0, 400);
    gradient.addColorStop(0, 'rgba(56, 189, 248, 0.5)'); 
    gradient.addColorStop(1, 'rgba(56, 189, 248, 0.0)');

    new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Linux HTTP Traffic Share (%)',
                data: linuxData,
                borderColor: '#38bdf8',
                backgroundColor: gradient,
                borderWidth: 2,
                pointRadius: 0,
                pointHitRadius: 10,
                fill: true,
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false,
            },
            plugins: {
                legend: { display: false }
            },
            scales: {
                x: {
                    grid: { display: false },
                    ticks: { maxTicksLimit: 10 }
                },
                y: {
                    grid: { color: 'rgba(255,255,255,0.05)' },
                    beginAtZero: true
                }
            }
        }
    });
}

function initSteamChart(data) {
    const loader = document.getElementById('steam-loader');
    if (loader) loader.style.display = 'none';
    
    if (!data || data.length === 0) return;

    // Steam didn't track Linux before 2014
    data = data.filter(d => d.date >= '2014');
    if (data.length === 0) return;

    // Display current value
    const current = data[data.length - 1];
    const currentEl = document.getElementById('steam-current');
    if (currentEl) currentEl.textContent = current.linux_share.toFixed(2);

    const labels = data.map(d => d.date);
    const shares = data.map(d => d.linux_share);

    const ctx = document.getElementById('steamChart').getContext('2d');
    
    const gradient = ctx.createLinearGradient(0, 0, 0, 400);
    gradient.addColorStop(0, 'rgba(16, 185, 129, 0.5)'); // Green-ish for Steam/gaming
    gradient.addColorStop(1, 'rgba(16, 185, 129, 0.0)');

    new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Steam Linux Share (%)',
                data: shares,
                borderColor: '#10b981',
                backgroundColor: gradient,
                borderWidth: 2,
                pointRadius: 4,
                pointBackgroundColor: '#10b981',
                pointHitRadius: 10,
                fill: true,
                tension: 0.3
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false,
            },
            plugins: {
                legend: { display: false }
            },
            scales: {
                x: {
                    grid: { display: false },
                    ticks: { maxTicksLimit: 10 }
                },
                y: {
                    grid: { color: 'rgba(255,255,255,0.05)' },
                    beginAtZero: true
                }
            }
        }
    });
}
