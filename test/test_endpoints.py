# this set of tests calls a series of endpoints that this API is meant to expose and tests them for content
import requests
import re
import pytest
import pprint as pp

SYSTEM_URI = 'http://13.236.122.60/asgs'
HEADERS_TTL = {'Accept': 'text/turtle'}
HEADERS_HTML = {'Accept': 'text/html'}


def valid_endpoint_content(uri, headers, pattern, print_out=False, allow_redirects=True):
    # dereference the URI
    r = requests.get(uri, headers=headers, allow_redirects=allow_redirects)
    if print_out:
        pp.pprint(r.content)
    # parse the content looking for the thing specified in REGEX
    if re.search(pattern, r.content.decode('utf-8'), re.MULTILINE):
        return True
    else:
        pp.pprint(r.content)
        return False


def test_asgs_landing_page_html():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/',
        None,
        r'<h1>ASGS Registers<\/h1>'
    ), 'ASGS landing page html failed'


def test_asgs_reg_route_html():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/reg/?_format=text/html',
        None,
        r'<li><a href="http:\/\/test\.linked\.data\.gov\.au\/dataset\/asgs\/sa2\/">Register of ASGS SA2 regions<\/a><\/li>'
    ), 'ASGS reg route html failed'


@pytest.mark.skip('ASGS reg route rdf turtle file extension not yet implemented')
def test_asgs_reg_route_rdf_turtle_file_extension():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/reg/index.ttl',
        None,
        r'rdfs:label "Register of ASGS SA3 regions"\^\^xsd:string ;'
    ), 'ASGS reg route rdf turtle file extension failed'


def test_asgs_reg_route_rdf_turtle_qsa():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/reg/?_format=text/turtle',
        None,
        r'rdfs:label "Register of ASGS SA3 regions"\^\^xsd:string ;'
    ), 'ASGS reg route rdf turtle qsa failed'


def test_asgs_reg_route_rdf_turtle_accept_header():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/reg/',
        HEADERS_TTL,
        r'rdfs:label "Register of ASGS SA3 regions"\^\^xsd:string ;'
    ), 'ASGS reg route rdf turtle accept header failed'


def test_asgs_reg_route_alternates_view_html():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/reg/?_view=alternates',
        None,
        r'<a href="\/asgs\/sa2\/">SA2s<\/a> \|'
    ), 'ASGS reg route alternates view html failed'


def test_asgs_reg_route_alternates_view_rdf_turtle_qsa():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/reg/?_view=alternates&_format=text/turtle',
        None,
        r'rdfs:label "Alternates"\^\^xsd:string ;'
    ), 'ASGS reg route alternates view rdf turtle qsa failed'


def test_asgs_australia_register_html():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/australia/',
        None,
        r'<li><a href=\"\/asgs\/australia\/036\">Australia \(036\)<\/a><\/li><\/ul>'
    ), 'ASGS Australia Register html failed'


@pytest.mark.skip('ASGS Australia Register rdf turtle file extension not yet implemented')
def test_asgs_australia_register_rdf_turtle_file_extension():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/australia/index.ttl',
        None,
        None #TODO
    ), 'ASGS Australia Register rdf turtle file extension failed'


def test_asgs_australia_register_rdf_turtle_qsa():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/australia/?_format=text/turtle',
        None,
        r'rdfs:label "Australia \(036\)"\^\^xsd:string ;'
    ), 'ASGS Australia Register rdf turtle qsa failed'


def test_asgs_australia_register_rdf_turtle_accept_header():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/australia/',
        HEADERS_TTL,
        r'rdfs:label "Australia \(036\)"\^\^xsd:string ;'
    ), 'ASGS Australia Register rdf turtle accept header failed'


def test_asgs_australia_register_alternates_view_html():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/australia/?_view=alternates&_format=text/html',
        None,
        r'<a href="\/asgs\/sa2\/">SA2s<\/a> \|'
    ), 'ASGS Australia Register alternates view html failed'


def test_asgs_australia_register_alternates_view_rdf_turtle_qsa():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/australia/?_view=alternates&_format=text/turtle',
        None,
        r'rdfs:comment "The view that lists all other views"\^\^xsd:string ;'
    ), 'ASGS Australia Register alternates view rdf turtle qsa failed'


def test_asgs_australia_register_alternates_view_rdf_turtle_accept_header():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/australia/?_view=alternates',
        HEADERS_TTL,
        r'rdfs:comment "The view that lists all other views"\^\^xsd:string ;'
    ), 'ASGS Australia Register alternates view rdf turtle accept header failed'


def test_asgs_australia_instance_036_html():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/australia/036',
        HEADERS_HTML,
        r'<li>Shape Area: 9652485198884\.504<\/li>',
    ), 'ASGS Australia instance 036 html failed'


#TODO: This is only working due to the redirect defaulting to text/turtle. It does not work in the browser.
@pytest.mark.skip('ASGS Australia instance 036 rdf turtle file extension not yet implemented')
def test_asgs_australia_instance_036_rdf_turtle_file_extension():
    pytest.fail(f'This does not work in the browser. Please visit {SYSTEM_URI}/australia/036.ttl manually to test.')
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/australia/036.ttl',
        None,
        r'qudt:numericValue 9652485198884.504',
        print_out=True
    ), 'ASGS Australia instance 036 rdf turtle file extension failed'


def test_asgs_australia_instance_036_rdf_turtle_qsa():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/australia/036?_format=text/turtle',
        None,
        r'qudt:numericValue 9652485198884.504',
    ), 'ASGS Australia instance 036 rdf turtle qsa failed'


def test_asgs_australia_instance_036_rdf_turtle_accept_header():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/australia/036',
        HEADERS_TTL,
        r'qudt:numericValue 9652485198884.504'
    ), 'ASGS Australia instance 036 rdf turtle accept header failed'


def test_asgs_australia_instance_036_asgs_view_html():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/australia/036?_view=asgs&_format=text/html',
        None,
        r'<li>Shape Area: 9652485198884\.504<\/li>',
    ), 'ASGS Australia instance 036 asgs view html failed'


def test_asgs_australia_instance_036_asgs_view_rdf_turtle_qsa():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/australia/036?_view=asgs&_format=text/turtle',
        None,
        r'qudt:numericValue 9652485198884.504',
    ), 'ASGS Australia instance 036 asgs view rdf turtle qsa failed'


def test_asgs_australia_instance_036_asgs_view_rdf_turtle_accept_header():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/australia/036?_view=asgs',
        HEADERS_TTL,
        r'qudt:numericValue 9652485198884.504'
    ), 'ASGS Australia instance 036 asgs view rdf turtle accept header failed'


def test_asgs_australia_instance_036_alternates_view_html():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/australia/036?_view=alternates&_format=text/html',
        None,
        r'<a href="\/asgs\/state\/">States<\/a>'
    ), 'ASGS Australia instance 036 alternates view html failed'


def test_asgs_australia_instance_036_alternates_view_rdf_turtle_qsa():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/australia/036?_view=alternates&_format=text/turtle',
        None,
        r'<http:\/\/test\.linked\.data\.gov\.au\/dataset\/asgs\/australia\/036>'
    ), 'ASGS Australia instance 036 alternates view rdf turtle qsa failed'


def test_asgs_australia_instance_036_alternates_view_rdf_turtle_accept_header():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/australia/036?_view=alternates',
        HEADERS_TTL,
        r'<http:\/\/test\.linked\.data\.gov\.au\/dataset\/asgs\/australia\/036>'
    ), 'ASGS Australia instance 036 alternates view rdf turtle qsa failed'


def test_asgs_australia_instance_036_geosparql_view_rdf_turtle_qsa():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/australia/036?_view=geosparql&_format=text/turtle',
        None,
        r'asgs:hasArea \[ qudt:numericValue 9652485198884\.504 ;'
    ), 'ASGS Australia instance 036 geosparql view rdf turtle qsa failed'


def test_asgs_australia_instance_036_geosparql_view_rdf_turtle_accept_header():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/australia/036?_view=geosparql',
        None,
        r'asgs:hasArea \[ qudt:numericValue 9652485198884\.504 ;'
    ), 'ASGS Australia instance 036 geosparql view rdf turtle accept header failed'


@pytest.mark.skip('ASGS Australia instance 036 wfs view xml qsa too large to test frequently')
def test_asgs_australia_instance_036_wfs_view_xml_qsa():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/australia/036?_view=wfs&_format=application/xml',
        None,
        "NONE"
    ), 'ASGS Australia instance 036 wfs view xml qsa failed'


def test_asgs_meshblock_register_html():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/meshblock/',
        None,
        r'<li><a href="\/asgs\/meshblock\/50055290000">MeshBlock ID: 50055290000<\/a><\/li>'
    ), 'ASGS Meshblock Register html failed'


@pytest.mark.skip('ASGS Meshblock Register rdf turtle file extension not yet implemented')
def test_asgs_meshblock_register_rdf_turtle_file_extension():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/meshblock/index.ttl',
        None,
        r'<http:\/\/test\.linked\.data\.gov\.au\/dataset\/asgs\/meshblock\/11205876400>'
    ), 'ASGS Meshblock Register rdf turtle file extension failed'


def test_asgs_meshblock_register_rdf_turtle_qsa():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/meshblock/?_format=text/turtle',
        None,
        r'<http:\/\/test\.linked\.data\.gov\.au\/dataset\/asgs\/meshblock\/11205876400>'
    ), 'ASGS Meshblock Register rdf turtle qsa failed'


def test_asgs_meshblock_register_rdf_turtle_accept_header():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/meshblock/',
        HEADERS_TTL,
        r'<http:\/\/test\.linked\.data\.gov\.au\/dataset\/asgs\/meshblock\/11205876400>'
    ), 'ASGS Meshblock Register rdf turtle accept header failed'


def test_asgs_meshblock_register_alternates_view_html():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/meshblock/?_view=alternates&_format=text/html',
        None,
        r'<td><a href="http:\/\/purl\.org\/linked-data\/registry">http:\/\/purl\.org\/linked-data\/registry<\/a><\/td>'
    ), 'ASGS Meshblock Register alternates view html failed'


def test_asgs_meshblock_register_alternates_view_rdf_turtle_qsa():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/meshblock/?_view=alternates&_format=text/turtle',
        None,
        r'<http:\/\/test\.linked\.data\.gov\.au\/dataset\/asgs\/meshblock\/> alt:hasDefaultView'
    ), 'ASGS Meshblock Register alternates view rdf turtle qsa failed'


def test_asgs_meshblock_register_alternates_view_rdf_turtle_accept_header():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/meshblock/?_view=alternates',
        HEADERS_TTL,
        r'<http:\/\/test\.linked\.data\.gov\.au\/dataset\/asgs\/meshblock\/> alt:hasDefaultView'
    ), 'ASGS Meshblock Register alternates view rdf turtle accept header failed'


def test_asgs_meshblock_register_reg_view_html():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/meshblock/?_view=reg',
        None,
        r'<li><a href="\/asgs\/meshblock\/50055290000">MeshBlock ID: 50055290000<\/a><\/li>'
    ), 'ASGS Meshblock Register reg view html failed'


def test_asgs_meshblock_register_reg_view_rdf_turtle_qsa():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/meshblock/?_view=reg&_format=text/turtle',
        None,
        r'<http:\/\/test\.linked\.data\.gov\.au\/dataset\/asgs\/meshblock\/11205876400>'
    ), 'ASGS Meshblock Register reg view rdf turtle qsa failed'


def test_asgs_meshblock_register_reg_view_rdf_turtle_accept_header():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/meshblock/?_view=reg',
        HEADERS_TTL,
        r'<http:\/\/test\.linked\.data\.gov\.au\/dataset\/asgs\/meshblock\/11205876400>'
    ), 'ASGS Meshblock Register reg view rdf turtle accept header failed'


def test_asgs_meshblock_instance_50055290000_html():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/meshblock/50055290000',
        HEADERS_HTML,
        r'<h1>Mesh Block 50055290000<\/h1>'
    ), 'ASGS Meshblock instance 50055290000 html failed'


@pytest.mark.skip('ASGS Meshblock instance 50055290000 rdf turtle file extension not yet implemented')
def test_asgs_meshblock_instance_50055290000_rdf_turtle_file_extension():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/meshblock/50055290000.ttl',
        None,
        r'<http:\/\/test\.linked\.data\.gov\.au\/dataset\/asgs\/meshblock\/50055290000>'
    ), 'ASGS Meshblock instance 50055290000 rdf turtle file extension failed'


def test_asgs_meshblock_instance_50055290000_rdf_turtle_qsa():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/meshblock/50055290000?_format=text/turtle',
        None,
        r'<http:\/\/test\.linked\.data\.gov\.au\/dataset\/asgs\/meshblock\/50055290000>'
    ), 'ASGS Meshblock instance 50055290000 rdf turtle qsa failed'


def test_asgs_meshblock_instance_50055290000_rdf_turtle_accept_header():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/meshblock/50055290000',
        HEADERS_TTL,
        r'<http:\/\/test\.linked\.data\.gov\.au\/dataset\/asgs\/meshblock\/50055290000>'
    ), 'ASGS Meshblock instance 50055290000 rdf turtle accept header failed'


def test_asgs_meshblock_instance_50055290000_alternates_view_html():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/meshblock/50055290000?_view=alternates',
        None,
        r'<td>An OGC Web Feature Service \(WFS\) view of a Mesh Block\.'
    ), 'ASGS Meshblock instance 50055290000 alternates view html failed'


def test_asgs_meshblock_instance_50055290000_alternates_view_rdf_turtle_qsa():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/meshblock/50055290000?_view=alternates&_format=text/turtle',
        None,
        r'<http:\/\/test\.linked\.data\.gov\.au\/dataset\/asgs\/meshblock\/50055290000>'
    ), 'ASGS Meshblock instance 50055290000 alternates view rdf turtle qsa failed'


def test_asgs_meshblock_instance_50055290000_alternates_view_rdf_turtle_accept_header():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/meshblock/50055290000?_view=alternates',
        HEADERS_TTL,
        r'<http:\/\/test\.linked\.data\.gov\.au\/dataset\/asgs\/meshblock\/50055290000>'
    ), 'ASGS Meshblock instance 50055290000 alternates view rdf turtle accept header failed'


def test_asgs_meshblock_instance_50055290000_asgs_view_html():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/meshblock/50055290000?_view=asgs&_format=text/html',
        None,
        r'<h1>Mesh Block 50055290000<\/h1>'
    ), 'ASGS Meshblock instance 50055290000 asgs view html failed'


def test_asgs_meshblock_instance_50055290000_asgs_view_rdf_turtle_qsa():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/meshblock/50055290000?_view=asgs&_format=text/turtle',
        None,
        r'<http:\/\/test\.linked\.data\.gov\.au\/dataset\/asgs\/meshblock\/50055290000>'
    ), 'ASGS Meshblock instance 50055290000 asgs view rdf turtle qsa failed'


def test_asgs_meshblock_instance_50055290000_asgs_view_rdf_turtle_accept_header():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/meshblock/50055290000?_view=asgs',
        HEADERS_TTL,
        r'<http:\/\/test\.linked\.data\.gov\.au\/dataset\/asgs\/meshblock\/50055290000>'
    ), 'ASGS Meshblock instance 50055290000 asgs view rdf turtle accept header failed'


def test_asgs_meshblock_instance_50055290000_geosparql_view_rdf_turtle_qsa():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/meshblock/50055290000?_view=geosparql&_format=text/turtle',
        None,
        r'<http:\/\/test\.linked\.data\.gov\.au\/dataset\/asgs\/meshblock\/50055290000>'
    ), 'ASGS Meshblock instance 50055290000 geosparql view rdf turtle qsa failed'


def test_asgs_meshblock_instance_50055290000_wfs_view_xml():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/meshblock/50055290000?_view=wfs&_format=application/xml',
        None,
        r'<MB:Shape_Area>52623\.743038533052<\/MB:Shape_Area>'
    ), 'ASGS Meshblock instance 50055290000 wfs view xml failed'


def test_asgs_sa1_register_html():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/sa1/',
        None,
        r'<li><a href="\/asgs\/sa1\/30804152813">SA1 Feature #30804152813<\/a><\/li>'
    ), 'ASGS SA1 Register html failed'


@pytest.mark.skip('ASGS SA1 Register rdf turtle file extension not yet implemented')
def test_asgs_sa1_register_rdf_turtle_file_extension():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/sa1/index.ttl',
        None,
        r'<http:\/\/test\.linked\.data\.gov\.au\/dataset\/asgs\/sa1\/10805116808>'
    ), 'ASGS SA1 Register rdf turtle file extension failed'


def test_asgs_sa1_register_rdf_turtle_qsa():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/sa1/?_format=text/turtle',
        None,
        r'<http:\/\/test\.linked\.data\.gov\.au\/dataset\/asgs\/sa1\/10805116808>'
    ), 'ASGS SA1 Register rdf turtle qsa failed'


def test_asgs_sa1_register_rdf_turtle_accept_header():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/sa1/',
        HEADERS_TTL,
        r'<http:\/\/test\.linked\.data\.gov\.au\/dataset\/asgs\/sa1\/10805116808>'
    ), 'ASGS SA1 Register rdf turtle accept headerfailed'


def test_asgs_sa1_register_reg_view_html():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/sa1/?_view=reg',
        None,
        r'<li><a href="\/asgs\/sa1\/30804152813">SA1 Feature #30804152813<\/a><\/li>'
    ), 'ASGS SA1 Register reg view html failed'


def test_asgs_sa1_register_reg_view_rdf_turtle_qsa():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/sa1/?_view=reg&_format=text/turtle',
        None,
        r'<http:\/\/test\.linked\.data\.gov\.au\/dataset\/asgs\/sa1\/10805116808>'
    ), 'ASGS SA1 Register reg view rdf turtle qsa failed'


def test_asgs_sa1_register_reg_view_rdf_turtle_accept_header():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/sa1/?_view=reg',
        HEADERS_TTL,
        r'<http:\/\/test\.linked\.data\.gov\.au\/dataset\/asgs\/sa1\/10805116808>'
    ), 'ASGS SA1 Register reg view rdf turtle accept headerfailed'


def test_asgs_sa1_register_alternates_view_html():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/sa1/?_view=alternates&_format=text/html',
        None,
        r'<h2>Instance <a href="http:\/\/test\.linked\.data\.gov\.au\/dataset\/asgs\/sa1\/">http:\/\/test\.linked\.data\.gov\.au\/dataset\/asgs\/sa1\/<\/a><\/h2>'
    ), 'ASGS SA1 Regster alternates view html'


def test_asgs_sa1_register_alternates_view_rdf_turtle_qsa():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/sa1/?_view=alternates&_format=text/turtle',
        None,
        r'<http:\/\/test\.linked\.data\.gov\.au\/dataset\/asgs\/sa1\/> alt:hasDefaultView'
    ), 'ASGS SA1 Regster alternates view rdf turtle qsa'


def test_asgs_sa1_register_alternates_view_rdf_turtle_accept_header():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/sa1/?_view=alternates',
        HEADERS_TTL,
        r'<http:\/\/test\.linked\.data\.gov\.au\/dataset\/asgs\/sa1\/> alt:hasDefaultView'
    ), 'ASGS SA1 Regster alternates view rdf turtle accept header'


def test_asgs_sa1_instance_30804152813_html():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/sa1/30804152813',
        HEADERS_HTML,
        r'<h1>SA1 Feature 30804152813<\/h1>'
    ), 'ASGS SA1 instance 30804152813 html failed'


@pytest.mark.skip('ASGS SA1 instance 30804152813 rdf turtle file extension not yet implemented')
def test_asgs_sa1_instance_30804152813_rdf_turtle_file_extension():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/sa1/30804152813.ttl',
        None,
        None #TODO
    ), 'ASGS SA1 instance 30804152813 rdf turtle file extension failed'


def test_asgs_sa1_instance_30804152813_rdf_turtle_qsa():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/sa1/30804152813?_format=text/turtle',
        None,
        r'<http:\/\/test\.linked\.data\.gov\.au\/dataset\/asgs\/sa1\/30804152813>'
    ), 'ASGS SA1 instance 30804152813 rdf turtle qsa failed'


def test_asgs_sa1_instance_30804152813_rdf_turtle_accept_header():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/sa1/30804152813',
        HEADERS_TTL,
        r'<http:\/\/test\.linked\.data\.gov\.au\/dataset\/asgs\/sa1\/30804152813>'
    ), 'ASGS SA1 instance 30804152813 rdf turtle accept header failed'


def test_asgs_sa1_instance_30804152813_asgs_view_html():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/sa1/30804152813?_view=asgs&_format=text/html',
        None,
        r'<h1>SA1 Feature 30804152813<\/h1>'
    ), 'ASGS SA1 instance 30804152813 asgs view html failed'


def test_asgs_sa1_instance_30804152813_asgs_view_rdf_turtle_qsa():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/sa1/30804152813',
        HEADERS_TTL,
        r'<http:\/\/test\.linked\.data\.gov\.au\/dataset\/asgs\/sa1\/30804152813>'
    ), 'ASGS SA1 instance 30804152813 asgs view rdf turtle qsa failed'


def test_asgs_sa1_instance_30804152813_asgs_view_rdf_turtle_accept_header():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/sa1/30804152813?_view=asgs',
        HEADERS_TTL,
        r'<http:\/\/test\.linked\.data\.gov\.au\/dataset\/asgs\/sa1\/30804152813>'
    ), 'ASGS SA1 instance 30804152813 asgs view rdf turtle accept header failed'


def test_asgs_sa1_instance_30804152813_alternates_view_html():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/sa1/30804152813?_view=alternates&_format=text/html',
        None,
        r'<h2>Instance <a href="http:\/\/test\.linked\.data\.gov\.au\/dataset\/asgs\/sa1\/30804152813">http:\/\/test\.linked\.data\.gov\.au\/dataset\/asgs\/sa1\/30804152813<\/a><\/h2>'
    ), 'ASGS SA1 instance 30804152813 alternates view html failed'


def test_asgs_sa1_instance_30804152813_alternates_view_rdf_turtle_qsa():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/sa1/30804152813?_view=alternates&_format=text/turtle',
        None,
        r'<http:\/\/test\.linked\.data\.gov\.au\/dataset\/asgs\/sa1\/30804152813>'
    ), 'ASGS SA1 instance 30804152813 alternates view rdf turtle qsa failed'


def test_asgs_sa1_instance_30804152813_alternates_view_rdf_turtle_accept_header():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/sa1/30804152813?_view=alternates',
        HEADERS_TTL,
        r'<http:\/\/test\.linked\.data\.gov\.au\/dataset\/asgs\/sa1\/30804152813>'
    ), 'ASGS SA1 instance 30804152813 alternates view rdf turtle accept header failed'


def test_asgs_sa1_instance_30804152813_geosparql_view_rdf_turtle_qsa():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/sa1/30804152813?_view=geosparql&_format=text/turtle',
        None,
        r'<http:\/\/test\.linked\.data\.gov\.au\/dataset\/asgs\/sa1\/30804152813> a asgs:SA1,'
    ), 'ASGS SA1 instance 30804152813 geosparql view rdf turtle qsa failed'


def test_asgs_sa1_instance_30804152813_geosparql_view_rdf_turtle_accept_header():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/sa1/30804152813?_view=geosparql',
        HEADERS_TTL,
        r'<http:\/\/test\.linked\.data\.gov\.au\/dataset\/asgs\/sa1\/30804152813> a asgs:SA1,'
    ), 'ASGS SA1 instance 30804152813 geosparql view rdf turtle accept header failed'


def test_asgs_sa1_instance_30804152813_wfs_view_xml():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/sa1/30804152813?_view=wfs&_format=application/xml',
        None,
        r'<SA1:Shape_Area>1660884\.7376417089<\/SA1:Shape_Area>'
    ), 'ASGS SA1 instance 30804152813 wfs view xml failed'


def test_asgs_sa2_register_html():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/sa2/',
        None,
        r'<li><a href="\/asgs\/sa2\/212051322">SA2 Feature #212051322<\/a><\/li>'
    ), 'ASGS SA2 Register html failed'


@pytest.mark.skip('ASGS SA2 Register rdf turtle file extension not yet implemented')
def test_asgs_sa2_register_rdf_turtle_file_extension():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/sa2/index.ttl',
        None,
        r'<http:\/\/test\.linked\.data\.gov\.au\/dataset\/asgs\/sa2\/104021086> a <http:\/\/test\.linked\.data\.gov\.au\/def\/asgs#SA2> ;'
    ), 'ASGS SA2 Register rdf turtle file extension failed'


def test_asgs_sa2_register_rdf_turtle_qsa():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/sa2/?_format=text/turtle',
        None,
        r'<http:\/\/test\.linked\.data\.gov\.au\/dataset\/asgs\/sa2\/104021086> a <http:\/\/test\.linked\.data\.gov\.au\/def\/asgs#SA2> ;'
    ), 'ASGS SA2 Register rdf turtle qsa failed'


def test_asgs_sa2_register_rdf_turtle_accept_header():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/sa2/',
        HEADERS_TTL,
        r'<http:\/\/test\.linked\.data\.gov\.au\/dataset\/asgs\/sa2\/104021086> a <http:\/\/test\.linked\.data\.gov\.au\/def\/asgs#SA2> ;'
    ), 'ASGS SA2 Register rdf turtle accept header failed'


def test_asgs_sa2_register_alternates_view_html():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/sa2/?_view=alternates&_format=text/html',
        None,
        r'<h4>Default view: <a href="http:\/\/test\.linked\.data\.gov\.au\/dataset\/asgs\/sa2\/">reg<\/a><\/h4>'
    ), 'ASGS SA2 Register alternates view html failed'


def test_asgs_sa2_register_alternates_view_rdf_turtle_qsa():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/sa2/?_view=alternates&_format=text/turtle',
        None,
        r'<http:\/\/test\.linked\.data\.gov\.au\/dataset\/asgs\/sa2\/> alt:hasDefaultView'
    ), 'ASGS SA2 Register alternates view rdf turtle qsa failed'


def test_asgs_sa2_register_alternates_view_rdf_turtle_accept_header():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/sa2/?_view=alternates',
        HEADERS_TTL,
        r'<http:\/\/test\.linked\.data\.gov\.au\/dataset\/asgs\/sa2\/> alt:hasDefaultView'
    ), 'ASGS SA2 Register alternates view rdf turtle accept header failed'


def test_asgs_sa2_register_reg_view_html():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/sa2/?_view=reg',
        None,
        r'<li><a href="\/asgs\/sa2\/212051322">SA2 Feature #212051322<\/a><\/li>'
    ), 'ASGS SA2 Register reg view html failed'


def test_asgs_sa2_register_reg_view_rdf_turtle_qsa():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/sa2/?_view=reg&_format=text/turtle',
        None,
        r'<http:\/\/test\.linked\.data\.gov\.au\/dataset\/asgs\/sa2\/104021086> a <http:\/\/test\.linked\.data\.gov\.au\/def\/asgs#SA2> ;'
    ), 'ASGS SA2 Register reg view rdf turtle qsa failed'


def test_asgs_sa2_register_reg_view_rdf_turtle_accept_header():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/sa2/?_view=reg',
        HEADERS_TTL,
        r'<http:\/\/test\.linked\.data\.gov\.au\/dataset\/asgs\/sa2\/104021086> a <http:\/\/test\.linked\.data\.gov\.au\/def\/asgs#SA2> ;'
    ), 'ASGS SA2 Register reg view rdf turtle accept header failed'


def test_asgs_sa2_instance_212051322_html():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/sa2/212051322',
        HEADERS_HTML,
        r'<h1>SA2 Feature - Glen Waverley - West&nbsp;\(212051322\)<\/h1>'
    ), 'ASGS SA2 instance 212051322 html failed'


@pytest.mark.skip('ASGS SA2 instance 212051322 rdf turtle file extension not yet implemented')
def test_asgs_sa2_instance_212051322_rdf_turtle_file_extension():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/sa2/212051322.ttl',
        None,
        r'<http:\/\/test\.linked\.data\.gov\.au\/dataset\/asgs\/sa2\/212051322> a asgs:SA2,'
    ), 'ASGS SA2 instance 212051322 rdf turtle file extension failed'


def test_asgs_sa2_instance_212051322_rdf_turtle_qsa():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/sa2/212051322?_format=text/turtle',
        None,
        r'<http:\/\/test\.linked\.data\.gov\.au\/dataset\/asgs\/sa2\/212051322> a asgs:SA2,'
    ), 'ASGS SA2 instance 212051322 rdf turtle qsa failed'


def test_asgs_sa2_instance_212051322_rdf_turtle_accept_header():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/sa2/212051322',
        HEADERS_TTL,
        r'<http:\/\/test\.linked\.data\.gov\.au\/dataset\/asgs\/sa2\/212051322> a asgs:SA2,'
    ), 'ASGS SA2 instance 212051322 rdf turtle accept header failed'


def test_asgs_sa2_instance_212051322_alternates_view_html():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/sa2/212051322?_view=alternates&_format=text/html',
        None,
        r'<h2>Instance <a href="http:\/\/test\.linked\.data\.gov\.au\/dataset\/asgs\/sa2\/212051322">http:\/\/test\.linked\.data\.gov\.au\/dataset\/asgs\/sa2\/212051322<\/a><\/h2>'
    ), 'ASGS SA2 instance 212051322 alternates view html failed'


def test_asgs_sa2_instance_212051322_alternates_view_rdf_turtle_qsa():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/sa2/212051322?_view=alternates&_format=text/turtle',
        None,
        r'<http:\/\/test\.linked\.data\.gov\.au\/dataset\/asgs\/sa2\/212051322> alt:hasDefaultView'
    ), 'ASGS SA2 instance 212051322 alternates view rdf turtle qsa failed'


def test_asgs_sa2_instance_212051322_alternates_view_rdf_turtle_accept_header():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/sa2/212051322?_view=alternates',
        HEADERS_TTL,
        r'<http:\/\/test\.linked\.data\.gov\.au\/dataset\/asgs\/sa2\/212051322> alt:hasDefaultView'
    ), 'ASGS SA2 instance 212051322 alternates view rdf turtle accept header failed'


def test_asgs_sa2_instance_212051322_asgs_view_html():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/sa2/212051322?_view=asgs',
        HEADERS_HTML,
        r'<h1>SA2 Feature - Glen Waverley - West&nbsp;\(212051322\)<\/h1>'
    ), 'ASGS SA2 instance 212051322 asgs view html failed'


def test_asgs_sa2_instance_212051322_asgs_view_rdf_turtle_qsa():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/sa2/212051322?_view=asgs&_format=text/turtle',
        None,
        r'<http:\/\/test\.linked\.data\.gov\.au\/dataset\/asgs\/sa2\/212051322> a asgs:SA2,'
    ), 'ASGS SA2 instance 212051322 asgs view rdf turtle qsa failed'


def test_asgs_sa2_instance_212051322_asgs_view_rdf_turtle_accept_header():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/sa2/212051322?_view=asgs',
        HEADERS_TTL,
        r'<http:\/\/test\.linked\.data\.gov\.au\/dataset\/asgs\/sa2\/212051322> a asgs:SA2,'
    ), 'ASGS SA2 instance 212051322 asgs view rdf turtle accept header failed'


def test_asgs_sa2_instance_212051322_wfs_view_xml():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/sa2/212051322?_view=wfs&_format=application/xml',
        None,
        r'<SA2:Shape_Area>12341661\.02505325<\/SA2:Shape_Area>'
    ), 'ASGS SA2 instance 212051322 wfs view xml failed'


def test_asgs_sa2_instance_212051322_geosparql_rdf_turtle_qsa():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/sa2/212051322?_view=geosparql&_format=text/turtle',
        None,
        r'<http:\/\/test\.linked\.data\.gov\.au\/dataset\/asgs\/sa2\/212051322> a asgs:SA2,'
    ), 'ASGS SA2 instance 212051322 geosparql view failed'


def test_asgs_sa3_register_html():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/sa3/',
        None,
        r'<li><a href="http:\/\/test\.linked\.data\.gov\.au\/def\/asgs#SA3">http:\/\/test\.linked\.data\.gov\.au\/def\/asgs#SA3<\/a><\/li>'
    ), 'ASGS SA3 Register html failed'


@pytest.mark.skip('ASGS SA3 Register rdf turtle file extension not yet implemented')
def test_asgs_sa3_register_rdf_turtle_file_extension():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/sa3/index.ttl',
        None,
        r'<http:\/\/test\.linked\.data\.gov\.au\/dataset\/asgs\/sa3\/10303> a <http:\/\/test\.linked\.data\.gov\.au\/def\/asgs#SA3> ;'
    ), 'ASGS SA3 Register rdf turtle file extension failed'


def test_asgs_sa3_register_rdf_turtle_qsa():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/sa3/?_format=text/turtle',
        None,
        r'<http:\/\/test\.linked\.data\.gov\.au\/dataset\/asgs\/sa3\/10303> a <http:\/\/test\.linked\.data\.gov\.au\/def\/asgs#SA3> ;'
    ), 'ASGS SA3 Register rdf turtle qsa failed'


def test_asgs_sa3_register_rdf_turtle_accept_header():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/sa3/',
        HEADERS_TTL,
        r'<http:\/\/test\.linked\.data\.gov\.au\/dataset\/asgs\/sa3\/10303> a <http:\/\/test\.linked\.data\.gov\.au\/def\/asgs#SA3> ;'
    ), 'ASGS SA3 Register rdf turtle accept header failed'


def test_asgs_sa3_register_reg_view_html():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/sa3/?_view=reg&_format=text/html',
        None,
        r'<li><a href="http:\/\/test\.linked\.data\.gov\.au\/def\/asgs#SA3">http:\/\/test\.linked\.data\.gov\.au\/def\/asgs#SA3<\/a><\/li>'
    ), 'ASGS SA3 Register reg view html failed'


def test_asgs_sa3_register_reg_view_rdf_turtle_qsa():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/sa3/?_view=reg&_format=text/turtle',
        None,
        r'<http:\/\/test\.linked\.data\.gov\.au\/dataset\/asgs\/sa3\/10303> a <http:\/\/test\.linked\.data\.gov\.au\/def\/asgs#SA3> ;'
    ), 'ASGS SA3 Register reg view rdf turtle qsa failed'


def test_asgs_sa3_register_reg_view_rdf_turtle_accept_header():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/sa3/?_view=reg',
        HEADERS_TTL,
        r'<http:\/\/test\.linked\.data\.gov\.au\/dataset\/asgs\/sa3\/10303> a <http:\/\/test\.linked\.data\.gov\.au\/def\/asgs#SA3> ;'
    ), 'ASGS SA3 Register reg view rdf turtle accept header failed'


def test_asgs_sa3_register_alternates_view_html():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/sa3/?_view=alternates&_format=text/html',
        None,
        r'<h2>Instance <a href="http:\/\/test\.linked\.data\.gov\.au\/dataset\/asgs\/sa3\/">http:\/\/test\.linked\.data\.gov\.au\/dataset\/asgs\/sa3\/<\/a><\/h2>'
    ), 'ASGS SA3 Register alternates view html failed'


def test_asgs_sa3_register_alternates_view_rdf_turtle_qsa():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/sa3/?_view=alternates&_format=text/turtle',
        None,
        r'<http:\/\/test\.linked\.data\.gov\.au\/dataset\/asgs\/sa3\/> alt:hasDefaultView'
    ), 'ASGS SA3 Register alternates view rdf turtle qsa failed'


def test_asgs_sa3_register_alternates_view_rdf_turtle_accept_header():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/sa3/?_view=alternates',
        HEADERS_TTL,
        r'<http:\/\/test\.linked\.data\.gov\.au\/dataset\/asgs\/sa3\/> alt:hasDefaultView'
    ), 'ASGS SA3 Register alternates view rdf turtle accept header failed'


def test_asgs_sa3_instance_21402_html():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/sa3/21402',
        HEADERS_HTML,
        r'<h1>SA3 Feature - Mornington Peninsula&nbsp;\(21402\)<\/h1>'
    ), 'ASGS SA3 instance 21402 html failed'


@pytest.mark.skip('ASGS SA3 instance 21402 rdf turtle file extension not yet implemented')
def test_asgs_sa3_instance_21402_rdf_turtle_file_extension():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/sa3/21402.ttl',
        None,
        r'<http:\/\/test\.linked\.data\.gov\.au\/dataset\/asgs\/sa3\/21402> a asgs:SA3,'
    ), 'ASGS SA3 instance 21402 rdf turtle file extension failed'


def test_asgs_sa3_instance_21402_rdf_turtle_qsa():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/sa3/21402?_format=text/turtle',
        None,
        r'<http:\/\/test\.linked\.data\.gov\.au\/dataset\/asgs\/sa3\/21402> a asgs:SA3,'
    ), 'ASGS SA3 instance 21402 rdf turtle qsa failed'


def test_asgs_sa3_instance_21402_rdf_turtle_accept_header():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/sa3/21402',
        HEADERS_TTL,
        r'<http:\/\/test\.linked\.data\.gov\.au\/dataset\/asgs\/sa3\/21402> a asgs:SA3,'
    ), 'ASGS SA3 instance 21402 rdf turtle accept header failed'


def test_asgs_sa3_instance_21402_asgs_view_html():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/sa3/21402?_view=asgs&_format=text/html',
        None,
        r'<h1>SA3 Feature - Mornington Peninsula&nbsp;\(21402\)<\/h1>'
    ), 'ASGS SA3 instance 21402 asgs view html failed'


def test_asgs_sa3_instance_21402_asgs_view_rdf_turtle_qsa():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/sa3/21402?_view=asgs&_format=text/turtle',
        None,
        r'<http:\/\/test\.linked\.data\.gov\.au\/dataset\/asgs\/sa3\/21402> a asgs:SA3,'
    ), 'ASGS SA3 instance 21402 asgs view rdf turtle qsa failed'


def test_asgs_sa3_instance_21402_asgs_view_rdf_turtle_accept_header():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/sa3/21402?_view=asgs',
        HEADERS_TTL,
        r'<http:\/\/test\.linked\.data\.gov\.au\/dataset\/asgs\/sa3\/21402> a asgs:SA3,'
    ), 'ASGS SA3 instance 21402 asgs view rdf turtle accept header failed'


def test_asgs_sa3_instance_21402_alternates_view_html():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/sa3/21402?_view=alternates&_format=text/html',
        None,
        r'<h2>Instance <a href="http:\/\/test\.linked\.data\.gov\.au\/dataset\/asgs\/sa3\/21402">http:\/\/test\.linked\.data\.gov\.au\/dataset\/asgs\/sa3\/21402<\/a><\/h2>'
    ), 'ASGS SA3 instance 21402 alternates view html failed'


def test_asgs_sa3_instance_21402_alternates_view_rdf_turtle_qsa():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/sa3/21402?_view=alternates&_format=text/turtle',
        None,
        r'<http:\/\/test\.linked\.data\.gov\.au\/dataset\/asgs\/sa3\/21402> alt:hasDefaultView'
    ), 'ASGS SA3 instance 21402 alternates view rdf turtle qsa failed'


def test_asgs_sa3_instance_21402_alternates_view_rdf_turtle_accept_header():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/sa3/21402?_view=alternates',
        HEADERS_TTL,
        r'<http:\/\/test\.linked\.data\.gov\.au\/dataset\/asgs\/sa3\/21402> alt:hasDefaultView'
    ), 'ASGS SA3 instance 21402 alternates view rdf turtle accept header failed'


def test_asgs_sa3_instance_21402_wfs_view_xml():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/sa3/21402?_view=wfs&_format=application/xml',
        None,
        r'<gml:lowerCorner>10777612\.616999999 -5425372\.8682000004<\/gml:lowerCorner>'
    ), 'ASGS SA3 instance 21402 wfs view application/xml failed'


def test_asgs_sa3_instance_21402_geosparql_rdf_turtle_qsa():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/sa3/21402?_view=geosparql&_format=text/turtle',
        None,
        r'<http:\/\/test\.linked\.data\.gov\.au\/dataset\/asgs\/sa3\/21402> a asgs:SA3,'
    ), 'ASGS SA3 instance 21402 geosparql view rdf turtle qsa failed'


def test_asgs_sa3_instance_21402_geosparql_rdf_turtle_accept_header():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/sa3/21402?_view=geosparql',
        HEADERS_TTL,
        r'<http:\/\/test\.linked\.data\.gov\.au\/dataset\/asgs\/sa3\/21402> a asgs:SA3,'
    ), 'ASGS SA3 instance 21402 geosparql view rdf turtle accept header failed'


def test_asgs_sa4_register_html():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/sa4/',
        None,
        r'<li><a href="http:\/\/test\.linked\.data\.gov\.au\/def\/asgs#SA4">http:\/\/test\.linked\.data\.gov\.au\/def\/asgs#SA4<\/a><\/li>'
    ), 'ASGS SA4 Register html failed'


@pytest.mark.skip('ASGS SA4 Register rdf turtle file extension not yet implemented')
def test_asgs_sa4_register_rdf_turtle_file_extension():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/sa4/index.ttl',
        None,
        r'<http:\/\/test\.linked\.data\.gov\.au\/dataset\/asgs\/sa4\/102> a <http:\/\/test\.linked\.data\.gov\.au\/def\/asgs#SA4> ;'
    ), 'ASGS SA4 Register rdf turtle file extension failed'


def test_asgs_sa4_register_rdf_turtle_qsa():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/sa4/?_format=text/turtle',
        None,
        r'<http:\/\/test\.linked\.data\.gov\.au\/dataset\/asgs\/sa4\/102> a <http:\/\/test\.linked\.data\.gov\.au\/def\/asgs#SA4> ;'
    ), 'ASGS SA4 Register rdf turtle qsa failed'


def test_asgs_sa4_register_rdf_turtle_accept_header():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/sa4/',
        HEADERS_TTL,
        r'<http:\/\/test\.linked\.data\.gov\.au\/dataset\/asgs\/sa4\/102> a <http:\/\/test\.linked\.data\.gov\.au\/def\/asgs#SA4> ;'
    ), 'ASGS SA4 Register rdf turtle accept header failed'


def test_asgs_sa4_register_reg_view_html():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/sa4/?_view=reg&_format=text/html',
        None,
        r'<li><a href="http:\/\/test\.linked\.data\.gov\.au\/def\/asgs#SA4">http:\/\/test\.linked\.data\.gov\.au\/def\/asgs#SA4<\/a><\/li>'
    ), 'ASGS SA4 Register reg view html failed'


def test_asgs_sa4_register_reg_view_rdf_turtle_qsa():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/sa4/?_view=reg&_format=text/turtle',
        None,
        r'<http:\/\/test\.linked\.data\.gov\.au\/dataset\/asgs\/sa4\/102> a <http:\/\/test\.linked\.data\.gov\.au\/def\/asgs#SA4> ;'
    ), 'ASGS SA4 Register reg view rdf turtle qsa failed'


def test_asgs_sa4_register_rdf_turtle_accept_header():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/sa4/?_view=reg',
        HEADERS_TTL,
        r'<http:\/\/test\.linked\.data\.gov\.au\/dataset\/asgs\/sa4\/102> a <http:\/\/test\.linked\.data\.gov\.au\/def\/asgs#SA4> ;'
    ), 'ASGS SA4 Register rdf reg view turtle accept header failed'


def test_asgs_sa4_register_alternates_view_html():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/sa4/?_view=alternates&_format=text/html',
        None,
        r'<h2>Instance <a href="http:\/\/test\.linked\.data\.gov\.au\/dataset\/asgs\/sa4\/">http:\/\/test\.linked\.data\.gov\.au\/dataset\/asgs\/sa4\/<\/a><\/h2>'
    ), 'ASGS SA4 Register alternates view html failed'


def test_asgs_sa4_register_alternates_view_rdf_turtle_qsa():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/sa4/?_view=alternates&_format=text/turtle',
        None,
        r'<http:\/\/test\.linked\.data\.gov\.au\/dataset\/asgs\/sa4\/> alt:hasDefaultView'
    ), 'ASGS SA4 Register alternates view rdf turtle qsa failed'


def test_asgs_sa4_register_alternates_view_rdf_turtle_accept_header():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/sa4/?_view=alternates',
        HEADERS_TTL,
        r'<http:\/\/test\.linked\.data\.gov\.au\/dataset\/asgs\/sa4\/> alt:hasDefaultView'
    ), 'ASGS SA4 Register alternates view rdf turtle accept header failed'

#TODO: Continue on asgs sa4 instance ... http://13.236.122.60/asgs/sa4/



#TODO: States register and instances ...


if __name__ == '__main__':
    pass
