import os
#import pickle
import cPickle as pickle
import logging
import random

import config
import godb
from godb import db_cache
import Orange
from pic_utils import generate_str_pic,  generate_style_pic
import str_patterns


def dummy_warn(*args,  **kwargs):
    logging.warn("Calling a dummy function.")

style_vg_osl = dummy_warn
style_cls = [None] * 4
#style_cls = [ lambda x : 1 +  10 *  random.random() ] * 4
style_sigmas = [1.43, 1.63, 1.42, 1.48 ]
style_keys = [ an[:2] for an in godb.data_about_players.Data.questionare_annotations ]
style_feat_domain = None

str_vg_osl = dummy_warn
str_cl = None
#str_cl = lambda x : -5 +  26 * random.random()
str_sigma = 2.63
str_feat_domain = None

def INIT_str_pathway():
    logging.info("Initializing str pathway")
    basedir =  os.path.join(config.TABS_DIR, 'KGS_wide_final_fast')
    
    spatial_dict = godb.utils.ResultFile(os.path.join(basedir, 'patterns.spat'))
    all_pat = godb.utils.ResultFile(os.path.join(basedir, 'all.pat'))
    train_table = Orange.data.Table(os.path.join(basedir, 'results.tab'))
    if config.RUNNING_LOCALLY:
        train_table = Orange.data.Table(train_table.domain,
                                        random.sample(train_table,
                                                      len(train_table)/20))
        
    
    ## pathway
    fes = godb.pokus.get_feature_extractors_from_file('fast_strength',
                                                      all_pat,
                                                      spatial_dict)
    global str_vg_osl
    str_vg_osl = godb.game_to_vec.OSLVectorGenerator(fes)
    
    ## domain
    
    full_domain = train_table.domain
    
    global str_feat_domain
    str_feat_domain = Orange.data.Domain(full_domain.features)
    
    ## classifier
    
    global str_cl
    
    pfile = os.path.join(config.PICKLE_DIR,  "STRENGTH.pkl")
    if os.path.exists(pfile):
        logging.info("Unpickling str classifier.")
        with open(pfile, 'rb') as fin:
            str_cl = pickle.load(fin)
    else:
        logging.info("No pickle, have to train first...")
        learner = godb.base_learners.get_initial_hand_tuned_learner()
        str_cl = learner(train_table)
        with open(pfile, 'wb') as fout:
            pickle.dump(str_cl, fout)
    
def INIT_style_pathway():
    logging.info("Initializing style pathway")
    basedir =  os.path.join(config.TABS_DIR, 'style2_16_12_final_best_all')
    
    spatial_dict = godb.utils.ResultFile(os.path.join(basedir, 'patterns.spat'))
    all_pat = godb.utils.ResultFile(os.path.join(basedir, 'all.pat'))
    train_table = Orange.data.Table(os.path.join(basedir, 'results.tab'))
    
    if config.RUNNING_LOCALLY:
        train_table = Orange.data.Table(train_table.domain,
                                        random.sample(train_table,
                                                      len(train_table)/5))
        
    
    ## pathway
    fes = godb.pokus.get_feature_extractors_from_file('best_style',
                                                      all_pat,
                                                      spatial_dict)
    global style_vg_osl
    style_vg_osl= godb.game_to_vec.OSLVectorGenerator(fes)
    
    ## domain
    
    full_domain = train_table.domain
    
    global style_feat_domain 
    style_feat_domain = Orange.data.Domain(full_domain.features)
    
    ## classifier
    
    global style_cls, style_keys
    
    pfile = os.path.join(config.PICKLE_DIR,  "STYLE.pkl")
    if os.path.exists(pfile):
        logging.info("Unpickling style classifiers.")
        print "Unpickling style classifiers."
        with open(pfile, 'rb') as fin:
            style_cls = pickle.load(fin)
    else:
        logging.info("No pickle, have to train first...")
        learner = godb.base_learners.get_initial_hand_tuned_learner()
        
        class_doms = [ full_domain[x] for x in
                       godb.data_about_players.Data.questionare_annotations]
        tts = []
        for class_dom in class_doms:
            new_domain = Orange.data.Domain(full_domain.features + [class_dom])
            tts.append(Orange.data.Table(new_domain, train_table))
            
        style_cls = map(learner, tts)
        with open(pfile, 'wb') as fout:
            pickle.dump(style_cls, fout)
    
            
#INIT_str_pathway()
#INIT_style_pathway()

def str2dan_kyu(strength):
    d = strength.copy()
    
    rank = godb.rank.Rank.from_key(float(strength['val']))
    d['val'] = str(rank)
    return d
    
import time

#{ 'val' : 10, 'sigma' : 10192, 'pic' : 'out.png' }
def str_regression(osl, out_dir):
    global str_vg_osl, str_cl, str_sigma, str_feat_domain
    
    # get the feature vector
    vec = str_vg_osl(osl)
    
    # make classification instance out of it
    inst = Orange.data.Instance(str_feat_domain, list(vec) )
    
    # compute strength
    strength = min(20, max(-5.0, float(str_cl(inst))))
    
    str_pat = str_patterns.get_str_patterns_html(out_dir, inst)
    
    return str_pat, {'val': strength, 
            'sigma': str_sigma,
            'pic' : generate_str_pic(out_dir, strength, str_sigma)
            }

#{'ag': { 'val' : 10, 'sigma' : 10192, 'pic' : 'out.png' } }
def style_regression(osl, out_dir):
    global style_vg_osl, style_cls, style_sigmas, style_keys, style_feat_domain
    
    vec = style_vg_osl(osl)
    
    # make classification instance out of it
    inst = Orange.data.Instance(style_feat_domain, list(vec) )
    
    styles = [ max(1.0, min(10.0, float(cl(inst)))) for cl in style_cls ]
    ret = {}
    for index, key in enumerate(style_keys):
        ret[key] = {
            'val': styles[index],
            'sigma': style_sigmas[index],
            'pic' : generate_style_pic(out_dir,
                                       styles[index],
                                       style_sigmas[index])
            }
        
    return ret
    
def is_style_unreliable(strength, style):
    pass
    return False

def get_relevant_pros(style):
    global style_keys
    
    return godb.data_about_players.get_interesting_pros(
                [ style[key]['val'] for key in style_keys ], 
                config.NUM_TOP_PROS,
                config.NUM_BOTTOM_PROS )


if __name__ == '__main__':
    d = {
	 'te' : { 'val': 1, 'sigma' : 1.2, 'pic': 'out2.png'},
	 'or' : { 'val': 1, 'sigma' : 1.2, 'pic': 'out2.png'},
	 'ag' : { 'val': 1, 'sigma' : 1.2, 'pic': 'out2.png'},
	 'th' : { 'val': 1, 'sigma' : 1.2, 'pic': 'out2.png'},
         }
    print get_relevant_pros(d)
    
    #print str2dan_kyu({'val': 10})
    pass
    
    #INIT_str_pathway()
    
    
    