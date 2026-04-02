from django.db import models
from django.core.validators import EmailValidator
from django.utils import timezone


class Role(models.Model):
    """
    Define available roles in the system.
    Role types define what actions users can perform.
    """
    ROLE_CHOICES = [
        ('viewer', 'Viewer'),
        ('analyst', 'Analyst'),
        ('admin', 'Admin'),
    ]

    name = models.CharField(max_length=20, choices=ROLE_CHOICES, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.get_name_display()}"


class User(models.Model):
    """
    User model for managing users in the finance system.
    Stores basic user information and role assignment.
    """
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    ]

    username = models.CharField(max_length=100, unique=True)
    email = models.EmailField(validators=[EmailValidator()], unique=True)
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    role = models.ForeignKey(Role, on_delete=models.PROTECT)
    status = models.CharField(
        max_length=10, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_login = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['username']),
            models.Index(fields=['email']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"{self.username} ({self.role.name})"

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip() or self.username

    def is_active(self):
        return self.status == 'active'
