# models.py - QuickGive Models
from django.db import models
from decimal import Decimal

class Campaign(models.Model):
    """Donation campaigns/causes"""
    CATEGORY_CHOICES = [
        ('humanitarian', 'Humanitarian Aid'),
        ('education', 'Education'),
        ('healthcare', 'Healthcare'),
        ('environment', 'Environment'),
        ('disaster', 'Disaster Relief'),
        ('community', 'Community'),
    ]
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    recipient_address = models.CharField(max_length=42)
    goal_amount = models.DecimalField(max_digits=20, decimal_places=6, default=Decimal('100.0'))
    raised_amount = models.DecimalField(max_digits=20, decimal_places=6, default=Decimal('0'))
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='humanitarian')
    emoji = models.CharField(max_length=10, default='💝')
    image_url = models.URLField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.emoji} {self.title}"
    
    class Meta:
        ordering = ['-created_at']

class Donation(models.Model):
    """Individual donations"""
    donor_address = models.CharField(max_length=42, db_index=True)
    sub_account_address = models.CharField(max_length=42, blank=True, null=True)
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name='donations')
    amount = models.DecimalField(max_digits=20, decimal_places=6)
    tx_hash = models.CharField(max_length=66, unique=True, db_index=True)
    block_number = models.IntegerField(blank=True, null=True)
    used_spend_permission = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.donor_address[:8]}... donated {self.amount} USDC"
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['donor_address', '-created_at']),
        ]

class UserProfile(models.Model):
    """User donation profiles"""
    wallet_address = models.CharField(max_length=42, unique=True, db_index=True)
    total_donated = models.DecimalField(max_digits=20, decimal_places=6, default=Decimal('0'))
    donation_count = models.IntegerField(default=0)
    sub_account_address = models.CharField(max_length=42, blank=True, null=True)
    has_sub_account = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.wallet_address[:8]}... - {self.donation_count} donations"
    
    class Meta:
        ordering = ['-total_donated']