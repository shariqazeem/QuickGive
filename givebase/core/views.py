# views.py - QuickGive: Auto Spend Permissions Demo
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Sum, Count, Q
from decimal import Decimal
import json
from datetime import datetime, timedelta
from .models import Donation, Campaign, UserProfile

def index(request):
    """Landing page showcasing Auto Spend Permissions"""
    return render(request, 'quickgive_landing.html')

def app(request):
    """Main app with Base Account SDK Sub Accounts + Auto Spend"""
    context = {
        'base_sepolia_rpc': 'https://sepolia.base.org',
        'chain_id': 84532,  # Base Sepolia
        'usdc_address': '0x036CbD53842c5426634e7929541eC2318f3dCF7e',  # USDC on Base Sepolia
        'spend_permission_manager': '0x506c54DFD93Cf6fa88e016d88aB8727516dC6405',  # Base Sepolia
    }
    return render(request, 'quickgive_app.html', context)

def campaigns(request):
    """Get active donation campaigns with real-time stats"""
    try:
        campaigns = Campaign.objects.filter(is_active=True).order_by('-created_at')
        
        campaigns_data = []
        for campaign in campaigns:
            # Calculate unique donors and instant donations
            donations = campaign.donations.all()
            unique_donors = donations.values('donor_address').distinct().count()
            instant_donations = donations.filter(used_spend_permission=True).count()
            
            campaigns_data.append({
                'id': campaign.id,
                'title': campaign.title,
                'description': campaign.description,
                'recipient_address': campaign.recipient_address,
                'goal_amount': str(campaign.goal_amount),
                'raised_amount': str(campaign.raised_amount),
                'donor_count': unique_donors,
                'instant_donations': instant_donations,
                'emoji': campaign.emoji,
                'category': campaign.category,
                'image_url': campaign.image_url,
                'progress': min(
                    (float(campaign.raised_amount) / float(campaign.goal_amount)) * 100, 
                    100
                ) if campaign.goal_amount > 0 else 0,
                'created_at': campaign.created_at.isoformat(),
            })
        
        return JsonResponse({
            'success': True,
            'campaigns': campaigns_data,
            'total': len(campaigns_data)
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

def stats(request):
    """Get platform statistics with Auto Spend metrics"""
    try:
        # Overall stats
        total_donated = Donation.objects.aggregate(
            Sum('amount')
        )['amount__sum'] or Decimal('0')
        
        total_donors = UserProfile.objects.filter(
            total_donated__gt=0
        ).count()
        
        active_campaigns = Campaign.objects.filter(is_active=True).count()
        total_donations = Donation.objects.count()
        
        # Auto Spend Permission specific stats
        sub_account_donations = Donation.objects.filter(
            used_spend_permission=True
        ).count()
        
        regular_donations = total_donations - sub_account_donations
        sub_account_percentage = (
            (sub_account_donations / total_donations * 100) 
            if total_donations > 0 else 0
        )
        
        # Recent activity (last 24 hours)
        yesterday = datetime.now() - timedelta(days=1)
        recent_donations = Donation.objects.filter(
            created_at__gte=yesterday
        ).count()
        
        recent_auto_donations = Donation.objects.filter(
            created_at__gte=yesterday,
            used_spend_permission=True
        ).count()
        
        # Users with sub accounts
        users_with_sub = UserProfile.objects.filter(
            has_sub_account=True
        ).count()
        
        return JsonResponse({
            'total_donated': str(total_donated),
            'total_donors': total_donors,
            'active_campaigns': active_campaigns,
            'total_donations': total_donations,
            'sub_account_donations': sub_account_donations,
            'regular_donations': regular_donations,
            'sub_account_percentage': round(sub_account_percentage, 1),
            'recent_donations': recent_donations,
            'recent_auto_donations': recent_auto_donations,
            'users_with_sub': users_with_sub,
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

def user_donations(request):
    """Get user's donation history with Auto Spend status"""
    wallet_address = request.GET.get('address', '').lower()
    
    if not wallet_address:
        return JsonResponse({
            'success': False,
            'error': 'Address required'
        }, status=400)
    
    try:
        # Get or create profile
        profile, created = UserProfile.objects.get_or_create(
            wallet_address=wallet_address,
            defaults={
                'total_donated': Decimal('0'),
                'donation_count': 0
            }
        )
        
        # Get donations
        donations = Donation.objects.filter(
            donor_address=wallet_address
        ).select_related('campaign').order_by('-created_at')
        
        donations_data = []
        for donation in donations[:50]:  # Last 50 donations
            donations_data.append({
                'id': donation.id,
                'campaign_id': donation.campaign.id,
                'campaign_title': donation.campaign.title,
                'campaign_emoji': donation.campaign.emoji,
                'amount': str(donation.amount),
                'tx_hash': donation.tx_hash,
                'used_sub_account': donation.used_spend_permission,
                'block_number': donation.block_number,
                'created_at': donation.created_at.isoformat(),
            })
        
        # Calculate auto spend usage
        auto_spend_count = donations.filter(used_spend_permission=True).count()
        auto_spend_percentage = (
            (auto_spend_count / donations.count() * 100) 
            if donations.count() > 0 else 0
        )
        
        return JsonResponse({
            'success': True,
            'donations': donations_data,
            'total_donated': str(profile.total_donated),
            'donation_count': profile.donation_count,
            'has_sub_account': profile.has_sub_account,
            'sub_account_address': profile.sub_account_address,
            'auto_spend_count': auto_spend_count,
            'auto_spend_percentage': round(auto_spend_percentage, 1),
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@csrf_exempt
def record_donation(request):
    """Record a donation with Auto Spend Permission tracking"""
    if request.method != 'POST':
        return JsonResponse({
            'success': False,
            'error': 'POST required'
        }, status=405)
    
    try:
        data = json.loads(request.body)
        
        # Validate required fields
        donor_address = data.get('donor_address', '').lower()
        sub_account_address = (
            data.get('sub_account_address', '').lower() 
            if data.get('sub_account_address') else None
        )
        campaign_id = data.get('campaign_id')
        amount = Decimal(str(data.get('amount', '0')))
        tx_hash = data.get('tx_hash', '')
        used_spend_permission = data.get('used_spend_permission', False)
        block_number = data.get('block_number')
        
        if not all([donor_address, campaign_id, amount, tx_hash]):
            return JsonResponse({
                'success': False,
                'error': 'Missing required fields'
            }, status=400)
        
        # Validate amount
        if amount <= 0:
            return JsonResponse({
                'success': False,
                'error': 'Invalid amount'
            }, status=400)
        
        # Get campaign
        try:
            campaign = Campaign.objects.get(id=campaign_id)
        except Campaign.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Campaign not found'
            }, status=404)
        
        # Check for duplicate transaction
        if Donation.objects.filter(tx_hash=tx_hash).exists():
            return JsonResponse({
                'success': False,
                'error': 'Donation already recorded'
            }, status=400)
        
        # Create donation record
        donation = Donation.objects.create(
            donor_address=donor_address,
            sub_account_address=sub_account_address,
            campaign=campaign,
            amount=amount,
            tx_hash=tx_hash,
            block_number=block_number,
            used_spend_permission=used_spend_permission,
        )
        
        # Update campaign total
        campaign.raised_amount = (campaign.raised_amount or 0) + amount
        campaign.save()
        
        # Update or create user profile
        profile, created = UserProfile.objects.get_or_create(
            wallet_address=donor_address,
            defaults={
                'total_donated': Decimal('0'),
                'donation_count': 0
            }
        )
        
        # Update profile stats
        profile.total_donated = (profile.total_donated or 0) + amount
        profile.donation_count = (profile.donation_count or 0) + 1
        
        # Update sub account info
        if sub_account_address:
            profile.sub_account_address = sub_account_address
            profile.has_sub_account = True
        
        profile.save()
        
        return JsonResponse({
            'success': True,
            'donation_id': donation.id,
            'message': 'Donation recorded successfully',
            'used_auto_spend': used_spend_permission,
            'campaign_progress': float(campaign.raised_amount / campaign.goal_amount * 100) if campaign.goal_amount > 0 else 0,
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@csrf_exempt
def update_sub_account(request):
    """Update user's sub account address for Auto Spend"""
    if request.method != 'POST':
        return JsonResponse({
            'success': False,
            'error': 'POST required'
        }, status=405)
    
    try:
        data = json.loads(request.body)
        
        wallet_address = data.get('wallet_address', '').lower()
        sub_account_address = data.get('sub_account_address', '').lower()
        
        if not all([wallet_address, sub_account_address]):
            return JsonResponse({
                'success': False,
                'error': 'Missing required fields'
            }, status=400)
        
        # Update or create profile
        profile, created = UserProfile.objects.get_or_create(
            wallet_address=wallet_address,
            defaults={
                'total_donated': Decimal('0'),
                'donation_count': 0
            }
        )
        
        profile.sub_account_address = sub_account_address
        profile.has_sub_account = True
        profile.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Sub account updated successfully',
            'created': created,
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@csrf_exempt
def check_permission(request):
    """Check if user has active spend permission"""
    wallet_address = request.GET.get('address', '').lower()
    
    if not wallet_address:
        return JsonResponse({
            'success': False,
            'error': 'Address required'
        }, status=400)
    
    try:
        profile = UserProfile.objects.get(wallet_address=wallet_address)
        
        # Check if they have made auto-spend donations
        has_permission = Donation.objects.filter(
            donor_address=wallet_address,
            used_spend_permission=True
        ).exists()
        
        return JsonResponse({
            'success': True,
            'has_permission': has_permission,
            'has_sub_account': profile.has_sub_account,
            'sub_account_address': profile.sub_account_address,
        })
        
    except UserProfile.DoesNotExist:
        return JsonResponse({
            'success': True,
            'has_permission': False,
            'has_sub_account': False,
            'sub_account_address': None,
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)