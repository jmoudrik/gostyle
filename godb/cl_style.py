import sqlalchemy
import itertools
import random
import numpy

import misc
from my_session import my_session_maker
from models import *
from rank import Rank

from data_about_players import Data, get_all_player_names

from cl_utils import * 



def create_style_images(s):
    for name in get_all_player_names(2):
        sv =  Data.questionare_total.get(name, None)
        if sv:
            s.add(ImageData('style_2: %s'%name, numpy.array(sv) ))
            
def iter_group_by_player(s, gogod, min_size=None, questionare_limit=2):
    """
    Iterates pairs (player, [ OneSideListAssociation, ... ])
    """
    # this is a "hack" to speed up a test for game being from the gogod archive
    gogod_ids = set(map( lambda game : game.id, gogod.games))
    def gogod_game(game):
        return game.id in gogod_ids
    
    for name in get_all_player_names(limit=2):
        
        pls = s.query(Player).filter(Player.name==name).all()
        if not pls:
            logging.info ("Not found: '%s', skipping."%(name))
            continue
        elif len(pls) != 1:
            raise RuntimeError("More than one player found: '%s'"%name)
        # exactly one player with this name one player
        else:
            player = pls[0]
            isinstance(player, Player)
            # we only want player's games from the gogod database
            games = list(itertools.ifilter(gogod_game, player.iter_games()))
            if not min_size or len(games) >= min_size:
                yield player, [ OneSideListAssociation(game, game.get_player_color(player)) for game in games ]
            else:
                print "skipping %s, has %d, needs %d" % (player, len(games), min_size)
            
def get_datamap_name(gl, size, splits, equisized=True, shuffle=True, questionare_limit=2):
    return get_name_template('Style_2', gl, size, size, splits, equisized, shuffle ) + ", Questionare Limit = %d" % questionare_limit
    
def create_style_datamap(s, gogod, size=10, splits=10,  shuffle=True, equisized=True, questionare_limit=2):
    dm = DataMap(name=get_datamap_name(gogod, size, splits, equisized, shuffle,  questionare_limit=questionare_limit), 
                 image_types=['continuous'] * len(Data.questionare_annotations),
                 image_annotations=Data.questionare_annotations)
    
    for player, osl in grouping_to_onesidelists( iter_group_by_player( s, gogod, size * splits, questionare_limit=questionare_limit),
                                                           lambda p, num : "%s, player %s, split %d"%(dm.name, p.name, num), 
                                                           size, size, splits, equisized=equisized,  shuffle=shuffle):
        # get image
        try:
            image = s.query(ImageData).filter(ImageData.name=="style_2: %s"%(player.name)).one()
        except sqlalchemy.orm.exc.NoResultFound:
            continue
        
        
        dm.add(osl, image)

    return dm
    
if __name__ == '__main__':
    import logging
    logging.getLogger().setLevel(logging.DEBUG)
    
    s = my_session_maker(filename='GODB.db')
    
    #create_style_images(s)
        
    GOGOD = s.query(GameList).filter(GameList.name == 'GoGoD').one()
    DATAMAP = create_style_datamap(s, GOGOD, 192, 1, equisized=True)
    
    print DATAMAP.name
    
    #assert DATAMAP.name == get_datamap_name(GOGOD, 16, 12)
    raise Exception
    
    
    s.add(DATAMAP)
    
    utils.bark()
    
    ## OSL
    if True:
    #if False:
        import create_db 
        oslm = create_db.datamap_merge_osl(DATAMAP)        
        s.add(oslm)
    
    ## ALL_PAT
    if True:
    #if False:
        gl = create_db.datamap_merge_gamelist(DATAMAP, name=DATAMAP.name + ' - Spatial Dict')        
        s.add(gl)
    
    #s.commit()