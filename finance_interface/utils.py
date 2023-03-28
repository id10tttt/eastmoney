# -*- coding: utf-8 -*-
import re
import copy
import warnings
from types import GeneratorType
from odoo.tools import config
import redis
import six


def get_redis_client(db):
    return redis.Redis(db=db, password=config.get('redis_password'), port=config.get('redis_port'))


class SortedDict(dict):
    """
    A dictionary that keeps its keys in the order in which they're inserted.
    """

    def __new__(cls, *args, **kwargs):
        instance = super(SortedDict, cls).__new__(cls, *args, **kwargs)
        instance.keyOrder = []
        return instance

    def __init__(self, data=None):
        if data is None:
            data = {}
        elif isinstance(data, GeneratorType):
            # Unfortunately we need to be able to read a generator twice.  Once
            # to get the data into self with our super().__init__ call and a
            # second time to setup keyOrder correctly
            data = list(data)
        super(SortedDict, self).__init__(data)
        if isinstance(data, dict):
            self.keyOrder = list(data)
        else:
            self.keyOrder = []
            seen = set()
            for key, value in data:
                if key not in seen:
                    self.keyOrder.append(key)
                    seen.add(key)

    def __deepcopy__(self, memo):
        return self.__class__([(key, copy.deepcopy(value, memo))
                               for key, value in self.iteritems()])

    def __copy__(self):
        # The Python's default copy implementation will alter the state
        # of self. The reason for this seems complex but is likely related to
        # subclassing dict.
        return self.copy()

    def __setitem__(self, key, value):
        if key not in self:
            self.keyOrder.append(key)
        super(SortedDict, self).__setitem__(key, value)

    def __delitem__(self, key):
        super(SortedDict, self).__delitem__(key)
        self.keyOrder.remove(key)

    def __iter__(self):
        return iter(self.keyOrder)

    def pop(self, k, *args):
        result = super(SortedDict, self).pop(k, *args)
        try:
            self.keyOrder.remove(k)
        except ValueError:
            # Key wasn't in the dictionary in the first place. No problem.
            pass
        return result

    def popitem(self):
        result = super(SortedDict, self).popitem()
        self.keyOrder.remove(result[0])
        return result

    def _iteritems(self):
        for key in self.keyOrder:
            yield key, self[key]

    def _iterkeys(self):
        for key in self.keyOrder:
            yield key

    def _itervalues(self):
        for key in self.keyOrder:
            yield self[key]

    iteritems = _iteritems
    iterkeys = _iterkeys
    itervalues = _itervalues

    def items(self):
        return list(self.iteritems())

    def keys(self):
        return list(self.iterkeys())

    def values(self):
        return list(self.itervalues())

    def update(self, dict_):
        for k, v in six.iteritems(dict_):
            self[k] = v

    def setdefault(self, key, default):
        if key not in self:
            self.keyOrder.append(key)
        return super(SortedDict, self).setdefault(key, default)

    def value_for_index(self, index):
        """Returns the value of the item at the given zero-based index."""
        # This, and insert() are deprecated because they cannot be implemented
        # using collections.OrderedDict (Python 2.7 and up), which we'll
        # eventually switch to
        warnings.warn(
            "SortedDict.value_for_index is deprecated", PendingDeprecationWarning,
            stacklevel=2
        )
        return self[self.keyOrder[index]]

    def insert(self, index, key, value):
        """Inserts the key, value pair before the item with the given index."""
        warnings.warn(
            "SortedDict.insert is deprecated", PendingDeprecationWarning,
            stacklevel=2
        )
        if key in self.keyOrder:
            n = self.keyOrder.index(key)
            del self.keyOrder[n]
            if n < index:
                index -= 1
        self.keyOrder.insert(index, key)
        super(SortedDict, self).__setitem__(key, value)

    def copy(self):
        """Returns a copy of this object."""
        # This way of initializing the copy means it works for subclasses, too.
        return self.__class__(self)

    def __repr__(self):
        """
        Replaces the normal dict.__repr__ with a version that returns the keys
        in their sorted order.
        """
        return '{%s}' % ', '.join(['%r: %r' % (k, v) for k, v in self.iteritems()])

    def clear(self):
        super(SortedDict, self).clear()
        self.keyOrder = []


class ConstType(type):
    def __new__(cls, name, bases, attrs):
        attrs_value = {}
        attrs_label = {}
        new_attrs = {}
        labels_to_values = {}

        for k, v in attrs.items():
            if k.startswith('__'):
                continue
            if isinstance(v, tuple):
                attrs_value[k] = v[0]
                attrs_label[k] = v[1]
                new_attrs[v[0]] = v[1]
                labels_to_values[v[1]] = v[0]
            elif isinstance(v, dict) and 'label' in v:
                attrs_value[k] = v['value']
                attrs_label[k] = v['label']
                labels_to_values[v['label']] = v['value']
                new_attrs[v['value']] = v['label']
            else:
                attrs_value[k] = v
                attrs_label[k] = v

        sort_new_attrs = sorted(six.iteritems(new_attrs), key=lambda kv: k[0])
        new_attrs = SortedDict(sort_new_attrs)

        obj = type.__new__(cls, name, bases, attrs_value)
        obj.values = attrs_value
        obj.labels = attrs_label
        obj.labels_to_values = labels_to_values
        obj.attrs = new_attrs
        return obj


class Const(six.with_metaclass(ConstType)):
    pass


class GoodsRecommendStatus(Const):
    normal = (False, u'普通')
    recommend = (True, u'推荐')


class OrderStatus(Const):
    closed = ('closed', u'已关闭')
    unpaid = ('unpaid', u'待支付')
    pending = ('pending', u'待发货')
    unconfirmed = ('unconfirmed', u'待收货')
    unevaluated = ('unevaluated', u'待评价')
    completed = ('completed', u'已完成')


class OrderRequestStatus(Const):
    closed = (-1, 'closed')
    unpaid = (0, 'unpaid')
    pending = (1, 'pending')
    unconfirmed = (2, 'unconfirmed')
    unevaluated = (3, 'unevaluated')
    completed = (4, 'completed')


class OrderResponseStatus(Const):
    closed = ('closed', -1)
    unpaid = ('unpaid', 0)
    pending = ('pending', 1)
    unconfirmed = ('unconfirmed', 2)
    unevaluated = ('unevaluated', 3)
    completed = ('completed', 4)


class BannerStatus(Const):
    visible = (True, u'显示')
    invisible = (False, u'不显示')


class WechatUserRegisterType(Const):
    app = ('app', u'小程序')
    gzh = ('gzh', u'公众号')


class WechatUserStatus(Const):
    default = ('default', u'默认')


class PaymentStatus(Const):
    unpaid = ('unpaid', '未支付')
    success = ('success', '成功')
    fail = ('fail', '失败')


def hump2underline(hunp_str):
    '''
    驼峰形式字符串转成下划线形式
    :param hunp_str: 驼峰形式字符串
    :return: 字母全小写的下划线形式字符串
    '''
    p = re.compile(r'([a-z]|\d)([A-Z])')
    sub = re.sub(p, r'\1_\2', hunp_str).lower()
    return sub


def underline2hump(underline_str):
    '''
    下划线形式字符串转成驼峰形式
    :param underline_str: 下划线形式字符串
    :return: 驼峰形式字符串
    '''
    sub = re.sub(r'(_\w)', lambda x: x.group(1)[1].upper(), underline_str)
    return sub


def get_precision():
    return 16, 2
