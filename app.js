async function jsonFetch(url, options = {}) {
  const res = await fetch(url, options);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ error: res.statusText }));
    throw new Error(err.error || `Request failed: ${res.status}`);
  }
  return res.json();
}

const form = document.getElementById("expenseForm");
const rows = document.getElementById("expenseRows");
const totalEl = document.getElementById("total");
const filterCategory = document.getElementById("filterCategory");
const searchText = document.getElementById("searchText");
const fromDate = document.getElementById("fromDate");
const toDate = document.getElementById("toDate");
const applyFilters = document.getElementById("applyFilters");

let editModal;

document.addEventListener("DOMContentLoaded", () => {
  editModal = new bootstrap.Modal(document.getElementById("editModal"));
  loadExpenses();

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const payload = {
      category: document.getElementById("category").value.trim(),
      amount: document.getElementById("amount").value,
      date: document.getElementById("date").value,
      note: document.getElementById("note").value.trim()
    };
    try {
      await jsonFetch("/api/expenses", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      form.reset();
      await loadExpenses();
    } catch (err) { alert(err.message); }
  });

  applyFilters.addEventListener("click", loadExpenses);
});

async function loadExpenses() {
  const params = new URLSearchParams();
  if (filterCategory.value.trim()) params.set("category", filterCategory.value.trim());
  if (searchText.value.trim()) params.set("q", searchText.value.trim());
  if (fromDate.value) params.set("from", fromDate.value);
  if (toDate.value) params.set("to", toDate.value);

  const data = await jsonFetch(`/api/expenses?${params.toString()}`);
  renderTable(data);
  updateTotal(data);
}

function renderTable(items) {
  rows.innerHTML = "";
  items.forEach((e, idx) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${idx + 1}</td>
      <td>${e.date}</td>
      <td>${e.category}</td>
      <td class="text-end">₹${Number(e.amount).toFixed(2)}</td>
      <td>${e.note || ""}</td>
      <td class="text-end">
        <button class="btn btn-sm btn-outline-primary me-1" onclick="openEdit(${e.id})">Edit</button>
        <button class="btn btn-sm btn-outline-danger" onclick="removeExpense(${e.id})">Delete</button>
      </td>`;
    rows.appendChild(tr);
  });
}

function updateTotal(items) {
  const sum = items.reduce((acc, e) => acc + Number(e.amount || 0), 0);
  totalEl.textContent = sum.toFixed(2);
}

async function openEdit(id) {
  const all = await jsonFetch("/api/expenses");
  const item = all.find(x => x.id === id);
  if (!item) return;
  document.getElementById("editId").value = item.id;
  document.getElementById("editCategory").value = item.category;
  document.getElementById("editAmount").value = item.amount;
  document.getElementById("editDate").value = item.date;
  document.getElementById("editNote").value = item.note || "";
  editModal.show();
}
window.openEdit = openEdit;

document.getElementById("saveEdit").addEventListener("click", async () => {
  const id = document.getElementById("editId").value;
  const payload = {
    category: document.getElementById("editCategory").value.trim(),
    amount: document.getElementById("editAmount").value,
    date: document.getElementById("editDate").value,
    note: document.getElementById("editNote").value.trim()
  };
  try {
    await jsonFetch(`/api/expenses/${id}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    editModal.hide();
    await loadExpenses();
  } catch (err) { alert(err.message); }
});

async function removeExpense(id) {
  if (!confirm("Delete this expense?")) return;
  try {
    await jsonFetch(`/api/expenses/${id}`, { method: "DELETE" });
    await loadExpenses();
  } catch (err) { alert(err.message); }
}
window.removeExpense = removeExpense;
