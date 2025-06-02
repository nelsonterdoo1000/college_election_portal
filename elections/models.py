from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _

class User(AbstractUser):
    STUDENT = 'student'
    ADMIN = 'admin'
    
    ROLE_CHOICES = [
        (STUDENT, 'Student'),
        (ADMIN, 'Administrator'),
    ]
    
    student_id = models.CharField(max_length=50, unique=True, null=True, blank=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default=STUDENT)
    
    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')

class Election(models.Model):
    UPCOMING = 'upcoming'
    ACTIVE = 'active'
    CLOSED = 'closed'
    ARCHIVED = 'archived'
    
    STATUS_CHOICES = [
        (UPCOMING, 'Upcoming'),
        (ACTIVE, 'Active'),
        (CLOSED, 'Closed'),
        (ARCHIVED, 'Archived'),
    ]
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=UPCOMING)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='created_elections')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-start_datetime']
    
    def __str__(self):
        return self.title

class Position(models.Model):
    election = models.ForeignKey(Election, on_delete=models.CASCADE, related_name='positions')
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['order', 'title']
        unique_together = ['election', 'title']
    
    def __str__(self):
        return f"{self.election.title} - {self.title}"

class Candidate(models.Model):
    position = models.ForeignKey(Position, on_delete=models.CASCADE, related_name='candidates')
    name = models.CharField(max_length=100)
    bio = models.TextField(blank=True)
    photo = models.ImageField(upload_to='candidate_photos/', null=True, blank=True)
    order = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['order', 'name']
    
    def __str__(self):
        return f"{self.position.title} - {self.name}"

class EligibleVoter(models.Model):
    election = models.ForeignKey(Election, on_delete=models.CASCADE, related_name='eligible_voters')
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='eligible_elections')
    has_voted = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ['election', 'student']
    
    def __str__(self):
        return f"{self.student.username} - {self.election.title}"

class Vote(models.Model):
    election = models.ForeignKey(Election, on_delete=models.CASCADE, related_name='votes')
    position = models.ForeignKey(Position, on_delete=models.CASCADE, related_name='votes')
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE, related_name='votes')
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='votes')
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['election', 'position']),
        ]
        unique_together = ['election', 'position', 'student']
    
    def __str__(self):
        return f"Vote for {self.candidate.name} in {self.position.title}"

class AuditLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='audit_logs')
    action = models.CharField(max_length=200)
    details = models.JSONField(default=dict)
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.action} by {self.user.username if self.user else 'System'} at {self.timestamp}" 