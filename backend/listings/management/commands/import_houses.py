from django.core.management.base import BaseCommand
from listings.models import House
import csv
from pathlib import Path
from django.conf import settings


class Command(BaseCommand):
    help = 'Import houses from CSV file'

    def add_arguments(self, parser):
        parser.add_argument('--csv', default=str(settings.BASE_DIR / 'data' / 'processed_data_with_images_cleaned.csv'))
        parser.add_argument('--commit', action='store_true', help='Commit changes to database')

    def handle(self, *args, **options):
        csv_path = Path(options['csv'])
        if not csv_path.exists():
            self.stdout.write(self.style.ERROR(f'CSV file not found: {csv_path}'))
            return

        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            count = 0
            for row in reader:
                if not options['commit']:
                    self.stdout.write(f'Dry run: Would import {row["title"]}')
                    count += 1
                    continue

                house, created = House.objects.get_or_create(
                    link=row['link'],
                    defaults={
                        'title': row['title'],
                        'city': row['city'],
                        'district': row['district'],
                        'community': row.get('community', ''),
                        'address': row['address'],
                        'total_price': float(row['total_price']) if row['total_price'] else 0,
                        'unit_price': float(row['unit_price']) if row['unit_price'] else None,
                        'area': float(row['area']) if row['area'] else 0,
                        'rooms': int(row['rooms']) if row['rooms'] else 0,
                        'halls': int(row['halls']) if row['halls'] else 0,
                        'orientation': row['orientation'],
                        'floor': row['floor'],
                        'decorate': row['decorate'],
                        'building_type': row['building_type'],
                        'followers': int(row['followers']) if row['followers'] else 0,
                        'cover': row['cover'],
                        'tags': row['tags'],
                        'longitude': float(row['longitude']) if row['longitude'] else None,
                        'latitude': float(row['latitude']) if row['latitude'] else None,
                    }
                )
                if created:
                    count += 1
                    self.stdout.write(f'Imported: {house.title}')
                else:
                    self.stdout.write(f'Skipped (exists): {house.title}')

        self.stdout.write(self.style.SUCCESS(f'Processed {count} houses'))