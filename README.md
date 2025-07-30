# Offline Attendance System

## 1. Overview

This project is a self-hosted, offline-first attendance management system designed for educational environments where internet connectivity is unreliable or unavailable. By creating a localized network via a standard Wi-Fi router or a mobile hotspot, the system enables teachers to conduct secure and verifiable attendance sessions. Students connect to this local network and use a unique session link to register their presence, which is validated through a multi-layered security protocol, ensuring data integrity and preventing academic dishonesty.

The entire ecosystem—from session creation to student check-in and dashboard monitoring—operates entirely on the Local Area Network (LAN), requiring zero internet access.

## 2. Core Features

* **Server-Independent Offline Operation:** Functions entirely within a local network, making it ideal for classrooms, workshops, and field locations.
* **Flexible Session Types:**
    * **Single Check-In:** A one-time attendance mark at the beginning of a session.
    * **Double Check-In:** Requires students to check-in at the start and check-out at the end, enforcing session duration.
* **Dynamic Session Control:** Teachers can define active time windows for check-in and specify minimum time intervals between check-in and check-out.
* **Effortless Onboarding:** Generates a session-specific URL and two QR codes: one for the attendance link and another for instant Wi-Fi network configuration (SSID/Password).
* **Real-Time Monitoring:** A live dashboard for the teacher to track attendance submissions, view student details, and manually enable the "Check-Out" phase.
* **Robust Anti-Manipulation Framework:** Implements a suite of security measures to prevent impersonation and proxy attendance.

## 3. How It Works: The Offline Architecture

The system's ability to function without the internet is based on standard local networking principles, where all communication is restricted to the physical boundaries of the Wi-Fi signal.

1.  **LAN Creation:** The teacher initiates a private network using a Wi-Fi router or by activating the mobile hotspot feature on their device. This creates an isolated LAN.
2.  **DHCP and IP Address Assignment:** The router/hotspot acts as a DHCP (Dynamic Host Configuration Protocol) server, automatically assigning a unique private IP address (e.g., `192.168.1.x` or `172.20.10.x`) to every device that connects to it, including the teacher's machine and each student's device.
3.  **Local Server Hosting:** The backend application (a Django server) runs directly on the teacher's computer. This machine becomes the host server for the attendance application, accessible only to other devices on the same LAN.
4.  **IP-Based Communication:** When the teacher creates a session, the generated attendance link is based on the local IP address of their machine (e.g., `http://192.168.1.5:8000`). When a student connected to the same network navigates to this URL, their browser sends an HTTP request directly to the teacher's machine over the local network. The request never leaves the LAN and does not traverse the public internet.
5.  **Data Persistence:** All attendance data is stored locally on the teacher's machine in the SQLite database, ensuring data sovereignty and privacy.

This architecture guarantees that only individuals physically present and connected to the designated local network can access the attendance portal.

```
+---------------------------------+
|      Teacher's Device           |
|  (e.g., Laptop)                 |
|                                 |
|  - Runs Web Server (Backend)    |
|  - Hosts Attendance App         |
|  - Local IP: 192.168.1.5        |
|  - Creates Mobile Hotspot/      |
|    Connects to Local Wi-Fi      |
+---------------------------------+
      ^                ^
      | Wi-Fi Signal   | Wi-Fi Signal
      | (IEEE 802.11)  | (IEEE 802.11)
      v                v
+----------------+   +----------------+
| Student Device |   | Student Device |
| - Connects to  |   | - Connects to  |
|   Hotspot/Wi-Fi|   |   Hotspot/Wi-Fi|
| - Local IP:    |   | - Local IP:    |
|   192.168.1.6  |   |   192.168.1.7  |
| - Accesses URL |   | - Accesses URL |
|   via Browser  |   |   via Browser  |
+----------------+   +----------------+
```

## 4. Security & Anti-Cheating Mechanisms

To ensure the integrity of the attendance data, the system relies on a combination of client-side and server-side validation techniques.

* **Network-Based Access Control:** The primary security layer. The web server is only bound to the local network interface, making it physically impossible to access from outside the LAN.
* **Ephemeral Session Tokenization:** Upon a successful initial check-in, the server generates a cryptographically secure, unique token for that specific student's session. This token is stored in the student's browser storage (e.g., `sessionStorage`) and is associated with their roll number on the server.
* **IP Address Logging:** The server logs the local IP address for every submission using `django-ipware`, serving as a powerful deterrent and diagnostic tool to flag multiple submissions originating from a single IP address.
* **Browser Fingerprinting (Optional Enhancement):** As an advanced measure, the system can generate a unique hash based on a combination of browser and device attributes (e.g., user-agent, screen resolution, installed fonts).
* **Server-Side State Validation:** The application logic stringently enforces a **one-submission-per-roll-number** rule for each session.

## 5. Proposed Tech Stack & Dependencies

* **Backend:** **Django (Python)** – A high-level Python web framework that encourages rapid development and clean, pragmatic design.
* **Frontend:** **Vanilla JavaScript (ES6+)**, **HTML5**, **CSS3** – Ensures maximum compatibility and performance on student devices.
* **Database:** **SQLite** – The default database for Django, it's a serverless, self-contained, file-based SQL engine perfect for local data persistence.
* **QR Code Generation:** A Python library like `qrcode` to dynamically generate QR codes.
* **IP Address Inspection:** A library like `django-ipware` to reliably get the client's IP address.

### Dependencies (`requirements.txt`)

```
asgiref==3.9.1
colorama==0.4.6
Django==5.2.4
django-ipware==7.0.1
pillow==11.3.0
qrcode==8.2
sqlparse==0.5.3
tzdata==2025.2
```

## 6. Installation and Setup

Follow these steps to get the application running on the teacher's device.

### Prerequisites

* **Git:** Must be installed to clone the repository.
* **Python:** Version 3.10 or newer is required.

### Steps

1.  **Clone the Repository:**
    ```bash
    git clone https://github.com/AuntMayBro/geolat.git
    cd geolat
    ```

2.  **Create and Activate a Virtual Environment:**
    It is highly recommended to use a virtual environment to manage project dependencies.

    * **On macOS/Linux:**
        ```bash
        python3 -m venv venv
        source venv/bin/activate
        ```
    * **On Windows:**
        ```bash
        python -m venv venv
        .\venv\Scripts\activate
        ```

3.  **Install Dependencies:**
    With the virtual environment activated, install all the required packages from the `requirements.txt` file.
    ```bash
    pip install -r requirements.txt
    ```

4.  **Initialize the Database:**
    Run the `migrate` command to create the `db.sqlite3` database file and set up the necessary tables.
    ```bash
    python manage.py migrate
    ```

5.  **Run the Local Server:**
    Start the Django development server. You must bind it to `<<your-local-ip-address> >` to make it accessible to other devices on your local network.
    ```bash
    python manage.py runserver <your-local-ip-address> :8000
    ```
    **Important:** Using `<your-local-ip-address> ` tells the server to listen on all available network interfaces. This is what allows students' devices on the same Wi-Fi network to connect to the teacher's machine.

## 7. Usage Flow

1.  **Network Setup:** The teacher creates a mobile hotspot or connects their device to a dedicated Wi-Fi router.
2.  **Find IP Address:** The teacher finds their computer's local IP address (e.g., by running `ipconfig` on Windows or `ifconfig`/`ip a` on macOS/Linux).
3.  **Launch Server:** The teacher follows the **Installation and Setup** steps above to start the server.
4.  **Session Creation:** The teacher navigates to the admin dashboard (e.g., `http://192.168.1.5:8000/admin`) and configures a new attendance session.
5.  **Distribution:** The system displays the session URL (using the computer's IP address) and QR codes. The teacher projects these for the class to see.
6.  **Student Connection:** Students connect their devices to the specified Wi-Fi network and scan the QR code or manually enter the URL.
7.  **Check-In:** Students fill in their details and submit. The server validates the request and logs their attendance.
8.  **Live Monitoring:** The teacher observes the incoming attendance on their live dashboard.
9.  **Session Completion:** The session automatically closes after the specified time, or the teacher can manually end it. The final attendance report is then available for export.
