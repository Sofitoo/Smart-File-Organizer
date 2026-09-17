const $ = (id) => document.getElementById(id);
const form = $("folder-form");
const pathInput = $("folder-path");
const dryRun = $("dry-run");
const message = $("message");
const results = $("results");
const modal = $("confirmation");
let currentPath = "";
let previewedPath = "";

const typeNames = {
  Images: "Image", Documents: "Document", Spreadsheets: "Spreadsheet",
  PDFs: "PDF", Audio: "Audio", Video: "Video", Archives: "Archive",
  Code: "Code", Other: "Other"
};
const categorySymbols = {
  Images: "▧", Documents: "▤", Spreadsheets: "▦", PDFs: "▤",
  Audio: "♫", Video: "▣", Archives: "▣", Code: "〈〉", Other: "◇"
};

function showMessage(text) {
  message.textContent = text;
  message.hidden = !text;
}

function setBusy(busy) {
  $("analyze-button").disabled = busy;
  $("organize-button").disabled = busy;
  $("confirm-button").disabled = busy;
}

async function send(endpoint, path) {
  const response = await fetch(endpoint, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ path })
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(typeof data.detail === "string" ? data.detail : "Unable to process this folder.");
  }
  return data;
}

function element(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function render(report) {
  results.hidden = false;
  const complete = !report.dry_run;
  $("results-title").textContent = complete ? "Organization complete" : "Organization Preview";
  $("results-subtitle").textContent = complete
    ? `Finished in ${report.elapsed_seconds.toFixed(3)}s. Your files are in place.`
    : "A clear plan for every file in your folder.";
  $("mode-pill").textContent = complete ? "COMPLETE" : "PREVIEW MODE";
  $("mode-pill").classList.toggle("complete", complete);
  $("files-count").textContent = report.processed;
  $("categories-count").textContent = Object.values(report.moved_by_category).filter((count) => count > 0).length;
  $("ignored-count").textContent = report.ignored.length;
  $("errors-count").textContent = report.errors.length;
  $("file-total").textContent = `${report.moves.length} ${report.moves.length === 1 ? "file" : "files"}`;

  const rows = $("file-rows");
  rows.replaceChildren();
  for (const move of report.moves) {
    const row = element("tr");
    const file = element("td", "file-name");
    file.append(element("span", "file-icon", categorySymbols[move.category] || "◇"), document.createTextNode(move.file));
    const destination = element("td", "destination", move.destination);
    destination.title = move.destination;
    const status = element("span", `status ${move.status}`, move.status === "ready" ? "Ready" : move.status === "moved" ? "Moved" : "Error");
    const statusCell = element("td");
    statusCell.append(status);
    row.append(file, element("td", "", typeNames[move.category] || move.category), destination, statusCell);
    rows.append(row);
  }
  $("empty-state").hidden = report.moves.length > 0;

  const cards = $("category-cards");
  cards.replaceChildren();
  for (const [category, count] of Object.entries(report.moved_by_category)) {
    if (!count) continue;
    const card = element("div", "category-card");
    const label = element("div");
    label.append(element("strong", "", category), element("small", "", `${count} ${count === 1 ? "file" : "files"}`));
    card.append(element("span", "category-icon", categorySymbols[category] || "◇"), label);
    cards.append(card);
  }

  $("organize-button").hidden = complete || report.processed === 0 || report.errors.length > 0;
  $("action-title").textContent = complete ? "Your folder is organized." : "Ready to tidy up?";
  $("action-detail").textContent = complete
    ? `${Object.values(report.moved_by_category).reduce((sum, count) => sum + count, 0)} moved · ${report.ignored.length} ignored · ${report.errors.length} errors · ${report.elapsed_seconds.toFixed(3)}s`
    : report.errors.length ? "Resolve the listed errors before organizing." : "Review the plan, then organize your files.";
}

function openConfirmation(fromPreview = false) {
  currentPath = pathInput.value.trim();
  if (fromPreview && currentPath !== previewedPath) {
    showMessage("The folder path changed. Analyze it again before organizing.");
    return;
  }
  $("confirm-path").textContent = currentPath;
  modal.hidden = false;
  $("cancel-button").focus();
}

function closeConfirmation() {
  modal.hidden = true;
  $("analyze-button").focus();
}

async function organizeFolder() {
  modal.hidden = true;
  setBusy(true);
  showMessage("");
  try {
    const report = await send("/api/organize", currentPath);
    render(report);
    previewedPath = "";
    if (report.errors.length) showMessage(report.errors.map((item) => `${item.file}: ${item.error}`).join(" · "));
  } catch (error) {
    showMessage(error.message);
  } finally {
    setBusy(false);
  }
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  showMessage("");
  currentPath = pathInput.value.trim();
  if (!dryRun.checked) {
    openConfirmation();
    return;
  }
  setBusy(true);
  try {
    const report = await send("/api/preview", currentPath);
    previewedPath = currentPath;
    render(report);
    if (report.errors.length) showMessage(report.errors.map((item) => `${item.file}: ${item.error}`).join(" · "));
  } catch (error) {
    results.hidden = true;
    showMessage(error.message);
  } finally {
    setBusy(false);
  }
});

dryRun.addEventListener("change", () => {
  $("analyze-button").innerHTML = dryRun.checked ? 'Analyze Folder <span aria-hidden="true">→</span>' : 'Organize Folder <span aria-hidden="true">→</span>';
  results.hidden = true;
  previewedPath = "";
});
pathInput.addEventListener("input", () => { results.hidden = true; previewedPath = ""; });
$("organize-button").addEventListener("click", () => openConfirmation(true));
$("cancel-button").addEventListener("click", closeConfirmation);
$("confirm-button").addEventListener("click", organizeFolder);
modal.addEventListener("click", (event) => { if (event.target === modal) closeConfirmation(); });
document.addEventListener("keydown", (event) => { if (event.key === "Escape" && !modal.hidden) closeConfirmation(); });

fetch("/api/config").then((response) => response.json()).then((config) => {
  if (config.demo_path) {
    $("demo-button").hidden = false;
    $("demo-button").addEventListener("click", () => {
      pathInput.value = config.demo_path;
      pathInput.focus();
    });
    if (new URLSearchParams(window.location.search).get("demo") === "1") {
      pathInput.value = config.demo_path;
      form.requestSubmit();
    }
  }
}).catch(() => {});
