const API_BASE = "/api";

/**
 * Handle user login across roles (patient, doctor, lab_technician, admin)
 */
async function handleLogin(event) {
    event.preventDefault();

    const form = event.currentTarget;
    const email = form.querySelector('[name="email"]').value.trim();
    const password = form.querySelector('[name="password"]').value;
    const message = form.querySelector("#login-message");
    const button = form.querySelector('button[type="submit"]');

    if (message) {
        message.textContent = "";
        message.style.color = "var(--bad, #B3261E)";
    }
    if (button) button.disabled = true;

    try {
        const response = await fetch(`${API_BASE}/auth/login`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ email, password })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.message || "Login failed");
        }

        const destinations = {
            patient: "PatientDashboard.html",
            doctor: "DoctorDashboard.html",
            lab_technician: "ProfessionalDashboard.html",
            admin: "AdminDashboard.html"
        };

        const destination = destinations[data.user.role] || "PatientDashboard.html";

        // Store session tokens and user metadata securely in sessionStorage
        sessionStorage.setItem("uhid_token", data.access_token);
        sessionStorage.setItem("uhid_user", JSON.stringify(data.user));
        sessionStorage.setItem("uhid_name", data.user.name);

        window.location.href = destination;

    } catch (error) {
        if (message) {
            message.textContent = error.message || "Unable to connect to the server";
        } else {
            alert(error.message || "Unable to connect to the server");
        }
    } finally {
        if (button) button.disabled = false;
    }
}

/**
 * Handle patient registration & UHID generation
 */
async function handleRegister(event) {
    event.preventDefault();

    const form = event.currentTarget;
    const button = form.querySelector('button[type="submit"]');

    let message = form.querySelector("#register-message");

    if (!message) {
        message = document.createElement("p");
        message.id = "register-message";
        message.setAttribute("role", "alert");
        message.setAttribute("aria-live", "polite");
        message.style.marginTop = "12px";
        message.style.fontWeight = "700";
        if (button) button.before(message);
    }

    const payload = {
        name: form.querySelector("#name").value.trim(),
        email: form.querySelector("#email").value.trim(),
        phone: form.querySelector("#phone") ? form.querySelector("#phone").value.trim() : "",
        password: form.querySelector("#password").value,
        date_of_birth: form.querySelector("#date_of_birth") ? form.querySelector("#date_of_birth").value : "",
        gender: form.querySelector("#gender") ? form.querySelector("#gender").value : "",
        address: form.querySelector("#address") ? form.querySelector("#address").value.trim() : ""
    };

    message.textContent = "";
    if (button) button.disabled = true;

    try {
        const response = await fetch(`${API_BASE}/auth/register`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(payload)
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.message || "Registration failed");
        }

        message.style.color = "var(--ok, #157F4B)";
        message.textContent = `${data.message}. Your UHID is ${data.user.uhid}. Redirecting to login...`;

        form.reset();

        window.setTimeout(() => {
            window.location.href = "LoginPage.html";
        }, 2500);

    } catch (error) {
        message.style.color = "var(--bad, #B3261E)";
        message.textContent = error.message || "Unable to connect to the server";
    } finally {
        if (button) button.disabled = false;
    }
}

/**
 * Handle professional doctor registration
 */
async function handleDoctorRegister(event) {
    event.preventDefault();

    const form = event.currentTarget;
    const button = form.querySelector('button[type="submit"]');

    let message = form.querySelector("#register-message");
    if (!message) {
        message = document.createElement("p");
        message.id = "register-message";
        message.setAttribute("role", "alert");
        message.setAttribute("aria-live", "polite");
        message.style.marginTop = "12px";
        message.style.fontWeight = "700";
        if (button) button.before(message);
    }

    const password = form.querySelector("#password").value;
    const confirmPassword = form.querySelector("#confirm_password").value;

    if (password !== confirmPassword) {
        message.style.color = "var(--bad, #B3261E)";
        message.textContent = "Passwords do not match.";
        return;
    }

    const payload = {
        name: form.querySelector("#name").value.trim(),
        email: form.querySelector("#email").value.trim(),
        password: password,
        license_number: form.querySelector("#license_number").value.trim(),
        specialization: form.querySelector("#specialization").value.trim(),
        hospital_id: form.querySelector("#hospital_id") ? form.querySelector("#hospital_id").value.trim() : null
    };

    message.textContent = "";
    if (button) button.disabled = true;

    try {
        const response = await fetch(`${API_BASE}/auth/register-doctor`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(payload)
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.message || "Doctor registration failed");
        }

        message.style.color = "var(--ok, #157F4B)";
        message.textContent = `${data.message}. Redirecting to login...`;

        form.reset();

        window.setTimeout(() => {
            window.location.href = "LoginPage.html";
        }, 2500);

    } catch (error) {
        message.style.color = "var(--bad, #B3261E)";
        message.textContent = error.message || "Unable to connect to the server";
    } finally {
        if (button) button.disabled = false;
    }
}

/**
 * Handle system administrator registration
 */
async function handleAdminRegister(event) {
    event.preventDefault();

    const form = event.currentTarget;
    const button = form.querySelector('button[type="submit"]');

    let message = form.querySelector("#register-message");
    if (!message) {
        message = document.createElement("p");
        message.id = "register-message";
        message.setAttribute("role", "alert");
        message.setAttribute("aria-live", "polite");
        message.style.marginTop = "12px";
        message.style.fontWeight = "700";
        if (button) button.before(message);
    }

    const password = form.querySelector("#password").value;
    const confirmPassword = form.querySelector("#confirm_password").value;

    if (password !== confirmPassword) {
        message.style.color = "var(--bad, #B3261E)";
        message.textContent = "Passwords do not match.";
        return;
    }

    const payload = {
        name: form.querySelector("#name").value.trim(),
        email: form.querySelector("#email").value.trim(),
        password: password,
        admin_key: form.querySelector("#admin_key").value.trim()
    };

    message.textContent = "";
    if (button) button.disabled = true;

    try {
        const response = await fetch(`${API_BASE}/auth/register-admin`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(payload)
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.message || "Admin registration failed");
        }

        message.style.color = "var(--ok, #157F4B)";
        message.textContent = `${data.message || "Admin registered successfully"}. Redirecting to login...`;

        form.reset();

        window.setTimeout(() => {
            window.location.href = "LoginPage.html";
        }, 2500);

    } catch (error) {
        message.style.color = "var(--bad, #B3261E)";
        message.textContent = error.message || "Unable to connect to the server";
    } finally {
        if (button) button.disabled = false;
    }
}

/**
 * Search patient by UHID (Doctor utility)
 */
async function searchPatientByUhid(uhid) {
    const token = sessionStorage.getItem("uhid_token");
    
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
        if (data.success) {
            alert("Access requested successfully! Awaiting patient approval.");
        } else {
            alert(data.message || "Patient not found");
        }
    } catch (err) {
        console.error("Error searching patient:", err);
    }
}

/**
 * Handle doctor search form submission
 */
async function handleDoctorSearch(event) {
    event.preventDefault();
    
    const uhidInput = document.getElementById("uhidSearchInput");
    const uhid = uhidInput ? uhidInput.value.trim() : "";
    const token = sessionStorage.getItem("uhid_token");

    if (!uhid) {
        alert("Please enter a patient UHID");
        return;
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
            alert("Access requested successfully! Check patient dashboard.");
            uhidInput.value = "";
        } else {
            alert(data.message || "Failed to request access");
        }
    } catch (err) {
        console.error("Network or server error:", err);
        alert("Could not connect to the server.");
    }
}

// ==================== HARDWARE RFID LOGIN LISTENER ====================
let isListeningForHardware = false;
let hardwarePollInterval = null;

function toggleHardwareLogin() {
    const statusEl = document.getElementById("hardwareStatus");
    const btnEl = document.getElementById("hardwareListenBtn");

    if (!isListeningForHardware) {
        isListeningForHardware = true;
        if (btnEl) {
            btnEl.textContent = "Cancel Hardware Listening";
            btnEl.style.background = "#fee2e2";
            btnEl.style.color = "#b91c1c";
        }
        if (statusEl) {
            statusEl.textContent = "Waiting for ESP32 card tap & PIN verification...";
        }

        // Poll backend every 2 seconds to check if the ESP32 successfully authenticated a scan
        hardwarePollInterval = setInterval(async () => {
            try {
                const res = await fetch(`${API_BASE}/auth/check-rfid-login`);
                const data = await res.json();

                if (data.success && data.token) {
                    clearInterval(hardwarePollInterval);
                    
                    // Store authentication token and user profile using standard session keys
                    sessionStorage.setItem("uhid_token", data.token);
                    sessionStorage.setItem("uhid_user", JSON.stringify(data.user));
                    sessionStorage.setItem("uhid_name", data.user.name);
                    
                    if (statusEl) {
                        statusEl.textContent = "Hardware login successful! Redirecting...";
                    }

                    const destinations = {
                        patient: "PatientDashboard.html",
                        doctor: "DoctorDashboard.html",
                        lab_technician: "ProfessionalDashboard.html",
                        admin: "AdminDashboard.html"
                    };
                    const destination = destinations[data.user.role] || "PatientDashboard.html";

                    setTimeout(() => {
                        window.location.href = destination;
                    }, 1000);
                }
            } catch (err) {
                console.error("Hardware poll error:", err);
            }
        }, 2000);
    } else {
        stopHardwareListening();
    }
}

function stopHardwareListening() {
    isListeningForHardware = false;
    clearInterval(hardwarePollInterval);
    const btnEl = document.getElementById("hardwareListenBtn");
    const statusEl = document.getElementById("hardwareStatus");
    if (btnEl) {
        btnEl.textContent = "Listen for Hardware Scan";
        btnEl.style.background = "";
        btnEl.style.color = "";
    }
    if (statusEl) {
        statusEl.textContent = "";
    }
}