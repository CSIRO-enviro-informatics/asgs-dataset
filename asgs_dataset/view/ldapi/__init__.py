# -*- coding: utf-8 -*-

from flask import render_template, Response, redirect
import pyldapi
from flask_paginate import Pagination
import asgs_dataset._config as config
from asgs_dataset.model import ASGSModel
from asgs_dataset.model.asgs_feature import ASGSFeature

ASGSView = pyldapi.View('ASGS',
    'Basic properties of a Mesh Block using the ASGS ontology and those it imports',
    ['text/html'] + pyldapi.Renderer.RDF_MIMETYPES,
    'text/turtle',
    languages=['en'],
    namespace='http://linked.data.gov.au/def/asgs#'
)
GEOSparqlView = pyldapi.View('GeoSPARQL',
    'A view of GeoSPARQL ontology properties and those of ontologies it imports only',
    pyldapi.Renderer.RDF_MIMETYPES,
    'text/turtle',
    languages=['en'],
    namespace='http://www.opengis.net/ont/geosparql#'
)
WFSView = pyldapi.View('Web Feature Service',
    'An OGC Web Feature Service (WFS) view of a Mesh Block.\n'
    'The ASGS-specific properties are defined in the ASGS product guide.',
    ['application/xml', 'text/xml'],
    'text/xml',
    languages=['en'],
    namespace='https://geo.abs.gov.au/arcgis/services/ASGS2016/MB/MapServer/WFSServer?service=wfs&version=2.0.0&request=GetCapabilities'
)


def render_error(request, e):
    try:
        import traceback
        traceback.print_tb(e.__traceback__)
    except Exception:
        pass
    if isinstance(e, pyldapi.ViewsFormatsException):
        error_type = 'Internal View Format Error'
        error_code = 406
        error_message = e.args[0] or "No message"
    elif isinstance(e, NotImplementedError):
        error_type = 'Not Implemented'
        error_code = 406
        error_message = e.args[0] or "No message"
    elif isinstance(e, RuntimeError):
        error_type = 'Server Error'
        error_code = 500
        error_message = e.args[0] or "No message"
    else:
        error_type = 'Unknown'
        error_code = 500
        error_message = "An Unknown Server Error Occurred."

    resp_text = '''<?xml version="1.0"?>
    <error>
      <errorType>{}</errorType>
      <errorCode>{}</errorCode>
      <errorMessage>{}</errorMessage>
    </error>
    '''.format(error_type, error_code, error_message)
    return Response(resp_text, status=error_code, mimetype='application/xml')


class ASGSClassRenderer(pyldapi.Renderer):
    ASGS_CLASS = None

    def __init__(self, request, uri, views, *args,
                 default_view_token=None, asgs_template=None, **kwargs):
        kwargs.setdefault('alternates_template', 'alternates.html')
        _views = views or {}
        self._add_default_asgs_views(_views)
        if default_view_token is None:
            default_view_token = 'asgs'
        super(ASGSClassRenderer, self).__init__(request, uri, _views, default_view_token, *args, **kwargs)
        try:
            vf_error = self.vf_error
            if vf_error:
                if not hasattr(self, 'view') or not self.view:
                    self.view = 'asgs'
                if not hasattr(self, 'format') or not self.format:
                    self.format = 'text/html'
        except AttributeError:
            pass
        self.asgs_template = asgs_template
        #self.identifier = None  # inheriting classes will need to add the Identifier themselves.
        #self.instance = None  # inheriting classes will need to add the Instance themselves.

    def render(self):
        response = super(ASGSClassRenderer, self).render()
        if response is not None:
            return response
        try:
            if self.view == 'asgs':
                return self._render_asgs_view()
            elif self.view == 'wfs':
                return self._render_wfs_view()
            elif self.view == 'geosparql':
                return self._render_geosparql_view()
            else:
                fn = getattr(self, '_render_{}_view'.format(str(self.view).lower()), None)
                if fn:
                    return fn()
                else:
                    raise RuntimeError("No renderer for view '{}'.".format(self.view))
        except Exception as e:
            from flask import request
            return render_error(request, e)

    def _render_asgs_view(self):
        if self.format == 'text/html':
            return self._render_asgs_view_html()
        elif self.format in ASGSClassRenderer.RDF_MIMETYPES:
            return self._render_asgs_view_rdf()
        else:
            raise RuntimeError("Cannot render 'asgs' View with format '{}'.".format(self.format))

    def _render_asgs_view_html(self, template_context=None):
        geometry = self.instance.geometry
        if len(geometry) > 0:
            (w, s, e, n) = self.instance.get_bbox()  # (minx, miny, maxx, maxy)
            bbox = [[w,s],[e,n]]
        else:
            bbox = None
        _template_context = {
            'uri': self.uri,
            'geometry': geometry,
            'bbox': bbox,
            'instance_id': self.identifier
        }
        if template_context is not None and len(template_context) > 0:
            _template_context.update(template_context)
        return Response(render_template(
            self.asgs_template,
            **_template_context
            ),
            headers=self.headers)

    def _render_asgs_view_rdf(self):
        g = self.instance._get_instance_rdf(profile='asgs')
        if self.format in ['application/ld+json', 'application/json']:
            serial_format = 'json-ld'
        elif self.format in self.RDF_MIMETYPES:
            serial_format = self.format
        else:
            serial_format = 'text/turtle'
            self.format = serial_format
        return Response(g.serialize(format=serial_format), mimetype=self.format, headers=self.headers)

    def _render_wfs_view(self):
        if self.format == 'text/html':
            return "Cannot create a HTML representation of a WFS view. Use application/xml."
        elif self.format in ['application/xml', 'text/xml']:
            return self._render_wfs_view_xml()
        else:
            raise RuntimeError("Cannot render 'wfs' View with format '{}'.".format(self.format))

    def _render_wfs_view_xml(self):
        return redirect(self.instance.get_wfs_query_for_feature_type(), 303)

    def _render_geosparql_view(self):
        if self.format == 'text/html':
            return "Cannot create a HTML representation of a GeoSPARQL View. Use an RDF format."
        elif self.format in ASGSClassRenderer.RDF_MIMETYPES:
            return self._render_geosparql_view_rdf()
        else:
            raise RuntimeError("Cannot render 'geosparql' View with format '{}'.".format(self.format))

    def _render_geosparql_view_rdf(self):
        g = self.instance._get_instance_rdf(profile='geosparql')
        if self.format in ['application/ld+json', 'application/json']:
            serial_format = 'json-ld'
        elif self.format in self.RDF_MIMETYPES:
            serial_format = self.format
        else:
            serial_format = 'text/turtle'
            self.format = serial_format
        return Response(
            g.serialize(format=serial_format), mimetype=self.format,
            headers=self.headers)

    @classmethod
    def _add_default_asgs_views(cls, _views):
        if 'asgs' in _views.keys():
            raise pyldapi.ViewsFormatsException(
                 'You must not manually add a view with token \'asgs\' as this is auto-created.'
            )
        if 'geosparql' in _views.keys():
            raise pyldapi.ViewsFormatsException(
                'You must not manually add a view with token \'geosparql\' as this is auto-created.'
            )
        if 'wfs' in _views.keys():
            raise pyldapi.ViewsFormatsException(
                'You must not manually add a view with token \'wfs\' as this is auto-created.'
            )
        _views['asgs'] = ASGSView
        _views['geosparql'] = GEOSparqlView
        _views['wfs'] = WFSView


class ASGSRegisterRenderer(pyldapi.RegisterRenderer):

    def __init__(self, _request, uri, label, comment, contained_item_classes,
                 register_total_count, asgs_model_class, *args, views=None,
                 default_view_token=None, **kwargs):
        kwargs.setdefault('alternates_template', 'alternates.html')
        kwargs.setdefault('register_template', 'register.html')
        super(ASGSRegisterRenderer, self).__init__(
            _request, uri, label, comment, None, contained_item_classes,
            register_total_count, *args, views=views,
            default_view_token=default_view_token, **kwargs)
        if asgs_model_class is not None:
            assert issubclass(asgs_model_class, ASGSModel)
        self.asgs_model_class = asgs_model_class
        try:
            vf_error = self.vf_error
            if vf_error:
                if not hasattr(self, 'view') or not self.view:
                    self.view = 'reg'
                if not hasattr(self, 'format') or not self.format:
                    self.format = 'text/html'
        except AttributeError:
            pass
        if self.view != "alternates" and asgs_model_class is not None:
            items = self.asgs_model_class.get_index(uri, self.page, self.per_page)
            for item_id in items:
                item_id = str(item_id)
                uri = ''.join([self.uri, item_id])
                # local_uri = self.asgs_model_class.make_local_url(uri, item_id)
                label = self.asgs_model_class.make_instance_label(uri, item_id)
                self.register_items.append((uri, label, item_id))

    def render(self):
        try:
            return super(ASGSRegisterRenderer, self).render()
        except Exception as e:
            from flask import request
            return render_error(request, e)

    def _render_reg_view_html(self, template_context=None):
        if self.asgs_model_class:
            register_view_items = [
                (self.asgs_model_class.make_local_url(uri, identifier), label)
                for uri, label, identifier in self.register_items
            ]
        else:
            try:
                register_view_items = [
                    (ASGSFeature.make_local_url(uri, identifier), label)
                    for uri, label, identifier in self.register_items
                ]
            except Exception as e:
                register_view_items = self.register_items
        _template_context = {
            'model': self.asgs_model_class,
            'register_items': register_view_items
        }
        if template_context is not None and isinstance(template_context, dict):
            _template_context.update(template_context)

        return super(ASGSRegisterRenderer, self).\
            _render_reg_view_html(template_context=_template_context)


class ASGSRegisterOfRegistersRenderer(pyldapi.RegisterOfRegistersRenderer):
    pass
