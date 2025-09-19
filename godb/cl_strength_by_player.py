import misc 
import numpy
import sqlalchemy
import random

from my_session import my_session_maker
from models import *
from rank import Rank

from cl_style import grouping_to_onesidelists
import create_db

def iter_osl_by_rank( gamelist, filter_fc, rank_fc=lambda rank: rank):
    """
    Iterates pairs (rank, [ OneSideListAssociation, ... ])
    """
    
    gl_ids = set()
    pit_set = set()
    for game in gamelist:
        gl_ids.add(game.id)
        pit_set.add(game.black)
        pit_set.add(game.white)
        
    def gl_game(osa):
        return osa.game.id in gl_ids
    
    name = lambda pit : "kgs_wide, player %s"%(pit)
    
    ns = set(map(name, pit_set))
    if len(ns) != len(pit_set):
        assert False
    
    d = {}
    
    for pit in pit_set:
        if filter_fc(pit.rank):
            rank = rank_fc(pit.rank)
            if rank:
                one_side_asss = filter(gl_game, pit.iter_one_side_associations() )
                if len(one_side_asss) < 10:
                    continue
                if len(one_side_asss) > 100:
                    one_side_asss = random.sample(one_side_asss, 100)
                    
                osl = OneSideList("kgs_wide 10 <= X <= 100, player %s"%(pit),  one_side_asss)
                
                d.setdefault(rank, []).append(osl)
            
    for rank, l in d.items():
        if len(l) >= 120:
            pop = random.sample(l, 120)
            for osl in pop:
                yield rank, osl

def get_datamap_name(gl):
    return gl.name + ", split by player and rank, 10 <= X <= 50"#, new"

def get_name_template(name, gl, max_size, min_size, min_splits, equisized, shuffle):
    if max_size and max_size == min_size:
        split_by = 'one split == %d games' % min_size
    elif min_size:
        assert not max_size
        split_by = 'one split >= %d games' % min_size
    elif max_size:
        split_by = 'one split <= %d games' % max_size
    else:
        split_by = 'one split all possible games' % max_size
        
    split_sign = '=='
    
    name = "%s, %s, %s, number of splits %s %s"% (name, repr(gl), split_by, split_sign, min_splits)
    if shuffle:
        name +=  ', Shuffled'
    return name

def create_by_player_datamap(s, gl):
    
    dm = DataMap(name=get_datamap_name(gl), 
                 image_types=['continuous'],
                 image_annotations=['player strength'])
    
    for rank, osl in iter_osl_by_rank(gl, lambda rank: Rank(8, 'd') >= rank >= Rank(30, 'k')):
        s.add(osl)
        
        # get image
        try:
            image = s.query(ImageData).filter(ImageData.name=="strength: %s"%(rank)).one()
        except sqlalchemy.orm.exc.NoResultFound:
            # only possible if
            #print rank
            assert rank == None
            continue
        
        print rank, repr(osl)
        dm.add(osl, image)

    return dm

def reduce_pop_120(dm):
    dm_new = DataMap(name=dm.name + ', new',
                 image_types=['continuous'],
                 image_annotations=['player strength'])
    
    d = {}
    
    for osl, im in dm:
        d.setdefault(im, []).append(osl)
        
    for image, l in d.iteritems():
        if len(l) >= 120:
            pop = random.sample(l, 120)
            for osl in pop:
                dm_new.add(osl, image)
                
    return dm_new

def reduce_games_50(dm):
    dm_new = DataMap(name=dm.name[:-3]+'50',
                 image_types=['continuous'],
                 image_annotations=['player strength'])
    
    d = {}
    
    for osl, im in dm:
        d.setdefault(im, []).append(osl)
        
    for image, l in sorted(d.iteritems(), key=lambda (i, l): i.data[0] ):
        if len(l) >= 120:
            pop = random.sample(l, 120)
            for osl in pop:
                lass = [ OneSideListAssociation(la.game, la.color) for la in osl.list_assocs ]
                l = len(lass)
                if l >= 50:
                    lass = random.sample(lass, random.randint(10, 50))
                    osl = OneSideList(osl.name + ', subsampled to max 50', lass)
                dm_new.add(osl, image)
                
    return dm_new


if __name__ == '__main__':
    import logging
    logging.getLogger().setLevel(logging.DEBUG)
    
    s = my_session_maker(filename='GODB_kgs_wide_120.db')
    
    #from cl_strength import create_strength_images
    #create_strength_images(s)
    #s.commit()
    
    #gl = s.query(GameList).filter(GameList.name == 'KGS wide 120').one()
    #dm = create_by_player_datamap(s, gl)
    #s.add(dm)
    
    KGS = s.query(GameList).filter(GameList.name == 'KGS wide 120').one()
    dm_name = get_datamap_name(KGS)
    
    DATAMAP = s.query(DataMap).filter(DataMap.name == dm_name).one()
    
    new = reduce_games_50(DATAMAP)
    
    #s.add(new)
    
    osl = create_db.datamap_merge_osl(new,  sample=0.2)
    #s.add(osl)
    
    #s.commit()
    