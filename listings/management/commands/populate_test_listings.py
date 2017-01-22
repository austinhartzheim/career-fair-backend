import base64
import datetime
import math
import random

from django.core.management.base import BaseCommand
from listings.models import Company, Day, Table


class Command(BaseCommand):
    help = 'Populate the database with test listings.'

    def add_arguments(self, parser):
        parser.add_argument('companies', type=int, default=25,
                            help='The number of companies to create')
        parser.add_argument('days', type=int, default=2,
                            help='The number of days to create data for')

    def handle(self, **options):
        companies_per_day = options['companies'] / options['days']

        days = []
        for i in range(0, options['days']):
            day = Day()
            day.date = datetime.datetime.utcnow()
            day.date += datetime.timedelta(i)
            day.number = i
            day.save()
            days.append(day)

        company_count = 0
        for d in range(0, options['days']):
            if d == 0:
                for c in range(0, math.ceil(companies_per_day)):
                    self._create_random_company(company_count,
                                                days[d],
                                                company_count)
                    company_count += 1

            else:
                for c in range(0, math.floor(companies_per_day)):
                    self._create_random_company(company_count,
                                                days[d],
                                                company_count)
                company_count += 1

        for i in range(0, options['companies']):
            self._create_random_company(company_count,
                                        days[d],
                                        company_count)
            company_count += 1

    def _create_random_company(self, number, day, table_number):
        def gen_random_attributes(length):
            attributes = bytes()
            for _ in range(length):
                attributes += bytes(chr(random.randint(0, 255)),
                                    'raw_unicode_escape')

            return base64.encodestring(attributes)

        company = Company()
        company.name = 'Company %i' % number
        company.website = 'https://%i.example.com/' % number
        company.description = 'We are company #%i' % number
        company.attributes = gen_random_attributes(20)
        company.save()

        table = Table()
        table.day = day
        table.number = table_number
        table.save()

        company.tables.add(table)
        company.save()

        return company
