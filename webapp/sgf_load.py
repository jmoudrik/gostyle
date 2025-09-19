import codecs
import logging

from sgflib import SGFParser

def my_err(exc):
    wrong_part = exc.object[exc.start:exc.end+1]
    try:
        us = wrong_part.decode('utf-8')
        return (us, exc.end+1)
    except:
        diff = exc.end-exc.start 
        if diff > 4:
            logging.warn("sgf_load.py : Long chain of chars (%d) badly encoded."%diff)
        return (u'?'*(exc.end-exc.start), exc.end)

codecs.register_error('my_err', my_err)

class ParseError(Exception):
    pass

def load_sgf_file_headers(filename):
    """Returns list of dictionaries.
    Each dictionary contains all header fields of corresponding gametree."""
    with open(filename, 'r') as f:
        sgfdata = f.read()

    try:
        collection = SGFParser(sgfdata).parse()
    except:
        raise ParseError

    ret = []
    for gametree in collection:
        ret.append(process_gametree(gametree))

    return ret

def list_attributes(node):
    return node.data.keys()

def get_attribute(node, atr):
    try:
        atr = node.data[atr].data[0]
        ret = atr.decode()
        return ret
    except:
        return None

def process_gametree(gametree):
    # cursor for tree traversal
    c = gametree.cursor()
    # first node is the header
    header = c.node

    attributes = list_attributes(header)
    d = {}
    for key in attributes:
        atr = get_attribute(header, key)
        if atr:
            d[key] = atr
    return d

if __name__ == '__main__':

    print load_sgf_file_headers('./files/1930-01-00a.sgf')
