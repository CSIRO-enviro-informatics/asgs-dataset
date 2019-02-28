from flask import Response, render_template, url_for
import requests
from io import StringIO, BytesIO

from lxml.etree import XMLSyntaxError
from rdflib import Graph, URIRef, Namespace, RDF, RDFS, XSD, OWL, Literal, BNode
from pyldapi import Renderer, View
import asgs_dataset._config as conf
from lxml import objectify
from lxml import etree
import requests
from io import StringIO
import os

from asgs_dataset.model import ASGSModel
from asgs_dataset.model.lookups import *


class MeshBlock(ASGSModel):
    """
    <wfs:FeatureCollection previous='-1' next='-1' numberMatched='-1' numberReturned='-1' xsi:schemaLocation='WFS https://geo.abs.gov.au/arcgis/services/ASGS2016/MB/MapServer/WFSServer?request=DescribeFeatureType%26version=2.0.0%26typename=MB http://www.opengis.net/wfs/2.0 http://schemas.opengis.net/wfs/2.0/wfs.xsd http://www.opengis.net/gml/3.2 http://schemas.opengis.net/gml/3.2.1/gml.xsd' xmlns:MB='WFS' xmlns:gml='http://www.opengis.net/gml/3.2' xmlns:wfs='http://www.opengis.net/wfs/2.0' xmlns:xlink='http://www.w3.org/1999/xlink' xmlns:xsi='http://www.w3.org/2001/XMLSchema-instance'>
        <gml:boundedBy>
            <gml:Envelope srsName='urn:ogc:def:crs:EPSG:6.9:3857'>
                <gml:lowerCorner>10777612.616999999 -5425372.8682000004</gml:lowerCorner>
                <gml:upperCorner>18701455.709399998 -1022048.4728000015</gml:upperCorner>
            </gml:Envelope>
        </gml:boundedBy>
        <gml:member>
            <MB:MB gml:id='F3__32913'>
                <MB:OBJECTID>32913</MB:OBJECTID>
                <MB:Shape>
                    <gml:MultiSurface srsName="urn:ogc:def:crs:EPSG:6.9:3857">
                        <gml:surfaceMember>
                            <gml:Polygon>
                                <gml:exterior>
                                    <gml:LinearRing>
                                        <gml:posList> 16590981.292599998 -4191104.8922999986 16590954.158799998 -4191133.177099999 16590937.353500001 -4191150.8869999982 16590928.776299998 -4191159.0601999983 16590912.860799998 -4191172.4125999995 16590877.015600003 -4191195.9796999991 16590838.801600002 -4191219.9802000001 16590844.120200001 -4191227.7980999984 16590843.778899997 -4191230.2201999985 16590845.107600003 -4191229.3858999982 16590857.951200001 -4191250.0069000013 16590946.605400003 -4191313.4930999987 16590957.470299996 -4191330.9386 16590981.536499999 -4191344.5130000003 16591041.561499998 -4191306.8068000004 16591073.587300003 -4191290.2685000002 16591129.963600002 -4191246.0223999992 16591124.388999999 -4191205.2289999984 16590991.828400001 -4191110.3057999983 16590990.503799997 -4191109.0203000009 16590981.292599998 -4191104.8922999986</gml:posList>
                                    </gml:LinearRing>
                                </gml:exterior>
                            </gml:Polygon>
                        </gml:surfaceMember>
                    </gml:MultiSurface>
                </MB:Shape>
                <MB:MB_CODE_2016>80006300000</MB:MB_CODE_2016>
                <MB:MB_CATEGORY_CODE_2016>45</MB:MB_CATEGORY_CODE_2016>
                <MB:MB_CATEGORY_NAME_2016>Residential</MB:MB_CATEGORY_NAME_2016>
                <MB:AREA_ALBERS_SQKM>0.0252</MB:AREA_ALBERS_SQKM>
                <MB:SA1_MAINCODE_2016>80101100403</MB:SA1_MAINCODE_2016>
                <MB:STATE_CODE_2016>8</MB:STATE_CODE_2016>
                <MB:DZN_CODE_2016>810041010</MB:DZN_CODE_2016>
                <MB:SSC_CODE_2016>80034</MB:SSC_CODE_2016>
                <MB:NRMR_CODE_2016>801</MB:NRMR_CODE_2016>
                <MB:ADD_CODE_2016>D03</MB:ADD_CODE_2016>
                <MB:Shape_Length>773.99466172015195</MB:Shape_Length>
                <MB:Shape_Area>37893.115782058383</MB:Shape_Area>
            </MB:MB>
        </gml:member>
    </wfs:FeatureCollection>

    <wfs:FeatureCollection previous='-1' next='-1' numberMatched='-1' numberReturned='-1' xsi:schemaLocation='WFS https://geo.abs.gov.au/arcgis/services/ASGS2016/MB/MapServer/WFSServer?request=DescribeFeatureType%26version=2.0.0%26typename=MB http://www.opengis.net/wfs/2.0 http://schemas.opengis.net/wfs/2.0/wfs.xsd http://www.opengis.net/gml/3.2 http://schemas.opengis.net/gml/3.2.1/gml.xsd' xmlns:MB='WFS' xmlns:gml='http://www.opengis.net/gml/3.2' xmlns:wfs='http://www.opengis.net/wfs/2.0' xmlns:xlink='http://www.w3.org/1999/xlink' xmlns:xsi='http://www.w3.org/2001/XMLSchema-instance'>
        <gml:boundedBy>
            <gml:Envelope srsName='urn:ogc:def:crs:EPSG:6.9:3857'>
                <gml:lowerCorner>10777612.616999999 -5425372.8682000004</gml:lowerCorner>
                <gml:upperCorner>18701455.709399998 -1022048.4728000015</gml:upperCorner>
            </gml:Envelope>
        </gml:boundedBy>
    </wfs:FeatureCollection>
    """

    @classmethod
    def make_instance_label(cls, instance_uri, instance_id):
        return "MeshBlock ID: {}".format(str(instance_id))

    @classmethod
    def get_index(cls, base_uri, page, per_page):
        per_page = max(int(per_page), 1)
        offset = (max(int(page), 1) - 1) * per_page
        url_template = 'https://geo.abs.gov.au/arcgis/services/ASGS2011/MB/MapServer/WFSServer' \
                       '?service=wfs&version=2.0.0&request=GetFeature&typeName=MB:MB' \
                       '&propertyName=MB:MB_CODE_2011' \
                       '&sortBy=MB:MB_CODE_2011&startIndex={startindex}&count={count}'
        url = url_template.format(startindex=offset, count=per_page)
        resp = requests.get(url)
        try:
            tree = etree.parse(BytesIO(resp.content))  # type lxml._ElementTree
        except (XMLSyntaxError, TypeError, AttributeError) as e:
            print(e)
            raise e
        items = tree.xpath('//MB:MB_CODE_2011/text()', namespaces=tree.getroot().nsmap)
        return items


    @classmethod
    def make_canonical_uri(cls, instance_uri, instance_id):
        return instance_uri

    @classmethod
    def make_local_url(cls, instance_uri, instance_id):
        return url_for("controller.redirect_meshblock", mb=instance_id)

    def __init__(self, uri):
        super(MeshBlock, self).__init__()
        self.uri = uri
        self.id = uri.split('/')[-1]


    def _get_instance_details(self, from_local_file=False):
        # handle anny connection exceptions
        try:
            root = None
            if from_local_file:  # a stub to use a local file for testing
                xml_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))), 'test', 'mb_' + self.id + '.xml')
                try:
                    root = etree.parse(xml_file)
                except (OSError, FileNotFoundError):
                    root = None
            if root is None:
                wfs_uri =   'https://geo.abs.gov.au/arcgis/services/ASGS2011/MB/MapServer/WFSServer'\
                            '?service=wfs&version=2.0.0&request=GetFeature&typeName=MB:MB'\
                            '&Filter=<ogc:Filter><ogc:PropertyIsEqualTo><ogc:PropertyName>MB:MB_CODE_2011</ogc:PropertyName>'\
                            '<ogc:Literal>{}</ogc:Literal>'\
                            '</ogc:PropertyIsEqualTo></ogc:Filter>'.format(self.id)
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

            d = {
                'wkt': '<http://www.opengis.net/def/crs/EPSG/0/3857>; POLYGON(({}))'.format(coords_wkt),
                'object_id': root.xpath('//MB:MB/MB:MB_CODE_2011', namespaces={'MB': 'WFS'})[0].text,
                # 'category': root.xpath('//MB:MB/MB:MB_CATEGORY_CODE_2011', namespaces={'MB': 'WFS'})[0].text,
                'category_name': root.xpath('//MB:MB/MB:MB_CATEGORY_2011', namespaces={'MB': 'WFS'})[0].text,
                # 'albers_area': root.xpath('//MB:MB/MB:AREA_ALBERS_SQKM', namespaces={'MB': 'WFS'})[0].text,
                'sa1': root.xpath('//MB:MB/MB:SA1_MAINCODE_2011', namespaces={'MB': 'WFS'})[0].text,
                'state': int(root.xpath('//MB:MB/MB:STATE_CODE_2011', namespaces={'MB': 'WFS'})[0].text),
                # 'dzn': root.xpath('//MB:MB/MB:DZN_CODE_2016', namespaces={'MB': 'WFS'})[0].text,
                # 'ssc': root.xpath('//MB:MB/MB:SSC_CODE_2016', namespaces={'MB': 'WFS'})[0].text,
                # 'nrmr': root.xpath('//MB:MB/MB:NRMR_CODE_2016', namespaces={'MB': 'WFS'})[0].text,
                # 'add': root.xpath('//MB:MB/MB:ADD_CODE_2016', namespaces={'MB': 'WFS'})[0].text,
                'gccsa_code': root.xpath('//MB:MB/MB:GCCSA_CODE_2011', namespaces={'MB': 'WFS'})[0].text,
                'shape_length': root.xpath('//MB:MB/MB:Shape_Length', namespaces={'MB': 'WFS'})[0].text,
                'shape_area': root.xpath('//MB:MB/MB:Shape_Area', namespaces={'MB': 'WFS'})[0].text
            }

            return True, d

        except Exception as e:
            return False, str(e)


    @staticmethod
    def total_meshblocks():
        return 100  # TODO: replace magic number with real count from Web Service
