import argparse
import datetime
import json
import csv
import re

import tqdm
import rigidity
import markdown
from libs import bitpack
from django.core.management.base import BaseCommand

from listings import models

EVENT_DATE = datetime.datetime(2017, 4, 7)

COL_EXHIBIT_NAME = 0
COL_DESCRIPTION = 5
COL_WEBSITE = 6
COL_STUDENT_EXHIBIT = 7
COL_COMPETITION = 8
COL_SPEAKER = 9
COL_INDUSTRY = 10
COL_OUTDOORS = 11

BP_STUDENT_EXHIBIT = 1
BP_COMPETITION = 2
BP_SPEAKER = 4
BP_INDUSTRY = 8


class FixDescription(rigidity.rules.Rule):
    def apply(self, value):
        value = value.replace('\u2013', '-')  # em-dash
        value = value.replace('\u2014', '-')  # em-dash
        value = value.replace('\xae', '')  # registered
        value = value.replace('\u2122', '')  # trademark
        value = value.replace('\u201c', '"')  # left-angle-quote
        value = value.replace('\u201d', '"')  # right-angle-quote
        value = value.replace('\t', '')  # tabs
        value = value.replace('  ', '')  # adjacent spaces
        value = value.replace('\u2019', '\'')  # angle-appos

        if 'www.' in value or 'http://' in value or 'https://' in value:
            raise ValueError('URL in description')

        return value


class Markdown(rigidity.rules.Rule):
    def apply(self, value):
        return markdown.markdown(value)


class UrlValidator(rigidity.rules.Rule):
    def apply(self, value):
        if value is None or value == '':
            return ''

        if not (value.startswith('http://') or value.startswith('https://')):
            raise ValueError('URL does not start with http:// or https://')
        if (value.find('http:', 1) != -1) or (value.find('https:', 1) != -1):
            raise ValueError('URL contains an extra http: or https:')

        # Check for a TLD, using a short, but validated list of known TLDs
        if not re.search('\.(com|org|net|edu|jobs|us|gov|mil|co)', value):
            raise ValueError('URL did not have a recognized TLD')

        return value


class Command(BaseCommand):
    help = 'Import a CSV file in the Engineering Expo format.'

    def add_arguments(self, parser):
        parser.add_argument('infile', type=argparse.FileType('r'))

    def handle(self, **options):
        # TODO: make code more robust: check if the day exists already from
        #   a previous run.
        day = models.Day()
        day.date = EVENT_DATE
        day.number = 0
        day.save()
        
        reader = csv.reader(options['infile'])
        rules = [
            [rigidity.rules.Strip()],  # Exhibit name
            [rigidity.rules.Strip()],  # Speaker
            [rigidity.rules.Strip()],  # Time
            [rigidity.rules.Strip()],  # Org
            [rigidity.rules.Strip(),
             rigidity.rules.Unique()],  # Booth ID
            [rigidity.rules.Strip(),  # Description
             FixDescription(),
             Markdown()],
            [rigidity.rules.NoneToEmptyString(),
             rigidity.rules.Strip(),
             UrlValidator()],  # Website
            [rigidity.rules.Boolean(allow_null=True)],
            [rigidity.rules.Boolean(allow_null=True)],
            [rigidity.rules.Boolean(allow_null=True)],
            [rigidity.rules.Boolean(allow_null=True)],
            [rigidity.rules.Boolean(allow_null=True)]
        ]
        r = rigidity.Rigidity(reader, rules,
                              display=rigidity.Rigidity.DISPLAY_SIMPLE)

        r.skip()  # Skip header
        table_number = 0
        for row in tqdm.tqdm(r):
            # Calculate attributes for company
            attributes = bitpack.BitPack(b'\x00', False)
            if row[COL_STUDENT_EXHIBIT]:
                attributes = attributes.bit_or(
                    bitpack.BitPack(chr(BP_STUDENT_EXHIBIT), False))
            if row[COL_COMPETITION]:
                attributes = attributes.bit_or(
                    bitpack.BitPack(chr(BP_COMPETITION), False))
            if row[COL_SPEAKER]:
                attributes = attributes.bit_or(
                    bitpack.BitPack(chr(BP_SPEAKER), False))
            if row[COL_INDUSTRY]:
                attributes = attributes.bit_or(
                    bitpack.BitPack(chr(BP_INDUSTRY), False))

            # Create Table object
            table = models.Table()
            table.day = day
            table.number = table_number
            table_number += 1
            table.save()

            # Create Company object
            company = models.Company()
            company.name = row[COL_EXHIBIT_NAME]
            company.website = row[COL_WEBSITE]
            company.description = row[COL_DESCRIPTION]
            company.attributes = attributes.base64()
            company.save()
            company.tables.add(table)
            company.save()
