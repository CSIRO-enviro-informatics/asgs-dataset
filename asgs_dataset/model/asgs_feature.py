from flask import Response, render_template, redirect, url_for
from rdflib import Graph, URIRef, Namespace, RDF, RDFS, XSD, OWL, Literal, BNode
from pyldapi import Renderer, View
import asgs_dataset._config as conf
from lxml import objectify
from lxml import etree
import requests
from io import StringIO, BytesIO
import os
from asgs_dataset.model import ASGSModel
from asgs_dataset.model.lookups import *


class ASGSFeature(ASGSModel):

    @classmethod
    def make_instance_label(cls, instance_id):
        return "asgs feature #{}".format(instance_id)

    @classmethod
    def get_index(cls, base_uri, page, per_page):
        per_page = max(int(per_page), 1)
        offset = (max(int(page), 1)-1)*per_page
        asgs_type = cls.determine_asgs_type(base_uri)
        return cls.get_feature_index(asgs_type, offset, per_page)

    @classmethod
    def make_canonical_uri(cls, instance_uri, instance_id):
        return instance_uri

    @classmethod
    def make_local_url(cls, instance_uri, instance_id):
        return url_for("controller.object", uri=instance_uri)

    def __init__(self, uri):
        super(ASGSFeature, self).__init__()
        # split ID out of URI for all ASGS Features
        self.uri = uri
        self.id = uri.split('/')[-1]

        # create at least these views for all ASGS Features
        self._assign_asgs_type()


    @classmethod
    def determine_asgs_type(cls, instance_uri):
        if '/meshblock/' in instance_uri:
            return 'MB'
        elif '/sa1/' in instance_uri:
            return 'SA1'
        elif '/sa2/' in instance_uri:
            return 'SA2'
        elif '/sa3/' in instance_uri:
            return 'SA3'
        elif '/sa4/' in instance_uri:
            return 'SA4'
        else:  # state
            return 'STATE'

    def _assign_asgs_type(self):
        self.asgs_type = self.determine_asgs_type(self.uri)

    def _get_instance_details(self, from_local_file=True):

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
                'name_abbrev': root.xpath('//STATE:STATE_NAME_ABBREV_2016', namespaces={'STATE': 'WFS'})[0].text,
                'albers_area': root.xpath('//STATE:AREA_ALBERS_SQKM', namespaces={'STATE': 'WFS'})[0].text,
                'state': int(root.xpath('//STATE:STATE_CODE_2016', namespaces={'STATE': 'WFS'})[0].text),
                'shape_length': root.xpath('//STATE:Shape_Length', namespaces={'STATE': 'WFS'})[0].text,
                'shape_area': root.xpath('//STATE:Shape_Area', namespaces={'STATE': 'WFS'})[0].text
            }
        # handle any connection exceptions
        try:
            root = None
            if from_local_file:  # a stub to use a local file for testing
                xml_file = os.path.join(
                    os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))),
                    'test',
                    self.asgs_type + '_' + self.id + '.xml')
                try:
                    root = etree.parse(xml_file)
                except (FileNotFoundError, OSError):
                    root = None
                except Exception as e:
                    print(e)
            if root is None:
                wfs_uri = self.get_wfs_query_for_feature_type()
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

            if self.asgs_type == 'MB':
                d = _get_mb_details(root)
            elif self.asgs_type == 'SA1':
                d = _get_sa1_details(root)
            elif self.asgs_type == 'SA2':
                d = _get_sa2_details(root)
            elif self.asgs_type == 'SA3':
                d = _get_sa3_details(root)
            elif self.asgs_type == 'SA4':
                d = _get_sa4_details(root)
            elif self.asgs_type == 'STATE':
                d = _get_state_details(root)
            else:
                raise RuntimeError()

            return True, d

        except Exception as e:
            return False, str(e)

    def _get_instance_rdf(self, profile='asgs'):  # fixed to asgs profile for now
        deets = self._get_instance_details()
        if not deets[0]:  # i.e. we have don't a result
            return Response(deets[1], status=500, mimetype='text/plain')

        if profile == 'asgs':
            g = Graph()
            ASGS = Namespace('http://linked.data.gov.au/def/asgs#')
            g.bind('asgs', ASGS)
            GEO = Namespace('http://www.opengis.net/ont/geosparql#')
            g.bind('geo', GEO)

            # ID & definition of the MB
            mb = URIRef(self.uri)
            g.add((mb, RDF.type, ASGS.MeshBlock))

            # State - top-level register
            g.add((mb, GEO.sfWithin, URIRef('http://linked.data.gov.au/state/' + STATES[deets[1]['state']])))
            # TODO: add hasState to ASGS ont as a subProperty of sfWithin wth fixed range value being an Aust state individual
            g.add((mb, ASGS.hasState, URIRef('http://linked.data.gov.au/state/' + STATES[deets[1]['state']])))

            # SA1 - 2nd level register
            g.add((mb, GEO.sfWithin, URIRef('http://linked.data.gov.au/dataset/asgs/sa1/' + deets[1]['sa1'])))

            # area
            # TODO: check multiplier on m^2 or km^2
            QUDT = Namespace('http://qudt.org/schema/qudt/')
            g.bind('qudt', QUDT)

            area = BNode()  # must be a qudt:QuantityValue as per QUDT
            # qudt:Quantity qudt:quantityValue qudt:QuantityValue
            #               qudt:QuantityKind
            # qudt:QuantityKind qudt:symbol (max 1) xsd:string ($\\ohm$) -> owl:DatatypeProperty , qudt:latexMathString
            # qudt:QuantityKind qudt:abbreviation (max 1) xsd:string (ohm) -> owl:DatatypeProperty
            g.add((mb, ASGS.hasArea, area))
            g.add((area, QUDT.numericValue, Literal(deets[1]['shape_area'], datatype=XSD.decimal)))
            g.add((area, QUDT.unit, QUDT.SquareMeter))

            # geometry
            geom = BNode()
            g.add((mb, GEO.hasGeometry, geom))
            g.add((geom, RDF.type, GEO.Geometry))
            g.add((geom, GEO.asWKT, Literal(deets[1]['wkt'], datatype=GEO.wktLiteral)))
        # TODO: add in these other views
        # elif profile == 'geosparql':
        # elif profile == 'schemaorg':
        # elif profile == 'wfs':
            return g
        else:
            return NotImplementedError(
                "RDF Export for profile \"{}\" is not implemented.".
                format(profile))

    @staticmethod
    def total_meshblocks():
        return 100  # TODO: replace magic number with real count from Web Service

    @staticmethod
    def total_sa1s():
        return 100  # TODO: replace magic number with real count from Web Service

    @staticmethod
    def total_sa2s():
        return 100  # TODO: replace magic number with real count from Web Service

    @staticmethod
    def total_sa3s():
        return 100  # TODO: replace magic number with real count from Web Service

    @staticmethod
    def total_sa4s():
        return 49  # TODO: replace magic number with real count from Web Service

    @staticmethod
    def total_states():
        return 10

    @classmethod
    def get_feature_index(cls, asgs_type, startindex, count):
        url = cls.get_wfs_query_for_index(asgs_type, startindex, count)
        resp = requests.get(url)
        tree = etree.parse(BytesIO(resp.content)) #type lxml._ElementTree
        if asgs_type == 'MB':
            propertyname = 'MB:MB_CODE_2016'
        elif asgs_type == 'SA1':
            propertyname = 'SA1:SA1_MAINCODE_2016'
        elif asgs_type == 'SA2':
            propertyname = 'SA2:SA2_MAINCODE_2016'
        elif asgs_type == 'SA3':
            propertyname = 'SA3:SA3_CODE_2016'
        elif asgs_type == 'SA4':
            propertyname = 'SA4:SA4_CODE_2016'
        else:  # state
            propertyname = 'STATE:STATE_CODE_2016'
        items = tree.xpath('//{}/text()'.format(propertyname), namespaces=tree.getroot().nsmap)
        return items


    @classmethod
    def get_wfs_query_for_index(cls, asgs_type, startindex, count):
        uri_template = 'https://geo.abs.gov.au/arcgis/services/ASGS2016/{service}/MapServer/WFSServer' \
                       '?service=wfs&version=2.0.0&request=GetFeature&typeName={typename}' \
                       '&propertyName={propertyname}' \
                       '&sortBy={propertyname}&startIndex={startindex}&count={count}'
        if asgs_type == 'MB':
            service = 'MB'
            typename = 'MB:MB'
            propertyname = 'MB:MB_CODE_2016'
        elif asgs_type == 'SA1':
            service = 'SA1'
            typename = 'SA1:SA1'
            propertyname = 'SA1:SA1_MAINCODE_2016'
        elif asgs_type == 'SA2':
            service = 'SA2'
            typename = 'SA2:SA2'
            propertyname = 'SA2:SA2_MAINCODE_2016'
        elif asgs_type == 'SA3':
            service = 'SA3'
            typename = 'SA3:SA3'
            propertyname = 'SA3:SA3_CODE_2016'
        elif asgs_type == 'SA4':
            service = 'SA4'
            typename = 'SA4:SA4'
            propertyname = 'SA4:SA4_CODE_2016'
        else:  # state
            service = 'STATE'
            typename = 'STATE:STATE'
            propertyname = 'STATE:STATE_CODE_2016'

        return uri_template.format(**{
            'service': service,
            'typename': typename,
            'propertyname': propertyname,
            'startindex': startindex,
            'count': count
        })

    def get_wfs_query_for_feature_type(self):
        featureid = self.uri.split('/')[-1]
        uri_template = 'https://geo.abs.gov.au/arcgis/services/ASGS2016/{service}/MapServer/WFSServer' \
                       '?service=wfs&version=2.0.0&request=GetFeature&typeName={typename}' \
                       '&Filter=<ogc:Filter><ogc:PropertyIsEqualTo><ogc:PropertyName>{propertyname}</ogc:PropertyName>' \
                       '<ogc:Literal>{featureid}</ogc:Literal>' \
                       '</ogc:PropertyIsEqualTo></ogc:Filter>'

        if self.asgs_type == 'MB':
            service = 'MB'
            typename = 'MB:MB'
            propertyname = 'MB:MB_CODE_2016'
        elif self.asgs_type == 'SA1':
            service = 'SA1'
            typename = 'SA1:SA1'
            propertyname = 'SA1:SA1_MAINCODE_2016'
        elif self.asgs_type == 'SA2':
            service = 'SA2'
            typename = 'SA2:SA2'
            propertyname = 'SA2:SA2_MAINCODE_2016'
        elif self.asgs_type == 'SA3':
            service = 'SA3'
            typename = 'SA3:SA3'
            propertyname = 'SA3:SA3_CODE_2016'
        elif self.asgs_type == 'SA4':
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


class Req:
    def __init__(self, values):
        self.values = values


if __name__ == '__main__':
    fake_req = Req({'_view': None, '_format': None})

    afr = ASGSFeature('http://test.linked.data.gov.au/dataset/asgs/sa4/801')
    print(afr.asgs_type)
    print(afr._get_instance_details(from_local_file=True))

    #print(AsgsFeatureRenderer.get_wfs_query_for_feature_type(
    #    'http://test.linked.data.gov.au/dataset/asgs/meshblock/80006300000'))
    # SA4
    # print(AsgsFeatureRenderer.get_wfs_query_for_feature_type(
    #     'http://test.linked.data.gov.au/dataset/asgs/sa4/801'))
