const searchInput = document.getElementById("searchInput");
const categorySelect = document.getElementById("categorySelect");
const versionSelect = document.getElementById("versionSelect");
const profileResults = document.getElementById("profileResults");
const statsPanel = document.getElementById("statsPanel");
const profileModal = document.getElementById("profileModal");
const modalTitle = document.getElementById("modalTitle");
const modalMeta = document.getElementById("modalMeta");
const modalVideoFrame = document.getElementById("modalVideoFrame");
const modalIncludedList = document.getElementById("modalIncludedList");
const modalDownloadBtn = document.getElementById("modalDownloadBtn");
const modalYoutubeBtn = document.getElementById("modalYoutubeBtn");

function debounce(fn, delay = 220) {
    let timeoutId;
    return (...args) => {
        window.clearTimeout(timeoutId);
        timeoutId = window.setTimeout(() => fn(...args), delay);
    };
}

function buildQuery() {
    const params = new URLSearchParams({
        query: searchInput.value.trim(),
        category: categorySelect.value,
        version: versionSelect.value,
    });
    return params.toString();
}

async function refreshProfiles() {
    const query = buildQuery();
    const response = await fetch(`/partials/profiles?${query}`, {
        headers: { "X-Requested-With": "fetch" },
    });

    if (!response.ok) {
        return;
    }

    const html = await response.text();
    profileResults.innerHTML = html;

    const apiResponse = await fetch(`/api/profiles?${query}`);
    if (apiResponse.ok) {
        const data = await apiResponse.json();
        statsPanel.textContent = `Showing ${data.visible_count} of ${data.all_count} profiles`;
    }

    const url = `${window.location.pathname}?${query}`;
    window.history.replaceState({}, "", url);
}

const refreshProfilesDebounced = debounce(refreshProfiles);
searchInput.addEventListener("input", refreshProfilesDebounced);
categorySelect.addEventListener("change", refreshProfiles);
versionSelect.addEventListener("change", refreshProfiles);

function withAutoplay(embedUrl) {
    return embedUrl.includes("?") ? `${embedUrl}&autoplay=1` : `${embedUrl}?autoplay=1`;
}

function clearIncludedList() {
    if (!modalIncludedList) {
        return;
    }

    modalIncludedList.innerHTML = "";
}

function appendIncludedItem(value) {
    if (!modalIncludedList || !value) {
        return;
    }

    const item = document.createElement("li");
    item.textContent = value;
    modalIncludedList.appendChild(item);
}

function openProfileModal(trigger) {
    if (!profileModal || !trigger) {
        return;
    }

    const title = trigger.dataset.title || "Untitled Theme";
    const category = trigger.dataset.category || "Unknown";
    const version = trigger.dataset.version || "Unknown";
    const embedUrl = trigger.dataset.videoEmbed || "";
    const youtubeLink = trigger.dataset.videoLink || "";
    const downloadLink = trigger.dataset.downloadLink || "";
    const includedRaw = trigger.dataset.included || "";

    if (modalTitle) {
        modalTitle.textContent = title;
    }
    if (modalMeta) {
        modalMeta.textContent = `${category} / ${version}`;
    }

    clearIncludedList();
    if (includedRaw.trim()) {
        includedRaw.split("||").map((item) => item.trim()).filter(Boolean).forEach(appendIncludedItem);
    } else {
        appendIncludedItem("Standard profile package");
    }

    if (modalVideoFrame) {
        modalVideoFrame.src = embedUrl ? withAutoplay(embedUrl) : "";
    }

    if (modalDownloadBtn) {
        modalDownloadBtn.href = downloadLink || "#";
        modalDownloadBtn.setAttribute("aria-disabled", downloadLink ? "false" : "true");
        modalDownloadBtn.classList.toggle("is-disabled", !downloadLink);
    }

    if (modalYoutubeBtn) {
        modalYoutubeBtn.href = youtubeLink || "#";
        modalYoutubeBtn.setAttribute("aria-disabled", youtubeLink ? "false" : "true");
        modalYoutubeBtn.classList.toggle("is-disabled", !youtubeLink);
    }

    profileModal.hidden = false;
    document.body.classList.add("modal-active");
}

function closeProfileModal() {
    if (!profileModal) {
        return;
    }

    profileModal.hidden = true;
    document.body.classList.remove("modal-active");
    if (modalVideoFrame) {
        modalVideoFrame.src = "";
    }
}

document.addEventListener("click", (event) => {
    const openTrigger = event.target.closest("[data-open-profile]");
    if (openTrigger) {
        openProfileModal(openTrigger);
        return;
    }

    const closeTrigger = event.target.closest("[data-close-modal]");
    if (closeTrigger) {
        closeProfileModal();
    }
});

document.addEventListener("keydown", (event) => {
    const openTrigger = event.target.closest("[data-open-profile]");
    if (openTrigger && (event.key === "Enter" || event.key === " ")) {
        event.preventDefault();
        openProfileModal(openTrigger);
        return;
    }

    if (event.key === "Escape" && profileModal && !profileModal.hidden) {
        closeProfileModal();
    }
});
