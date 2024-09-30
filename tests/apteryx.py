import ctypes
from ctypes.util import find_library
import os
# from os.path import normpath, basename

DEBUG = False
UINT64_MAX = 18446744073709551615

c_libc = ctypes.cdll.LoadLibrary(find_library("c"))
c_libc.malloc.argtypes = [ctypes.c_size_t]
c_libc.malloc.restype = ctypes.c_void_p
c_libc.free.argtypes = [ctypes.c_void_p]


class GList(ctypes.Structure):
    pass


GList._fields_ = [
    ("data", ctypes.c_char_p),
    ("next", ctypes.POINTER(GList)),
    ("prev", ctypes.POINTER(GList))
]


class GNode(ctypes.Structure):
    def __init__(self, data, next=None, prev=None, parent=None, children=None):
        super(GNode, self).__init__(data, next, prev, parent, children)


GNode._fields_ = [
    ("data", ctypes.c_char_p),
    ("next", ctypes.POINTER(GNode)),
    ("prev", ctypes.POINTER(GNode)),
    ("parent", ctypes.POINTER(GNode)),
    ("children", ctypes.POINTER(GNode))
]


def dump(self, obj):
    for attr in dir(obj):
        print("obj.%s = %r" % (attr, getattr(obj, attr)))


c_apteryx = ctypes.cdll.LoadLibrary(os.path.abspath(".build/apteryx/libapteryx.so.4"))
c_apteryx.apteryx_init(DEBUG)
c_apteryx_set_full = c_apteryx.apteryx_set_full
c_apteryx_set_full.restype = ctypes.c_bool
c_apteryx_get = c_apteryx.apteryx_get
c_apteryx_get.restype = ctypes.c_char_p
c_apteryx_prune = c_apteryx.apteryx_prune
c_apteryx_prune.restype = ctypes.c_bool
c_apteryx_search = c_apteryx.apteryx_search
c_apteryx_search.restype = ctypes.POINTER(GList)
c_apteryx_set_tree_full = c_apteryx.apteryx_set_tree_full
c_apteryx_set_tree_full.argtypes = [ctypes.POINTER(GNode), ctypes.c_int, ctypes.c_bool]
c_apteryx_set_tree_full.restype = ctypes.c_bool
c_apteryx_get_tree = c_apteryx.apteryx_get_tree
c_apteryx_get_tree.restype = ctypes.POINTER(GNode)


def set(path, value):
    return c_apteryx_set_full(path.encode('utf-8'), value.encode('utf-8'), UINT64_MAX, False)


def get(path):
    return c_apteryx_get(path.encode('utf-8')).decode('utf-8')


def prune(path):
    return c_apteryx_prune(path.encode('utf-8'))


def search(path):
    c_paths = c_apteryx_search(path.encode('utf-8'))
    paths = []
    while bool(c_paths):
        paths.append(c_paths.contents.data.decode('utf-8'))
        c_paths = c_paths.contents.next
    return paths


def set_tree(tree):
    def get_children(children):
        first = None
        last = None
        for key, value in children.items():
            node = GNode(data=key.encode('utf-8'))
            if type(value) is dict:
                node.children = get_children(value)
            else:
                node.children = ctypes.pointer(GNode(data=value.encode('utf-8')))
            if first is None:
                first = node
            if last is not None:
                last.next = ctypes.pointer(node)
            last = node
        return ctypes.pointer(first)
    rname = next(iter(tree))
    c_tree = GNode(data=('/' + rname).encode('utf-8'))
    c_tree.children = get_children(tree[rname])
    return c_apteryx_set_tree_full(c_tree, UINT64_MAX, False)


def get_tree(path):
    def get_children(c_node):
        nodes = {}
        while bool(c_node):
            c_child = c_node.contents.children
            if bool(c_node.contents.children) and bool(c_child.contents.children):
                nodes[c_node.contents.data.decode('utf-8')] = get_children(c_child)
            else:
                nodes[c_node.contents.data.decode('utf-8')] = c_child.contents.data.decode('utf-8')
            c_node = c_node.contents.next
        return nodes
    c_root = c_apteryx_get_tree(path.encode('utf-8'))
    tree = {}
    if bool(c_root):
        key = basename(normpath(c_root.contents.data.decode('utf-8')))
        tree[key] = get_children(c_root.contents.children)
    return tree
