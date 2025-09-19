import sys
import os
import json
import logging

def load_file(filename):
    with open(filename) as fin:
        dump = json.load(fin)
    
    d = {}
        
    for group_list in dump['group_lists']:
        for player in group_list['list']:
            if player['skip'] != 'yes':
                style = player['style']
                vec = [ style['te'], style['or'], style['ag'], style['th'] ]
                try:
                    vec = map(int, vec)
                except:
                    continue
                
                d[player['name']] = tuple(vec)
                
    return d

def scan_d(directory):
    ds = []
    for dirname, dirnames, filenames in os.walk(directory):
        # print path to all filenames.
        for filename in filenames:
            fn = os.path.join(dirname, filename)
            try:
                ds.append(load_file(fn))
            except:
                logging.warn("Scanning of questionare file '%s' failed, skipping."%fn)
                continue
                
    return ds

if __name__ == '__main__':
    #fn = sys.argv[1]
    #print load_file(fn)
    
    print scan_d('./QUESTIONARE')