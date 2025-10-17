from django.core.management.base import BaseCommand
from decimal import Decimal
from core.models import DonationPool

class Command(BaseCommand):
    help = 'Setup initial global donation pools'

    def handle(self, *args, **options):
        self.stdout.write('🚀 Setting up global donation pools...')
        
        pools_data = [
            {
                'name': 'Emergency Fund',
                'pool_type': 'emergency',
                'description': 'Help those in urgent need worldwide',
                'wallet_address': '0x55c3aBb091D1a43C3872718b3b8B3AE8c20B592E',  # Replace with real address
                'emoji': '🚨',
                'color': 'red',
                'allocation_percentage': Decimal('0.40')
            },
            {
                'name': 'Community Projects', 
                'pool_type': 'community',
                'description': 'Fund community initiatives and infrastructure',
                'wallet_address': '0x55c3aBb091D1a43C3872718b3b8B3AE8c20B592E',  # Replace with real address
                'emoji': '🏘️',
                'color': 'green', 
                'allocation_percentage': Decimal('0.30')
            },
            {
                'name': 'Creator Support',
                'pool_type': 'creators',
                'description': 'Support content creators and innovators', 
                'wallet_address': '0x55c3aBb091D1a43C3872718b3b8B3AE8c20B592E',  # Replace with real address
                'emoji': '🎨',
                'color': 'purple',
                'allocation_percentage': Decimal('0.20')
            },
            {
                'name': 'Platform Development',
                'pool_type': 'development', 
                'description': 'Improve and maintain the GiveBase platform',
                'wallet_address': '0x55c3aBb091D1a43C3872718b3b8B3AE8c20B592E',  # Replace with real address
                'emoji': '⚡',
                'color': 'blue',
                'allocation_percentage': Decimal('0.10')
            }
        ]

        created_count = 0
        for pool_data in pools_data:
            pool, created = DonationPool.objects.get_or_create(
                pool_type=pool_data['pool_type'],
                defaults=pool_data
            )
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Created pool: {pool.emoji} {pool.name}')
                )
                created_count += 1
            else:
                self.stdout.write(
                    self.style.WARNING(f'⚠️  Pool already exists: {pool.emoji} {pool.name}')
                )

        if created_count > 0:
            self.stdout.write(
                self.style.SUCCESS(f'\n🎉 Successfully created {created_count} donation pools!')
            )
        else:
            self.stdout.write(
                self.style.WARNING('\n⚠️  All pools already exist. No new pools created.')
            )
        
        # Show current pools
        self.stdout.write('\n📊 Current active pools:')
        for pool in DonationPool.objects.filter(is_active=True):
            self.stdout.write(f'   {pool.emoji} {pool.name} - {pool.wallet_address}')