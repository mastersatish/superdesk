import datetime
from ..etree import etree
from superdesk.io import Parser


class NewsMLOneParser(Parser):
    """NewsMl xml 1.2 parser"""

    def parse_message(self, tree):
        """Parse NewsMessage."""
        item = {}
        self.root = tree

        parsed_el = tree.find('NewsItem/NewsComponent/AdministrativeMetadata/Source')
        if parsed_el is not None:
            item['original_source'] = parsed_el.find('Party').get('FormalName', '')

        parsed_el = tree.find('NewsEnvelope/TransmissionId')
        if parsed_el is not None:
            item['ingest_provider_sequence'] = parsed_el.text

        item['NewsIdentifier'] = self.parse_elements(tree.find('NewsItem/Identification/NewsIdentifier'))
        item['NewsManagement'] = self.parse_elements(tree.find('NewsItem/NewsManagement'))
        item['NewsLines'] = self.parse_elements(tree.find('NewsItem/NewsComponent/NewsLines'))
        item['DescriptiveMetadata'] = self.parse_multivalued_elements(
            tree.find('NewsItem/NewsComponent/DescriptiveMetadata'))
        item['located'] = self.parse_attributes_as_dictionary(
            tree.find('NewsItem/NewsComponent/DescriptiveMetadata/Location'))

        keywords = tree.findall('NewsItem/NewsComponent/DescriptiveMetadata/Property')
        item['keywords'] = self.parse_attribute_values(keywords, 'Keyword')

        subjects = tree.findall('NewsItem/NewsComponent/DescriptiveMetadata/SubjectCode/SubjectDetail')
        subjects += tree.findall('NewsItem/NewsComponent/DescriptiveMetadata/SubjectCode/SubjectMatter')
        subjects += tree.findall('NewsItem/NewsComponent/DescriptiveMetadata/SubjectCode/Subject')

        item['Subjects'] = self.parse_attributes_as_dictionary(subjects)
        item['ContentItem'] = self.parse_attributes_as_dictionary(
            tree.find('NewsItem/NewsComponent/ContentItem'))
        # item['Content'] = etree.tostring(
        # tree.find('NewsItem/NewsComponent/ContentItem/DataContent/nitf/body/body.content'))
        item['body_html'] = etree.tostring(
            tree.find('NewsItem/NewsComponent/ContentItem/DataContent/nitf/body/body.content'))

        return self.populate_fields(item)

    def parse_elements(self, tree):
        items = {}
        for item in tree:
            if item.text is None:
                # read the attribute for the item
                if item.tag != 'HeadLine':
                    items[item.tag] = item.attrib
            else:
                # read the value for the item
                items[item.tag] = item.text
        return items

    def parse_multivalued_elements(self, tree):
        items = {}
        for item in tree:
            if item.tag not in items:
                items[item.tag] = [item.text]
            else:
                items[item.tag].append(item.text)

        return items

    def parse_attributes_as_dictionary(self, items):
        attributes = [item.attrib for item in items]
        return attributes

    def parse_attribute_values(self, items, attribute):
        attributes = []
        for item in items:
            if item.attrib['FormalName'] == attribute:
                attributes.append(item.attrib['Value'])
        return attributes

    def datetime(self, string):
        return datetime.datetime.strptime(string, '%Y%m%dT%H%M%S+0000')

    def populate_fields(self, item):
        item['guid'] = item['NewsIdentifier']['PublicIdentifier']
        item['type'] = 'text'
        item['urgency'] = item['NewsManagement']['Urgency']['FormalName']
        item['version'] = item['NewsIdentifier']['RevisionId']
        item['versioncreated'] = self.datetime(item['NewsManagement']['ThisRevisionCreated'])
        item['firstcreated'] = self.datetime(item['NewsManagement']['FirstCreated'])
        item['pubstatus'] = item['NewsManagement']['Status']['FormalName']
        item['subject'] = item['Subjects']

        if 'HeadLine' in item['NewsLines']:
            item['headline'] = item['NewsLines']['HeadLine']
        elif item['NewsManagement']['NewsItemType']['FormalName'] == 'Alert':
            item['headline'] = 'Alert'

        return item
