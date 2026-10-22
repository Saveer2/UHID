document.addEventListener("DOMContentLoaded", function() {
    const token = sessionStorage.getItem("uhid_token");
    
    if (!token) {
        window.location.href = "LoginPage.html";
        return;
    }

    // Set doctor name header safely from session storage or default
    const docName = sessionStorage.getItem("uhid_name") || "Doctor";
    const welcomeHeading = document.getElementById("welcomeHeading");
    const sidebarName = document.getElementById("sidebarName");

    if (welcomeHeading) {
        welcomeHeading.textContent = `Welcome, Dr. ${docName}`;
    }
    if (sidebarName) {
        sidebarName.textContent = `Dr. ${docName}`;
    }

    // Handle UHID Lookup Form & Backend Request Integration
    const lookupForm = document.getElementById("uhidLookupForm");
    if (lookupForm) {
        lookupForm.addEventListener("submit", async function(e) {
            e.preventDefault();
            const uhidInput = document.getElementById("searchUhid");
            const uhid = uhidInput ? uhidInput.value.trim() : "";
            const resultContainer = document.getElementById("lookupResult");
            const searchBtn = document.getElementById("searchBtn");
            
            if (!uhid) return;

            if (searchBtn) {
                searchBtn.disabled = true;
                searchBtn.textContent = "Sending Request...";
            }
            if (resultContainer) {
                resultContainer.innerHTML = `<p style="color: #666;">Checking database and submitting access request...</p>`;
            }

            try {
                const response = await fetch("/api/doctors/search-patient", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        "Authorization": `Bearer ${token}`
                    },
                    body: JSON.stringify({ uhid: uhid })
                });

                const data = await response.json();

                if (response.ok && data.success) {
                    if (resultContainer) {
                        resultContainer.innerHTML = `
                            <div class="row" style="background: #f8fafc; padding: 12px; border-radius: 8px; border-left: 4px solid var(--teal, #0d9488);">
                                <b>UHID:</b> ${uhid}<br>
                                <small style="color: var(--teal, #0d9488); font-weight: 600; display: block; margin-top: 4px;">${data.message}</small>
                                <button onclick="loadPatientRecords('${uhid}')" class="btn" style="margin-top: 10px; font-size: 12px; padding: 6px 12px;">Check Records / Refresh Status</button>
                            </div>
                        `;
                    }
                } else {
                    if (resultContainer) {
                        resultContainer.innerHTML = `
                            <div class="row" style="background: #fef2f2; padding: 12px; border-radius: 8px; border-left: 4px solid #dc2626;">
                                <b>Error:</b> <span style="color: #dc2626;">${data.message || "Failed to request access"}</span>
                            </div>
                        `;
                    }
                }
            } catch (error) {
                console.error("Network or API error:", error);
                if (resultContainer) {
                    resultContainer.innerHTML = `
                        <div class="row" style="background: #fef2f2; padding: 12px; border-radius: 8px;">
                            <span style="color: #dc2626;">Network error connecting to server. Please try again.</span>
                        </div>
                    `;
                }
            } finally {
                if (searchBtn) {
                    searchBtn.disabled = false;
                    searchBtn.textContent = "Request Access";
                }
            }
        });
    }

    // Handle Logout
    const logoutBtn = document.getElementById("logoutBtn");
    if (logoutBtn) {
        logoutBtn.addEventListener("click", function(e) {
            e.preventDefault();
            sessionStorage.clear();
            window.location.href = "LandingPage.html";
        });
    }
});

// Global helper function to load patient records once access is approved by the patient
async function loadPatientRecords(uhid) {
    const token = sessionStorage.getItem("uhid_token");
    const consultationsContainer = document.getElementById("consultationsList");

    if (!consultationsContainer) return;

    consultationsContainer.innerHTML = `<p style="color: #666;">Loading medical records for ${uhid}...</p>`;

    try {
        const response = await fetch(`/api/doctors/patient-records/${uhid}`, {
            method: "GET",
            headers: { "Authorization": `Bearer ${token}` }
        });

        const data = await response.json();

        if (response.ok && data.success) {
            if (data.records && data.records.length > 0) {
                consultationsContainer.innerHTML = data.records.map(rec => `
                    <div class="row" style="background: #f8fafc; padding: 14px; margin-bottom: 10px; border-radius: 8px; border-left: 4px solid var(--teal, #0d9488);">
                        <p><strong>Type:</strong> ${rec.record_type}</p>
                        <p><strong>Description:</strong> ${rec.description || 'N/A'}</p>
                        <p><small style="color: #666;">Date: ${rec.created_at}</small></p>
                        ${rec.document_path ? `<a href="${rec.document_path}" target="_blank" class="btn" style="font-size: 12px; padding: 4px 8px; margin-top: 6px; display: inline-block;">View Document</a>` : ''}
                    </div>
                `).join('');
            } else {
                consultationsContainer.innerHTML = `<p style="padding: 10px 0; color: #666;">No medical records found for this patient.</p>`;
            }
        } else {
            consultationsContainer.innerHTML = `
                <div style="background: #fef2f2; padding: 12px; border-radius: 8px; border-left: 4px solid #dc2626;">
                    <span style="color: #dc2626; font-weight: 600;">${data.message || "Access denied or records unavailable. Please ensure the patient has approved your request."}</span>
                </div>
            `;
        }
    } catch (error) {
        console.error("Error loading records:", error);
        consultationsContainer.innerHTML = `<p style="color: #dc2626;">Failed to load records. Check network connection.</p>`;
    }
}