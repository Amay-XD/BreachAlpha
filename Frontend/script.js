/* ============================================
   CONFIGURATION
   ============================================ */

const API_BASE_URL = 'http://localhost:5000/api/v1';
const DEBOUNCE_DELAY = 300;

/* ============================================
   DOM ELEMENTS
   ============================================ */

const searchForm = document.getElementById('searchForm');
const searchInput = document.getElementById('searchInput');
const searchButton = document.querySelector('.search-button');
const suggestionsDropdown = document.getElementById('suggestionsDropdown');
const suggestionsList = document.getElementById('suggestionsList');

const resultsSection = document.getElementById('resultsSection');
const loadingState = document.getElementById('loadingState');
const errorState = document.getElementById('errorState');
const notFoundState = document.getElementById('notFoundState');
const metricsContainer = document.getElementById('metricsContainer');
const analysisContainer = document.getElementById('analysisContainer');
const breachInfoContainer = document.getElementById('breachInfoContainer');
const chartContainer = document.getElementById('chartContainer');

const companyChangeEl = document.getElementById('companyChange');
const marketChangeEl = document.getElementById('marketChange');
const relativeImpactEl = document.getElementById('relativeImpact');
const recoveryDaysEl = document.getElementById('recoveryDays');
const analysisTextEl = document.getElementById('analysisText');

const suggestedCompaniesEl = document.getElementById('suggestedCompanies');
const suggestBtn = document.getElementById('suggestBtn');
const suggestionModal = document.getElementById('suggestionModal');

/* ============================================
   STATE
   ============================================ */

let allBreaches = [];
let debounceTimer = null;
let chartInstance = null;
let lastSearchQuery = '';

/* ============================================
   INITIALIZATION
   ============================================ */

document.addEventListener('DOMContentLoaded', async () => {
    await loadAllBreaches();
    populateSuggestedCompanies();
    attachEventListeners();
});

/* ============================================
   EVENT LISTENERS
   ============================================ */

function attachEventListeners() {
    searchForm.addEventListener('submit', handleSearch);
    searchInput.addEventListener('focus', handleInputFocus);
    searchInput.addEventListener('input', handleInputChange);
    document.addEventListener('click', handleDocumentClick);
    suggestBtn.addEventListener('click', openSuggestionModal);
}

function handleSearch(e) {
    e.preventDefault();
    const query = searchInput.value.trim();
    if (query.length > 0) {
        lastSearchQuery = query;
        analyzeQuery(query);
    }
}

function handleInputFocus() {
    if (searchInput.value.length > 0) {
        showSuggestions();
    }
}

function handleInputChange(e) {
    const query = e.target.value.trim();
    clearTimeout(debounceTimer);
    
    if (query.length === 0) {
        suggestionsDropdown.style.display = 'none';
        return;
    }
    
    debounceTimer = setTimeout(() => {
        filterAndShowSuggestions(query);
    }, DEBOUNCE_DELAY);
}

function handleDocumentClick(e) {
    if (!e.target.closest('.search-form')) {
        suggestionsDropdown.style.display = 'none';
    }
}

/* ============================================
   API CALLS
   ============================================ */

async function loadAllBreaches() {
    try {
        const response = await fetch(`${API_BASE_URL}/breaches?per_page=100`);
        const data = await response.json();
        allBreaches = data.breaches || [];
    } catch (error) {
        console.error('Failed to load breaches:', error);
        allBreaches = [];
    }
}

async function analyzeQuery(query) {
    showLoadingState();
    searchButton.disabled = true;
    
    // Simulate min loading time for smooth UX
    const minLoadTime = 1500;
    const startTime = Date.now();
    
    try {
        const response = await fetch(`${API_BASE_URL}/market/analyze`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ query })
        });
        
        const data = await response.json();
        
        // Ensure minimum loading time
        const elapsedTime = Date.now() - startTime;
        if (elapsedTime < minLoadTime) {
            await new Promise(resolve => setTimeout(resolve, minLoadTime - elapsedTime));
        }
        
        if (data.found) {
            displayResults(data.result, data.analysis);
        } else {
            // Not found - show friendly message
            displayNotFound(query, data.analysis);
        }
    } catch (error) {
        console.error('API error:', error);
        displayAPIError(`Unable to connect to the analysis engine. Please check your connection and try again.`);
    } finally {
        searchButton.disabled = false;
    }
}

/* ============================================
   UI UPDATES
   ============================================ */

function showLoadingState() {
    resultsSection.style.display = 'block';
    loadingState.style.display = 'flex';
    errorState.style.display = 'none';
    notFoundState.style.display = 'none';
    metricsContainer.style.display = 'none';
    analysisContainer.style.display = 'none';
    breachInfoContainer.style.display = 'none';
    chartContainer.style.display = 'none';
    
    resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function displayResults(result, analysis) {
    hideLoadingState();
    
    // Update metric cards
    displayMetric(companyChangeEl, result.company_pct_change, '%');
    displayMetric(marketChangeEl, result.market_pct_change, '%', 'neutral');
    displayMetric(relativeImpactEl, result.relative_impact, '%');
    displayRecovery(recoveryDaysEl, result.recovery_days, result.recovery_text);
    
    // Update analysis
    analysisTextEl.textContent = analysis;
    
    // Update breach info
    updateBreachInfo(result);
    
    // Show containers
    metricsContainer.style.display = 'grid';
    analysisContainer.style.display = 'block';
    breachInfoContainer.style.display = 'block';
    errorState.style.display = 'none';
    notFoundState.style.display = 'none';
}

function displayMetric(element, value, unit = '', type = 'default') {
    let displayValue = '';
    
    if (type === 'neutral') {
        displayValue = `${value}${unit}`;
        element.className = 'metric-value';
    } else if (value > 0) {
        displayValue = `+${value}${unit}`;
        element.className = 'metric-value positive';
    } else if (value < 0) {
        displayValue = `${value}${unit}`;
        element.className = 'metric-value negative';
    } else {
        displayValue = `${value}${unit}`;
        element.className = 'metric-value';
    }
    
    element.textContent = displayValue;
}

function displayRecovery(element, days, text) {
    if (days === null) {
        element.textContent = 'No recovery';
        element.className = 'metric-value negative';
    } else {
        element.textContent = `${days} days`;
        element.className = 'metric-value positive';
    }
}

function updateBreachInfo(result) {
    document.getElementById('breachCompany').textContent = result.company || '—';
    document.getElementById('breachTicker').textContent = result.ticker || '—';
    document.getElementById('breachDate').textContent = result.breach_date || '—';
    
    const severityEl = document.getElementById('breachSeverity');
    const severity = result.severity?.toLowerCase() || 'unknown';
    severityEl.textContent = result.severity || '—';
    severityEl.className = `info-value severity ${severity}`;
    
    document.getElementById('breachSector').textContent = result.sector || '—';
    document.getElementById('breachType').textContent = result.breach_type || '—';
    document.getElementById('breachRecords').textContent = result.records_affected || '—';
    document.getElementById('breachVector').textContent = result.attack_vector || '—';
}

function displayNotFound(query, fallbackAnalysis) {
    hideLoadingState();
    notFoundState.style.display = 'block';
    document.getElementById('notFoundMessage').textContent = `We couldn't find a major breach for "${query}" in our database. This could mean the company is private, the breach was below our reporting threshold, or there may be a spelling difference.`;
    
    // Find closest matches
    displayClosestMatches(query);
    
    // Show fallback analysis if available
    if (fallbackAnalysis) {
        const errorFallback = document.getElementById('errorFallback');
        errorFallback.textContent = fallbackAnalysis;
        errorFallback.style.display = 'block';
    }
}

function displayClosestMatches(query) {
    const lowerQuery = query.toLowerCase();
    const matches = allBreaches.filter(breach => 
        breach.company.toLowerCase().includes(lowerQuery) ||
        (breach.ticker && breach.ticker.toLowerCase().includes(lowerQuery))
    ).slice(0, 5);
    
    const closestMatchesEl = document.getElementById('closestMatches');
    closestMatchesEl.innerHTML = '';
    
    if (matches.length > 0) {
        matches.forEach(breach => {
            const btn = document.createElement('button');
            btn.className = 'closest-match';
            btn.type = 'button';
            btn.innerHTML = `
                <div class="match-name">${breach.company}</div>
                <div class="match-ticker">${breach.ticker || 'N/A'}</div>
            `;
            btn.addEventListener('click', () => {
                searchInput.value = breach.company;
                analyzeQuery(breach.company);
            });
            closestMatchesEl.appendChild(btn);
        });
    } else {
        closestMatchesEl.innerHTML = '<p style="color: var(--color-text-muted); margin: 0;">No similar companies found</p>';
    }
}

function displayAPIError(message) {
    hideLoadingState();
    errorState.style.display = 'block';
    document.getElementById('errorMessage').textContent = message;
}

function hideLoadingState() {
    loadingState.style.display = 'none';
}

/* ============================================
   SUGGESTIONS & DROPDOWN
   ============================================ */

function filterAndShowSuggestions(query) {
    const lowerQuery = query.toLowerCase();
    const filtered = allBreaches.filter(breach => 
        breach.company.toLowerCase().includes(lowerQuery) ||
        (breach.ticker && breach.ticker.toLowerCase().includes(lowerQuery))
    ).slice(0, 8);
    
    if (filtered.length > 0) {
        displaySuggestions(filtered);
    } else {
        suggestionsDropdown.style.display = 'none';
    }
}

function displaySuggestions(suggestions) {
    suggestionsList.innerHTML = '';
    suggestions.forEach(breach => {
        const li = document.createElement('li');
        li.className = 'suggestion-item';
        li.innerHTML = `
            <span class="suggestion-company">${breach.company}</span>
            <span class="suggestion-ticker">${breach.ticker || 'N/A'}</span>
        `;
        li.addEventListener('click', () => {
            searchInput.value = breach.company;
            suggestionsDropdown.style.display = 'none';
            analyzeQuery(breach.company);
        });
        suggestionsList.appendChild(li);
    });
    suggestionsDropdown.style.display = 'block';
}

function showSuggestions() {
    if (allBreaches.length > 0) {
        displaySuggestions(allBreaches.slice(0, 8));
    }
}

/* ============================================
   FEATURED COMPANIES
   ============================================ */

function populateSuggestedCompanies() {
    suggestedCompaniesEl.innerHTML = '';
    const featured = allBreaches.slice(0, 12);
    featured.forEach(breach => {
        const button = document.createElement('button');
        button.className = 'company-button';
        button.type = 'button';
        button.innerHTML = `
            <span class="company-button-name">${breach.company}</span>
            <span class="company-button-ticker">${breach.ticker || 'N/A'}</span>
        `;
        button.addEventListener('click', (e) => {
            e.preventDefault();
            searchInput.value = breach.company;
            analyzeQuery(breach.company);
        });
        suggestedCompaniesEl.appendChild(button);
    });
}

/* ============================================
   SUGGESTION MODAL
   ============================================ */

function openSuggestionModal() {
    suggestionModal.style.display = 'flex';
    document.getElementById('suggestCompanyInput').value = lastSearchQuery;
}

function closeSuggestionModal() {
    suggestionModal.style.display = 'none';
    document.getElementById('suggestCompanyInput').value = '';
    document.getElementById('suggestTickerInput').value = '';
    document.getElementById('suggestDetailsInput').value = '';
}

function submitSuggestion() {
    const company = document.getElementById('suggestCompanyInput').value.trim();
    const ticker = document.getElementById('suggestTickerInput').value.trim();
    const details = document.getElementById('suggestDetailsInput').value.trim();
    
    if (!company) {
        alert('Please enter a company name');
        return;
    }
    
    // In a real app, this would send data to backend
    console.log('Suggestion:', { company, ticker, details });
    
    // Show confirmation
    alert(`Thank you! Your suggestion for "${company}" has been submitted. We'll review it and add it to our dataset soon.`);
    closeSuggestionModal();
}

/* ============================================
   UTILITY FUNCTIONS
   ============================================ */

function clearSearch() {
    searchInput.value = '';
    resultsSection.style.display = 'none';
    suggestionsDropdown.style.display = 'none';
    searchInput.focus();
}

function scrollToFeatured() {
    document.getElementById('featuredSection').scrollIntoView({ behavior: 'smooth' });
}

window.closeSuggestionModal = closeSuggestionModal;
window.submitSuggestion = submitSuggestion;
window.clearSearch = clearSearch;
window.scrollToFeatured = scrollToFeatured;
