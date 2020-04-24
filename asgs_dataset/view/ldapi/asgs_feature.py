# -*- coding: utf-8 -*-
from asgs_dataset.model import NotFoundError
from asgs_dataset.model import asgs_feature
from asgs_dataset.view.ldapi import ASGSClassRenderer
import asgs_dataset._config as config


class ASGSFeatureRenderer(ASGSClassRenderer):
    ASGS_CLASS = config.URI_ASGSFEATURE_CLASS

    def __init__(self, request, identifier, views, *args,
                 default_view_token=None, **kwargs):
        _views = views or {}
        if identifier.startswith("http:") or identifier.startswith("https:"):
            _uri = identifier
            identifier = _uri.split('/')[-1]
        else:
            _uri = ''.join([config.URI_ASGSFEATURE_INSTANCE_BASE, identifier])
        self.identifier = identifier
        try:
            self.instance = asgs_feature.ASGSFeature(_uri)
            kwargs.setdefault('asgs_template',
                              'asgs-' + self.instance.asgs_type + '-en.html')
        except Exception as e:
            self.instance = e
            kwargs.setdefault('asgs_template',
                              'asgs-error-en.html')
        super(ASGSFeatureRenderer, self).__init__(
            request, _uri, _views, *args,
            default_view_token=default_view_token, **kwargs)
        if isinstance(self.instance, Exception) and self.view == "_internal":
            raise self.instance

    def _render_asgs_view_html(self, template_context=None):
        # Adds more template-context stuff from ASGSFeature,
        # to augment the asgs_view renderer in ASGSClassRenderer
        _template_context = {
            'deets': self.instance.properties,
            'instance_id': self.identifier
        }
        geometry = self.instance.geometry
        if len(geometry) > 0:
            (w, s, e, n) = self.instance.get_bbox()  # (minx, miny, maxx, maxy)
            bbox = [[w,s],[e,n]]
            _template_context.update({
                'geometry': geometry,
                'bbox': bbox,
            })
        else:
            _template_context.update({
                'geometry': None,
                'bbox': None,
            })
        if asgs_feature.STATES_USE_NAMEABBREV:
            _template_context['STATES_USE_NAMEABBREV'] = True
        if template_context is not None and len(template_context) > 0:
            _template_context.update(template_context)
        return super(ASGSFeatureRenderer, self).\
            _render_asgs_view_html(_template_context)

    def _render_asgs_view_rdf(self, g=None):
        # Renders both the 'asgs' view or the 'loci' view
        profile = self.view
        g = self.instance._get_instance_rdf(profile=profile)
        return super(ASGSFeatureRenderer, self)._render_asgs_view_rdf(g=g)

    def _render_geosparql_view_rdf(self, g=None):
        profile = 'geosparql'
        g = self.instance._get_instance_rdf(profile=profile)
        return super(ASGSFeatureRenderer, self)._render_geosparql_view_rdf(g=g)

    def _render_alternates_view_html(self, template_context=None):
        _template_context = {
            'uri': self.instance.make_local_url(self.uri, self.identifier),
        }
        if template_context is not None and isinstance(template_context, dict):
            _template_context.update(template_context)
        return super(ASGSFeatureRenderer, self).\
            _render_alternates_view_html(_template_context)
