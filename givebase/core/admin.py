# admin.py - Enhanced Admin for QuickGive
from django.contrib import admin
from django.utils.html import format_html
from .models import Campaign, Donation, UserProfile

@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    list_display = ['emoji_display', 'title', 'category', 'recipient_short', 'raised_amount', 'goal_amount', 'progress_display', 'is_active']
    list_filter = ['category', 'is_active', 'created_at']
    search_fields = ['title', 'description', 'recipient_address']
    list_editable = ['is_active']
    readonly_fields = ['raised_amount', 'created_at', 'updated_at', 'recipient_link']
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('title', 'description', 'emoji', 'category', 'image_url')
        }),
        ('Financial', {
            'fields': ('goal_amount', 'raised_amount')
        }),
        ('Blockchain', {
            'fields': ('recipient_address', 'recipient_link'),
            'description': 'Set the wallet address where donations will be sent. Must be a valid Ethereum address.'
        }),
        ('Status', {
            'fields': ('is_active', 'created_at', 'updated_at')
        }),
    )
    
    def emoji_display(self, obj):
        return obj.emoji
    emoji_display.short_description = ''
    
    def recipient_short(self, obj):
        if obj.recipient_address and len(obj.recipient_address) > 10:
            return f"{obj.recipient_address[:6]}...{obj.recipient_address[-4:]}"
        return obj.recipient_address or 'Not Set'
    recipient_short.short_description = 'Recipient'
    
    def recipient_link(self, obj):
        if obj.recipient_address:
            return format_html(
                '<a href="https://sepolia.basescan.org/address/{}" target="_blank">{}</a>',
                obj.recipient_address,
                obj.recipient_address
            )
        return 'Not set'
    recipient_link.short_description = 'Recipient Address (View on BaseScan)'
    
    def progress_display(self, obj):
        if obj.goal_amount > 0:
            progress = float((obj.raised_amount / obj.goal_amount) * 100)
            progress_capped = min(progress, 100)
            color = '#10B981' if progress >= 100 else '#3B82F6'
            progress_text = '{:.1f}%'.format(progress)
            
            return format_html(
                '<div style="width:100px; background:#e5e7eb; border-radius:10px; overflow:hidden;">'
                '<div style="width:{}%; background:{}; height:20px; border-radius:10px;"></div>'
                '</div>'
                '<span style="margin-left:5px;">{}</span>',
                progress_capped,
                color,
                progress_text
            )
        return '0%'
    progress_display.short_description = 'Progress'

@admin.register(Donation)
class DonationAdmin(admin.ModelAdmin):
    list_display = ['donor_short', 'campaign', 'amount', 'auto_spend_badge', 'tx_link', 'created_at']
    list_filter = ['used_spend_permission', 'campaign', 'created_at']
    search_fields = ['donor_address', 'sub_account_address', 'tx_hash']
    readonly_fields = ['donor_address', 'sub_account_address', 'campaign', 'amount', 'tx_hash', 'block_number', 'used_spend_permission', 'created_at', 'tx_explorer_link']
    
    fieldsets = (
        ('Donor Info', {
            'fields': ('donor_address', 'sub_account_address')
        }),
        ('Donation Details', {
            'fields': ('campaign', 'amount', 'used_spend_permission')
        }),
        ('Blockchain', {
            'fields': ('tx_hash', 'tx_explorer_link', 'block_number')
        }),
        ('Metadata', {
            'fields': ('created_at',)
        }),
    )
    
    def donor_short(self, obj):
        return f"{obj.donor_address[:6]}...{obj.donor_address[-4:]}"
    donor_short.short_description = 'Donor'
    
    def auto_spend_badge(self, obj):
        if obj.used_spend_permission:
            return format_html(
                '<span style="background:#10B981; color:white; padding:2px 8px; border-radius:10px; font-size:11px;">⚡ AUTO</span>'
            )
        return format_html(
            '<span style="background:#6B7280; color:white; padding:2px 8px; border-radius:10px; font-size:11px;">MANUAL</span>'
        )
    auto_spend_badge.short_description = 'Type'
    
    def tx_link(self, obj):
        return format_html(
            '<a href="https://sepolia.basescan.org/tx/{}" target="_blank">View TX</a>',
            obj.tx_hash
        )
    tx_link.short_description = 'Transaction'
    
    def tx_explorer_link(self, obj):
        return format_html(
            '<a href="https://sepolia.basescan.org/tx/{}" target="_blank">{}</a>',
            obj.tx_hash,
            obj.tx_hash
        )
    tx_explorer_link.short_description = 'Transaction Hash (View on BaseScan)'

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['wallet_short', 'total_donated', 'donation_count', 'sub_account_badge', 'created_at']
    list_filter = ['has_sub_account', 'created_at']
    search_fields = ['wallet_address', 'sub_account_address']
    readonly_fields = ['wallet_address', 'total_donated', 'donation_count', 'sub_account_address', 'has_sub_account', 'created_at', 'updated_at', 'wallet_link']
    
    fieldsets = (
        ('Wallet Info', {
            'fields': ('wallet_address', 'wallet_link')
        }),
        ('Sub Account', {
            'fields': ('sub_account_address', 'has_sub_account')
        }),
        ('Statistics', {
            'fields': ('total_donated', 'donation_count')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def wallet_short(self, obj):
        return f"{obj.wallet_address[:6]}...{obj.wallet_address[-4:]}"
    wallet_short.short_description = 'Wallet'
    
    def sub_account_badge(self, obj):
        if obj.has_sub_account:
            return format_html(
                '<span style="background:#10B981; color:white; padding:2px 8px; border-radius:10px; font-size:11px;">✓ YES</span>'
            )
        return format_html(
            '<span style="background:#6B7280; color:white; padding:2px 8px; border-radius:10px; font-size:11px;">NO</span>'
        )
    sub_account_badge.short_description = 'Sub Account'
    
    def wallet_link(self, obj):
        return format_html(
            '<a href="https://sepolia.basescan.org/address/{}" target="_blank">{}</a>',
            obj.wallet_address,
            obj.wallet_address
        )
    wallet_link.short_description = 'Wallet Address (View on BaseScan)'

# Customize admin site
admin.site.site_header = 'QuickGive Admin ⚡'
admin.site.site_title = 'QuickGive'
admin.site.index_title = 'Manage Campaigns & Donations'