from sqlalchemy import create_engine, and_
from sqlalchemy.orm import sessionmaker, aliased

from sqlalchemy.orm.session import Session 

import logging
import os
import re

from rank import Rank
from models import *
import misc
import timer
from sgf_load import load_sgf_file_headers, ParseError

class GoSession(Session):
    def godb_get_player(self, name, note=u''):
        """Looks if the player with @name is in the DB and returns it.
        Otw. creates a new player with these attributes.
        This new player is NOT added into the session.        
        """
        pls = self.query(Player).filter(Player.name==name).all()
        assert len(pls) <= 1
        if len(pls) == 1:
            player = pls[0]
            if player.note != note:
                logging.warn("%s has different note than '%s'"%(repr(player), note))
            return player
        if len(pls) == 0:
            return Player(name, note)
        
    def godb_get_player_in_time(self, name, current_name=None, current_rank=None, current_note=''):
        """
        NOT adding anything into the session.        
        """
        player = self.godb_get_player(name)
        if current_name == None:
            current_name = name

        pits = self.query(PlayerInTime).filter( PlayerInTime.player == player )

        if current_name:
            pits = pits.filter( PlayerInTime.name == current_name )
        if current_rank:
            pits = pits.filter( PlayerInTime.rank == current_rank )
        if current_note:
            pits = pits.filter( PlayerInTime.note == current_note )

        pit_all = pits.all() 
        if len(pit_all):
            return pit_all[0]

        return PlayerInTime(player, current_name, current_rank, current_note)

    def godb_sgf_to_game(self, filename):
        """
        Creates a Game object from .sgf file.

        Currently, only sgf files with a single gametree are supported.
        
        Does NOT add the game in the session but it 
        DOES ADD players in the game in there.
        """
        try:
            headers = load_sgf_file_headers(filename)
        except ParseError:
            logging.warn("Could not parse '%s', probably not a .sgf file, skipping."%(filename,))
            return None
            
        if not headers:
            logging.warn("No headers in .sgf file '%s', skipping."%(filename,))
            return None

        if len(headers) > 1:
            logging.warn("More game trees in a file, skipping '%s'."%(filename,))
            return None

        hd = headers[0]

        # load players' names and ranks
        # we add them to the session to have consistency and correctly interjoined objects
        # (e.g. when pw == pb (anonymous) then only the first call actually
        # creates a new object. The second call uses the same object.
        pw = self.godb_get_player_in_time(hd.get('PW', ''), current_rank=Rank.from_string(hd.get('WR','')))
        self.add(pw)
        pb = self.godb_get_player_in_time(hd.get('PB', ''), current_rank=Rank.from_string(hd.get('BR','')))
        self.add(pb)

        return Game( filename.decode('utf-8'), pb, pw, hd )

    def godb_add_dir_as_gamelist(self, directory, gamelist=None):
        """Recursively scans the @directory for sgf files.
        The valid games are added into a gamelist (either provided by @gamelist kwarg,
        or new if @gamelist == None).
        
        Both players in each of the games scanned are added into the session.
        (see self.godb_sgf_to_game)
        
        The gamelist is returned and not added into the session.
        """
        t = timer.Timer()
        games = []
        t.start()
        for filepath in misc.iter_files(directory):
            if re.search('sgf$', filepath):
                logging.debug("Scanning '%s'"%(filepath))
                
                # create Game object from the sgf file
                t.start()
                game = self.godb_sgf_to_game(filepath)
                if game:
                    games.append(game)
                t.stop()
                
        t.stop_n_log('  Total time', 'Game')

        if gamelist == None:
            gamelist = GameList("Games from '%s'."%(directory,))
        
        gamelist.games += games
        logging.info("Added %d games to: %s"%(len(games), gamelist))
            
        return gamelist
    
    """
    ## TODO make it faster!!!
    def godb_list_player_games_white(self, pits):
        #pits = self.query(PlayerInTime.id).filter(PlayerInTime.player_id == player.id).all()
        #pits = player.in_times
        return self.query(Game).filter(Game.white_id.in_(pits) ).all()
    def godb_list_player_games_black(self, pits):
        #pits = ( pit.id for pit in player.in_times )
        #pits = self.query(PlayerInTime.id).filter(PlayerInTime.player_id == player.id).all()
        return self.query(Game).filter(Game.black_id.in_(pits) ).all()
        #return self.query(Game).\
        #    join(PlayerInTime, Game.black_id==PlayerInTime.id).\
        #    filter(PlayerInTime.player_id == player.id).all()
    """

MySession = sessionmaker(class_=GoSession) 

def my_session_maker(filename, echo=False):
    engine = create_engine('sqlite:///%s'%filename, echo=echo)
    Base.metadata.create_all(engine) 

    s = MySession(bind=engine)
    # for wingide completion...
    isinstance(s, GoSession)
    return s

if __name__ == '__main__':
    import logging
    logging.getLogger().setLevel(logging.DEBUG)

    s = my_session_maker(filename='GODB.db')#, echo=True)
    #s = my_session_maker(filename=':memory:')#, echo=True)

    
    #gogod = s.query(GameList).filter(GameList.name == 'GoGoD').one()
    #gogod = s.query(GameList).filter(GameList.name == 'Go Teaching Ladder').one()
    
    #g = s.godb_sgf_to_game('../data/go_teaching_ladder/reviews/6321-Ayari-Christophe-Sebastien.sgf')
    #print unicode(g)
    
    
    #repr(g)
    
          
    #gl = s.godb_add_dir_as_gamelist('./files')    
    #for g in gl :
    #    print g.black.rank
    #    print g.white.rank
