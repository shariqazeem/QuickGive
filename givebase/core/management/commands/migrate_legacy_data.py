from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from decimal import Decimal
from core.models import (
    Donation, Recipient, DonorProfile,  # Legacy models
    UserProfile, DonationPool, PoolDonation, TokenReward  # New models
)

class Command(BaseCommand):
    help = 'Migrate legacy donation data to new global system'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be migrated without making changes',
        )

    def handle(self, *args, **kwargs):
        dry_run = kwargs['dry_run']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))
        
        # Migrate DonorProfile to UserProfile
        self.migrate_donor_profiles(dry_run)
        
        # Migrate Recipients to appropriate pools
        self.migrate_recipients_to_pools(dry_run)
        
        # Migrate Donations to PoolDonations
        self.migrate_donations(dry_run)
        
        # Create token rewards for existing users
        self.create_token_rewards(dry_run)
        
        if not dry_run:
            self.stdout.write(
                self.style.SUCCESS('🎉 Migration completed successfully!')
            )
        else:
            self.stdout.write(
                self.style.WARNING('Dry run completed. Use --no-dry-run to apply changes.')
            )

    def migrate_donor_profiles(self, dry_run):
        """Migrate DonorProfile to UserProfile"""
        legacy_profiles = DonorProfile.objects.filter(migrated_to_user_profile=False)
        
        self.stdout.write(f'Migrating {legacy_profiles.count()} donor profiles...')
        
        for legacy_profile in legacy_profiles:
            if not dry_run:
                with transaction.atomic():
                    user_profile, created = UserProfile.objects.get_or_create(
                        wallet_address=legacy_profile.wallet_address,
                        defaults={
                            'ens_name': legacy_profile.ens_name,
                            'total_donated': legacy_profile.total_donated,
                            'total_points': legacy_profile.total_points,
                            'donation_count': legacy_profile.donation_count,
                            'is_public_profile': legacy_profile.is_public,
                            'first_donation_date': legacy_profile.first_donation_date,
                            'last_donation_date': legacy_profile.last_donation_date,
                            'created_at': legacy_profile.created_at,
                        }
                    )
                    
                    if created:
                        self.stdout.write(f'  ✓ Migrated: {legacy_profile.wallet_address[:8]}...')
                    
                    # Mark as migrated
                    legacy_profile.migrated_to_user_profile = True
                    legacy_profile.save()
            else:
                self.stdout.write(f'  Would migrate: {legacy_profile.wallet_address[:8]}...')

    def migrate_recipients_to_pools(self, dry_run):
        """Map legacy recipients to appropriate pools"""
        recipients = Recipient.objects.filter(is_verified=True)
        
        # Get pools
        emergency_pool = DonationPool.objects.filter(pool_type='emergency').first()
        community_pool = DonationPool.objects.filter(pool_type='community').first()
        
        category_mapping = {
            'medical': emergency_pool,
            'homeless': emergency_pool,
            'student': community_pool,
        }
        
        self.stdout.write(f'Mapping {recipients.count()} recipients to pools...')
        
        for recipient in recipients:
            target_pool = category_mapping.get(recipient.category, emergency_pool)
            
            if not dry_run and target_pool:
                # Add recipient's raised amount to pool
                target_pool.total_raised += recipient.raised_amount
                target_pool.save()
                
                self.stdout.write(f'  ✓ {recipient.name} → {target_pool.name} ({recipient.raised_amount} ETH)')
            else:
                pool_name = target_pool.name if target_pool else 'No pool'
                self.stdout.write(f'  Would map: {recipient.name} → {pool_name}')

    def migrate_donations(self, dry_run):
        """Migrate legacy donations to pool donations"""
        legacy_donations = Donation.objects.filter(migrated_to_pool=False)
        
        # Get pools for mapping
        emergency_pool = DonationPool.objects.filter(pool_type='emergency').first()
        community_pool = DonationPool.objects.filter(pool_type='community').first()
        
        self.stdout.write(f'Migrating {legacy_donations.count()} donations to pools...')
        
        for donation in legacy_donations:
            # Determine target pool based on recipient category
            target_pool = emergency_pool  # Default
            
            if donation.recipient:
                if donation.recipient.category in ['medical', 'homeless']:
                    target_pool = emergency_pool
                elif donation.recipient.category == 'student':
                    target_pool = community_pool
            
            if not dry_run and target_pool:
                with transaction.atomic():
                    # Create pool donation
                    pool_donation = PoolDonation.objects.create(
                        donor_address=donation.donor_address,
                        pool=target_pool,
                        amount=donation.amount,
                        tx_hash=donation.tx_hash + '_migrated',  # Avoid duplicate hash
                        block_number=donation.block_number,
                        points_earned=donation.points_earned,
                    )
                    
                    # Update pool donor count
                    target_pool.donor_count = target_pool.donations.values('donor_address').distinct().count()
                    target_pool.save()
                    
                    # Mark as migrated
                    donation.migrated_to_pool = True
                    donation.save()
                    
                    self.stdout.write(f'  ✓ {donation.amount} ETH → {target_pool.name}')
            else:
                pool_name = target_pool.name if target_pool else 'No pool'
                self.stdout.write(f'  Would migrate: {donation.amount} ETH → {pool_name}')

    def create_token_rewards(self, dry_run):
        """Create token rewards for existing users"""
        user_profiles = UserProfile.objects.filter(total_points__gt=0)
        
        self.stdout.write(f'Creating token rewards for {user_profiles.count()} users...')
        
        for profile in user_profiles:
            if not dry_run:
                # Calculate base token reward (1 point = 0.1 tokens)
                base_tokens = Decimal(str(profile.total_points)) * Decimal('0.1')
                
                # Early adopter bonus (2x if first donation was > 7 days ago)
                multiplier = Decimal('2.0') if (profile.first_donation_date and 
                                               profile.first_donation_date < timezone.now() - timezone.timedelta(days=7)) else Decimal('1.0')
                
                final_amount = base_tokens * multiplier
                
                # Create token reward
                TokenReward.objects.get_or_create(
                    user=profile,
                    reason='migration_bonus',
                    defaults={
                        'amount': final_amount,
                        'multiplier': multiplier,
                    }
                )
                
                # Update profile tokens earned
                profile.tokens_earned = final_amount
                profile.save()
                
                self.stdout.write(f'  ✓ {profile.wallet_address[:8]}... → {final_amount} $GIVE tokens')
            else:
                base_tokens = Decimal(str(profile.total_points)) * Decimal('0.1')
                self.stdout.write(f'  Would create: {profile.wallet_address[:8]}... → ~{base_tokens} tokens')
