from django.core.management.base import BaseCommand
from django.db.models import Sum
from decimal import Decimal
import json
from datetime import datetime
from core.models import UserProfile, TokenReward

class Command(BaseCommand):
    help = 'Generate production airdrop data for $GIVE token'

    def add_arguments(self, parser):
        parser.add_argument(
            '--min-points',
            type=int,
            default=50,
            help='Minimum points required for airdrop (default: 50)',
        )
        parser.add_argument(
            '--output',
            type=str,
            default='givebase_airdrop.json',
            help='Output file name (default: givebase_airdrop.json)',
        )
        parser.add_argument(
            '--total-supply',
            type=str,
            default='1000000',
            help='Total token supply for airdrop (default: 1,000,000)',
        )

    def handle(self, *args, **kwargs):
        min_points = kwargs['min_points']
        output_file = kwargs['output']
        total_supply = Decimal(kwargs['total_supply'])

        # Get eligible users
        eligible_users = UserProfile.objects.filter(
            total_points__gte=min_points,
            is_public_profile=True
        ).order_by('-total_points')

        airdrop_data = []
        total_allocated_tokens = Decimal('0')

        self.stdout.write(f'Generating airdrop for {eligible_users.count()} eligible users...')

        for user in eligible_users:
            # Get all token rewards for this user
            rewards = TokenReward.objects.filter(user=user)
            total_user_tokens = rewards.aggregate(Sum('amount'))['amount__sum'] or Decimal('0')
            
            # If no specific rewards, calculate from points
            if total_user_tokens == 0:
                base_tokens = Decimal(str(user.total_points)) * Decimal('0.1')
                
                # Apply multipliers based on user activity
                multiplier = Decimal('1.0')
                multiplier_reasons = []
                
                # Early adopter bonus
                if user.first_donation_date and (datetime.now().replace(tzinfo=user.first_donation_date.tzinfo) - user.first_donation_date).days > 30:
                    multiplier = Decimal('2.0')
                    multiplier_reasons.append('Early Adopter')
                
                # High activity bonus
                if user.donation_count >= 10:
                    multiplier = max(multiplier, Decimal('1.5'))
                    multiplier_reasons.append('Active Donor')
                
                # Frame interaction bonus
                frame_rewards = rewards.filter(frame_interaction=True).count()
                if frame_rewards >= 5:
                    multiplier = max(multiplier, Decimal('1.2'))
                    multiplier_reasons.append('Frame User')
                
                total_user_tokens = base_tokens * multiplier
            else:
                multiplier_reasons = ['Token Rewards Calculated']

            # Cap individual allocations (max 1% of total supply)
            max_individual = total_supply * Decimal('0.01')
            final_tokens = min(total_user_tokens, max_individual)
            
            airdrop_data.append({
                'wallet_address': user.wallet_address,
                'display_name': user.display_name or None,
                'ens_name': user.ens_name or None,
                'farcaster_username': user.farcaster_username or None,
                'total_points': user.total_points,
                'total_donated': str(user.total_donated),
                'total_received': str(user.total_received),
                'donation_count': user.donation_count,
                'token_amount': str(final_tokens),
                'multiplier_reasons': multiplier_reasons,
                'first_donation': user.first_donation_date.isoformat() if user.first_donation_date else None,
                'last_donation': user.last_donation_date.isoformat() if user.last_donation_date else None,
            })
            
            total_allocated_tokens += final_tokens

        # Generate summary
        summary = {
            'total_eligible_users': len(airdrop_data),
            'total_tokens_allocated': str(total_allocated_tokens),
            'total_supply': str(total_supply),
            'allocation_percentage': str((total_allocated_tokens / total_supply) * 100),
            'min_points_threshold': min_points,
            'generated_at': datetime.now().isoformat(),
            'platform_stats': {
                'total_users': UserProfile.objects.count(),
                'total_donated': str(UserProfile.objects.aggregate(Sum('total_donated'))['total_donated__sum'] or Decimal('0')),
                'total_points_distributed': UserProfile.objects.aggregate(Sum('total_points'))['total_points__sum'] or 0,
            }
        }

        # Save to file
        output = {
            'summary': summary,
            'airdrop_recipients': airdrop_data
        }

        with open(output_file, 'w') as f:
            json.dump(output, f, indent=2)

        # Print summary
        self.stdout.write(
            self.style.SUCCESS(f'✓ Generated airdrop data for {len(airdrop_data)} eligible users')
        )
        self.stdout.write(f'📊 Total tokens allocated: {total_allocated_tokens:,.2f} $GIVE')
        self.stdout.write(f'📈 Allocation percentage: {(total_allocated_tokens / total_supply) * 100:.2f}%')
        self.stdout.write(f'💾 Data saved to: {output_file}')
        
        # Show top 10 recipients
        self.stdout.write('\n🏆 Top 10 Recipients:')
        for i, recipient in enumerate(airdrop_data[:10]):
            name = recipient['display_name'] or recipient['farcaster_username'] or recipient['wallet_address'][:8]
            self.stdout.write(f'  {i+1}. {name} - {recipient["token_amount"]} $GIVE ({recipient["total_points"]} pts)')


# management/commands/setup_farcaster_integration.py
from django.core.management.base import BaseCommand
from django.conf import settings
import os

class Command(BaseCommand):
    help = 'Setup Farcaster integration configuration'

    def handle(self, *args, **kwargs):
        self.stdout.write('Setting up Farcaster integration...')
        
        # Create frame endpoints configuration
        frame_config = '''
# Farcaster Frame Configuration for GiveBase

## Frame URLs
- Donation Frame: https://yourapp.com/frames/donate
- Profile Frame: https://yourapp.com/frames/profile  
- Leaderboard Frame: https://yourapp.com/frames/leaderboard

## Required Environment Variables
FARCASTER_HUB_URL=https://nemes.farcaster.xyz:2281
FRAME_BASE_URL=https://yourapp.com
NEXT_PUBLIC_BASE_URL=https://yourapp.com

## Frame Metadata Template
```html
<meta property="fc:frame" content="vNext" />
<meta property="fc:frame:image" content="https://yourapp.com/frames/donate/image" />
<meta property="fc:frame:button:1" content="0.001 ETH" />
<meta property="fc:frame:button:2" content="0.01 ETH" />
<meta property="fc:frame:button:3" content="0.1 ETH" />
<meta property="fc:frame:post_url" content="https://yourapp.com/frames/donate/action" />
```

## Implementation Steps
1. Add frame endpoints to Django URLs
2. Create frame image generation
3. Add Farcaster user verification
4. Implement one-click donations
5. Add social sharing features
'''
        
        # Write configuration file
        with open('farcaster_setup.md', 'w') as f:
            f.write(frame_config)
        
        self.stdout.write(
            self.style.SUCCESS('✓ Farcaster configuration saved to farcaster_setup.md')
        )
        
        # Show next steps
        self.stdout.write('\n📋 Next Steps for Farcaster Integration:')
        self.stdout.write('1. Set up frame endpoints in your Django app')
        self.stdout.write('2. Create dynamic frame images')
        self.stdout.write('3. Add Farcaster user verification')
        self.stdout.write('4. Test donation frames')
        self.stdout.write('5. Deploy and share frames in Farcaster')
        
        self.stdout.write('\n🔗 Useful Resources:')
        self.stdout.write('- Frames.js: https://framesjs.org/')
        self.stdout.write('- Farcaster Docs: https://docs.farcaster.xyz/')
        self.stdout.write('- Frame Validator: https://warpcast.com/~/developers/frames')


# management/commands/analytics_report.py
from django.core.management.base import BaseCommand
from django.db.models import Sum, Count, Avg
from decimal import Decimal
from datetime import datetime, timedelta
from core.models import UserProfile, DonationPool, SocialDonation, PoolDonation, TokenReward

class Command(BaseCommand):
    help = 'Generate analytics report for GiveBase platform'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Number of days to analyze (default: 30)',
        )

    def handle(self, *args, **kwargs):
        days = kwargs['days']
        start_date = datetime.now() - timedelta(days=days)
        
        self.stdout.write(f'📊 GiveBase Analytics Report - Last {days} Days')
        self.stdout.write('=' * 50)
        
        # Platform Overview
        self.platform_overview()
        
        # User Analytics
        self.user_analytics(start_date)
        
        # Donation Analytics
        self.donation_analytics(start_date)
        
        # Pool Performance
        self.pool_performance()
        
        # Token Analytics
        self.token_analytics()
        
        # Growth Metrics
        self.growth_metrics(days)

    def platform_overview(self):
        total_users = UserProfile.objects.count()
        total_donated = UserProfile.objects.aggregate(Sum('total_donated'))['total_donated__sum'] or Decimal('0')
        total_points = UserProfile.objects.aggregate(Sum('total_points'))['total_points__sum'] or 0
        total_tokens = TokenReward.objects.aggregate(Sum('amount'))['amount__sum'] or Decimal('0')
        
        self.stdout.write('\n🌟 Platform Overview:')
        self.stdout.write(f'  Total Users: {total_users:,}')
        self.stdout.write(f'  Total Donated: {total_donated:.4f} ETH')
        self.stdout.write(f'  Total Points: {total_points:,}')
        self.stdout.write(f'  Total Tokens Earned: {total_tokens:.2f} $GIVE')

    def user_analytics(self, start_date):
        active_users = UserProfile.objects.filter(last_donation_date__gte=start_date).count()
        new_users = UserProfile.objects.filter(created_at__gte=start_date).count()
        public_profiles = UserProfile.objects.filter(is_public_profile=True).count()
        
        # Top donors
        top_donors = UserProfile.objects.filter(
            total_donated__gt=0
        ).order_by('-total_donated')[:5]
        
        self.stdout.write('\n👥 User Analytics:')
        self.stdout.write(f'  Active Users: {active_users:,}')
        self.stdout.write(f'  New Users: {new_users:,}')
        self.stdout.write(f'  Public Profiles: {public_profiles:,}')
        
        self.stdout.write('\n🏆 Top 5 Donors:')
        for i, donor in enumerate(top_donors, 1):
            name = donor.display_name or donor.farcaster_username or f'{donor.wallet_address[:8]}...'
            self.stdout.write(f'  {i}. {name}: {donor.total_donated:.4f} ETH ({donor.total_points:,} pts)')

    def donation_analytics(self, start_date):
        # Pool donations
        recent_pool_donations = PoolDonation.objects.filter(created_at__gte=start_date)
        pool_count = recent_pool_donations.count()
        pool_volume = recent_pool_donations.aggregate(Sum('amount'))['amount__sum'] or Decimal('0')
        
        # Social donations
        recent_social_donations = SocialDonation.objects.filter(created_at__gte=start_date)
        social_count = recent_social_donations.count()
        social_volume = recent_social_donations.aggregate(Sum('amount'))['amount__sum'] or Decimal('0')
        
        # Frame interactions
        frame_donations = recent_social_donations.filter(frame_interaction=True).count()
        
        self.stdout.write('\n💰 Donation Analytics:')
        self.stdout.write(f'  Pool Donations: {pool_count:,} ({pool_volume:.4f} ETH)')
        self.stdout.write(f'  Social Donations: {social_count:,} ({social_volume:.4f} ETH)')
        self.stdout.write(f'  Frame Donations: {frame_donations:,}')
        self.stdout.write(f'  Total Volume: {pool_volume + social_volume:.4f} ETH')

    def pool_performance(self):
        pools = DonationPool.objects.filter(is_active=True).order_by('-total_raised')
        
        self.stdout.write('\n🏦 Pool Performance:')
        for pool in pools:
            self.stdout.write(f'  {pool.emoji} {pool.name}:')
            self.stdout.write(f'    Raised: {pool.total_raised:.4f} ETH')
            self.stdout.write(f'    Donors: {pool.donor_count:,}')
            self.stdout.write(f'    Avg Donation: {(pool.total_raised / pool.donor_count):.4f} ETH' if pool.donor_count > 0 else '    Avg Donation: 0 ETH')

    def token_analytics(self):
        total_rewards = TokenReward.objects.count()
        total_tokens = TokenReward.objects.aggregate(Sum('amount'))['amount__sum'] or Decimal('0')
        claimed_tokens = TokenReward.objects.filter(is_claimed=True).aggregate(Sum('amount'))['amount__sum'] or Decimal('0')
        
        # Reward breakdown
        reward_types = TokenReward.objects.values('reason').annotate(
            count=Count('id'),
            total=Sum('amount')
        ).order_by('-total')
        
        self.stdout.write('\n🪙 Token Analytics:')
        self.stdout.write(f'  Total Rewards: {total_rewards:,}')
        self.stdout.write(f'  Total Tokens: {total_tokens:.2f} $GIVE')
        self.stdout.write(f'  Claimed Tokens: {claimed_tokens:.2f} $GIVE')
        self.stdout.write(f'  Claim Rate: {(claimed_tokens / total_tokens * 100):.1f}%' if total_tokens > 0 else '  Claim Rate: 0%')
        
        self.stdout.write('\n💎 Reward Types:')
        for reward in reward_types:
            self.stdout.write(f'  {reward["reason"]}: {reward["count"]:,} rewards ({reward["total"]:.2f} $GIVE)')

    def growth_metrics(self, days):
        # Calculate growth rates
        now = datetime.now()
        period_start = now - timedelta(days=days)
        prev_period_start = now - timedelta(days=days*2)
        
        # Current period
        current_users = UserProfile.objects.filter(created_at__gte=period_start).count()
        current_donations = (PoolDonation.objects.filter(created_at__gte=period_start).count() + 
                            SocialDonation.objects.filter(created_at__gte=period_start).count())
        
        # Previous period
        prev_users = UserProfile.objects.filter(
            created_at__gte=prev_period_start,
            created_at__lt=period_start
        ).count()
        prev_donations = (PoolDonation.objects.filter(
            created_at__gte=prev_period_start,
            created_at__lt=period_start
        ).count() + SocialDonation.objects.filter(
            created_at__gte=prev_period_start,
            created_at__lt=period_start
        ).count())
        
        # Calculate growth rates
        user_growth = ((current_users - prev_users) / prev_users * 100) if prev_users > 0 else 0
        donation_growth = ((current_donations - prev_donations) / prev_donations * 100) if prev_donations > 0 else 0
        
        self.stdout.write('\n📈 Growth Metrics:')
        self.stdout.write(f'  User Growth: {user_growth:+.1f}% ({current_users:,} vs {prev_users:,})')
        self.stdout.write(f'  Donation Growth: {donation_growth:+.1f}% ({current_donations:,} vs {prev_donations:,})')
        
        self.stdout.write('\n' + '=' * 50)
        self.stdout.write('📋 Recommendations:')
        
        if user_growth < 10:
            self.stdout.write('• Focus on user acquisition campaigns')
        if donation_growth < 20:
            self.stdout.write('• Increase donation incentives and gamification')
        if TokenReward.objects.filter(frame_interaction=True).count() < 100:
            self.stdout.write('• Promote Farcaster frame usage for viral growth')
        
        self.stdout.write('• Continue developing social features')
        self.stdout.write('• Plan token launch when metrics are strong')