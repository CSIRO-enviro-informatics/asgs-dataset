from rdflib import Graph, URIRef, Namespace, RDF, RDFS, XSD, OWL, Literal, BNode
from lxml import etree
import os
import requests
from io import StringIO
from model.lookups import *


def get_asgs_type(uri):
    # get the type from the URI
    if 'meshblock' in uri:
        asgs_type = 'MB'
    elif 'sa1' in uri:
        asgs_type = 'SA1'
    elif 'sa2' in uri:
        asgs_type = 'SA2'
    elif 'sa3' in uri:
        asgs_type = 'SA3'
    elif 'sa4' in uri:
        asgs_type = 'SA4'
    else:  # state
        asgs_type = 'STATE'

    return asgs_type


def _get_instance_details(uri, from_local_file=True):
    # get the ID from the URI
    id = uri.split('/')[-1]
    # get the ASGS type from the URI
    asgs_type = get_asgs_type(uri)

    def get_wfs_query_for_feature_type():
        featureid = uri.split('/')[-1]
        uri_template = 'https://geo.abs.gov.au/arcgis/services/ASGS2016/{service}/MapServer/WFSServer' \
                       '?service=wfs&version=2.0.0&request=GetFeature&typeName={typename}' \
                       '&Filter=<ogc:Filter><ogc:PropertyIsEqualTo><ogc:PropertyName>{propertyname}</ogc:PropertyName>' \
                       '<ogc:Literal>{featureid}</ogc:Literal>' \
                       '</ogc:PropertyIsEqualTo></ogc:Filter>'

        if asgs_type == 'meshblock':
            service = 'MB'
            typename = 'MB:MB'
            propertyname = 'MB:MB_CODE_2016'
        elif asgs_type == 'sa1':
            service = 'SA1'
            typename = 'SA1:SA1'
            propertyname = 'SA1:SA1_MAINCODE_2016'
        elif asgs_type == 'sa2':
            service = 'SA2'
            typename = 'SA2:SA2'
            propertyname = 'SA2:SA2_MAINCODE_2016'
        elif asgs_type == 'sa3':
            service = 'SA3'
            typename = 'SA3:SA3'
            propertyname = 'SA3:SA3_CODE_2016'
        elif asgs_type == 'sa4':
            service = 'SA4'
            typename = 'SA4:SA4'
            propertyname = 'SA4:SA4_CODE_2016'
        else:  # state
            service = 'STATE'
            typename = 'STATE:STATE'
            propertyname = 'STATE:STATE_NAME_ABBREV_2016'

        return uri_template.format(**{
            'service': service,
            'typename': typename,
            'propertyname': propertyname,
            'featureid': featureid
        })

    def _get_mb_details(root):
        return {
            'wkt': '<http://www.opengis.net/def/crs/EPSG/0/3857>; POLYGON(({}))'.format(coords_wkt),
            'object_id': root.xpath('//MB:MB/MB:MB_CODE_2016', namespaces={'MB': 'WFS'})[0].text,
            'category': root.xpath('//MB:MB/MB:MB_CATEGORY_CODE_2016', namespaces={'MB': 'WFS'})[0].text,
            'category_name': root.xpath('//MB:MB/MB:MB_CATEGORY_NAME_2016', namespaces={'MB': 'WFS'})[0].text,
            'albers_area': root.xpath('//MB:MB/MB:AREA_ALBERS_SQKM', namespaces={'MB': 'WFS'})[0].text,
            'sa1': root.xpath('//MB:MB/MB:SA1_MAINCODE_2016', namespaces={'MB': 'WFS'})[0].text,
            'state': int(root.xpath('//MB:MB/MB:STATE_CODE_2016', namespaces={'MB': 'WFS'})[0].text),
            'dzn': root.xpath('//MB:MB/MB:DZN_CODE_2016', namespaces={'MB': 'WFS'})[0].text,
            'ssc': root.xpath('//MB:MB/MB:SSC_CODE_2016', namespaces={'MB': 'WFS'})[0].text,
            'nrmr': root.xpath('//MB:MB/MB:NRMR_CODE_2016', namespaces={'MB': 'WFS'})[0].text,
            'add': root.xpath('//MB:MB/MB:ADD_CODE_2016', namespaces={'MB': 'WFS'})[0].text,
            'shape_length': root.xpath('//MB:MB/MB:Shape_Length', namespaces={'MB': 'WFS'})[0].text,
            'shape_area': root.xpath('//MB:MB/MB:Shape_Area', namespaces={'MB': 'WFS'})[0].text
        }

    def _get_sa1_details(root):
        return {
            'wkt': '<http://www.opengis.net/def/crs/EPSG/0/3857>; POLYGON(({}))'.format(coords_wkt),
            'object_id': root.xpath('//SA1:OBJECTID', namespaces={'SA1': 'WFS'})[0].text,
            'albers_area': root.xpath('//SA1:AREA_ALBERS_SQKM', namespaces={'SA1': 'WFS'})[0].text,
            'sa2': root.xpath('//SA1:SA2_MAINCODE_2016', namespaces={'SA1': 'WFS'})[0].text,
            'state': int(root.xpath('//SA1:STATE_CODE_2016', namespaces={'SA1': 'WFS'})[0].text),
            'shape_length': root.xpath('//SA1:Shape_Length', namespaces={'SA1': 'WFS'})[0].text,
            'shape_area': root.xpath('//SA1:Shape_Area', namespaces={'SA1': 'WFS'})[0].text
        }

    def _get_sa2_details(root):
        return {
            'wkt': '<http://www.opengis.net/def/crs/EPSG/0/3857>; POLYGON(({}))'.format(coords_wkt),
            'object_id': root.xpath('//SA2:OBJECTID', namespaces={'SA2': 'WFS'})[0].text,
            'albers_area': root.xpath('//SA2:AREA_ALBERS_SQKM', namespaces={'SA2': 'WFS'})[0].text,
            'sa3': root.xpath('//SA2:SA3_CODE_2016', namespaces={'SA2': 'WFS'})[0].text,
            'state': int(root.xpath('//SA2:STATE_CODE_2016', namespaces={'SA2': 'WFS'})[0].text),
            'shape_length': root.xpath('//SA2:Shape_Length', namespaces={'SA2': 'WFS'})[0].text,
            'shape_area': root.xpath('//SA2:Shape_Area', namespaces={'SA2': 'WFS'})[0].text
        }

    def _get_sa3_details(root):
        return {
            'wkt': '<http://www.opengis.net/def/crs/EPSG/0/3857>; POLYGON(({}))'.format(coords_wkt),
            'object_id': root.xpath('//SA3:SA3/SA3:SA3_CODE_2016', namespaces={'SA3': 'WFS'})[0].text,
            'name': root.xpath('//SA3:SA3/SA3:SA3_NAME_2016', namespaces={'SA3': 'WFS'})[0].text,
            'albers_area': root.xpath('//SA3:SA3/SA3:AREA_ALBERS_SQKM', namespaces={'SA3': 'WFS'})[0].text,
            'sa4': root.xpath('//SA3:SA3/SA3:SA3_CODE_2016', namespaces={'SA3': 'WFS'})[0].text,
            'state': int(root.xpath('//SA3:SA3/SA3:STATE_CODE_2016', namespaces={'SA3': 'WFS'})[0].text),
            'shape_length': root.xpath('//SA3:SA3/SA3:Shape_Length', namespaces={'SA3': 'WFS'})[0].text,
            'shape_area': root.xpath('//SA3:SA3/SA3:Shape_Area', namespaces={'SA3': 'WFS'})[0].text
        }

    def _get_sa4_details(root):
        return {
            'wkt': '<http://www.opengis.net/def/crs/EPSG/0/3857>; POLYGON(({}))'.format(coords_wkt),
            'object_id': root.xpath('//SA4:OBJECTID', namespaces={'SA4': 'WFS'})[0].text,
            'name': root.xpath('//SA4:SA4_NAME_2016', namespaces={'SA4': 'WFS'})[0].text,
            'albers_area': root.xpath('//SA4:AREA_ALBERS_SQKM', namespaces={'SA4': 'WFS'})[0].text,
            'state': int(root.xpath('//SA4:STATE_CODE_2016', namespaces={'SA4': 'WFS'})[0].text),
            'shape_length': root.xpath('//SA4:Shape_Length', namespaces={'SA4': 'WFS'})[0].text,
            'shape_area': root.xpath('//SA4:Shape_Area', namespaces={'SA4': 'WFS'})[0].text
        }

    def _get_state_details(root):
        return {
            'wkt': '<http://www.opengis.net/def/crs/EPSG/0/3857>; POLYGON(({}))'.format(coords_wkt),
            'object_id': root.xpath('//STATE:OBJECTID', namespaces={'STATE': 'WFS'})[0].text,
            'name': root.xpath('//SA4:STATE_NAME_2016', namespaces={'SA4': 'WFS'})[0].text,
            'albers_area': root.xpath('//STATE:AREA_ALBERS_SQKM', namespaces={'STATE': 'WFS'})[0].text,
            'state': int(root.xpath('//STATE:STATE_CODE_2016', namespaces={'STATE': 'WFS'})[0].text),
            'shape_length': root.xpath('//STATE:Shape_Length', namespaces={'STATE': 'WFS'})[0].text,
            'shape_area': root.xpath('//STATE:Shape_Area', namespaces={'STATE': 'WFS'})[0].text
        }

    # handle any connection exceptions
    try:
        if from_local_file:  # a stub to use a local file for testing
            xml_file = os.path.join(
                os.path.dirname(os.path.dirname(os.path.realpath(__file__))),
                'test',
                asgs_type + '_' + id + '.xml')
            print(xml_file)
            root = etree.parse(xml_file)
        else:
            wfs_uri = get_wfs_query_for_feature_type()
            r = requests.get(wfs_uri)

            # check we have a valid result with an XPath to get the posList (polygon coordinates)
            root = etree.parse(StringIO(r.text))
        try:
            coords = root.xpath('//gml:posList', namespaces={'gml': 'http://www.opengis.net/gml/3.2'})
        except IndexError as e:
            return False, 'No Mesh Block with that ID was found'

        coords_wkt = ''
        c = coords[0].text.strip().split(' ')  # must strip to remove leading ' '

        for i in range(0, len(c), 2):
            coords_wkt += c[i] + ',' + c[i + 1] + ' '

        if asgs_type == 'MB':
            d = _get_mb_details(root)
        elif asgs_type == 'SA1':
            d = _get_sa1_details(root)
        elif asgs_type == 'SA2':
            d = _get_sa2_details(root)
        elif asgs_type == 'SA3':
            d = _get_sa3_details(root)
        elif asgs_type == 'SA4':
            d = _get_sa4_details(root)
        elif asgs_type == 'STATE':
            d = _get_state_details(root)

        return True, d

    except Exception as e:
        return False, str(e)


def make_rdf(uri, profile='asgs'):  # fixed to ASGS profile for now
    # get the ASGS type from the URI
    asgs_type = get_asgs_type(uri)

    if profile == 'asgs':
        g = Graph()
        ASGS = Namespace('http://linked.data.gov.au/def/asgs#')
        g.bind('asgs', ASGS)
        GEO = Namespace('http://www.opengis.net/ont/geosparql#')
        g.bind('geo', GEO)

        # ID & definition of the MB
        mb = URIRef('http://linked.data.gov.au/meshblock/2016/' + mb_obj['object_id'])
        g.add((mb, RDF.type, ASGS.MeshBlock))

        # State - top-level register
        g.add((mb, GEO.sfWithin, URIRef('http://linked.data.gov.au/state/' + STATES[mb_obj['state']])))
        # TODO: add hasState to ASGS ont as a subProperty of sfWithin wth fixed range value being an Aust state individual
        g.add((mb, ASGS.hasState, URIRef('http://linked.data.gov.au/state/' + STATES[mb_obj['state']])))

        # SA1 - 2nd level register
        g.add((mb, GEO.sfWithin, URIRef('http://linked.data.gov.au/dataset/asgs/sa1/' + mb_obj['sa1'])))

        # area
        # TODO: check multiplier on m^2 or km^2
        QUDT = Namespace('http://qudt.org/schema/qudt/')
        g.bind('qudt', QUDT)

        area = BNode()
        g.add((mb, ASGS.hasArea, area))
        g.add((area, QUDT.numericValue, Literal(mb_obj['shape_area'], datatype=XSD.decimal)))
        g.add((area, QUDT.unit, QUDT.SquareMeter))

        # geometry
        geom = BNode()
        g.add((mb, GEO.hasGeometry, geom))
        g.add((geom, RDF.type, GEO.Geometry))
        g.add((geom, GEO.asWKT, Literal(mb_obj['wkt'], datatype=GEO.wktLiteral)))

        return g
    else:
        return None





class Fake:
    def __init__(self, uri):
        self.uri = uri
        self.asgs_type = None

    def get_wfs_query_for_feature_type(self):
        featureid = self.uri.split('/')[-1]
        uri_template = 'https://geo.abs.gov.au/arcgis/services/ASGS2016/{service}/MapServer/WFSServer' \
                       '?service=wfs&version=2.0.0&request=GetFeature&typeName={typename}' \
                       '&Filter=<ogc:Filter><ogc:PropertyIsEqualTo><ogc:PropertyName>{propertyname}</ogc:PropertyName>' \
                       '<ogc:Literal>{featureid}</ogc:Literal>' \
                       '</ogc:PropertyIsEqualTo></ogc:Filter>'

        if self.asgs_type == 'meshblock':
            service = 'MB'
            typename = 'MB:MB'
            propertyname = 'MB:MB_CODE_2016'
        elif self.asgs_type == 'sa1':
            service = 'SA1'
            typename = 'SA1:SA1'
            propertyname = 'SA1:SA1_MAINCODE_2016'
        elif self.asgs_type == 'sa2':
            service = 'SA2'
            typename = 'SA2:SA2'
            propertyname = 'SA2:SA2_MAINCODE_2016'
        elif self.asgs_type == 'sa3':
            service = 'SA3'
            typename = 'SA3:SA3'
            propertyname = 'SA3:SA3_CODE_2016'
        elif self.asgs_type == 'sa4':
            service = 'SA4'
            typename = 'SA4:SA4'
            propertyname = 'SA4:SA4_CODE_2016'
        else:  # state
            service = 'STATE'
            typename = 'STATE:STATE'
            propertyname = 'STATE:STATE_NAME_ABBREV_2016'

        return uri_template.format(**{
            'service': service,
            'typename': typename,
            'propertyname': propertyname,
            'featureid': featureid
        })


if __name__  == '__main__':
    example_uris = {
        'mb': 'http://test.linked.data.gov.au/dataset/asgs/meshblock/80006300000',
        'sa1': 'http://test.linked.data.gov.au/dataset/asgs/sa1/80101100403',
        'sa2': 'http://test.linked.data.gov.au/dataset/asgs/sa2/801011004',
        'sa3': 'http://test.linked.data.gov.au/dataset/asgs/sa3/80101',
        'sa4': 'http://test.linked.data.gov.au/dataset/asgs/sa4/801',
        'state': 'http://test.linked.data.gov.au/dataset/asgs/state/ACT',
    }
    mb_id = '80101100403'

    f = Fake(example_uris['state'])
    print(f.get_wfs_query_for_feature_type())


