# -*- coding: utf-8 -*-
from __future__ import absolute_import
import datetime
import glob
import logging
import logging.config
import os
import tempfile
import xml.etree.ElementTree as ET

import click
import requests
from timeit import default_timer as timer

from foist import (create_container, initialize_custom_prefixes,
                   parse_text_encoding_errors, Thesis, update_metadata,
                   upload_thesis)

from foist.pipeline import (extract_text, get_collection_names, get_pdf_url,
                            get_record, get_record_list, is_thesis,
                            is_in_fedora, parse_record_list)

CUR_DIR = os.path.dirname(os.path.realpath(__file__))

logger = logging.getLogger(__name__)
logging.config.dictConfig({
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'full': {
            'format': '%(levelname)s: [%(asctime)s] %(message)s'
        }
    },
    'handlers': {
        'console': {
            'formatter': 'full',
            'class': 'logging.StreamHandler',
            'stream': 'ext://sys.stdout'
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'formatter': 'full',
            'filename': 'logfile.log',
            'maxBytes': 1024*1024,
            'backupCount': 3
        }
    },
    'loggers': {
        'foist': {
            'level': 'DEBUG',
            'handlers': ['console', 'file']
        }
    }
})


@click.group()
def main():
    pass


@main.command()
@click.argument('parent_container')
@click.option('-f', '--fedora-uri',
              default='http://localhost:8080/fcrepo/rest/',
              help=('Base Fedora REST URI. Default is '
                    'http://localhost:8080/fcrepo/rest/'))
@click.option('-u', '--username')
@click.option('-p', '--password')
def initialize_fedora(parent_container, fedora_uri, username, password):
    auth = (username, password) if username else None
    logger.info(fedora_uri)
    initialize_custom_prefixes(fedora_uri, auth=auth)
    logger.info('Custom prefixes initialized, dummy initialization resource '
                'deleted')
    uri = fedora_uri + parent_container
    turtle = '''
        @prefix pcdm: <http://pcdm.org/models#>

        <> a pcdm:Collection .
        '''
    try:
        r = create_container(uri, turtle=turtle, auth=auth)
        logger.info('Parent container created at location: %s' %
                    (r.headers['Location']))
    except requests.exceptions.HTTPError as e:
        logger.error(e)
    except KeyError as e:
        logger.warning('Parent container %s already exists' % parent_container)


@main.command()
@click.argument('input_directory', type=click.Path(exists=True,
                                                   file_okay=False,
                                                   resolve_path=True))
@click.argument('department')
@click.option('-o', '--output_directory', default='',
              type=click.Path(exists=False, file_okay=False,
                              resolve_path=False),
              help=('Output directory for thesis metadata files. Default is '
                    'same as input directory.'))
def process_metadata(input_directory, department, output_directory):
    '''Parse metadata for all thesis items in a directory.

    This script traverses the given INPUT_DIRECTORY of thesis files and for
    each thesis creates a turtle file of metadata statements and SPARQL update
    files for each file representation of the thesis. These get stored in the
    OUTPUT_DIRECTORY, which if not specified defaults to the INPUT_DIRECTORY.
    '''
    if output_directory == '':
        output_directory = input_directory
    error_file = glob.glob(os.path.join(input_directory, '*.tab'))[0]
    text_encoding_errors = parse_text_encoding_errors(error_file)
    dirnames = next(os.walk(os.path.join(input_directory, '.')))[1]
    department = [department]
    count = 0
    for d in dirnames:
        if not os.path.exists(os.path.join(input_directory, d, d + '.pdf')):
            logger.warning(('No PDF file for item %s. Item metadata not '
                           'processed.') % d)
            continue
        try:
            mets = ET.parse(os.path.join(input_directory, d,
                                         d + '.xml')).getroot()
        except IOError as e:
            logger.warning('No XML file for item %s. %s' % (d, e))
        thesis = Thesis(d, mets, department, text_encoding_errors.get(d))
        with open(os.path.join(output_directory, thesis.name, thesis.name +
                               '.ttl'), 'wb') as f:
            f.write(thesis.get_metadata())
        with open(os.path.join(output_directory, thesis.name, thesis.name +
                               '.pdf.ru'), 'wb') as f:
            f.write(thesis.create_file_sparql_update('.pdf').encode('utf-8'))
        with open(os.path.join(output_directory, thesis.name, thesis.name +
                               '.txt.ru'), 'wb') as f:
            f.write(thesis.create_file_sparql_update('.txt').encode('utf-8'))
        count += 1
    logger.info('TOTAL: %s theses processed in folder %s' % (str(count),
                                                             input_directory))


@main.command()
@click.argument('directory', type=click.Path(exists=True, file_okay=False,
                                             resolve_path=True))
@click.option('-f', '--fedora-uri',
              default='http://localhost:8080/fcrepo/rest/',
              help=('Base Fedora REST URI. Default is '
                    'http://localhost:8080/fcrepo/rest/'))
@click.option('-c', '--parent-collection', default='theses')
@click.option('-u', '--username')
@click.option('-p', '--password')
def batch_upload_theses(directory, fedora_uri, parent_collection, username,
                        password):
    '''Uploads all thesis items in a directory to Fedora.

    This script traverses the given DIRECTORY of thesis files exported from
    DSpace@MIT and for each thesis creates an item container, uploads files,
    adds file metadata, and adds PCDM relationship statements between the
    collection, item, and files.
    '''
    auth = (username, password) if username else None
    dirnames = next(os.walk(os.path.join(directory, '.')))[1]
    thesis_count = 0
    start = timer()

    for d in dirnames:
        pdf_file = os.path.join(directory, d, d + '.pdf')

        if os.path.isfile(os.path.join(directory, d, d + '-new.txt')):
            text_file = os.path.join(directory, d, d + '-new.txt')
        elif os.path.isfile(os.path.join(directory, d, d + '.txt')):
            text_file = os.path.join(directory, d, d + '.txt')
        else:
            text_file = None

        try:
            with open(os.path.join(directory, d, d + '.pdf.ru'), 'rb') as ps, \
                 open(os.path.join(directory, d, d + '.txt.ru'), 'rb') as ts, \
                 open(os.path.join(directory, d, d + '.ttl'), 'rb') as tu:

                pdf_sparql = ps.read()
                text_sparql = ts.read()
                turtle = tu.read()

                u = upload_thesis(fedora_uri, parent_collection, d, turtle,
                                  pdf_file, pdf_sparql, text_file,
                                  text_sparql, auth=auth)
                if u == 'Success':
                    logger.info('Thesis "%s" uploaded' % d)
                    thesis_count += 1
                elif u == 'Exists':
                    logger.warning('Item "%s" already in collection' % d)
                    thesis_count += 1
                else:
                    logger.warning('Thesis "%s" upload failed' % d)
        except FileNotFoundError as e:
            logger.warning('Missing needed RDF file for item "%s", not '
                           'uploaded to Fedora.' % d)
            continue

    end = timer()
    logger.info(end - start)
    logger.info('TOTAL: %s theses ingested.\n' % thesis_count)


@main.command()
@click.argument('directory', type=click.Path(exists=True, file_okay=False,
                                             resolve_path=True))
@click.argument('sparql')
@click.option('-f', '--fedora-uri',
              default='http://localhost:8080/fcrepo/rest/',
              help=('Base Fedora REST URI. Default is '
                    'http://localhost:8080/fcrepo/rest/'))
@click.option('-u', '--username')
@click.option('-p', '--password')
def update_metadata_for_collection(directory, sparql, fedora_uri, username,
                                   password):
    '''Updates a single metadata field for all items in a collection, using
    the provided SPARQL query
    '''
    auth = (username, password) if username else None
    items = next(os.walk(os.path.join(directory, '.')))[1]
    thesis_count = 0
    for i in items:
        try:
            uri = fedora_uri + 'theses/' + i
            update_metadata(uri, sparql, auth=auth)
            logger.debug('Thesis %s updated.' % i)
            thesis_count += 1
        except Exception as e:
            logger.warning('Thesis %s update failed' % i)
            logger.debug(e)
    logger.info('TOTAL: %s theses updated.\n' % thesis_count)


def validate_date(ctx, param, value):
    if value is not None:
        try:
            datetime.datetime.strptime(value, '%Y-%m-%d')
            return value
        except ValueError:
            raise click.BadParameter('Date must be given using YYYY-MM-DD'
                                     'format')


@main.command()
@click.argument('dspace_oai_uri')
@click.argument('dspace_oai_identifier')
@click.option('-md', '--metadata-format', default='mets')
@click.option('-sd', '--start-date', callback=validate_date,
              help='Start date for theses to ingest.')
@click.option('-ed', '--end-date', callback=validate_date,
              help='End date for theses to ingest.')
@click.option('-f', '--fedora-uri',
              default='http://localhost:8080/fcrepo/rest/',
              help=('Base Fedora REST URI. Default is '
                    'http://localhost:8080/fcrepo/rest/'))
@click.option('-u', '--username')
@click.option('-p', '--password')
def ingest_new_theses(dspace_oai_uri, dspace_oai_identifier, metadata_format,
                      start_date, end_date, fedora_uri, username, password):
    '''Adds new theses added to DSpace repository since start_date to Fedora
    repository.
    '''
    total_items_processed = 0
    not_a_thesis = 0
    added_to_fedora = 0
    already_in_fedora = 0
    no_full_text = 0

    auth = (username, password) if username else None
    items = get_record_list(dspace_oai_uri, metadata_format, start_date,
                            end_date)
    parsed_items = parse_record_list(items)
    for item in parsed_items:
        logger.debug('Checking item %s' % item['handle'])
        total_items_processed += 1
        if not is_thesis(item['sets']):
            not_a_thesis += 1
            continue
        if is_in_fedora(item['handle'], fedora_uri, 'theses', auth=auth):
            logger.info('%s already in Fedora' % item['handle'])
            already_in_fedora += 1
            continue
        logger.debug('Processing item %s' % item['handle'])
        metadata = get_record(dspace_oai_uri, dspace_oai_identifier,
                              item['identifier'], metadata_format)
        mets = ET.fromstring(metadata)
        depts = get_collection_names(item['sets'])

        thesis = Thesis(item['handle'], mets, depts)
        pdf_url = get_pdf_url(mets)

        with tempfile.NamedTemporaryFile() as pdf_file:
            r = requests.get(pdf_url, stream=True)
            r.raise_for_status()
            for chunk in r.iter_content(1024):
                pdf_file.write(chunk)
            pdf_file.flush()
            pdf_sparql = thesis.create_file_sparql_update('.pdf')

            try:
                text_string = extract_text(pdf_file.name)
                text_sparql = thesis.create_file_sparql_update('.txt')
            except Exception as e:
                logger.debug(e)
                text_string = None
                text_sparql = None
                thesis.no_full_text = 'True'
                no_full_text += 1

            turtle = thesis.get_metadata()
            u = upload_thesis(fedora_uri, 'theses', item['handle'], turtle,
                              pdf_file.name, pdf_sparql,
                              text_content=text_string,
                              text_sparql=text_sparql, auth=auth)
            if u == 'Success':
                logger.info('Thesis "%s" uploaded' % item['handle'])
                added_to_fedora += 1
            elif u == 'Exists':
                logger.warning('Item "%s" already in collection' %
                               item['handle'])
                already_in_fedora += 1
            else:
                logger.warning('Thesis "%s" upload failed' % item['handle'])

    logger.info('\n%s total new items processed\n%s non-thesis items\n%s '
                'theses added to Fedora\n%s theses already in Fedora\n%s '
                'theses with no full text' %
                (total_items_processed, not_a_thesis, added_to_fedora,
                 already_in_fedora, no_full_text))


if __name__ == '__main__':
    main()
