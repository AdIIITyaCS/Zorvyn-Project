from django.db import models
from django.core.validators import MinValueValidator
from users.models import User


class FinancialRecord(models.Model):
    """
    Model for storing financial transactions (income/expense entries).
    Each record represents a single financial transaction.
    """
    TRANSACTION_TYPE_CHOICES = [
        ('income', 'Income'),
        ('expense', 'Expense'),
    ]

    CATEGORY_CHOICES = [
        ('salary', 'Salary'),
        ('investment', 'Investment'),
        ('bonus', 'Bonus'),
        ('food', 'Food'),
        ('transportation', 'Transportation'),
        ('utilities', 'Utilities'),
        ('entertainment', 'Entertainment'),
        ('healthcare', 'Healthcare'),
        ('education', 'Education'),
        ('other', 'Other'),
    ]

    # Core fields
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='financial_records')
    amount = models.DecimalField(
        max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    transaction_type = models.CharField(
        max_length=10, choices=TRANSACTION_TYPE_CHOICES)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    date = models.DateField()

    # Additional fields
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)  # Soft delete

    class Meta:
        ordering = ['-date', '-created_at']
        indexes = [
            models.Index(fields=['user', '-date']),
            models.Index(fields=['user', 'transaction_type']),
            models.Index(fields=['user', 'category']),
            models.Index(fields=['is_deleted']),
        ]

    def __str__(self):
        return f"{self.get_transaction_type_display()}: {self.amount} ({self.category})"

    def save(self, *args, **kwargs):
        """Ensure amount is positive."""
        if self.amount < 0:
            raise ValueError("Amount must be positive")
        super().save(*args, **kwargs)
