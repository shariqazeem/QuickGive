# management/commands/add_sample_recipients.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from decimal import Decimal
from core.models import Recipient

class Command(BaseCommand):
    help = 'Add sample recipients for testing'

    def handle(self, *args, **kwargs):
        recipients = [
            {
                'name': 'Sarah Johnson',
                'category': 'medical',
                'description': 'Single mother of two facing urgent medical bills after emergency surgery. Unable to work during recovery and needs help with treatment costs.',
                'wallet_address': '0x55c3aBb091D1a43C3872718b3b8B3AE8c20B592E',  # Sample address
                'goal_amount': Decimal('0.5'),
                'verification_proof': 'Hospital verification #MED2024-001',
                'location': 'Chicago, IL',
                'urgency_level': 5,
            },
            {
                'name': 'Michael Chen',
                'category': 'student',
                'description': 'Computer Science student at risk of dropping out due to financial hardship. Needs funds for laptop and next semester tuition.',
                'wallet_address': '0x55c3aBb091D1a43C3872718b3b8B3AE8c20B592E',  # Sample address
                'goal_amount': Decimal('0.3'),
                'verification_proof': 'University verification #STU2024-042',
                'location': 'Austin, TX',
                'urgency_level': 4,
            },
            {
                'name': 'James Wilson',
                'category': 'homeless',
                'description': 'Veteran experiencing homelessness, working with local shelter to secure permanent housing. Needs deposit and first month rent.',
                'wallet_address': '0x55c3aBb091D1a43C3872718b3b8B3AE8c20B592E',  # Sample address
                'goal_amount': Decimal('0.4'),
                'verification_proof': 'Shelter verification #HOM2024-017',
                'location': 'Seattle, WA',
                'urgency_level': 4,
            },
            {
                'name': 'Maria Garcia',
                'category': 'medical',
                'description': 'Elderly woman requiring critical medication not covered by insurance. Monthly prescription costs threatening her health.',
                'wallet_address': '0x55c3aBb091D1a43C3872718b3b8B3AE8c20B592E',  # Sample address
                'goal_amount': Decimal('0.2'),
                'verification_proof': 'Pharmacy verification #MED2024-089',
                'location': 'Miami, FL',
                'urgency_level': 5,
            },
            {
                'name': 'David Thompson',
                'category': 'homeless',
                'description': 'Recently lost job and home due to company closure. Living in car with family, needs immediate assistance for temporary shelter.',
                'wallet_address': '0x55c3aBb091D1a43C3872718b3b8B3AE8c20B592E',  # Sample address
                'goal_amount': Decimal('0.35'),
                'verification_proof': 'Social services verification #HOM2024-033',
                'location': 'Detroit, MI',
                'urgency_level': 5,
            },
        ]

        for recipient_data in recipients:
            recipient, created = Recipient.objects.get_or_create(
                wallet_address=recipient_data['wallet_address'],
                defaults={
                    **recipient_data,
                    'is_verified': True,
                    'verification_date': timezone.now(),
                    'verified_by': 'GiveBase Partner Network',
                }
            )
            
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Created recipient: {recipient.name}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Recipient already exists: {recipient.name}')
                )

        self.stdout.write(
            self.style.SUCCESS(f'Successfully processed {len(recipients)} recipients')
        )