import logging
from logging import handlers
import sys
import itertools
import numpy
import random

from models import *
from my_session import my_session_maker

from itertools import chain

sources =  {
   #  name : directory 
   "Go Teaching Ladder" :  '../data/go_teaching_ladder/prefixed_with_date',
   "GoGoD" :  '../data/GoGoD/Database',
   "Gokifu KGS" :  '../data/kgs',
   "Gokifu Pro" :  '../data/pro',
    
}

def basic_game_lists(s,  ignore=()):
    gamelists =  []
    for name, directory in sources.iteritems():
        if name not in ignore:
            gl = GameList(name)
            s.godb_add_dir_as_gamelist(directory, gl)
            s.add(gl)
            gamelists.append(gl)

    
    if "Spatial Dict Games" not in ignore:
        spd =  make_spatial_dict_gamelist(gamelists)
        s.add(spd)
        
def make_spatial_dict_gamelist(gamelists):
        #   Spatial dict 
        games = []
        for g in chain.from_iterable(( gl.games for gl in gamelists )):
            # only take games without handicap
            # and that are played on big board (size must be specified explicitly)
            if 0 == int(g.sgf_header.get('HA', 0)) and 19 == int(g.sgf_header.get('SZ', 0)):
                games.append(g)
                
        return GameList("Spatial Dict Games", games)
    
"""
def player_osl(s):
    import data_about_players
    
    # define the DB
    gogod = s.query(GameList).filter(GameList.name == 'GoGoD').one()
    
    # this is a "hack" to speed up a test for game being from the gogod archive
    gogod_ids = set(map( lambda game : game.id, gogod.games))
    def gogod_game(game):
        return game.id in gogod_ids
    
    print "start"
    
    # for all players
    names = data_about_players.Data.players_all
    yp = []
    for name in names:
        pls = s.query(Player).filter(Player.name==name).all()
        if not pls:
            print "Not found: '%s', skipping."%(name)
        elif len(pls) != 1:
            raise RuntimeError("More than one player found: '%s'"%name)
        # exactly one player with this name one player
        else:
            player = pls[0]
            isinstance(player, Player)
            
            # we only want player's games from the gogod database
            games = list(itertools.ifilter(gogod_game, player.iter_games()))
            years = [ g.get_year() for g in games ]
            
            # filter out unsucessful year guesses (year == None)
            mean_year = numpy.mean(numpy.array( [ y for y in years if y != None ] ))
            
            yp.append((mean_year, len(games), player.name))
    
    for y, g, p in sorted(yp):
        print "%.0f - %d - %s"%(y, g, p)
"""    

def GTL_all_pat(s):
    GTL = s.query(GameList).filter(GameList.name == 'Go Teaching Ladder').one()
    all_pat_from_GL(s, GTL)
    
def all_pat_from_GL(s, gl):
    gtl_osl = OneSideList(gl.name + ' - all_pat OSL')
    gtl_osl.batch_add(gl, PLAYER_COLOR_BLACK)
    gtl_osl.batch_add(gl, PLAYER_COLOR_WHITE)
    s.add(gtl_osl)
    
def gokifu_join(s):
    gokifu_KGS = s.query(GameList).filter(GameList.name == 'Gokifu KGS').one()
    gokifu_PRO = s.query(GameList).filter(GameList.name == 'Gokifu Pro').one()
    gokifu_joined = GameList('Gokifu KGS + Pro',  games=gokifu_KGS.games + gokifu_PRO.games )
    
    s.add(gokifu_joined)

def datamap_merge_osl(dm, name=None, sample=1.0):
    """Returns OSL created by merging all the osl's in the datamap @dm"""
    if name == None:
        name = dm.name + " - OSL merged"
        if sample != 1.0:
            name +=  ', %d%% sample' % (100 * sample)
    
    ret = OneSideList(name)
    
    for r in dm:
        for a in r.one_side_list:
            if random.random() < sample:
                ret.add(a.game, color=a.color)
        
    return ret

def datamap_merge_gamelist(dm, name=None, sample=1.0):
    """Returns GameList created by merging all the osl's in the datamap @dm"""
    
    if name == None:
        name = dm.name + " - Gamelist merged"
        if sample != 1.0:
            name +=  ', %d%% sample' % (100 * sample)
    
    gameset = set()
    for osl, image in dm:
        for game, color in osl:
            gameset.add(game)
    
    gamelist = list(gameset)
    
    if sample != 1.0:
        gamelist = random.sample(gamelist, int(sample * len(gameset)))
    
    return GameList(name,  games=gamelist)

if __name__ == '__main__':
    import logging
    logging.getLogger().setLevel(logging.DEBUG)
    
    s = my_session_maker(filename='GODB_kgs_wide_120.db')
    
    #basic_game_lists(s,  ignore=['GoGoD', 'Go Teaching Ladder', "Spatial Dict Games" ])
    #GTL_all_pat(s)
    #gokifu_join(s)
    #gokifu = s.query(GameList).filter(GameList.name == 'Gokifu KGS + Pro').one()
    #all_pat_from_GL(s, gokifu)
    #s.commit()
    
    gl = GameList('KGS wide 120')
    s.godb_add_dir_as_gamelist('../data/kgs_wide/games_120_min_10_per_rank/', gl)
    s.add(gl)
    
    s.commit()
    
    print gl    

    
    
    
    