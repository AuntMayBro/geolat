import uuid
import re
from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError

class AttendanceSession(models.Model):
    """
    Represents a single attendance session created by a teacher.
    """
    SESSION_TYPE_CHOICES = [
        ('single', 'Single Check-In'),
        ('double', 'Double Check-In'),
    ]

    # Core Session Details
    title = models.CharField(max_length=200, help_text="e.g., 'CS101 Morning Lecture'")
    session_type = models.CharField(max_length=10, choices=SESSION_TYPE_CHOICES, default='single')
    session_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, help_text="Unique ID for the session URL.")
    
    # Time Window
    start_time = models.DateTimeField(default=timezone.now, help_text="When the session becomes active.")
    end_time = models.DateTimeField(help_text="When the session closes.")
    
    # Double Check-In Specific
    min_interval = models.PositiveIntegerField(default=5, help_text="Minimum minutes between check-in and check-out (for Double Check-In).")
    checkout_enabled = models.BooleanField(default=False, help_text="Teacher enables this to allow check-outs.")

    # Network Details for QR Code
    wifi_ssid = models.CharField(max_length=100, blank=True, null=True, help_text="Wi-Fi Network Name (SSID)")
    wifi_password = models.CharField(max_length=100, blank=True, null=True, help_text="Wi-Fi Password")

    # Roll Number Formatting Rules
    roll_number_prefix = models.CharField(max_length=10, blank=True, null=True, help_text="e.g., 'C' or 'ENG'")
    roll_number_letters = models.PositiveIntegerField(blank=True, null=True, help_text="Number of alphabet characters after the prefix.")
    roll_number_digits = models.PositiveIntegerField(blank=True, null=True, help_text="Number of digits at the end.")

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} ({self.get_session_type_display()})"

    @property
    def is_active(self):
        """Checks if the current time is within the session's active window."""
        now = timezone.now()
        return self.start_time <= now <= self.end_time

    def get_roll_number_format_regex(self):
        """Generates a regex pattern based on the defined format rules."""
        if not any([self.roll_number_prefix, self.roll_number_letters, self.roll_number_digits]):
            return None 

        parts = ['^']
        if self.roll_number_prefix:
            parts.append(re.escape(self.roll_number_prefix))
        if self.roll_number_letters:
            parts.append(f'[a-zA-Z]{{{self.roll_number_letters}}}')
        if self.roll_number_digits:
            parts.append(f'\\d{{{self.roll_number_digits}}}')
        parts.append('$')
        return "".join(parts)
        
class AttendanceRecord(models.Model):
    """
    Represents a single student's attendance record for a session.
    """
    session = models.ForeignKey(AttendanceSession, on_delete=models.CASCADE, related_name='records')
    
    # Student Details
    student_name = models.CharField(max_length=100)
    roll_number = models.CharField(max_length=50)

    # Verification & Security
    checkin_token = models.UUIDField(default=uuid.uuid4, editable=False, help_text="Unique hidden token for this student's check-in.")
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    browser_fingerprint = models.CharField(max_length=255, null=True, blank=True, help_text="A hash representing the user's browser configuration.")

    # Timestamps
    check_in_time = models.DateTimeField(auto_now_add=True)
    check_out_time = models.DateTimeField(null=True, blank=True)

    class Meta:
        # Ensures a student can only check in once per session with the same roll number OR IP.
        unique_together = (('session', 'roll_number'), ('session', 'ip_address'))

    def __str__(self):
        return f"{self.student_name} ({self.roll_number}) - {self.session.title}"