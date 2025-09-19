from collections import namedtuple


PLAYER_COLOR_WHITE = 'W'
PLAYER_COLOR_BLACK = 'B'

PLAYER_COLORS = ( PLAYER_COLOR_BLACK, PLAYER_COLOR_WHITE )

class BlackWhite(namedtuple('BlackWhite', 'black white')):
    def map_both(self, f):
        return BlackWhite(*map( f, self ))
    
    def map_pathway(self, func_list):
        bw = self
        for f in func_list:
            bw = bw.map_both(f)
        return bw

def the_other_color(color):
    if color == PLAYER_COLOR_BLACK:
        return PLAYER_COLOR_WHITE
    return PLAYER_COLOR_BLACK
