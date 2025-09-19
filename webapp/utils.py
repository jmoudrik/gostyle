import dateutil.parser

import os
import time
import datetime
import logging

import calendar
import misc

def osl_to_html(osl,  player):
    def en_tag(tag, text):
        return "<%s>\n%s\n</%s>" % (tag, text, tag)
    def en_tr(text):
        return en_tag('tr', text)
    def en_td(text):
        return en_tag('td', text)
    def en_b(text):
        return en_tag('b', text)
    
    l = [ "<table class='table table-striped table-condensed'>",
          "<tr>" ] + [
              en_td(en_tag('b', fieldname)) for fieldname in [
                  "#", '', 
                 'Black' ,'', 'White', 'Date', 'Setup', 'Result'
              ]
          ] + [ "</tr>"]
    
    
    for num, (game, color) in enumerate(sorted(osl, key=lambda (g, c):g.sgf_header.get('DT', ''))):
        b, w = game.black.str2(), game.white.str2()
        
        res = game.sgf_header.get('RE', '').lower()
        if res and res[0] == 'b':
            b = en_b(b)
        elif res and res[0] == 'w':
            w = en_b(w)
            
        bicon, wicon, icon = '', '',  '<span class="glyphicon glyphicon-arrow-right"></span>'
        if game.black.player == player:
            bicon = icon
        else:
            wicon = icon
            
        szt = ''
        sz = game.sgf_header.get('SZ', None)
        if sz:
            szt = '%s&times;%s' % (sz, sz)
        kmt = ''
        km = game.sgf_header.get('KM', None)
        if km:
            kmt = 'Komi %s' % km
        
        l.append(en_tr(
            ''.join(map(en_td, [
                    num + 1, 
                    bicon, b,
                    wicon, w, 
                    game.sgf_header.get('DT', ''), 
                    ' '.join(filter(lambda x:x, [
                        szt,
                        kmt
                    ])),
                    game.sgf_header.get('RE', 'Unfinished')
            ]))
        ))

    l.append( "</table>" )
    
    return '\n'.join(l)    

def get_text(stri):
    date =  dateutil.parser.parse(stri)
    return "%s %s" % (calendar.month_name[int(date.month)], date.year)

def get_timespan(osl):
    dates = misc.filter_null( g.sgf_header.get('DT', '') for g, col in osl )
    
    if not dates:
        return ''
    
    start, stop = min(dates), max(dates)
    
    try:
        d_start, d_stop = get_text(start), get_text(stop)
    except:
        return ''
    
    if d_start == d_stop:
        return ", from %s" % d_start
    
    return ", spanning from %s to %s" % ( d_start, d_stop )
    
def remove_old_files(directory, timedelta):
    """Recursively removes all files in @directory that are older than the @timedelta from now"""
    
    if not directory:
        logging.warn("Directory to remove files from not specified, skipping." )
        return
    
    now = datetime.datetime.now()
    logging.info("Removing files older than '%s' in directory '%s'"%(now - timedelta, directory) )
    count = 0
    failed_count = 0
    for dirpath, dirnames, filenames in os.walk(directory):
        for filename in filenames:
            curpath = os.path.join(dirpath, filename)
            file_modified = datetime.datetime.fromtimestamp(os.path.getmtime(curpath))
            if now - file_modified > timedelta:
                try:
                    os.remove(curpath)                
                    count += 1
                    #logging.debug("Removed '%s'."%(curpath,) )
                except OSError as exc:
                    failed_count += 1
                    logging.info("Failure: " + str(exc))
                    
    logging.info("Removed total of %d files."%(count,) )
    if failed_count:
        logging.warn("Removing of %d files failed."%(failed_count,) )

    
    
    
    

