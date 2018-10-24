# -*- coding: utf-8 -*-
from asgs_dataset.model.asgs_feature import ASGSFeature
from asgs_dataset.model.ldapi import ASGSClassRenderer
import asgs_dataset._config as config


class ASGSFeatureRenderer(ASGSClassRenderer):
    ASGS_CLASS = config.URI_ASGSFEATURE_CLASS

    def __init__(self, request, identifier, views, *args,
                 default_view_token=None, **kwargs):
        _views = views or {}
        _uri = ''.join([config.URI_ASGSFEATURE_INSTANCE_BASE, identifier])
        kwargs.setdefault('asgs_template', 'asgs-STATE-en.html')
        super(ASGSFeatureRenderer, self).__init__(
            request, _uri, _views, *args,
            default_view_token=default_view_token, **kwargs)
        self.identifier = identifier
        self.instance = ASGSFeature(self.identifier)

