import os
import random

import config
import pic_utils

import godb
import numpy

from pic_utils import generate_str_pic,  generate_style_pic

POLY_D = {'f0(s:4677)': [-0.0044639397984546246, 0.078071315441855041],
          'f0(s:3172)': [0.0037897577550676021, 0.0059373087918339843],
          'f1(local seq < 10: sente - gote)': [-0.17628344473214899, 4.7219260618450312],
          'f0(s:4676)': [-0.0062163495635112129, 0.10596058239054341],
          'f0(s:528)': [-0.01393308164474435, 0.4742450476052662],
          'f1(local seq < 10: sente)': [-0.23335521408517831, 10.251727652598419],
          'f0(s:642)': [-0.0027834828662450968, 0.061562132943168896],
          'f0(s:463)': [-0.011679541953412715, 0.26317670175599711],
          'f0(s:8)': [-0.017490870037029288, 0.51881395625119064],
          'f0(s:81)': [-0.024899640910233063, 1.0508253699266714],
          'f3(capture histogram: move <= 60, captured)': [0.02697014488626804, 0.44851052406603431],
          'f0(s:251)': [-0.0046122569579398883, 0.099047297071349669],
          'f1(local seq < 10: gote)': [-0.057071769409717657, 5.5298015953181778],
          'f0(s:1981)': [0.0047252212569775459, 0.0086278920838786747],
          'f0(s:562)': [-0.0078760351009160914, 0.21903415496461767],
          'f0(s:159)': [0.004570710168540929, 0.10137797762536714],
          'f0(s:4800)': [-0.0030553760655927247, 0.060544213266474196]}

# Xth kyu
EVAL_BOUND = 1

def eval_attr(attr_name, rank):
    return numpy.polyval(numpy.array(POLY_D[attr_name]), rank)

# increasing strength (decreasing image) correlates with increasing attribute value
def is_attr_good(attr_name ):
    return POLY_D[attr_name][0] < 0
def is_attr_bad(attr_name ):
    return not is_attr_good(attr_name)

def is_relevant(attr_name, vec):
    # ignore patterns not present (0, 0.0)
    if not vec[attr_name]:
        return False
    
    try:
        return any((
        # attribute is good to play often
        # and the player does not play it more often than the reference player
         is_attr_good(attr_name) and vec[attr_name] < eval_attr(attr_name, EVAL_BOUND),
        # attribute is bad to play often
        # and the player DOES play it often
         is_attr_bad(attr_name) and vec[attr_name] > eval_attr(attr_name, EVAL_BOUND)
         ))
    except KeyError:
        return False

def get_str_patterns_html(outdir, vec):
    stuff_to_say = []
    
    def add_row(*cols):
        stuff_to_say.append(
        """
        <tr>
       <td colspan="%d">
        %s 
       </td>
        </tr>
        """%(2 if len(cols) == 1 else 1, '</td><td style="vertical-align:middle">'.join(cols)))
    
    if is_relevant('f1(local seq < 10: sente)', vec) or\
       is_relevant('f1(local seq < 10: sente - gote)',  vec):
        add_row("""
        You should concrentrate on the concept of sente and gote.
        Do you ask after every enemy move,
        <i>Do I need to respond to this?</i> and If so, <i>Do I have a possibility
        to respond on some unexpected place so that the threat is neutralized, but
        the opponent in turn has to respond?</i>
        """ )
    if is_relevant('f3(capture histogram: move <= 60, captured)',  vec):
        add_row("""
        We found out, that you really like to capture stones. This is not necessarily
        a bad thing, but are you always sure, that the stones you captured are important
        and the mere 6 points you get for capturing them is the best move on board?
        (E.g. in the opening, ...)
        """
        )
        
    if is_relevant('f0(s:1981)',  vec):
        add_row("<img src='/STR_PATT/f0(s:1981).png'>", 
        """
        Huh, we think that you like the empty triangle.
        Please, remember, that this shape is usually terrible and try not to play it..
        Are the stones you are trying to save necessary?
        """
        )
        
    if is_relevant('f0(s:3172)',  vec):
        add_row(""" <img src='/STR_PATT/f0(s:3172).png'> """, """
        Huh, we think that you like the empty triangle.
        Please, remember, that this shape is usually terrible and try not to play it..
        Wouldn't a jump be a better idea?
        """
        )
        
    if is_relevant('f0(s:159)',  vec):
        add_row(""" <img src='/STR_PATT/f0(s:159).png'>""", """
        You seem to <a href='http://senseis.xmp.net/?PushingFromBehind'>push from behind</a> a lot.
        You should realize, that this allows the opponent to hane at the head of your stones...
        """
        )
        
    scale_patterns = []
    for pat in [ 'f0(s:4677)', 'f0(s:4676)', 'f0(s:528)',
                 'f0(s:642)', 'f0(s:463)', 'f0(s:8)', 'f0(s:81)',
                 'f0(s:4800)', 'f0(s:251)', 'f0(s:562)' ]:
        if not is_relevant(pat, vec):
            continue
        
        strong, weak, player = max(0.01, eval_attr(pat, -5)), max(0.01, eval_attr(pat, 20)), vec[pat]
        
        if player < 0.01:
            continue
        
        spg, wpg, ppg = 1 / strong, 1 / weak, 1 / player
        
        if not (spg <= ppg <= wpg):
            continue
        
        pic = pic_utils.generate_rel_freq_pic(outdir, spg, ppg, wpg)
        scale_patterns.append("""
        <tr>
       <td>
       <img src='/STR_PATT/%s.png'>
       </td>
       <td style="vertical-align:middle">
       <img src='%s'>
       </td>
        </tr>
       """% (pat, pic))
    
    s1 = """<h4>Bad things you play</h4>
    <p>Hmm, we've got nothing to say to you..</p>
    """
    if stuff_to_say:
        s1 = """<h4>Bad things you play</h4>
        <p><table class='table table-striped'>
        """ + '\n'.join(stuff_to_say) + "\n</table></p>"
       
    s2 = ''
    if scale_patterns:
        s2 = """
        <h4>Other notable stuff</h4>
        <p>
        The following table shows some typical patterns that stronger players play more than you (on average).
        The scales on the right show the relative frequency of the moves: "The move is played
        every Xth game.". The strong players are on the left, weak on the right,
        your frequency estimated from the sample is the red bar.
        </p>
        <p>
        You can get some inspiration here! ;-) Do not take this too seriously, though...
        </p>
        
        """ + "<table class='table table-striped table-condensed'>\n" + '\n'.join(scale_patterns) + '\n</table></p>'
        
    return s1 +  "\n" + s2
        
            
            
        
        
        
        
        
    