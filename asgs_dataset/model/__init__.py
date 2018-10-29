# -*- coding: utf-8 -*-
from abc import ABCMeta, abstractmethod

class ASGSModel:
    __metaclass__ = ABCMeta

    @classmethod
    @abstractmethod
    def make_instance_label(cls, instance_id):
        raise NotImplementedError()

    @classmethod
    @abstractmethod
    def get_index(cls, base_uri, page, per_page):
        raise NotImplementedError()

    @classmethod
    @abstractmethod
    def make_canonical_uri(cls, instance_uri, instance_id):
        raise NotImplementedError()

    @classmethod
    @abstractmethod
    def make_local_url(cls, instance_uri, instance_id):
        raise NotImplementedError()

    @abstractmethod
    def __init__(self):
        pass


