(() => {
  "use strict";

  const COLORS = {
    S1: "#4D4D4D",
    S2: "#6A1B9A",
    S3: "#008A50",
    S4: "#F57C00",
    accent: "#E64626",
    ink: "#111111",
    muted: "#565656",
    grid: "#E5E5E5",
    refund: "#B00020",
    cap: "#C2185B",
  };
  const FONT = "Noto Sans CJK SC, Noto Sans, system-ui, sans-serif";
  const VIEWS = new Set(["3d", "rf", "rm", "fm", "customer-13777"]);
  const $ = (selector) => document.querySelector(selector);
  const plot = $("#plot");
  const detail = $("#detail");
  const status = $("#status");
  const note = $("#view-note");
  let data;
  let resizeFrame;

  function resizeVisiblePlots() {
    for (const element of [plot, $("#timeline")]) {
      if (!element || element.hidden || !element._fullLayout) continue;
      element.style.width = element === plot ? `${document.documentElement.clientWidth}px` : "100%";
      const bounds = element.getBoundingClientRect();
      if (bounds.width > 0 && bounds.height > 0) Plotly.Plots.resize(element);
    }
  }

  function schedulePlotResize() {
    if (resizeFrame) cancelAnimationFrame(resizeFrame);
    resizeFrame = requestAnimationFrame(() => {
      resizeFrame = requestAnimationFrame(resizeVisiblePlots);
    });
  }

  function activeView() {
    const query = new URLSearchParams(window.location.search);
    const candidate = query.get("view") || "3d";
    return VIEWS.has(candidate) ? candidate : "3d";
  }

  function setView(view) {
    const url = new URL(window.location.href);
    url.searchParams.set("view", view);
    history.replaceState({}, "", url);
    render(view);
  }

  function baseLayout() {
    return {
      autosize: true,
      paper_bgcolor: "#FFFFFF",
      plot_bgcolor: "#FFFFFF",
      font: { family: FONT, color: COLORS.ink, size: 10 },
      margin: { l: 46, r: 14, t: 25, b: 42 },
      legend: { orientation: "h", x: 0, y: 1.08, font: { size: 9 } },
      hoverlabel: { font: { family: FONT, size: 8 }, align: "left" },
    };
  }

  function pointText(point) {
    const label = point.demo ? "Customer 13777" : point.id;
    return `<b>${label} · ${point.segment}</b><br>` +
      `Recency: ${point.r} days<br>Frequency: ${point.f} orders<br>` +
      `Observed Net value: £${point.m.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}<br>` +
      `Touches cap: ${point.capped ? "Yes" : "No"}`;
  }

  function traces3d() {
    const traces = [];
    for (const segment of ["S1", "S2", "S3", "S4"]) {
      for (const capped of [false, true]) {
        const points = data.points.filter((point) => point.segment === segment && point.capped === capped);
        traces.push({
          type: "scatter3d",
          mode: "markers",
          name: segment,
          legendgroup: segment,
          showlegend: !capped,
          x: points.map((point) => point.x),
          y: points.map((point) => point.y),
          z: points.map((point) => point.z),
          text: points.map(pointText),
          hovertemplate: "%{text}<extra></extra>",
          marker: {
            size: capped ? 2.8 : 1.8,
            color: COLORS[segment],
            opacity: capped ? 0.65 : 0.35,
            line: { color: capped ? COLORS.cap : COLORS[segment], width: capped ? 1.3 : 0 },
          },
        });
      }
    }
    traces.push({
      type: "scatter3d",
      mode: "markers+text",
      name: "Centroids",
      x: data.centroids.map((row) => row.scaled_recency),
      y: data.centroids.map((row) => row.scaled_frequency),
      z: data.centroids.map((row) => row.scaled_net_monetary),
      text: data.centroids.map((row) => row.segment_code),
      textposition: "top center",
      hovertemplate: "<b>%{text} centroid</b><extra></extra>",
      marker: { size: 4, symbol: "diamond", color: COLORS.ink, line: { color: "white", width: 1.2 } },
    });
    return traces;
  }

  function render3d() {
    const layout = baseLayout();
    layout.height = Math.max(window.innerHeight - 55, 180);
    layout.margin = { l: 0, r: 0, t: 12, b: 0 };
    layout.legend = { orientation: "h", x: 0, y: 0.98, font: { size: 8 } };
    layout.scene = {
      xaxis: { title: { text: "R", font: { size: 8 } }, tickfont: { size: 7 }, gridcolor: COLORS.grid, zerolinecolor: "#999" },
      yaxis: { title: { text: "F", font: { size: 8 } }, tickfont: { size: 7 }, gridcolor: COLORS.grid, zerolinecolor: "#999" },
      zaxis: { title: { text: "Net M", font: { size: 8 } }, tickfont: { size: 7 }, gridcolor: COLORS.grid, zerolinecolor: "#999" },
      bgcolor: "#FFFFFF",
      camera: { eye: { x: 1.9, y: 1.9, z: 1.35 } },
    };
    layout.uirevision = "presentation-camera-v1";
    Plotly.react(plot, traces3d(), layout, { responsive: true, displaylogo: false, displayModeBar: false })
      .then(schedulePlotResize);
    note.textContent = "4,338 customers · 4 centroids · rotate once";
  }

  function renderSlice(view) {
    const specs = {
      rf: ["x", "y", "Scaled Recency", "Scaled capped Frequency"],
      rm: ["x", "z", "Scaled Recency", "Scaled capped Net value"],
      fm: ["y", "z", "Scaled capped Frequency", "Scaled capped Net value"],
    };
    const [xKey, yKey, xTitle, yTitle] = specs[view];
    const traces = ["S1", "S2", "S3", "S4"].map((segment) => {
      const points = data.points.filter((point) => point.segment === segment);
      return {
        type: "scattergl",
        mode: "markers",
        name: segment,
        x: points.map((point) => point[xKey]),
        y: points.map((point) => point[yKey]),
        text: points.map(pointText),
        hovertemplate: "%{text}<extra></extra>",
        marker: { size: 4.5, color: COLORS[segment], opacity: 0.58 },
      };
    });
    const centroidKeys = { x: "scaled_recency", y: "scaled_frequency", z: "scaled_net_monetary" };
    traces.push({
      type: "scatter",
      mode: "markers+text",
      name: "Centroids",
      x: data.centroids.map((row) => row[centroidKeys[xKey]]),
      y: data.centroids.map((row) => row[centroidKeys[yKey]]),
      text: data.centroids.map((row) => row.segment_code),
      textposition: "top center",
      hovertemplate: "<b>%{text} centroid</b><extra></extra>",
      marker: { size: 8, symbol: "diamond", color: COLORS.ink },
    });
    const layout = baseLayout();
    layout.xaxis = { title: xTitle, gridcolor: COLORS.grid, zeroline: false };
    layout.yaxis = { title: yTitle, gridcolor: COLORS.grid, zeroline: false };
    Plotly.react(plot, traces, layout, { responsive: true, displaylogo: false, displayModeBar: false })
      .then(schedulePlotResize);
    note.textContent = "same model coordinates, not PCA";
  }

  function renderCustomer() {
    Plotly.purge(plot);
    plot.hidden = true;
    detail.hidden = false;
    const customer = data.demo_customer;
    detail.innerHTML = `
      <div class="customer-grid">
        <article class="customer-summary">
          <p class="eyebrow">Real customer near the S4 centroid</p>
          <h2>${customer.customer_id}</h2>
          <p class="rfm"><strong>R</strong>${customer.recency} day</p>
          <p class="rfm"><strong>F</strong>${customer.frequency} valid purchase invoices</p>
          <p class="rfm"><strong>M</strong>£${customer.net_monetary.toLocaleString(undefined, { minimumFractionDigits: 2 })}</p>
          <div class="invoice-counts">
            <b>${customer.invoice_count}</b> recorded invoices<br>
            <b>${customer.frequency}</b> valid purchases<br>
            <b style="color:${COLORS.refund}">${customer.cancellation_count}</b> C-prefixed cancellations
          </div>
          <p class="warning">Observed example, not a persona or response prediction.</p>
        </article>
        <div id="timeline" class="timeline"></div>
      </div>`;
    const timeline = customer.timeline;
    const timelineHeight = Math.max(detail.clientHeight - 16, 190);
    Plotly.newPlot("timeline", [{
      type: "bar",
      x: timeline.map((row) => row.invoice_date),
      y: timeline.map((row) => row.invoice_amount),
      marker: { color: timeline.map((row) => row.is_cancellation ? COLORS.refund : COLORS.S4) },
      text: timeline.map((row) => `<b>Invoice ${row.invoice_no}</b><br>Amount: £${row.invoice_amount.toLocaleString(undefined, { minimumFractionDigits: 2 })}`),
      hovertemplate: "%{text}<extra></extra>",
    }], {
      ...baseLayout(),
      height: timelineHeight,
      margin: { l: 48, r: 8, t: 24, b: 38 },
      title: { text: "Invoice and cancellation timeline", x: 0.02, font: { size: 13 } },
      xaxis: { gridcolor: COLORS.grid },
      yaxis: { title: "Invoice amount (£)", gridcolor: COLORS.grid, zerolinecolor: COLORS.ink },
      showlegend: false,
    }, { responsive: true, displaylogo: false, displayModeBar: false })
      .then(schedulePlotResize);
    note.textContent = "Customer 13777 · purchases and cancellations";
  }

  function render(view) {
    for (const button of document.querySelectorAll("[data-view]")) {
      button.setAttribute("aria-current", String(button.dataset.view === view));
    }
    status.textContent = "";
    plot.hidden = false;
    detail.hidden = true;
    detail.innerHTML = "";
    if (view === "3d") render3d();
    else if (["rf", "rm", "fm"].includes(view)) renderSlice(view);
    else renderCustomer();
  }

  for (const button of document.querySelectorAll("[data-view]")) {
    button.addEventListener("click", () => setView(button.dataset.view));
  }
  window.addEventListener("popstate", () => render(activeView()));
  window.addEventListener("resize", schedulePlotResize);
  window.addEventListener("message", (event) => {
    if (event.source === window.parent && event.data?.type === "retail-rfm:resize") schedulePlotResize();
  });
  new ResizeObserver(schedulePlotResize).observe(document.documentElement);

  fetch("data.json", { cache: "no-store" })
    .then((response) => {
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      return response.json();
    })
    .then((payload) => {
      data = payload;
      if (data.schema_version !== 3 || data.points.length !== 4338 || data.centroids.length !== 4) {
        throw new Error("presentation data integrity check failed");
      }
      render(activeView());
    })
    .catch((error) => {
      status.textContent = `Unable to load local presentation data: ${error.message}`;
      status.style.color = COLORS.refund;
    });
})();
