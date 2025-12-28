const API_BASE = window.location.origin.replace(/:\d+$/, ":8000");

// Tabs
const searchTab = document.getElementById("tab-search");
const ingestTab = document.getElementById("tab-ingest");
const metricsTab = document.getElementById("tab-metrics");
const searchView = document.getElementById("search-view");
const ingestView = document.getElementById("ingest-view");
const metricsView = document.getElementById("metrics-view");

function setActiveTab(tab) {
  [searchTab, ingestTab, metricsTab].forEach(t => t.classList.remove("active"));
  tab.classList.add("active");
  [searchView, ingestView, metricsView].forEach(v => v.classList.add("hidden"));
  if (tab === searchTab) searchView.classList.remove("hidden");
  if (tab === ingestTab) ingestView.classList.remove("hidden");
  if (tab === metricsTab) metricsView.classList.remove("hidden");
}

searchTab.addEventListener("click", () => setActiveTab(searchTab));
ingestTab.addEventListener("click", () => setActiveTab(ingestTab));
metricsTab.addEventListener("click", () => setActiveTab(metricsTab));

// Search
const searchForm = document.getElementById("search-form");
const resultsEl = document.getElementById("results");
const searchStatus = document.getElementById("search-status");
const recentEl = document.getElementById("recent-searches");
const clearBtn = document.getElementById("clear-results");

function loadRecent() {
  const arr = JSON.parse(localStorage.getItem("recent_searches") || "[]");
  if (!arr.length) { recentEl.textContent = ""; return; }
  recentEl.innerHTML = arr.map(s => `<span class="tag">${s}</span>`).join(" ");
  recentEl.querySelectorAll('.tag').forEach(tag => {
    tag.style.display = 'inline-block';
    tag.style.padding = '4px 8px';
    tag.style.background = '#1f2937';
    tag.style.border = '1px solid #374151';
    tag.style.borderRadius = '999px';
    tag.style.marginRight = '6px';
    tag.style.cursor = 'pointer';
    tag.addEventListener('click', () => {
      document.getElementById('query').value = tag.textContent;
    });
  });
}

function saveRecent(q) {
  const arr = JSON.parse(localStorage.getItem("recent_searches") || "[]");
  const next = [q, ...arr.filter(x => x !== q)].slice(0, 10);
  localStorage.setItem("recent_searches", JSON.stringify(next));
  loadRecent();
}

clearBtn.addEventListener("click", () => { resultsEl.innerHTML = ""; searchStatus.textContent = ""; });
loadRecent();

searchForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  resultsEl.innerHTML = "";
  searchStatus.textContent = "Searching...";
  const q = document.getElementById("query").value;
  const filters = {};
  const category = document.getElementById("filter-category").value;
  const brand = document.getElementById("filter-brand").value;
  const categories = document.getElementById("filter-categories").value;
  const brands = document.getElementById("filter-brands").value;
  const priceMin = document.getElementById("filter-price-min").value;
  const priceMax = document.getElementById("filter-price-max").value;
  const ratingMin = document.getElementById("filter-rating-min").value;
  const topK = parseInt(document.getElementById("top-k").value || "20", 10);
  const sortBy = document.getElementById("sort-by").value;
  const scoreThreshold = document.getElementById("score-threshold").value;
  const showExplanations = document.getElementById("show-explanations").checked;
  if (category) filters["category"] = category;
  if (brand) filters["brand"] = brand;
  if (categories) filters["categories"] = categories.split(",").map(s => s.trim()).filter(Boolean);
  if (brands) filters["brands"] = brands.split(",").map(s => s.trim()).filter(Boolean);
  if (priceMin) filters["price_min"] = parseFloat(priceMin);
  if (priceMax) filters["price_max"] = parseFloat(priceMax);
  if (ratingMin) filters["rating_min"] = parseFloat(ratingMin);

  try {
    const res = await fetch(`${API_BASE}/search`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ q, filters, top_k: topK })
    });
    let data = await res.json();

    // client-side sort & threshold since backend doesn’t yet support these fields
    if (scoreThreshold) {
      const thr = parseFloat(scoreThreshold);
      data = data.filter(r => r.score >= thr);
    }
    if (sortBy === "price_asc") {
      data.sort((a,b) => a.product.price - b.product.price);
    } else if (sortBy === "price_desc") {
      data.sort((a,b) => b.product.price - a.product.price);
    } else if (sortBy === "rating_desc") {
      data.sort((a,b) => b.product.rating - a.product.rating);
    } // relevance is server default

    searchStatus.textContent = `Returned ${data.length} results`;
    renderResults(data.map(r => ({...r, explanation: showExplanations ? r.explanation : ''})), q);
    saveRecent(q);
  } catch (err) {
    searchStatus.textContent = `Error: ${err.message}`;
  }
});

function renderResults(items, queryText) {
  resultsEl.innerHTML = items.map(({ product, score, explanation }) => {
    const attrs = Object.entries(product.attributes || {}).map(([k, v]) => `${k}: ${v}`).join(", ");
    return `
      <div class="result-card" data-id="${product.id}">
        <div class="result-header">
          <div class="result-title">${product.title}</div>
          <div class="result-meta">₹${product.price} • ⭐ ${product.rating.toFixed(1)}</div>
        </div>
        <div class="result-meta">${product.brand} • ${product.category}</div>
        <div>${product.description}</div>
        <div class="result-meta">${attrs}</div>
        <div class="explanation">${explanation || ''}</div>
        <div class="actions">
          <button class="btn" data-action="click" data-id="${product.id}">Click</button>
          <button class="btn" data-action="add_to_cart" data-id="${product.id}">Add to Cart</button>
          <button class="btn" data-action="purchase" data-id="${product.id}">Purchase</button>
        </div>
      </div>
    `;
  }).join("");

  // Bind buttons
  resultsEl.querySelectorAll("button[data-action]").forEach(btn => {
    btn.addEventListener("click", () => {
      const productId = parseInt(btn.getAttribute("data-id"), 10);
      const type = btn.getAttribute("data-action");
      publishEvent(type, { query_text: queryText, product_id: productId });
    });
  });

  // Dwell tracking on result cards
  const hoverStarts = new Map();
  resultsEl.querySelectorAll(".result-card").forEach(card => {
    const productId = parseInt(card.getAttribute("data-id"), 10);
    card.addEventListener("mouseenter", () => {
      hoverStarts.set(productId, Date.now());
    });
    card.addEventListener("mouseleave", () => {
      const start = hoverStarts.get(productId);
      if (start) {
        const dwellSec = Math.round((Date.now() - start) / 1000);
        if (dwellSec > 0) {
          publishEvent("dwell", { query_text: queryText, product_id: productId, dwell_sec: dwellSec });
        }
        hoverStarts.delete(productId);
      }
    });
  });
}

async function publishEvent(type, payload) {
  try {
    await fetch(`${API_BASE}/events/publish`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ type, payload })
    });
  } catch (err) {
    console.error("publishEvent error", err);
  }
}

// Ingest CSV
const ingestForm = document.getElementById("ingest-form");
const ingestStatus = document.getElementById("ingest-status");

ingestForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const fileInput = document.getElementById("csv-file");
  const f = fileInput.files && fileInput.files[0];
  if (!f) { ingestStatus.textContent = "Please select a CSV file"; return; }
  ingestStatus.textContent = "Uploading and ingesting...";
  const form = new FormData();
  form.append("file", f);
  try {
    const res = await fetch(`${API_BASE}/products/ingest_csv`, {
      method: "POST",
      body: form
    });
    const data = await res.json();
    ingestStatus.textContent = `Ingested ${data.length} products`;
  } catch (err) {
    ingestStatus.textContent = `Error: ${err.message}`;
  }
});

// Metrics
const refreshMetrics = document.getElementById("refresh-metrics");
const metricsEl = document.getElementById("metrics");
refreshMetrics.addEventListener("click", async () => {
  try {
    const res = await fetch(`${API_BASE}/metrics`);
    const data = await res.json();
    metricsEl.textContent = JSON.stringify(data, null, 2);
  } catch (err) {
    metricsEl.textContent = `Error: ${err.message}`;
  }
});

// Default active tab
setActiveTab(searchTab);

// Single product ingestion
const ingestOneBtn = document.getElementById('ingest-one-btn');
const ingestOneStatus = document.getElementById('ingest-one-status');
ingestOneBtn && ingestOneBtn.addEventListener('click', async () => {
  const title = document.getElementById('one-title').value;
  const category = document.getElementById('one-category').value;
  const brand = document.getElementById('one-brand').value;
  const price = parseFloat(document.getElementById('one-price').value);
  const rating = parseFloat(document.getElementById('one-rating').value || '0');
  const description = document.getElementById('one-description').value;
  let attributes = {};
  const attrText = document.getElementById('one-attributes').value;
  try { attributes = attrText ? JSON.parse(attrText) : {}; } catch (e) { ingestOneStatus.textContent = 'Invalid attributes JSON'; return; }
  const payload = [{ title, description, category, brand, attributes, price, rating }];
  ingestOneStatus.textContent = 'Ingesting...';
  try {
    const res = await fetch(`${API_BASE}/products/ingest`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload)
    });
    const data = await res.json();
    ingestOneStatus.textContent = `Ingested product id ${data[0]?.id ?? 'n/a'}`;
  } catch (err) {
    ingestOneStatus.textContent = `Error: ${err.message}`;
  }
});