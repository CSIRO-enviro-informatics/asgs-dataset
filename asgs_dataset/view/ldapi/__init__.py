# -*- coding: utf-8 -*-

from flask import render_template, Response, redirect

import pyldapi
from asgs_dataset.model import ASGSModel, NotFoundError
from asgs_dataset.model.asgs_feature import ASGSFeature

ASGSView = pyldapi.View('ASGS',
    'View of an ASGS Feature using the ASGS ontology and those it imports',
    ['text/html', '_internal'] + pyldapi.Renderer.RDF_MIMETYPES,
    'text/turtle',
    languages=['en'],
    namespace='http://linked.data.gov.au/def/asgs#'
)
LOCIView = pyldapi.View('LOCI',
    'View of an ASGS Feature using a mixture of ASGS ontology and LOCI harmonised properties',
    ['text/html', '_internal'] + pyldapi.Renderer.RDF_MIMETYPES,
    'text/turtle',
    languages=['en'],
    namespace='http://linked.data.gov.au/def/loci#'
)
GEOSparqlView = pyldapi.View('GeoSPARQL',
    'A view of GeoSPARQL ontology properties and those of ontologies it imports only',
    pyldapi.Renderer.RDF_MIMETYPES,
    'text/turtle',
    languages=['en'],
    namespace='http://www.opengis.net/ont/geosparql#'
)
WFSView = pyldapi.View('Web Feature Service',
    'An OGC Web Feature Service (WFS) view of an ASGS Feature.\n'
    'The ASGS-specific properties are defined in the ASGS product guide.',
    ['application/xml', 'text/xml'],
    'text/xml',
    languages=['en'],
    namespace='https://geo.abs.gov.au/arcgis/services/ASGS2016/MB/MapServer/WFSServer?service=wfs&version=2.0.0&request=GetCapabilities'
)


def render_error(request, e):
    try:
        print(e)
        import traceback
        traceback.print_tb(e.__traceback__)
    except Exception:
        pass
    if isinstance(e, pyldapi.ViewsFormatsException):
        error_type = 'Internal View Format Error'
        error_code = 406
        error_message = e.args[0] or "No message"
    elif isinstance(e, NotFoundError):
        error_type = 'Feature Not Found'
        error_code = 404
        error_message = "Feature Not Found"
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
            default_view_token = 'loci'
        super(ASGSClassRenderer, self).__init__(request, uri, _views, default_view_token, *args, **kwargs)
        try:
            vf_error = self.vf_error
            if vf_error:
                if not hasattr(self, 'view') or not self.view:
                    self.view = 'loci'
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
            instance = self.instance
            if instance is None:
                instance = NotFoundError()
            if isinstance(instance, Exception):
                from flask import request
                return render_error(request, instance)
        except AttributeError:
            pass
        try:
            if self.view in {'asgs', 'loci'}:
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
        if self.format == "_internal":
            return self
        if self.format == 'text/html':
            return self._render_asgs_view_html()
        elif self.format in ASGSClassRenderer.RDF_MIMETYPES:
            return self._render_asgs_view_rdf()
        else:
            profile = self.view
            raise RuntimeError("Cannot render '{}' View with format '{}'.".format(profile, self.format))

    def _render_asgs_view_html(self, template_context=None):
        # Renders both the 'asgs' view or the 'loci' view
        _template_context = {
            'uri': self.uri,
        }
        if template_context is not None and len(template_context) > 0:
            _template_context.update(template_context)
        return Response(render_template(
            self.asgs_template,
            **_template_context
            ),
            headers=self.headers)

    def _render_asgs_view_rdf(self, g=None):
        # Renders both the 'asgs' view or the 'loci' view
        if g is None:
            profile = self.view
            try:
                i = self.instance
                g = i._get_instance_rdf(profile=profile)
            except AttributeError:
                raise RuntimeError("ASGS RDF Renderer doesn't know which graph to render")
        if self.format in {'application/ld+json', 'application/json'}:
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

    def _render_geosparql_view_rdf(self, g=None):
        if g is None:
            profile = 'geosparql'
            try:
                i = self.instance
                g = i._get_instance_rdf(profile=profile)
            except AttributeError:
                raise RuntimeError("Geosparql RDF Renderer doesn't know which graph to render")

        if self.format in {'application/ld+json', 'application/json'}:
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
        if 'loci' in _views.keys():
            raise pyldapi.ViewsFormatsException(
                 'You must not manually add a view with token \'loci\' as this is auto-created.'
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
        _views['loci'] = LOCIView
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
            make_local_url = self.asgs_model_class.make_local_url
        else:
            make_local_url = ASGSFeature.make_local_url
        try:
            register_view_items = [
                (make_local_url(uri, identifier), label)
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
