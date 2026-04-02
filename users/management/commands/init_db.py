"""
Initial setup script to populate the database with roles and sample data.
Run this once after migrations.
"""

from django.core.management.base import BaseCommand
from users.models import Role, User
from records.models import FinancialRecord
from dashboard.models import DashboardCache
from datetime import datetime, timedelta
from decimal import Decimal


class Command(BaseCommand):
    help = 'Initialize database with roles and sample data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--no-sample',
            action='store_true',
            help='Skip sample data creation',
        )

    def handle(self, *args, **options):
        self.stdout.write('Starting database initialization...')

        # Create roles
        self.create_roles()

        # Create sample users
        self.create_sample_users()

        # Create sample financial records
        if not options['no_sample']:
            self.create_sample_records()

        self.stdout.write(
            self.style.SUCCESS('✓ Database initialization complete!')
        )

    def create_roles(self):
        """Create the three roles."""
        roles_data = [
            {
                'name': 'viewer',
                'description': 'Can only view dashboard data and their own records'
            },
            {
                'name': 'analyst',
                'description': 'Can view records, access insights, and create records'
            },
            {
                'name': 'admin',
                'description': 'Full management access - can create, update, delete records and manage users'
            },
        ]

        for role_data in roles_data:
            role, created = Role.objects.get_or_create(
                name=role_data['name'],
                defaults={'description': role_data['description']}
            )
            if created:
                self.stdout.write(f'  ✓ Created role: {role.name}')
            else:
                self.stdout.write(f'  • Role already exists: {role.name}')

    def create_sample_users(self):
        """Create sample users with different roles."""
        role_viewer = Role.objects.get(name='viewer')
        role_analyst = Role.objects.get(name='analyst')
        role_admin = Role.objects.get(name='admin')

        users_data = [
            {
                'username': 'admin_user',
                'email': 'admin@finance.local',
                'first_name': 'Admin',
                'last_name': 'User',
                'role': role_admin,
                'status': 'active'
            },
            {
                'username': 'analyst_user',
                'email': 'analyst@finance.local',
                'first_name': 'Analyst',
                'last_name': 'User',
                'role': role_analyst,
                'status': 'active'
            },
            {
                'username': 'viewer_user',
                'email': 'viewer@finance.local',
                'first_name': 'Viewer',
                'last_name': 'User',
                'role': role_viewer,
                'status': 'active'
            },
        ]

        for user_data in users_data:
            user, created = User.objects.get_or_create(
                username=user_data['username'],
                defaults={
                    'email': user_data['email'],
                    'first_name': user_data['first_name'],
                    'last_name': user_data['last_name'],
                    'role': user_data['role'],
                    'status': user_data['status'],
                }
            )
            if created:
                self.stdout.write(
                    f'  ✓ Created user: {user.username} ({user.role.name})')
            else:
                self.stdout.write(f'  • User already exists: {user.username}')

    def create_sample_records(self):
        """Create sample financial records."""
        analyst = User.objects.get(username='analyst_user')
        viewer = User.objects.get(username='viewer_user')

        today = datetime.now().date()

        # Sample income records
        income_samples = [
            {'amount': 5000, 'category': 'salary', 'days_ago': 0},
            {'amount': 500, 'category': 'bonus', 'days_ago': 5},
            {'amount': 1000, 'category': 'investment', 'days_ago': 10},
            {'amount': 2000, 'category': 'salary', 'days_ago': 30},
            {'amount': 300, 'category': 'other', 'days_ago': 15},
        ]

        # Sample expense records
        expense_samples = [
            {'amount': 50, 'category': 'food', 'days_ago': 0},
            {'amount': 200, 'category': 'transportation', 'days_ago': 2},
            {'amount': 100, 'category': 'utilities', 'days_ago': 5},
            {'amount': 75, 'category': 'entertainment', 'days_ago': 7},
            {'amount': 120, 'category': 'healthcare', 'days_ago': 10},
            {'amount': 300, 'category': 'education', 'days_ago': 15},
            {'amount': 30, 'category': 'food', 'days_ago': 18},
            {'amount': 150, 'category': 'utilities', 'days_ago': 25},
        ]

        records_created = 0

        for sample in income_samples:
            FinancialRecord.objects.create(
                user=analyst,
                amount=Decimal(str(sample['amount'])),
                transaction_type='income',
                category=sample['category'],
                date=today - timedelta(days=sample['days_ago']),
                description=f'Sample income record'
            )
            records_created += 1

        for sample in expense_samples:
            FinancialRecord.objects.create(
                user=analyst,
                amount=Decimal(str(sample['amount'])),
                transaction_type='expense',
                category=sample['category'],
                date=today - timedelta(days=sample['days_ago']),
                description=f'Sample expense record'
            )
            records_created += 1

        # Create a few records for viewer
        FinancialRecord.objects.create(
            user=viewer,
            amount=Decimal('3000'),
            transaction_type='income',
            category='salary',
            date=today,
            description='Monthly salary'
        )
        records_created += 1

        FinancialRecord.objects.create(
            user=viewer,
            amount=Decimal('500'),
            transaction_type='expense',
            category='food',
            date=today - timedelta(days=5),
            description='Weekly groceries'
        )
        records_created += 1

        self.stdout.write(
            f'  ✓ Created {records_created} sample financial records')

        # Refresh dashboard caches
        DashboardCache.refresh_cache(analyst)
        DashboardCache.refresh_cache(viewer)
        self.stdout.write('  ✓ Refreshed dashboard caches')
