from m.ext import Extension
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Query, class_mapper
from sqlalchemy.orm.exc import UnmappedClassError
from math import ceil
from datetime import datetime
from pyhocon import ConfigException
from webob.exc import HTTPNotFound


class Model:
    query_class = None
    query = None

    def dictify(self, found=None, relationships=True, exclude=None):
        if found is None:
            found = set()
        if exclude is None:
            exclude = set()
        result = {}
        mapper = class_mapper(self.__class__)
        columns = [column.key for column in mapper.columns]
        for column in columns:
            if column in exclude:
                continue
            value = getattr(self, column)
            if isinstance(value, datetime):
                result[column] = value.isoformat()
            else:
                result[column] = value
        if relationships:
            for name, relation in mapper.relationships.items():
                if relation not in found:
                    found.add(relation)
                    related_obj = getattr(self, name)
                    prefix = '{}.'.format(name)
                    if related_obj is not None:
                        _exclude = {x.replace(prefix, '', 1) for x in exclude if x.startswith(prefix)}
                        if relation.uselist:
                            result[name] = [o.dictify(found=found, exclude=_exclude) for o in related_obj]
                        else:
                            result[name] = related_obj.dictify(found=found, exclude=_exclude)
        return result


class Pagination:
    def __init__(self, page, size, total, items):
        self.page = page
        self.items = items
        self.size = size
        self.total = total
        self.pages = int(ceil(self.total / float(self.size)))
        self.has_prev = self.page > 1
        self.has_next = self.page < self.pages

    def dictify(self, relationships=True, exclude=None):
        return {
            'page': self.page,
            'size': self.size,
            'total': self.total,
            'pages': self.pages,
            'has_prev': self.has_prev,
            'has_next': self.has_next,
            'items': [item.dictify(relationships=relationships, exclude=exclude) for item in self.items]
        }


class BaseQuery(Query):
    def first_or_404(self, detail=''):
        ret = self.first()
        if ret is None:
            raise HTTPNotFound(detail=detail)
        return ret

    def paginate(self, page=1, size=50):
        total = self.count()
        items = self.offset((page-1)*size).limit(size).all()
        return Pagination(page, size, total, items)


class _QueryProperty(object):
    def __init__(self, sa):
        self.sa = sa

    def __get__(self, obj, type):
        try:
            mapper = class_mapper(type)
            if mapper:
                return type.query_class(mapper, session=self.sa.session)
        except UnmappedClassError:
            return None


class SQLAlchemy(Extension):
    def __init__(self, app=None, **kwargs):
        super().__init__(**kwargs)
        self.app = app
        self.prefix = kwargs.get('config_prefix', 'sqlalchemy')
        if app:
            self.initialize(app)
        self._model = declarative_base(cls=Model, name='Model')
        self._engine = None
        self._session = None
        self._url = 'sqlite:///'
        self._params = {}

    def initialize(self, app):
        super().initialize(app)
        try:
            config = self.app.config.get_config(self.prefix)
            self._url = config.get_string('url', 'sqlite:///')
            self._params = {'echo': config.get_bool('echo', False)}
            try:
                self._params['encode'] = config.get_string('encode')
            except ConfigException:
                pass
            try:
                self._params['pool_size']= config.get_int('pool.size')
            except ConfigException:
                pass
            try:
                self._params['pool_size']=config.get_int('pool.size')
            except ConfigException:
                pass
            try:
                self._params['pool_recycle'] = config.get_int('pool.recycle')
            except ConfigException:
                pass
            try:
                self._params['pool_timeout'] = config.get_int('pool.timeout')
            except ConfigException:
                pass
            try:
                self._params['max_overflow'] = config.get_int('pool.overflow')
            except ConfigException:
                pass
        except ConfigException:
            pass
        self._engine = create_engine(self._url, **self._params)
        self._session = sessionmaker(bind=self._engine)()
        self._model.query_class = BaseQuery
        self._model.query = _QueryProperty(self)
        self._model.metadata.bind = self._engine

    @property
    def Model(self):
        return self._model

    @property
    def metadata(self):
        return self.Model.metadata

    @property
    def session(self):
        if self.initialized:
            return self._session
        raise Exception('not initialized')

