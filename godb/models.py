import os 
from itertools import chain

import logging
import re

from sqlalchemy import Table, Column, Integer, ForeignKey, Text, Date, Float, Enum, UniqueConstraint, PickleType
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.declarative import declarative_base

import utils
from rank import Rank
from colors import *

Base = declarative_base()

class ProcessingError(Exception):
    pass

##
##  hack to workaround this bug: http://bugs.python.org/issue5876
## > Oh ok, gotcha: repr() always returns a str string. If obj.__repr__() returns a 
## > Unicode string, the string is encoded to the default encoding. By default, the 
## > default encoding is ASCII.
## => unicode chars in repr cause "ordinal not in range err"
import functools
import misc
def ununicode(f):
    @functools.wraps(f)
    def g(*args, **kwargs):
        return misc.unicode2ascii(f(*args, **kwargs))
    return g 

class Player(Base):
    """Class (and ORM Table) about go player.
    The name must be unique (born name, ..). This class should have one instance (db record)
    for one go player.

    Player may change name, rank, .. in time, or use different nicknames, etc.
    The consistency (so that all these variations are connected) is maintained
    together with the PlayerInTime.
    """
    __tablename__ = 'player'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(Text, nullable=False, unique=True, index=True)
    note = Column(Text)
    # list in_times from backrefs

    #__table_args__ = ( UniqueConstraint('name'), )

    def __init__(self, name, note=u''):
        self.name = name
        self.note = note

    def iter_games_as(self, color, pit_filter=lambda pit:True):
        return chain.from_iterable(pit.iter_games_as(color) 
                                   for pit in self.in_times if pit_filter(pit) )

    def iter_one_side_associations(self,
                                   pit_filter=lambda pit:True,
                                   **kwargs):
        return chain.from_iterable( pit.iter_one_side_associations(**kwargs)
                                    for pit in self.in_times if pit_filter(pit) )
    # Shortcuts
    def iter_games_as_white(self, **kwargs):
        return self.iter_games_as(PLAYER_COLOR_WHITE, **kwargs)
    def iter_games_as_black(self, **kwargs):
        return self.iter_games_as(PLAYER_COLOR_BLACK, **kwargs)
    def iter_games(self):
        return chain(self.iter_games_as_black(), self.iter_games_as_white())

    def __str__(self):
        return self.name

    @ununicode
    def __repr__(self):
        return u"Player(%s, '%s','%s')" % (self.id,
                                          self.name,
                                          self.note)
    
import pickle

class PlayerInTime(Base):
    """Captures evolution of players in time - change of rank, name, different identities."""
    __tablename__ = 'player_in_time'
    id = Column(Integer, primary_key=True, index=True)

    player_id = Column(Integer, ForeignKey('player.id'), index=True)
    player = relationship("Player", backref=backref('in_times', order_by=id))

    name = Column(Text)
    
    rank = Column(PickleType) # (pickler=pickle))
    note = Column(Text)
    # list games_as_black from backrefs
    # list games_as_white from backrefs

    def __init__(self, player, name='', rank=None, note=''):
        if isinstance(rank, basestring):
            rank = Rank.from_string(rank)
            
        self.player = player
        self.name = name
        self.rank = rank
        self.note = note

    def get_games_as(self, color):
        if color == PLAYER_COLOR_BLACK :
            return self.games_as_black
        if color == PLAYER_COLOR_WHITE :
            return self.games_as_white
        raise KeyError(color)

    def iter_games_as(self, color):
        return iter(self.get_games_as(color))

    def iter_one_side_associations(self,
                                   color_filter=lambda color:True,
                                   game_filter=lambda game:True ):
        return ( OneSideListAssociation(game, color)
                 for color in PLAYER_COLORS if color_filter(color)
                 for game in self.iter_games_as(color) if game_filter(game) )

    def __str__(self):
        return self.name + ( " (%s)"%(self.rank) if self.rank else '')
    
    def str2(self):
        return self.name + ( " [%s]"%(self.rank) if self.rank else '')

    @ununicode
    def __repr__(self):
        return u"PlayerInTime(%s, %s, '%s', '%s', '%s')" % (
            self.id,
            repr(self.player),
            self.name,
            self.rank,
            self.note )

class SchizophrenicPlayerError(Exception):
    """Used in context of problems with games between the same players.
    E.g. Anonymous vs. Anonymous"""
    pass

class Game(Base):
    """Class (and ORM Table) holding game information like
        - sgf filename
        - info about players - who played black, who played white
        - sgf header with further info
    """
    __tablename__ = 'game'
    id = Column(Integer, primary_key=True, index=True)    
    sgf_file = Column(Text, nullable=False)    

    black_id = Column(Integer, ForeignKey('player_in_time.id'), index=True)
    white_id = Column(Integer, ForeignKey('player_in_time.id'), index=True)

    black = relationship("PlayerInTime", primaryjoin="PlayerInTime.id==Game.black_id",
                         backref=backref('games_as_black', order_by=id))
    white = relationship("PlayerInTime", primaryjoin="PlayerInTime.id==Game.white_id",
                         backref=backref('games_as_white', order_by=id))    

    sgf_header = Column(PickleType)    

    # We store the whole header instead of these

    #date = Column(Text)    
    #komi = Column(Float)    
    #handicap = Column(Integer)
    #size = Column(Integer)
    #result = Column(Text)
    #note = Column(Text)

    def __init__(self, sgf_file, black, white, sgf_header={}):
        self.sgf_file = sgf_file
        self.black = black
        self.white = white
        self.sgf_header = sgf_header

    @ununicode
    def __repr__(self):
        return u"Game(%s, '%s', '%s', '%s')" %(
            self.id,
            self.sgf_file,
            repr(self.white) if self.white else '', 
            repr(self.black) if self.black else '')

    def abs_path(self):
        return os.path.abspath(self.sgf_file)

    def iter_pit_color(self):
        yield (self.black, PLAYER_COLOR_BLACK)
        yield (self.white, PLAYER_COLOR_WHITE)

    def get_player_by_color(self, color):
        for gpit, gcolor in self.iter_pit_color():
            if color == gcolor:
                return gpit.player
        raise ValueError("Wrong color '%s'."%color)

    def get_player_color(self, player):
        if self.black.player == self.white.player :
            # we cannot expect for this method to return different values for one player...
            # (so this would always return black, because it has no way of knowing if we ask for
            # black or white player)
            raise SchizophrenicPlayerError("Asked for color for game between identical players: %s"%(self,))

        for gpit, gcolor in self.iter_pit_color():
            if player == gpit.player:
                return gcolor

        raise ValueError("Game %s is not a game of %s."%(repr(self), repr(player)))
    
    def get_year(self, try_filename_prefix=True):
        # Year from DT field of sgf file
        dt = self.sgf_header.get('DT', 'Unknown')
        year = utils.get_year(dt)
        
        # try to guess name from filename prefix (e.g. gogod)
        if year == None and try_filename_prefix:
            fn = os.path.basename(self.sgf_file)[:4]
            return utils.get_year(fn)
        
        # return year or None if failure
        return year

    def open_in_viewer(self):
        utils.viewer_open(self.abs_path())

game_list_association = Table('game_list_association', Base.metadata,
                              Column('game_list_id', Integer, ForeignKey('game_list.id'), index=True),
                              Column('game_id', Integer, ForeignKey('game.id'), index=True)
)

class GameList(Base):
    """List of games.
    """
    __tablename__ = 'game_list'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(Text, nullable=False, unique=True, index=True)

    games = relationship('Game', secondary=game_list_association, backref='game_lists')

    def __init__(self, name, games=None):
        self.name = name
        if games != None:
            assert not self.games
            self.games = list(games)

    def iter_players_black(self):
        """Iterate players who played in a game (from this list) as black."""
        for game in self.games:
            yield game.black.player 

    def iter_players_white(self):
        """Look at self.get_players_black and guess."""
        for game in self.games:
            yield game.white.player 

    def iter_players(self):
        """Iterate players who played a game from this list."""
        return chain(self.iter_players_black(), self.iter_players_white())

    def append(self, game):
        self.games.append(game)

    #def __str__(self):
    #    ret = [ self.name ] + map(str, self.games)
    #    
    #    return '\n'.join(ret)
    
    def __getitem__(self, val):
        return self.games[val]

    def __len__(self):
        return len(self.games)

    @ununicode
    def __repr__(self):
        return "GameList(%s, '%s', #games = %d)" %( self.id, self.name, len(self) )
    
    
class Merger:
    def __init__(self):
        pass
    def __repr__(self):
        return self.__class__.__name__ + "()"
    def start(self, bw_gen):
        raise NotImplementedError
    def add(self, result, color):
        raise NotImplementedError
    def finish(self):
        raise NotImplementedError
    

class OneSideListAssociation(Base):
    __tablename__ = 'one_side_list_association'
    id = Column(Integer, primary_key=True, index=True)
    one_side_list_id = Column(Integer, ForeignKey('one_side_list.id'), index=True)
    game_id = Column(Integer, ForeignKey('game.id'), index=True) 

    # what is the color of the player of interest in this game?
    color = Column(Enum(PLAYER_COLOR_BLACK, PLAYER_COLOR_WHITE))
    game = relationship("Game", backref="one_side_lists_assoc")

    # one game ( for one side ) can be in one game list only once
    __table_args__ = ( UniqueConstraint('one_side_list_id', 'game_id', 'color'), )

    def __init__(self, game, color):
        self.game = game
        self.color = color
        
    def __iter__(self):
        yield self.game
        yield self.color

    @ununicode
    def __repr__(self):
        return u"OneSideListAssociation(%s, '%s')" %( repr(self.game), self.color )
    
class OneSideList(Base):
    """List of games, for e.g. players with 10kyu, Honinbo Shusaku's games, ...

    Note that the list distinguishes between sides. That is, if you are interested
    in both sides (default behaviour of the `add` method), the game will be added
    twice - once for black, once for white.
    """
    __tablename__ = 'one_side_list'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(Text, nullable=False, unique=True, index=True)

    list_assocs = relationship('OneSideListAssociation', backref='one_side_list')    

    def __init__(self, name, assocs=None):
        self.name = name
        if assocs != None:
            assert not self.list_assocs
            self.list_assocs = list(assocs)
            
    def __getitem__(self, val):
        return self.list_assocs[val]

    def batch_add(self, games, color):
        """Add games played with one color in batch."""
        self.list_assocs += [ OneSideListAssociation(game, color) for game in games ]

    def add(self, game, player=None, color=None):
        """Adds game to the list. If @player (or @color) specified, adds only
        one side of the game - the one that @player played (or played with @color).
        Otw. both sides get added (game is added twice - once for black, once for white)
        """
        if player != None: 
            pc = game.get_player_color(player)
            if color and color != cp:
                raise ValueError( """Provided color (%s) is different from provided player's (%s) color in the game %s."""%
                                  ( color, player, game ))
            color = pc

        if color != None:
            # if color of the desired player specified
            citer = ( color, )
        else:
            # add both black's game and white's game
            citer = PLAYER_COLORS

        for color in citer:
            self.list_assocs.append(OneSideListAssociation(game, color))

    def for_one_side_list(self, merger, bw_processor):
        """
        Processes the whole OneSideList, so that @bw_processor is called on every game. And the 
        result of interest (black or white) is added to @merger, via @merger.add(result, color).
        At the end @merger.finish() is called and this should return the desired data.
        """
        #assert isinstance(merger, Merger)
        
        merger.start(bw_processor)
        
        for ga in self.list_assocs:
            try:
                black, white = bw_processor(ga.game)
            except ProcessingError as exc:
                logging.debug("Exception %s occured in processing the game %s, skipping!!"%(repr(exc), ga.game))
                continue
            except Exception as exc:
                logging.exception("Exception %s occured in processing the game %s!!"%(repr(exc), ga.game))
                raise
                #continue

            desired = black if ga.color == PLAYER_COLOR_BLACK else white
            merger.add(desired, ga.color)

        return merger.finish()
    
    def __len__(self):
        return len(self.list_assocs)

    def __str__(self):
        ret = [ self.name ]
        for ga in self.list_assocs:
            ret.append("%s : %s"%(ga.color, ga.game))

        return '\n'.join(ret)

    @ununicode
    def __repr__(self):
        return "OneSideList(%s, '%s', #games = %d)"%( self.id, self.name, len(self) )

class DataMap(Base):
    """
    One DataMap holds info about the mapping:
    OneSideList -> ImageData
    """
    __tablename__ = 'datamap'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(Text, nullable=False, unique=True, index=True)
    
    # information about the image domain
    image_types = Column(PickleType)
    image_annotations = Column(PickleType)

    relations = relationship("DataMapRelation", backref='datamap')
    
    def add(self, one_side_list, image):
        self.relations.append(DataMapRelation(one_side_list=one_side_list,
                                              image=image))
    def __len__(self):
        return len(self.relations)
    
    def __getitem__(self, val):
        return self.relations[val]
    
    @ununicode
    def __repr__(self):
        return "DataMap(%d, '%s', #relations = %d )"%(self.id,  self.name, len( self.relations))
    
class DataMapRelation(Base):
    """
    One OneSideList gets mapped to data (usually a python vector).
    """
    __tablename__ = 'datamap_relation'
    id = Column(Integer, primary_key=True, index=True)
    # id of the current dataset
    datamap_id = Column(Integer, ForeignKey('datamap.id'), index=True)
    # domain
    one_side_list_id = Column(Integer, ForeignKey('one_side_list.id'), index=True)
    # image
    image_id = Column(Integer, ForeignKey('image_data.id'), index=True)

    one_side_list = relationship("OneSideList")#, backref='relations')
    image = relationship("ImageData")
    
    def __iter__(self):
        yield self.one_side_list
        yield self.image
    
    def __repr__(self):
        return "DataMapRelation(%s,%s)" % (repr(self.one_side_list),
                                           repr(self.image))
    

class ImageData(Base):
    """ Class used to hold python-pickled data under unique name. Meant to be
        used for holding right side of the mapping defined by DataMapRelation,
        so that multiple OneSideLists may share the same image.
    """
    __tablename__ = 'image_data'
    id = Column(Integer, primary_key=True, index=True)
    # e.g. 'style: Otake Hideo'
    name = Column(Text, nullable=False, unique=True, index=True)
    # e.g. the style vector itself
    data = Column(PickleType)

    def __init__(self, name, data):
        self.name = name
        self.data = data

    @ununicode
    def __repr__(self):
        return "ImageData(%s, %s, %s)"%(self.id, self.name, self.data)

if __name__ == '__main__':
    pass    