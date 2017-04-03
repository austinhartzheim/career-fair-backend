import argparse
import json

import tqdm
from django.core.management.base import BaseCommand
from listings.models import Company


class Command(BaseCommand):
    help = 'Export company information to a JSON file'

    def add_arguments(self, parser):
        parser.add_argument('outfile', type=argparse.FileType('w'))
        parser.add_argument('--compact', '-c', action='store_true',
                            help='Do not indent the JSON output')

    def handle(self, **options):
        companies = {}

        # Load all companies
        for company in tqdm.tqdm(Company.objects.all()):
            companies[company.pk] = company.get_object()

        # Set up JSON export
        json_kwargs = {
            'indent': 2
        }
        if options['compact']:
            json_kwargs['indent'] = 0

        # Dump JSON to file
        json.dump(companies, options['outfile'], **json_kwargs)
