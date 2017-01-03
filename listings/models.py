from django.db import models


class Company(models.Model):
    name = models.CharField(max_length=128)
    website = models.URLField()
    description = models.TextField()
    tables = models.ManyToManyField('Table')

    attributes = models.CharField(max_length=128)

    def get_object(self):
        table_mappings = self.tables.all()
        max_day_index = max([t.day.number for t in table_mappings])
        tables = [[]] * (max_day_index + 1)

        for table in table_mappings:
            tables[table.day.number].append(table.number)

        return {
            'name': self.name,
            'website': self.website,
            'description': self.description,  # TODO: truncate description,
            'tables': tables,
            'attributes': self.attributes
        }

    def __str__(self):
        return 'Company: %s' % self.name


class Day(models.Model):
    date = models.DateField()
    number = models.IntegerField(unique=True)

    def __str__(self):
        return 'Day #%i: %s' % (self.number, self.date)


class Table(models.Model):
    day = models.ForeignKey('Day')
    number = models.IntegerField()

    def __str__(self):
        return 'Table #%i on (%s)' % (self.number, self.day)
