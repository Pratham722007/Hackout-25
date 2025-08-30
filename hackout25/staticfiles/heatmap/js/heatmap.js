// Heatmap JavaScript functionality
// This file provides additional utility functions for the heatmap

// Utility functions for heatmap functionality
const HeatmapUtils = {
    
    /**
     * Create custom markers based on report type and severity
     */
    createCustomMarker: function(report) {
        let color = '#007bff'; // default blue
        let size = 8;
        
        // Color based on severity
        switch (report.severity) {
            case 'low':
                color = '#28a745';
                size = 6;
                break;
            case 'medium':
                color = '#ffc107';
                size = 8;
                break;
            case 'high':
                color = '#fd7e14';
                size = 10;
                break;
            case 'critical':
                color = '#dc3545';
                size = 12;
                break;
        }
        
        // Create custom icon
        const customIcon = L.divIcon({
            className: 'custom-marker',
            html: `<div style="
                width: ${size * 2}px;
                height: ${size * 2}px;
                background-color: ${color};
                border: 2px solid white;
                border-radius: 50%;
                box-shadow: 0 2px 4px rgba(0,0,0,0.3);
            "></div>`,
            iconSize: [size * 2, size * 2],
            iconAnchor: [size, size]
        });
        
        return L.marker([report.latitude, report.longitude], {
            icon: customIcon
        });
    },
    
    /**
     * Calculate heatmap intensity based on severity
     */
    calculateIntensity: function(severity) {
        const intensityMap = {
            'low': 0.3,
            'medium': 0.5,
            'high': 0.7,
            'critical': 1.0
        };
        return intensityMap[severity] || 0.5;
    },
    
    /**
     * Group reports by location for clustering
     */
    groupReportsByLocation: function(reports, precision = 0.001) {
        const grouped = {};
        
        reports.forEach(report => {
            const lat = Math.round(report.latitude / precision) * precision;
            const lng = Math.round(report.longitude / precision) * precision;
            const key = `${lat},${lng}`;
            
            if (!grouped[key]) {
                grouped[key] = [];
            }
            grouped[key].push(report);
        });
        
        return grouped;
    },
    
    /**
     * Create cluster markers for grouped reports
     */
    createClusterMarker: function(reports, lat, lng) {
        const count = reports.length;
        const size = Math.min(Math.max(count * 3 + 20, 25), 50);
        
        // Determine cluster color based on highest severity
        let maxSeverity = 'low';
        reports.forEach(report => {
            if (this.getSeverityValue(report.severity) > this.getSeverityValue(maxSeverity)) {
                maxSeverity = report.severity;
            }
        });
        
        const colors = {
            'low': '#28a745',
            'medium': '#ffc107',
            'high': '#fd7e14',
            'critical': '#dc3545'
        };
        
        const clusterIcon = L.divIcon({
            className: 'cluster-marker',
            html: `<div style="
                width: ${size}px;
                height: ${size}px;
                background-color: ${colors[maxSeverity]};
                border: 3px solid white;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                color: white;
                font-weight: bold;
                font-size: ${Math.max(size * 0.3, 12)}px;
                box-shadow: 0 3px 6px rgba(0,0,0,0.3);
            ">${count}</div>`,
            iconSize: [size, size],
            iconAnchor: [size / 2, size / 2]
        });
        
        return L.marker([lat, lng], { icon: clusterIcon });
    },
    
    /**
     * Get numeric value for severity comparison
     */
    getSeverityValue: function(severity) {
        const values = {
            'low': 1,
            'medium': 2,
            'high': 3,
            'critical': 4
        };
        return values[severity] || 1;
    },
    
    /**
     * Create popup content for cluster markers
     */
    createClusterPopup: function(reports) {
        const typeCount = {};
        const severityCount = {};
        
        reports.forEach(report => {
            typeCount[report.report_type] = (typeCount[report.report_type] || 0) + 1;
            severityCount[report.severity] = (severityCount[report.severity] || 0) + 1;
        });
        
        let content = `
            <div class="cluster-popup">
                <h4>${reports.length} Reports at this location</h4>
                <div class="cluster-stats">
                    <h5>By Type:</h5>
                    <ul>
        `;
        
        Object.keys(typeCount).forEach(type => {
            const displayType = type.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase());
            content += `<li>${displayType}: ${typeCount[type]}</li>`;
        });
        
        content += `
                    </ul>
                    <h5>By Severity:</h5>
                    <ul>
        `;
        
        Object.keys(severityCount).forEach(severity => {
            const displaySeverity = severity.charAt(0).toUpperCase() + severity.slice(1);
            content += `<li>${displaySeverity}: ${severityCount[severity]}</li>`;
        });
        
        content += `
                    </ul>
                </div>
                <small>Click individual markers to see details</small>
            </div>
        `;
        
        return content;
    },
    
    /**
     * Format date for display
     */
    formatDate: function(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    },
    
    /**
     * Debounce function for search/filter inputs
     */
    debounce: function(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },
    
    /**
     * Show notification message
     */
    showNotification: function(message, type = 'info', duration = 3000) {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <div class="notification-content">
                <span>${message}</span>
                <button class="notification-close">&times;</button>
            </div>
        `;
        
        // Add styles
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 15px 20px;
            border-radius: 6px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            z-index: 10000;
            max-width: 400px;
            color: white;
            font-size: 14px;
            transform: translateX(100%);
            transition: transform 0.3s ease;
        `;
        
        // Set background color based on type
        const colors = {
            'success': '#28a745',
            'error': '#dc3545',
            'warning': '#ffc107',
            'info': '#007bff'
        };
        notification.style.backgroundColor = colors[type] || colors.info;
        
        // Add to DOM
        document.body.appendChild(notification);
        
        // Animate in
        setTimeout(() => {
            notification.style.transform = 'translateX(0)';
        }, 100);
        
        // Close functionality
        const closeBtn = notification.querySelector('.notification-close');
        closeBtn.addEventListener('click', () => {
            this.removeNotification(notification);
        });
        
        // Auto remove
        if (duration > 0) {
            setTimeout(() => {
                this.removeNotification(notification);
            }, duration);
        }
        
        return notification;
    },
    
    /**
     * Remove notification
     */
    removeNotification: function(notification) {
        notification.style.transform = 'translateX(100%)';
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 300);
    },
    
    /**
     * Export map data to different formats
     */
    exportData: function(reports, format = 'csv') {
        if (format === 'csv') {
            return this.exportToCSV(reports);
        } else if (format === 'json') {
            return this.exportToJSON(reports);
        }
    },
    
    /**
     * Export reports to CSV
     */
    exportToCSV: function(reports) {
        const headers = [
            'ID', 'Title', 'Description', 'Type', 'Severity', 'Status',
            'Latitude', 'Longitude', 'Location', 'Reporter', 'Created At'
        ];
        
        let csv = headers.join(',') + '\\n';
        
        reports.forEach(report => {
            const row = [
                report.id,
                `"${report.title.replace(/"/g, '""')}"`,
                `"${report.description.replace(/"/g, '""')}"`,
                report.report_type_display,
                report.severity_display,
                report.status_display,
                report.latitude,
                report.longitude,
                `"${(report.location_name || '').replace(/"/g, '""')}"`,
                `"${(report.reporter_name || '').replace(/"/g, '""')}"`,
                report.created_at
            ];
            csv += row.join(',') + '\\n';
        });
        
        // Create and download file
        const blob = new Blob([csv], { type: 'text/csv' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `environmental_reports_${new Date().toISOString().split('T')[0]}.csv`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
    },
    
    /**
     * Export reports to JSON
     */
    exportToJSON: function(reports) {
        const data = {
            exported_at: new Date().toISOString(),
            count: reports.length,
            reports: reports
        };
        
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `environmental_reports_${new Date().toISOString().split('T')[0]}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
    }
};

// Make HeatmapUtils globally available
if (typeof window !== 'undefined') {
    window.HeatmapUtils = HeatmapUtils;
}

// Initialize additional functionality when DOM is ready
// Note: Only add utility functions, do not initialize maps here to avoid conflicts
if (typeof window !== 'undefined') {
    // Add export functionality if export button exists
    const exportBtn = document.getElementById('exportData');
    if (exportBtn) {
        exportBtn.addEventListener('click', function() {
            if (typeof currentReports !== 'undefined' && currentReports.length > 0) {
                HeatmapUtils.exportData(currentReports, 'csv');
                HeatmapUtils.showNotification('Data exported successfully!', 'success');
            } else {
                HeatmapUtils.showNotification('No data to export', 'warning');
            }
        });
    }
    
    // Add keyboard shortcuts
    document.addEventListener('keydown', function(e) {
        // Only add shortcuts if we're on the heatmap page
        if (!document.getElementById('map')) return;
        
        // Ctrl/Cmd + R to refresh map
        if ((e.ctrlKey || e.metaKey) && e.key === 'r') {
            e.preventDefault();
            if (typeof updateMapData === 'function') {
                updateMapData();
                HeatmapUtils.showNotification('Map refreshed', 'info');
            }
        }
        
        // Ctrl/Cmd + H to toggle heatmap
        if ((e.ctrlKey || e.metaKey) && e.key === 'h') {
            e.preventDefault();
            if (typeof toggleHeatmap === 'function') {
                toggleHeatmap();
            }
        }
        
        // Escape to reset view
        if (e.key === 'Escape') {
            if (typeof resetView === 'function') {
                resetView();
            }
        }
    });
}
