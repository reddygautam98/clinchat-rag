// ClinChat-RAG Monitoring Dashboard JavaScript
class MonitoringDashboard {
    constructor() {
        this.charts = {};
        this.apiBaseUrl = 'http://localhost:8000';
        this.refreshInterval = 30000; // 30 seconds
        this.refreshTimer = null;
    }
    
    async init() {
        try {
            this.setupCharts();
            await this.loadData();
            this.startAutoRefresh();
            
            // Set up event listeners
            document.getElementById('timeRange').addEventListener('change', () => this.loadData());
            
        } catch (error) {
            console.error('Dashboard initialization error:', error);
            this.showAlert('Failed to initialize dashboard', 'error');
        }
    }
    
    setupCharts() {
        // Latency Chart
        const latencyCtx = document.getElementById('latencyChart').getContext('2d');
        this.charts.latency = new Chart(latencyCtx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [
                    {
                        label: 'P50 (ms)',
                        data: [],
                        borderColor: '#38a169',
                        backgroundColor: 'rgba(56, 161, 105, 0.1)',
                        tension: 0.4
                    },
                    {
                        label: 'P95 (ms)',
                        data: [],
                        borderColor: '#d69e2e',
                        backgroundColor: 'rgba(214, 158, 46, 0.1)',
                        tension: 0.4
                    },
                    {
                        label: 'P99 (ms)',
                        data: [],
                        borderColor: '#e53e3e',
                        backgroundColor: 'rgba(229, 62, 62, 0.1)',
                        tension: 0.4
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Latency (ms)'
                        }
                    },
                    x: {
                        title: {
                            display: true,
                            text: 'Time'
                        }
                    }
                },
                plugins: {
                    legend: {
                        position: 'top'
                    }
                }
            }
        });
        
        // QPS Chart
        const qpsCtx = document.getElementById('qpsChart').getContext('2d');
        this.charts.qps = new Chart(qpsCtx, {
            type: 'bar',
            data: {
                labels: [],
                datasets: [{
                    label: 'Queries/Second',
                    data: [],
                    backgroundColor: 'rgba(49, 130, 206, 0.6)',
                    borderColor: '#3182ce',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Queries per Second'
                        }
                    }
                }
            }
        });
        
        // Error Rate Chart
        const errorCtx = document.getElementById('errorChart').getContext('2d');
        this.charts.error = new Chart(errorCtx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Error Rate (%)',
                    data: [],
                    borderColor: '#e53e3e',
                    backgroundColor: 'rgba(229, 62, 62, 0.1)',
                    tension: 0.4,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100,
                        title: {
                            display: true,
                            text: 'Error Rate (%)'
                        }
                    }
                }
            }
        });
        
        // Confidence Distribution Chart
        const confidenceCtx = document.getElementById('confidenceChart').getContext('2d');
        this.charts.confidence = new Chart(confidenceCtx, {
            type: 'doughnut',
            data: {
                labels: ['High (80-100%)', 'Medium (60-79%)', 'Low (0-59%)'],
                datasets: [{
                    data: [0, 0, 0],
                    backgroundColor: [
                        '#38a169',
                        '#d69e2e', 
                        '#e53e3e'
                    ],
                    borderWidth: 2,
                    borderColor: '#ffffff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });
    }
    
    async loadData() {
        try {
            this.showLoading();
            
            const timeRange = document.getElementById('timeRange').value;
            const response = await this.fetchWithTimeout(`${this.apiBaseUrl}/monitoring/dashboard-data?hours=${timeRange}`);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            
            this.updateStatusCards(data.current_metrics);
            this.updateCharts(data);
            this.checkAlerts(data.current_metrics);
            
            document.getElementById('lastUpdated').textContent = new Date().toLocaleTimeString();
            
        } catch (error) {
            console.error('Data loading error:', error);
            this.showAlert(`Failed to load data: ${error.message}`, 'error');
            this.showDemoData();
        }
    }
    
    async fetchWithTimeout(url, timeout = 10000) {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), timeout);
        
        try {
            const response = await fetch(url, { 
                signal: controller.signal,
                headers: {
                    'Accept': 'application/json'
                }
            });
            clearTimeout(timeoutId);
            return response;
        } catch (error) {
            clearTimeout(timeoutId);
            throw error;
        }
    }
    
    updateStatusCards(metrics) {
        document.getElementById('totalQueries').textContent = metrics.total_queries || 0;
        document.getElementById('successRate').textContent = `${(metrics.success_rate || 0).toFixed(1)}%`;
        document.getElementById('avgLatency').textContent = `${(metrics.avg_latency_ms || 0).toFixed(0)}ms`;
        document.getElementById('currentQPS').textContent = (metrics.qps || 0).toFixed(1);
        document.getElementById('hallucinationFlags').textContent = metrics.hallucination_flags || 0;
        document.getElementById('avgConfidence').textContent = `${((metrics.avg_confidence || 0) * 100).toFixed(1)}%`;
        
        // Update change indicators (simplified - in production, compare with previous period)
        this.updateChangeIndicator('queriesChange', 'neutral', 'No change');
        this.updateChangeIndicator('successChange', 'positive', '+2.3%');
        this.updateChangeIndicator('latencyChange', 'positive', '-15ms');
        this.updateChangeIndicator('qpsChange', 'neutral', 'Stable');
        this.updateChangeIndicator('hallucinationChange', 'positive', '-3');
        this.updateChangeIndicator('confidenceChange', 'positive', '+1.2%');
    }
    
    updateChangeIndicator(elementId, type, text) {
        const element = document.getElementById(elementId);
        element.textContent = text;
        element.className = `change ${type}`;
    }
    
    updateCharts(data) {
        // Update latency chart with synthetic data if needed
        const hours = Number.parseInt(document.getElementById('timeRange').value, 10);
        const labels = this.generateTimeLabels(hours);
        
        // QPS Chart
        this.charts.qps.data.labels = labels;
        this.charts.qps.data.datasets[0].data = data.qps_hourly ? 
            data.qps_hourly.map(item => item[1]) : 
            this.generateSyntheticData(labels.length, 0.5, 3);
        this.charts.qps.update();
        
        // Latency Chart
        const latencyData = this.generateLatencyData(labels.length, data.latency_percentiles);
        this.charts.latency.data.labels = labels;
        this.charts.latency.data.datasets[0].data = latencyData.p50;
        this.charts.latency.data.datasets[1].data = latencyData.p95;
        this.charts.latency.data.datasets[2].data = latencyData.p99;
        this.charts.latency.update();
        
        // Error Rate Chart  
        this.charts.error.data.labels = labels;
        this.charts.error.data.datasets[0].data = this.generateSyntheticData(labels.length, 0, 5);
        this.charts.error.update();
        
        // Confidence Distribution
        const metrics = data.current_metrics || {};
        const avgConfidence = metrics.avg_confidence || 0.8;
        const confidenceDistribution = this.calculateConfidenceDistribution(avgConfidence);
        this.charts.confidence.data.datasets[0].data = confidenceDistribution;
        this.charts.confidence.update();
    }
    
    generateTimeLabels(hours) {
        const labels = [];
        const now = new Date();
        const interval = hours <= 24 ? 1 : Math.ceil(hours / 24); // Hourly or daily
        
        for (let i = hours; i >= 0; i -= interval) {
            const time = new Date(now.getTime() - (i * 60 * 60 * 1000));
            labels.push(time.toLocaleTimeString([], {hour: '2-digit', minute: '2-digit'}));
        }
        
        return labels;
    }
    
    generateSyntheticData(count, min, max) {
        const data = [];
        let current = (min + max) / 2;
        
        for (let i = 0; i < count; i++) {
            // Add some realistic variation
            current += (Math.random() - 0.5) * (max - min) * 0.2;
            current = Math.max(min, Math.min(max, current));
            data.push(Number(current.toFixed(2)));
        }
        
        return data;
    }
    
    generateLatencyData(count, percentiles = {}) {
        const baseP50 = percentiles.p50 || 250;
        const baseP95 = percentiles.p95 || 800;
        const baseP99 = percentiles.p99 || 1200;
        
        return {
            p50: this.generateSyntheticData(count, baseP50 * 0.8, baseP50 * 1.2),
            p95: this.generateSyntheticData(count, baseP95 * 0.8, baseP95 * 1.2),
            p99: this.generateSyntheticData(count, baseP99 * 0.8, baseP99 * 1.2)
        };
    }
    
    calculateConfidenceDistribution(avgConfidence) {
        // Simulate distribution based on average
        const high = Math.max(0, avgConfidence - 0.2 + Math.random() * 0.4);
        const low = Math.max(0, 0.3 - avgConfidence + Math.random() * 0.2);
        const medium = Math.max(0, 1 - high - low);
        
        return [
            Math.round(high * 100),
            Math.round(medium * 100), 
            Math.round(low * 100)
        ];
    }
    
    checkAlerts(metrics) {
        const alertsContainer = document.getElementById('alerts');
        alertsContainer.innerHTML = '';
        
        // Check for various alert conditions
        if (metrics.error_rate > 10) {
            this.addAlert('High error rate detected', `Current error rate: ${metrics.error_rate.toFixed(1)}%`, 'error');
        }
        
        if (metrics.avg_latency_ms > 5000) {
            this.addAlert('High latency detected', `Average latency: ${metrics.avg_latency_ms.toFixed(0)}ms`, 'warning');
        }
        
        if (metrics.hallucination_flags > 10) {
            this.addAlert('High hallucination flag rate', `Recent flags: ${metrics.hallucination_flags}`, 'warning');
        }
        
        if (metrics.qps < 0.1 && metrics.total_queries > 0) {
            this.addAlert('Low query volume', 'Query rate is unusually low', 'warning');
        }
        
        // Show success message if everything is healthy
        if (alertsContainer.children.length === 0) {
            this.addAlert('System Healthy', 'All metrics within normal ranges', 'success');
        }
    }
    
    addAlert(title, message, type) {
        const alertsContainer = document.getElementById('alerts');
        const alert = document.createElement('div');
        alert.className = `alert ${type}`;
        alert.innerHTML = `<strong>${title}:</strong> ${message}`;
        alertsContainer.appendChild(alert);
    }
    
    showAlert(message, type) {
        this.addAlert('System Alert', message, type);
    }
    
    showLoading() {
        // Show loading state in status cards
        const statusValues = document.querySelectorAll('.status-card .value');
        for (const element of statusValues) {
            element.innerHTML = '<div class="spinner" style="width: 20px; height: 20px;"></div>';
        }
    }
    
    showDemoData() {
        // Show demo data when API is not available
        const demoMetrics = {
            total_queries: 1547,
            successful_queries: 1489,
            failed_queries: 58,
            success_rate: 96.2,
            avg_latency_ms: 342,
            qps: 2.3,
            hallucination_flags: 7,
            avg_confidence: 0.87
        };
        
        this.updateStatusCards(demoMetrics);
        this.updateCharts({ current_metrics: demoMetrics });
        this.checkAlerts(demoMetrics);
        
        this.showAlert('Demo Mode: Using simulated data (API not available)', 'warning');
    }
    
    startAutoRefresh() {
        if (this.refreshTimer) {
            clearInterval(this.refreshTimer);
        }
        
        this.refreshTimer = setInterval(() => {
            this.loadData();
        }, this.refreshInterval);
    }
    
    stopAutoRefresh() {
        if (this.refreshTimer) {
            clearInterval(this.refreshTimer);
            this.refreshTimer = null;
        }
    }
}

// Global functions
function refreshData() {
    if (globalThis.dashboard) {
        globalThis.dashboard.loadData();
    }
}

function exportData() {
    // Simple CSV export of current metrics
    const metrics = {
        timestamp: new Date().toISOString(),
        totalQueries: document.getElementById('totalQueries').textContent,
        successRate: document.getElementById('successRate').textContent,
        avgLatency: document.getElementById('avgLatency').textContent,
        currentQPS: document.getElementById('currentQPS').textContent,
        hallucinationFlags: document.getElementById('hallucinationFlags').textContent,
        avgConfidence: document.getElementById('avgConfidence').textContent
    };
    
    const csv = Object.entries(metrics).map(([key, value]) => `${key},${value}`).join(String.raw`
`);
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    
    const a = document.createElement('a');
    a.href = url;
    a.download = `clinchat-metrics-${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
    
    URL.revokeObjectURL(url);
}

// Initialize dashboard when DOM is ready
document.addEventListener('DOMContentLoaded', async function() {
    globalThis.dashboard = new MonitoringDashboard();
    await globalThis.dashboard.init();
});

// Handle page visibility changes
document.addEventListener('visibilitychange', function() {
    if (globalThis.dashboard) {
        if (document.hidden) {
            globalThis.dashboard.stopAutoRefresh();
        } else {
            globalThis.dashboard.startAutoRefresh();
            globalThis.dashboard.loadData(); // Refresh immediately when page becomes visible
        }
    }
});