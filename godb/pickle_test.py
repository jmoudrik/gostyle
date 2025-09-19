import Orange

from models import *
from game_to_vec import *

from my_session import my_session_maker
            
import pickle
import random

import base_learners

def main():
    ## init stuff
    logger = logging.getLogger()
    logger.setLevel(logging.WARNING)

    ###
    basedir = './TABS/KGS_wide_final_fast'
    
    table = Orange.data.Table(os.path.join(basedir, 'results_short.tab'))
    
    table = Orange.data.Table(table.domain,
                                    random.sample(table,
                                                  len(table)/10))
    
    learner = base_learners.get_initial_hand_tuned_learner()
    cl = learner(table)
    
    
    with open('TEST.PKL', 'wb') as fout:
        pickle.dump(cl, fout)
        
    print "saved"
        
    ##
    
    
    
    
    

if __name__ == '__main__':
    print main()
    
    with open('TEST.PKL', 'rb') as fin:
        cl_loaded = pickle.load(fin)
        
    pass    
