const state = {
  books: [],
  search: "",
  rating: "all",
  sortKey: "id",
  sortDir: "asc",
  page: 1,
  pageSize: 20,
};

let pollTimer = null;

const els = {
  scrapeBtn: document.getElementById("scrapeBtn"),
  statusText: document.getElementById("statusText"),
  themeToggle: document.getElementById("themeToggle"),
  searchInput: document.getElementById("searchInput"),
  ratingFilter: document.getElementById("ratingFilter"),
  resultsInfo: document.getElementById("resultsInfo"),
  tableBody: document.getElementById("tableBody"),
  prevBtn: document.getElementById("prevBtn"),
  nextBtn: document.getElementById("nextBtn"),
  pageInfo: document.getElementById("pageInfo"),
  statTotal: document.getElementById("statTotal"),
  statPrice: document.getElementById("statPrice"),
  statRating: document.getElementById("statRating"),
};

// ---------- Helpers ----------

function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}

function stars(rating) {
  return "★".repeat(rating) + "☆".repeat(5 - rating);
}

// ---------- Data ----------

async function loadBooks() {
  const response = await fetch("/api/books");
  state.books = await response.json();
  state.page = 1;
  render();
}

function getVisibleBooks() {
  const query = state.search.trim().toLowerCase();

  let list = state.books.filter((book) => {
    const matchesSearch = book.title.toLowerCase().includes(query);
    const matchesRating =
      state.rating === "all" || book.rating === Number(state.rating);
    return matchesSearch && matchesRating;
  });

  const key = state.sortKey;
  const direction = state.sortDir === "asc" ? 1 : -1;

  list.sort((a, b) => {
    if (typeof a[key] === "number") {
      return (a[key] - b[key]) * direction;
    }
    return String(a[key]).localeCompare(String(b[key])) * direction;
  });

  return list;
}

// ---------- Rendering ----------

function renderStats() {
  const total = state.books.length;
  els.statTotal.textContent = total.toLocaleString();

  if (total === 0) {
    els.statPrice.textContent = "£0.00";
    els.statRating.textContent = "0.0";
    return;
  }

  const avgPrice = state.books.reduce((sum, b) => sum + b.price, 0) / total;
  const avgRating = state.books.reduce((sum, b) => sum + b.rating, 0) / total;
  els.statPrice.textContent = "£" + avgPrice.toFixed(2);
  els.statRating.textContent = avgRating.toFixed(1);
}

function renderTable() {
  const visible = getVisibleBooks();
  const totalPages = Math.max(1, Math.ceil(visible.length / state.pageSize));
  if (state.page > totalPages) state.page = totalPages;

  const start = (state.page - 1) * state.pageSize;
  const pageItems = visible.slice(start, start + state.pageSize);

  if (pageItems.length === 0) {
    els.tableBody.innerHTML =
      '<tr><td colspan="6" class="empty">No books to show. Click "Run scraper" to collect data.</td></tr>';
  } else {
    els.tableBody.innerHTML = pageItems
      .map(
        (book) => `
        <tr>
          <td>${book.id}</td>
          <td><a href="${escapeHtml(book.url)}" target="_blank" rel="noopener">${escapeHtml(book.title)}</a></td>
          <td>£${book.price.toFixed(2)}</td>
          <td><span class="stars">${stars(book.rating)}</span></td>
          <td>${escapeHtml(book.availability)}</td>
          <td>${escapeHtml(book.scraped_at)}</td>
        </tr>`
      )
      .join("");
  }

  els.resultsInfo.textContent = `${visible.length} of ${state.books.length} books`;
  els.pageInfo.textContent = `Page ${state.page} of ${totalPages}`;
  els.prevBtn.disabled = state.page <= 1;
  els.nextBtn.disabled = state.page >= totalPages;

  document.querySelectorAll("th[data-sort]").forEach((th) => {
    th.classList.remove("sorted-asc", "sorted-desc");
    if (th.dataset.sort === state.sortKey) {
      th.classList.add(state.sortDir === "asc" ? "sorted-asc" : "sorted-desc");
    }
  });
}

function render() {
  renderStats();
  renderTable();
}

// ---------- Scraping ----------

async function checkStatus() {
  const response = await fetch("/api/status");
  const status = await response.json();

  els.statusText.textContent = status.message;
  els.scrapeBtn.disabled = status.running;
  els.scrapeBtn.textContent = status.running ? "Scraping..." : "Run scraper";

  if (!status.running && pollTimer) {
    clearInterval(pollTimer);
    pollTimer = null;
    await loadBooks();
  }

  return status;
}

function startPolling() {
  if (pollTimer) return;
  pollTimer = setInterval(checkStatus, 1500);
}

async function startScrape() {
  els.scrapeBtn.disabled = true;
  const response = await fetch("/api/scrape", { method: "POST" });

  if (response.status === 409) {
    els.statusText.textContent = "A scrape is already running";
  }

  await checkStatus();
  startPolling();
}

// ---------- Theme ----------

function applyTheme(theme) {
  document.documentElement.setAttribute("data-theme", theme);
  els.themeToggle.textContent = theme === "dark" ? "Light mode" : "Dark mode";
  try {
    localStorage.setItem("theme", theme);
  } catch (e) {}
}

function toggleTheme() {
  const current = document.documentElement.getAttribute("data-theme");
  applyTheme(current === "dark" ? "light" : "dark");
}

// ---------- Events ----------

els.scrapeBtn.addEventListener("click", startScrape);
els.themeToggle.addEventListener("click", toggleTheme);

els.searchInput.addEventListener("input", (event) => {
  state.search = event.target.value;
  state.page = 1;
  renderTable();
});

els.ratingFilter.addEventListener("change", (event) => {
  state.rating = event.target.value;
  state.page = 1;
  renderTable();
});

document.querySelectorAll("th[data-sort]").forEach((th) => {
  th.addEventListener("click", () => {
    const key = th.dataset.sort;
    if (state.sortKey === key) {
      state.sortDir = state.sortDir === "asc" ? "desc" : "asc";
    } else {
      state.sortKey = key;
      state.sortDir = "asc";
    }
    state.page = 1;
    renderTable();
  });
});

els.prevBtn.addEventListener("click", () => {
  state.page -= 1;
  renderTable();
});

els.nextBtn.addEventListener("click", () => {
  state.page += 1;
  renderTable();
});

// ---------- Start ----------

applyTheme(document.documentElement.getAttribute("data-theme") || "light");
loadBooks();
checkStatus().then((status) => {
  if (status.running) startPolling();
});