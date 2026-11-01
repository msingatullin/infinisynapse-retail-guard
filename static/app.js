let currentPlan = null;
let currentFilter = 'all';

document.addEventListener("DOMContentLoaded", () => {
    const btnLoadSample = document.getElementById("btn-load-sample");
    const csvFileInput = document.getElementById("csv-file-input");
    const btnExportPo = document.getElementById("btn-export-po");
    const filterBtns = document.querySelectorAll(".filter-btn");

    btnLoadSample.addEventListener("click", () => {
        btnLoadSample.innerText = "⏳ Running Agent...";
        btnLoadSample.disabled = true;
        fetch("/api/load-sample")
            .then(res => res.json())
            .then(data => {
                currentPlan = data;
                renderDashboard(data);
            })
            .catch(err => alert("Error: " + err))
            .finally(() => {
                btnLoadSample.innerText = "⚡ Load Retail Inventory (40 SKUs)";
                btnLoadSample.disabled = false;
            });
    });

    csvFileInput.addEventListener("change", (e) => {
        const file = e.target.files[0];
        if (!file) return;
        const formData = new FormData();
        formData.append("file", file);

        btnLoadSample.disabled = true;
        fetch("/api/upload-csv", { method: "POST", body: formData })
            .then(res => res.json())
            .then(data => {
                currentPlan = data;
                renderDashboard(data);
            })
            .catch(err => alert("Upload error: " + err))
            .finally(() => {
                btnLoadSample.disabled = false;
                csvFileInput.value = "";
            });
    });

    btnExportPo.addEventListener("click", () => {
        if (!currentPlan || !currentPlan.reorder_items.length) return;
        fetch("/api/export-po-csv", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ items: currentPlan.reorder_items })
        })
        .then(res => res.blob())
        .then(blob => {
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = url;
            a.download = "infinisynapse_purchase_orders.csv";
            document.body.appendChild(a);
            a.click();
            a.remove();
        });
    });

    filterBtns.forEach(btn => {
        btn.addEventListener("click", () => {
            filterBtns.forEach(b => b.classList.remove("active"));
            btn.classList.add("active");
            currentFilter = btn.dataset.filter;
            if (currentPlan) renderTable(currentPlan.all_items);
        });
    });
});

function renderDashboard(data) {
    document.getElementById("metric-total-skus").innerText = data.total_skus;
    document.getElementById("metric-critical-skus").innerText = data.critical_skus;
    document.getElementById("metric-reorder-skus").innerText = data.reorder_skus;
    document.getElementById("metric-po-cost").innerText = "$" + data.total_po_cost.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2});

    const directiveCard = document.getElementById("directive-container");
    directiveCard.style.display = "block";
    document.getElementById("executive-narrative-text").innerText = data.executive_narrative;

    document.getElementById("btn-export-po").disabled = data.reorder_skus === 0;
    renderTable(data.all_items);
}

function renderTable(items) {
    const tbody = document.getElementById("inventory-tbody");
    tbody.innerHTML = "";

    const filtered = items.filter(item => {
        if (currentFilter === "reorder") return item.suggested_reorder_qty > 0;
        if (currentFilter === "critical") return item.risk_tier === "CRITICAL_OUT" || item.risk_tier === "HIGH_STOCKOUT_RISK";
        return true;
    });

    if (filtered.length === 0) {
        tbody.innerHTML = '<tr><td colspan="10" class="empty-state">No SKUs matching selected filter.</td></tr>';
        return;
    }

    filtered.forEach(it => {
        const tr = document.createElement("tr");
        let badgeClass = "badge-info";
        let tierLabel = it.risk_tier;
        if (it.risk_tier === "CRITICAL_OUT") { badgeClass = "badge-danger"; tierLabel = "Out of Stock"; }
        else if (it.risk_tier === "HIGH_STOCKOUT_RISK") { badgeClass = "badge-warning"; tierLabel = "High Risk"; }
        else if (it.risk_tier === "REORDER_WINDOW") { badgeClass = "badge-info"; tierLabel = "Reorder Window"; }
        else { badgeClass = "badge-success"; tierLabel = "Healthy"; }

        tr.innerHTML = `
            <td><strong>${it.sku_id}</strong></td>
            <td>${it.product_name}</td>
            <td>${it.category}</td>
            <td>${it.current_stock}</td>
            <td>${it.daily_velocity} / day</td>
            <td>${it.lead_time_days} days</td>
            <td>${it.days_to_stockout} d</td>
            <td><span class="badge ${badgeClass}">${tierLabel}</span></td>
            <td><strong>${it.suggested_reorder_qty > 0 ? it.suggested_reorder_qty + ' units' : '-'}</strong></td>
            <td>${it.estimated_po_cost > 0 ? '$' + it.estimated_po_cost.toFixed(2) : '-'}</td>
        `;
        tbody.appendChild(tr);
    });
}
