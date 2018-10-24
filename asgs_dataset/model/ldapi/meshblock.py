# -*- coding: utf-8 -*-
from asgs_dataset.model.meshblock import MeshBlock
from asgs_dataset.model.ldapi import ASGSClassRenderer
import asgs_dataset._config as config


class MeshBlockRenderer(ASGSClassRenderer):
    ASGS_CLASS = config.URI_MESHBLOCK_CLASS

    def __init__(self, request, identifier, views, *args,
                 default_view_token=None, **kwargs):
        _views = views or {}
        _uri = ''.join([config.URI_MESHBLOCK_INSTANCE_BASE, identifier])
        kwargs.setdefault('asgs_template', 'asgs-MB-en.html')
        super(MeshBlockRenderer, self).__init__(
            request, _uri, _views, *args,
            default_view_token=default_view_token, **kwargs)
        self.identifier = identifier
        self.instance = MeshBlock(self.identifier)


