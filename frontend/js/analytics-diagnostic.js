// ===============================================
// ANALYTICS DIAGNOSTIC SCRIPT
// Add this temporarily to check what's happening
// ===============================================

(function () {
    document.addEventListener('DOMContentLoaded', () => {
        console.log('🔍 ANALYTICS DIAGNOSTIC START');

        // Check if section exists and is visible
        const analyticsSection = document.getElementById('analyticsSection');
        console.log('Analytics section:', analyticsSection);
        console.log('Section display:', analyticsSection?.style.display);
        console.log('Section classes:', analyticsSection?.className);

        // Check all stat elements
        const elements = {
            totalChats: document.getElementById('statTotalChats'),
            uniqueUsers: document.getElementById('statUniqueUsers'),
            avgSession: document.getElementById('statAvgSession'),
            growthRate: document.getElementById('statGrowthRate'),
            engagementScore: document.getElementById('statEngagement'),
            chatsChart: document.getElementById('chatsPerDayChart'),
            hourlyChart: document.getElementById('hourlyChart'),
            topQuestionsBody: document.getElementById('topQuestionsBody'),
            zakatPopularityBody: document.getElementById('zakatPopularityBody')
        };

        console.log('📋 DOM ELEMENTS CHECK:');
        Object.entries(elements).forEach(([key, element]) => {
            console.log(`  ${key}:`, element ? '✅ Found' : '❌ NOT FOUND');
            if (element) {
                console.log(`    - Parent visible:`, element.offsetParent !== null);
                console.log(`    - Current content:`, element.textContent || element.innerHTML?.substring(0, 50));
            }
        });

        // Check if analytics section HTML exists
        console.log('📄 ANALYTICS HTML CHECK:');
        const analyticsHTML = document.body.innerHTML.includes('analyticsSection');
        console.log('  Analytics section in HTML:', analyticsHTML ? '✅ Yes' : '❌ No');

        // Check all stat cards
        const statCards = document.querySelectorAll('.analytics-stat-card');
        console.log('  Stat cards found:', statCards.length);
        statCards.forEach((card, i) => {
            console.log(`    Card ${i}:`, card.querySelector('.stat-value')?.id || 'no ID');
        });

        console.log('🔍 DIAGNOSTIC END');
    });
})();