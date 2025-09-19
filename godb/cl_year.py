import misc 
import numpy
import sqlalchemy
import itertools

import misc
from my_session import my_session_maker
from models import *
import colors
from rank import Rank
import cl_style

import year_select

def get_image_name(year_interval):
    a, b =  year_interval
    return 'year: <%d, %d)'%(a, b)

def create_year_images(s):
    for a, b in year_select.get_all_intervals():
        ida = ImageData(get_image_name((a, b)), numpy.array([(a + b)/2.0]) )
        s.add(ida)
            
def iter_group_by_year(s, gogod, take_first=None):
    """
    Iterates pairs (year, [ OneSideListAssociation, ... ])
    """
    if take_first == None:
        take_first = len(gogod)
        
    by_year = {}
    for game in gogod:
        cls = year_select.get_interval(year_select.class_boundaries, game.get_year())
        if cls:
            by_year.setdefault(cls, []).append(game)
            
    for year_interval, games in by_year.iteritems():
        yg = []
        for game in games[:take_first]:
            # add the game for each player
            for color in colors.PLAYER_COLORS:
                yg.append(OneSideListAssociation(game, color))
            
        yield year_interval, yg
            
def get_datamap_name(gl, max_size, take_first):
    return "Year, %s, split by maxsize = %s, take first = %s"% (repr(gl), max_size, take_first)
    
def create_year_datamap_equisized(s, gogod, max_size=10, take_first=500):
    dm = DataMap(name=get_datamap_name(gogod, max_size, take_first), 
                 image_types=['continuous'],
                 image_annotations=['mean year'])
    
    for year_interval, osl in cl_style.grouping_to_onesidelists( iter_group_by_year( s, gogod, take_first=take_first ),
                                                           lambda interval, num : "%s, %s, split %d"%(dm.name, interval, num), 
                                                           max_size, min_splits=0):
        # get image
        image = s.query(ImageData).filter(ImageData.name==get_image_name( year_interval )).one()
        
        #print repr(osl)
        # Add!
        dm.add(osl, image)

    return dm
    
if __name__ == '__main__':
    import logging
    import sys
    logging.getLogger().setLevel(logging.DEBUG)
    
    s = my_session_maker(filename='GODB.db')

    GOGOD = s.query(GameList).filter(GameList.name == 'GoGoD').one()
    
    ## Images
    create_year_images(s)
    #s.flush()
    
    #sys.exit()
    ## Datamap
    dm = create_year_datamap_equisized(s, GOGOD, max_size=20, take_first=500)
    s.add(dm)
    
    ## all_pat OSL
    import create_db
    import random
    all_pat = create_db.datamap_merge_osl(dm)
    all_games = list(set( game for game,  color in all_pat ))
    
    all_pat.list_assocs = random.sample(all_pat.list_assocs, len(all_pat.list_assocs) / 3)
    all_pat.name +=  ', sampled 33%'
    s.add(all_pat)
    #print repr(all_pat)
    
    ## Spatial Dict Games
    
    sample =  random.sample( all_games,  len(all_games) / 2 )
    #print len(sample)
    
    spatial_dict = GameList(dm.name + ' - Spatial Dict, sampled 50%', games=sample)
    s.add(spatial_dict)
                
    s.commit()