# this set of tests calls a series of endpoints that this API is meant to expose and tests them for content
import requests
import re
import pytest

SYSTEM_URI = 'http://13.236.122.60/asgs'
HEADERS_TTL = {'Accept': 'text/turtle'}


def valid_endpoint_content(uri, headers, pattern):
    # dereference the URI
    r = requests.get(uri, headers=headers)

    # parse the content looking for the thing specified in REGEX
    if re.search(pattern, r.content.decode('utf-8'), re.MULTILINE):
        return True
    else:
        return False


def test_asgs_landing_page_html():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/',
        None,
        r'<h1>ASGS Registers<\/h1>'
    ), 'ASGS landing page html failed'


@pytest.mark.skip('ASGS landing page rdf turtle file extension not yet implemented')
def test_asgs_landing_page_rdf_turtle_file_extension():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/index.ttl',
        None,
        None #TODO
    ), 'ASGS landing page rdf turtle file extension failed'


@pytest.mark.skip('ASGS landing page rdf turtle qsa not yet implemented')
def test_asgs_landing_page_rdf_turtle_file_extension():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/_format=text/turtle',
        None,
        None #TODO
    ), 'ASGS landing page rdf turtle qsa failed'


if __name__ == '__main__':
    pass
