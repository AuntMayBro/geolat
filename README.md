# GeoLat: Geo-Location Based Attendance System

GeoLat is a web-based application built with Django that allows for taking attendance based on the user's geographical location. It is designed for scenarios like classrooms, workshops, or small events where attendance needs to be verified against a specific location.

A teacher can create an attendance "session," which captures the teacher's current location. Students can then "check-in" or "check-out" of the session. The system verifies that the student is within a predefined radius of the teacher's location before marking their attendance.

## Table of Contents

- [Features](#features)
- [How It Works](#how-it-works)
- [Project Structure](#project-structure)
- [Setup and Installation](#setup-and-installation)
- [Usage](#usage)
- [Dependencies](#dependencies)

## Features

-   **Teacher Dashboard:** Teachers can create new attendance sessions and view details of past sessions.
-   **Session Management:** Each session is identified by a unique code and is tied to the teacher's geographical coordinates at the time of creation.
-   **Student Check-in/Check-out:** Students can join a session using its unique code and mark their attendance.
-   **Geo-fencing:** The core feature of the application. It uses the student's browser-based location and compares it to the session's location. Attendance is only successful if the student is within a 100-meter radius.
-   **Attendance Tracking:** Records the check-in and check-out times for each student in a session.

## How It Works

The application flow is divided into two main user roles: Teacher and Student.

1.  **Session Creation (Teacher):**
    * A teacher navigates to the "Create Session" page.
    * The browser prompts for location access. Once granted, the teacher's latitude and longitude are captured.
    * Upon submission, a new `Session` object is created in the database with the captured coordinates and a unique 6-character code is generated.
    * The teacher shares this code with the students.

2.  **Attendance (Student):**
    * A student goes to the home page and enters the session code provided by the teacher.
    * The system validates the code and directs the student to the check-in/check-out form.
    * The student enters their name and email. The browser again requests their location.
    * This location data, along with the student's details, is sent to the server.

3.  **Location Verification (Backend):**
    * The backend receives the student's coordinates and the session's coordinates from the database.
    * It uses the `geopy` library to calculate the great-circle distance between the two points.
    * If the calculated distance is less than or equal to the allowed radius (hardcoded to 100 meters in the `views.py`), the attendance is marked as successful.
    * The student's details and their check-in/check-out time are saved in the `Attendance` model.
    * If the distance is greater than the radius, an error page is displayed to the student.

4.  **Viewing Attendance (Teacher):**
    * The teacher can go to their dashboard and click on any session to see a detailed list of all students who have successfully checked in or out.

## Project Structure

The project is a standard Django application with one core app named `attendance`.


GeoLat/
├── GeoLat/                 # Main Django project configuration
│   ├── settings.py         # Project settings
│   ├── urls.py             # Root URL configuration
│   ├── wsgi.py             # WSGI entry-point
│   └── ...
├── attendance/             # The core application for attendance logic
│   ├── migrations/         # Database migration files
│   ├── templates/          # HTML templates for the app
│   │   └── attendance/
│   │       ├── base.html
│   │       ├── create_session.html
│   │       ├── error.html
│   │       ├── home.html
│   │       ├── session_details.html
│   │       ├── student_checked_in.html
│   │       ├── student_checked_out.html
│   │       ├── student_form.html
│   │       └── teacher_dashboard.html
│   ├── admin.py            # Django admin configurations
│   ├── models.py           # Database models (Session, Student, Attendance)
│   ├── urls.py             # App-specific URL routes
│   └── views.py            # Application logic, request handling
├── templates/              # Global templates
│   └── geolat/
│       └── base.html
├── bash.sh                 # A shell script (likely for setup or deployment)
├── db.sqlite3              # The SQLite database file
├── manage.py               # Django's command-line utility
└── requirements.txt        # Python package dependencies


## Setup and Installation

To run this project on your local machine, follow these steps:

1.  **Clone the Repository / Download Files**
    ```bash
    git clone <repository-url>
    cd GeoLat
    ```
    Or simply extract the provided project files into a folder named `GeoLat`.

2.  **Create and Activate a Virtual Environment** (Recommended)
    ```bash
    # For Windows
    python -m venv venv
    venv\Scripts\activate

    # For macOS/Linux
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Install Dependencies**
    Install all the required Python packages using the `requirements.txt` file.
    ```bash
    pip install -r requirements.txt
    ```

4.  **Run Database Migrations**
    This will apply the database schema from the `attendance/migrations` files.
    ```bash
    python manage.py migrate
    ```

5.  **Create a Superuser** (Optional)
    This allows you to access the Django admin interface to manage data directly.
    ```bash
    python manage.py createsuperuser
    ```
    Follow the prompts to create a username and password.

6.  **Run the Development Server**
    ```bash
    python manage.py runserver
    ```
    The application will be available at `http://127.0.0.1:8000/`.

    **Note:** The browser's Geolocation API requires a secure context (HTTPS) to work on most modern browsers, except for `localhost`. When running locally, it should work fine. If you deploy it, you must use HTTPS.

## Usage

-   **Teacher:**
    1.  Go to `http://127.0.0.1:8000/teacher/`.
    2.  Click on "Create New Session".
    3.  Allow the browser to access your location.
    4.  A new session with a unique code will be created. Share this code with students.
    5.  View attendance by clicking on the session code on the dashboard.

-   **Student:**
    1.  Go to the home page: `http://127.0.0.1:8000/`.
    2.  Enter the session code.
    3.  Fill in your name and email.
    4.  Allow the browser to access your location for verification.
    5.  You will see a confirmation message upon successful check-in/check-out.

## Dependencies

The main dependencies for this project are:

-   **Django:** The web framework used to build the application.
-   **geopy:** A Python library for calculating geodesic distance between geographical points.

All dependencies are listed in the `requirements.txt` file.