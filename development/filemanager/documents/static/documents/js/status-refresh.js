let lastStatusMessage = "";

async function refreshDocumentsStatus() {
    try {
        const response = await fetch("/api/status/");
        const data = await response.json();

        updateLiveStatus(data.latest_status);
        updateSavedDocuments(data.documents);
        updatePendingDocuments(data.pending_documents);

    } catch (error) {
        console.error("Erreur lors du rafraîchissement :", error);
    }
}

function getCsrfToken() {
    const input = document.querySelector("[name=csrfmiddlewaretoken]");
    return input ? input.value : "";
}

function updateLiveStatus(statusData) {
    const container = document.getElementById("live-status-container");

    if (!container) {
        return;
    }

    if (!statusData) {
        container.innerHTML = "";
        lastStatusMessage = "";
        return;
    }

    if (lastStatusMessage === statusData.message) {
        return;
    }

    lastStatusMessage = statusData.message;

    let cssClass = "warning";

    if (statusData.type === "success") {
        cssClass = "success";
    }

    if (statusData.type === "error") {
        cssClass = "error";
    }

    container.innerHTML = `
        <div class="message ${cssClass}">
            ${statusData.message}
        </div>
    `;

    if (statusData.type !== "warning") {
        setTimeout(() => {
            container.innerHTML = "";
        }, 8000);
    }
}

function updateSavedDocuments(documents) {
    const tbody = document.getElementById("documents-table-body");

    if (!tbody) {
        return;
    }

    tbody.innerHTML = "";

    if (documents.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="4">Aucun fichier enregistré</td>
            </tr>
        `;
        return;
    }

    documents.forEach(doc => {
        tbody.innerHTML += `
            <tr>
                <td>📄 ${doc.filename}</td>

                <td style="font-size:12px;">
                    ${doc.file_hash.substring(0, 40)}
                </td>

                <td>
                    <span class="badge badge-success">
                        Enregistré
                    </span>
                </td>

                <td>
                    <div class="actions">
                        <a href="${doc.file_url}" target="_blank" class="btn-info">
                            Ouvrir
                        </a>

                        <form method="POST" action="/delete/${doc.id}/">
                            <input type="hidden" name="csrfmiddlewaretoken" value="${getCsrfToken()}">
                            <button type="submit"
                                    class="btn-danger"
                                    onclick="return confirm('Supprimer ce fichier ?');">
                                Supprimer
                            </button>
                        </form>
                    </div>
                </td>
            </tr>
        `;
    });
}

function updatePendingDocuments(pendingDocuments) {
    const tbody = document.getElementById("pending-table-body");

    if (!tbody) {
        return;
    }

    tbody.innerHTML = "";

    if (pendingDocuments.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="5">Aucun fichier similaire en attente</td>
            </tr>
        `;
        return;
    }

    pendingDocuments.forEach(pending => {
        tbody.innerHTML += `
            <tr>
                <td>📄 ${pending.new_filename}</td>

                <td>📄 ${pending.old_filename}</td>

                <td>
                    <span class="badge badge-warning">
                        ${pending.similarity_score}%
                    </span>
                </td>

                <td>
                    <div class="comparison-box">
                        <div class="content-box">
                            <div class="content-title">Ancien fichier</div>
                            <pre style="white-space:pre-wrap;">${pending.old_content}</pre>
                        </div>

                        <div class="content-box">
                            <div class="content-title">Nouveau fichier</div>
                            <pre style="white-space:pre-wrap;">${pending.new_content}</pre>
                        </div>
                    </div>
                </td>

                <td>
                    <div class="actions">
                        <a href="${pending.old_file_url}" target="_blank" class="btn-info">
                            Ancien
                        </a>

                        <a href="${pending.new_file_url}" target="_blank" class="btn-info">
                            Nouveau
                        </a>

                        <form method="POST" action="/pending/${pending.id}/validate/">
                            <input type="hidden" name="csrfmiddlewaretoken" value="${getCsrfToken()}">
                            <button type="submit"
                                    class="btn-success"
                                    onclick="return confirm('Valider le remplacement ?');">
                                ✅ Valider
                            </button>
                        </form>

                        <form method="POST" action="/pending/${pending.id}/reject/">
                            <input type="hidden" name="csrfmiddlewaretoken" value="${getCsrfToken()}">
                            <button type="submit"
                                    class="btn-danger"
                                    onclick="return confirm('Refuser ce fichier ?');">
                                ❌ Refuser
                            </button>
                        </form>
                    </div>
                </td>
            </tr>
        `;
    });
}

document.addEventListener("DOMContentLoaded", () => {
    refreshDocumentsStatus();
    setInterval(refreshDocumentsStatus, 3000);
});