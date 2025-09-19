import misc 
import numpy
import sqlalchemy

from my_session import my_session_maker
from models import *
from rank import Rank

from cl_utils import * 

def create_strength_images(s):
    for rank in Rank.iter_all():
        s.add(ImageData('strength: %s'%rank, numpy.array([rank.key()]) ))

def iter_group_by_rank(gamelist, filter_fc,  rank_fc=lambda rank: rank):
    """
    Iterates pairs (rank, [ OneSideListAssociation, ... ])
    """
    # rank -> list of OneSideListAssociation
    oslass = {}
    for game in gamelist:
        for pit, color in game.iter_pit_color():
            isinstance(pit, PlayerInTime)
            rank = pit.rank
            if filter_fc(rank):
                rank = rank_fc(rank) 
                oslass.setdefault(rank, []).append( OneSideListAssociation(game, color) )
    
    return oslass.iteritems()

def get_datamap_name(gl, max_size, min_size, min_splits, equisized=True, shuffle=False):
    return get_name_template('Strength', gl, max_size, min_size, min_splits, equisized, shuffle )

def create_strength_datamap(s, gl, max_size=10, min_size=10, min_splits=10,  equisized=True, shuffle=False):
    
    dm = DataMap(name=get_datamap_name(gl, max_size, min_size, min_splits, equisized, shuffle), 
                 image_types=['continuous'],
                 image_annotations=['player strength'])
    
    for rank, osl in grouping_to_onesidelists( iter_group_by_rank(gl, lambda rank: Rank(3, 'd') >= rank >= Rank(28, 'k')), 
                                                           lambda r, num : "%s, rank %s, split %d"%(dm.name, r, num), 
                                                           max_size, min_size, min_splits, equisized=equisized,  shuffle=shuffle):
        # get image
        try:
            image = s.query(ImageData).filter(ImageData.name=="strength: %s"%(rank)).one()
        except sqlalchemy.orm.exc.NoResultFound:
            # only possible if
            assert rank == None
            continue
        
        dm.add(osl, image)

    return dm

def Gokifu_join(s, max_size,  min_splits):
    ## Gokifu PRO + Gokifu KGS
    gokifu_joined = s.query(GameList).filter(GameList.name == 'Gokifu KGS + Pro').one()
    # this is a distribution of ranks in the GL
    # KGS
    """
       1402 4d
       2171 5d
       3422 6d
       2734 7d
       1324 8d
        188 9d"""
    # PRO
    """
        623 1p
       1201 2p
       2092 3p
       2103 4p
       2662 5p
       1903 6p
       2607 7p
       1846 8p
      10125 9p"""


    # only take games of players stronger than 4d
    filter_fc = lambda rank: Rank(4, 'd') <= rank
    
    # according to http://senseis.xmp.net/?RankWorldwideComparison
    # KGS 8 dan == PRO 1 dan so we merge and map like this
    # so that the rank scale has no holes.
    
    def merge_ranks(rank):
        if rank <= Rank(7, 'd'):
            # 7d -> 10d
            assert rank.kdp == 'd'
            return Rank(rank.number + 3, 'd')
        
        if rank <= Rank(10, 'd'):
            # 8 dan -> 1 pro
            return Rank(rank.number - 7, 'p')
        
        # 1 pro -> 1 pro
        return rank            
    
    dm = DataMap(name=get_datamap_name(gokifu_joined, max_size, min_splits), 
                 image_types=['continuous'],
                 image_annotations=['player strength'])
    
    for rank, osl in grouping_to_onesidelists( iter_group_by_rank(gokifu_joined, filter_fc, merge_ranks ),
                                                           lambda r, num : "%s, rank %s, split %d"%(dm.name, r, num),
                                                           max_size, min_splits, equisized=True):
        # get image
        try:
            image = s.query(ImageData).filter(ImageData.name=="strength: %s"%(rank)).one()
        except sqlalchemy.orm.exc.NoResultFound:
            # only possible if
            assert rank == None
            continue
        
        dm.add(osl, image)

    return dm

if __name__ == '__main__':
    import logging
    logging.getLogger().setLevel(logging.DEBUG)
    
    s = my_session_maker(filename='GODB.db')
    
    def GTL_Str():
        ## GTL strength
        
        #import create_db
        #create_db.GTL_all_pat(s)
        
        #create_strength_images(s)
        
        GTL = s.query(GameList).filter(GameList.name == 'Go Teaching Ladder').one()
        dm = create_strength_datamap(s, GTL,  max_size=5, min_size=5, min_splits=24)
        
        s.add(dm)
        return dm
    
    dm = GTL_Str()
    print dm.name
    s.commit()
    
    
        
    #dm = Gokifu_join(s, 100, 1)
    #s.add(dm)
    #s.commit()
    