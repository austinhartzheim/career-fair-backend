import unittest
from listings.models import *


class TestListingsModelsCompany(unittest.TestCase):
    '''
    Test the listings.models.Company class.
    '''
    def test_get_object_description_truncation(self):
        '''
        Test that the Company class properly truncates descriptions.
        '''
        import datetime
        d = Day()
        d.date = datetime.datetime(2016, 1, 3)
        d.number = 1
        d.save()

        t = Table()
        t.day = d
        t.number = 0
        t.save()

        c = Company()
        c.name = 'CompanyX',
        c.website = 'http://example.com/'
        c.description = 'A' * 141
        c.attributes = '\x00\x00\x00\x00'
        c.save()

        c.tables.add(t)
        c.save()

        obj = c.get_object()
        self.assertEquals(obj['description'], 'A'*140 + '...')
