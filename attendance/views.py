import qrcode
import base64
import datetime
import re
import csv # Import the csv module
from io import BytesIO
from django.db import IntegrityError
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.urls import reverse
from django.utils import timezone
from django.utils.timezone import make_aware
from django.views.decorators.http import require_POST
from ipware import get_client_ip

from .models import AttendanceSession, AttendanceRecord

# --- Teacher Views ---


def home(request):
    return render(request,'attendance/home.html') 

def readme(request):
    return render(request,'attendance/readme.html') 

def teacher_dashboard(request):
    """
    Displays a list of all created attendance sessions.
    """
    sessions = AttendanceSession.objects.all().order_by('-created_at')
    return render(request, 'attendance/teacher_dashboard.html', {'sessions': sessions})

def create_session(request):
    """
    Handles the creation of a new attendance session by the teacher.
    """
    if request.method == 'POST':
        # Get naive datetime strings from the form
        start_time_str = request.POST.get('start_time')
        end_time_str = request.POST.get('end_time')

        # Convert them to datetime objects
        start_time_naive = datetime.datetime.fromisoformat(start_time_str)
        end_time_naive = datetime.datetime.fromisoformat(end_time_str)

        # Make them timezone-aware using the project's current timezone
        start_time_aware = make_aware(start_time_naive)
        end_time_aware = make_aware(end_time_naive)

        # Create a new session object with the timezone-aware datetimes
        session = AttendanceSession.objects.create(
            title=request.POST.get('title'),
            session_type=request.POST.get('session_type'),
            start_time=start_time_aware,
            end_time=end_time_aware,
            min_interval=request.POST.get('min_interval', 5),
            wifi_ssid=request.POST.get('wifi_ssid', ''),
            wifi_password=request.POST.get('wifi_password', ''),
            # New Roll Number Format fields
            roll_number_prefix=request.POST.get('roll_number_prefix') or None,
            roll_number_letters=request.POST.get('roll_number_letters') or None,
            roll_number_digits=request.POST.get('roll_number_digits') or None,
        )
        # Redirect to the details page for the newly created session
        return redirect('session_details', session_id=session.session_id)
    
    return render(request, 'attendance/create_session.html')

def session_details(request, session_id):
    """
    Displays the details for a specific session, including the attendance link,
    QR codes, and a live list of attendees.
    """
    session = get_object_or_404(AttendanceSession, session_id=session_id)
    
    # Generate the full URL for students to access
    attendance_link = request.build_absolute_uri(reverse('student_form', args=[session.session_id]))
    
    # Generate QR code for the attendance link
    qr_img = qrcode.make(attendance_link)
    buffer = BytesIO()
    qr_img.save(buffer, format="PNG")
    link_qr_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')

    # Generate QR code for Wi-Fi credentials
    wifi_qr_base64 = None
    if session.wifi_ssid:
        wifi_string = f"WIFI:T:WPA;S:{session.wifi_ssid};P:{session.wifi_password};;"
        wifi_qr_img = qrcode.make(wifi_string)
        buffer = BytesIO()
        wifi_qr_img.save(buffer, format="PNG")
        wifi_qr_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')

    context = {
        'session': session,
        'attendance_link': attendance_link,
        'link_qr_base64': link_qr_base64,
        'wifi_qr_base64': wifi_qr_base64,
    }
    return render(request, 'attendance/session_details.html', context)

@require_POST
def toggle_checkout(request, session_id):
    """
    Allows the teacher to enable or disable the checkout functionality for a session.
    """
    session = get_object_or_404(AttendanceSession, session_id=session_id)
    session.checkout_enabled = not session.checkout_enabled
    session.save()
    return redirect('session_details', session_id=session.session_id)

def get_live_attendance(request, session_id):
    """
    API endpoint to fetch live attendance data for the teacher's dashboard.
    """
    session = get_object_or_404(AttendanceSession, session_id=session_id)
    records = session.records.all().values(
        'student_name', 'roll_number', 'check_in_time', 'check_out_time', 'ip_address'
    )
    # Convert datetime objects to string for JSON serialization
    for record in records:
        record['check_in_time'] = record['check_in_time'].strftime('%Y-%m-%d %H:%M:%S') if record['check_in_time'] else None
        record['check_out_time'] = record['check_out_time'].strftime('%Y-%m-%d %H:%M:%S') if record['check_out_time'] else None

    return JsonResponse({'records': list(records)})

def download_attendance_csv(request, session_id):
    """
    Generates and serves a CSV file of the attendance records for a specific session.
    """
    session = get_object_or_404(AttendanceSession, session_id=session_id)
    
    # Sanitize the filename
    filename = re.sub(r'[^a-zA-Z0-9_]', '', session.title.replace(' ', '_'))
    
    # Create the HttpResponse object with the appropriate CSV header.
    response = HttpResponse(
        content_type='text/csv',
        headers={'Content-Disposition': f'attachment; filename="attendance_{filename}.csv"'},
    )

    writer = csv.writer(response)
    
    # Write the header row
    writer.writerow(['Student Name', 'Roll Number', 'Check-In Time', 'Check-Out Time', 'IP Address'])

    # Write data rows
    records = session.records.all().order_by('check_in_time')
    for record in records:
        check_in_time = record.check_in_time.strftime('%Y-%m-%d %H:%M:%S') if record.check_in_time else 'N/A'
        check_out_time = record.check_out_time.strftime('%Y-%m-%d %H:%M:%S') if record.check_out_time else 'N/A'
        
        writer.writerow([
            record.student_name,
            record.roll_number,
            check_in_time,
            check_out_time,
            record.ip_address
        ])

    return response


# --- Student Views ---

def student_form(request, session_id):
    """
    The main view for students. Handles both check-in and check-out logic.
    """
    session = get_object_or_404(AttendanceSession, session_id=session_id)
    client_ip, _ = get_client_ip(request)
    
    server_ip = request.META.get('SERVER_NAME')
    is_local = server_ip == '127.0.0.1' or server_ip == 'localhost' or (client_ip and client_ip.startswith('192.168.'))

    if not is_local:
         return render(request, 'attendance/error.html', {'message': 'You must be connected to the local Wi-Fi network to access this page.'})

    if not session.is_active:
        error_context = {
            'message': 'This attendance session is not currently active.',
            'details': f"The session is scheduled to be active from {session.start_time.strftime('%b %d, %H:%M')} to {session.end_time.strftime('%b %d, %H:%M')} (Server Time: {timezone.now().strftime('%b %d, %H:%M')})."
        }
        return render(request, 'attendance/error.html', error_context)

    if request.method == 'POST':
        action = request.POST.get('action')
        roll_number = request.POST.get('roll_number')
        
        if action == 'check-in':
            return handle_check_in(request, session, client_ip)
        elif action == 'check-out':
            return handle_check_out(request, session, roll_number)

    # --- Prepare roll number format details for the template ---
    roll_number_format_details = {
        'placeholder': "Your Roll Number",
        'title': "Please enter your roll number.",
        'pattern': ".*", # Default: allow any characters
    }
    format_parts = []
    if session.roll_number_prefix:
        format_parts.append(f"starts with '{session.roll_number_prefix}'")
    if session.roll_number_letters:
        format_parts.append(f"{session.roll_number_letters} letters")
    if session.roll_number_digits:
        format_parts.append(f"{session.roll_number_digits} digits")

    if format_parts:
        roll_number_format_details['placeholder'] = f"Format: {session.roll_number_prefix or ''}{'A'* (session.roll_number_letters or 0)}{'D'* (session.roll_number_digits or 0)}"
        roll_number_format_details['title'] = f"Roll number must be in the format: {', '.join(format_parts)}."
        roll_number_format_details['pattern'] = session.get_roll_number_format_regex()

    context = {
        'session': session,
        'is_local': is_local,
        'roll_number_format': roll_number_format_details
    }
    return render(request, 'attendance/student_form.html', context)


def handle_check_in(request, session, client_ip):
    """
    Processes a student's check-in request with enhanced validation.
    """
    roll_number = request.POST.get('roll_number', '').strip()
    student_name = request.POST.get('student_name', '').strip()

    # 1. Validate Roll Number Format
    required_pattern = session.get_roll_number_format_regex()
    if required_pattern and not re.match(required_pattern, roll_number):
        error_message = f"Invalid roll number format. Please ensure your roll number is in the correct format and try again."
        return render(request, 'attendance/error.html', {'message': error_message})

    try:
        # 2. Create the record. The database will enforce uniqueness.
        record = AttendanceRecord.objects.create(
            session=session,
            student_name=student_name,
            roll_number=roll_number,
            ip_address=client_ip,
            browser_fingerprint=request.POST.get('fingerprint', '')
        )
    except IntegrityError:
        # This block catches violations of the `unique_together` constraint
        if AttendanceRecord.objects.filter(session=session, ip_address=client_ip).exists():
            # The IP address is the duplicate
            return render(request, 'attendance/error.html', {'message': 'This device has already filled the form.'})
        elif AttendanceRecord.objects.filter(session=session, roll_number=roll_number).exists():
             # The Roll Number is the duplicate
            return render(request, 'attendance/error.html', {'message': 'This roll number has already been used for this session.'})
        else:
            # A different, unexpected integrity error
            return render(request, 'attendance/error.html', {'message': 'A database error occurred. Please try again.'})


    # The checkin_token is sent to the student's browser to be stored in localStorage
    return render(request, 'attendance/student_checked_in.html', {
        'session': session,
        'record': record,
        'checkin_token': record.checkin_token
    })

def handle_check_out(request, session, roll_number):
    """
    Processes a student's check-out request.
    """
    if not session.checkout_enabled:
        return render(request, 'attendance/error.html', {'message': 'Check-out is not yet enabled for this session.'})

    try:
        record = AttendanceRecord.objects.get(session=session, roll_number=roll_number)
    except AttendanceRecord.DoesNotExist:
        return render(request, 'attendance/error.html', {'message': 'No check-in record found for this roll number.'})

    # Verify the token sent from the student's browser
    submitted_token = request.POST.get('checkin_token')
    if str(record.checkin_token) != submitted_token:
        return render(request, 'attendance/error.html', {'message': 'Invalid session token. Check-out failed.'})

    if record.check_out_time is not None:
        return render(request, 'attendance/error.html', {'message': 'You have already checked out.'})
        
    # Check minimum interval
    time_since_checkin = (timezone.now() - record.check_in_time).total_seconds() / 60
    if time_since_checkin < session.min_interval:
        return render(request, 'attendance/error.html', {'message': f'You must wait at least {session.min_interval} minutes before checking out.'})

    record.check_out_time = timezone.now()
    record.save()
    return render(request, 'attendance/student_checked_out.html', {'record': record})