# -*- coding: utf-8 -*-
from __future__ import absolute_import
import json
import logging
import os
import requests
import xml.etree.ElementTree as ET

from tika import parser

CUR_DIR = os.path.dirname(os.path.realpath(__file__))
with open(CUR_DIR + '/resources/thesis_set_list.json', 'r') as f:
    THESIS_SET_LIST = json.loads(f.read())

mets_namespace = {'mets': 'http://www.loc.gov/METS/',
                  'mods': 'http://www.loc.gov/mods/v3',
                  'oai': 'http://www.openarchives.org/OAI/2.0/'}

log = logging.getLogger(__name__)


def extract_text(pdf_file):
    parsed = parser.from_file(pdf_file)
    return parsed['content'].encode('utf-8')


def get_collection_names(set_specs):
    '''Gets and returns set of normalized collection names from set spec list.
    '''
    names = set()
    for set_spec in set_specs:
        try:
            name = THESIS_SET_LIST[set_spec]
            name = name.replace(' - ', '(').replace(' (', '(')
            split_name = name.split('(')
            names.add(split_name[0])
        except KeyError as e:
            pass
    return names


def get_pdf_url(mets):
    '''Gets and returns download URL for PDF from METS record.
    '''
    record = mets.find('.//mets:file[@MIMETYPE="application/pdf"]/',
                       mets_namespace)
    url = record.get('{http://www.w3.org/1999/xlink}href')
    return url


def get_record(dspace_oai_uri, dspace_oai_identifier, identifier,
               metadata_format):
    '''Gets metadata record for a single item in OAI-PMH repository in
    specified metadata format.
    '''
    params = {'verb': 'GetRecord',
              'identifier': dspace_oai_identifier + identifier,
              'metadataPrefix': metadata_format}
    r = requests.get(dspace_oai_uri, params=params)
    return r.text


def get_record_list(dspace_oai_uri, metadata_format, start_date=None,
                    end_date=None):
    '''Returns a list of record headers for items in OAI-PMH repository. Must
    pass in desired metadata format prefix. Can optionally pass bounding dates
    to limit harvest to.
    '''
    params = {'verb': 'ListIdentifiers', 'metadataPrefix': metadata_format}

    if start_date:
        params['from'] = start_date
    if end_date:
        params['until'] = end_date

    r = requests.get(dspace_oai_uri, params=params)
    return r.text


def is_in_fedora(handle, fedora_uri, parent_container, auth=None):
    '''Returns True if given thesis item is already in the given Fedora
    repository, otherwise returns False.
    '''
    url = fedora_uri + parent_container + '/' + handle
    r = requests.head(url, auth=auth)
    if r.status_code == 200:
        return True
    elif r.status_code == 404:
        return False
    else:
        raise requests.exceptions.HTTPError(r)


def is_thesis(sets):
    '''Returns True if any set_spec in given sets is in the
    thesis_set_spec_list, otherwise returns false.
    '''
    return any((s in THESIS_SET_LIST.keys() for s in sets))


def parse_record_list(record_xml):
    xml = ET.fromstring(record_xml)
    records = xml.findall('.//oai:header', mets_namespace)
    for record in records:
        handle = record.find('oai:identifier', mets_namespace).text\
            .replace('oai:dspace.mit.edu:', '').replace('/', '-')
        identifier = handle.replace('1721.1-', '')
        setSpecs = record.findall('oai:setSpec', mets_namespace)
        sets = [s.text for s in setSpecs]
        yield {'handle': handle, 'identifier': identifier, 'sets': sets}
