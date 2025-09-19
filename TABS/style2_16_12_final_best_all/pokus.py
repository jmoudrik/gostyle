import logging
from logging import handlers

from models import *
from game_to_vec import *
from my_session import my_session_maker
import cl_strength, cl_style, cl_year,  cl_strength_by_player
import db_cache
import timer
import config
    
def get_feature_extractors(SPATIAL_dict_data, ALL_PAT_OSL, t=timer.Timer()):
    with t(log=True):
        spatial_dict = generate_spatial_dictionary(SPATIAL_dict_data, spatmin=500)
        logging.info('spatial dict made:\n %s\n -> %s'%(repr(SPATIAL_dict_data), repr(spatial_dict)))

    with t(log=True):
        # the pathway: game -> bw rawpat files -> bw transformed rawpat files -> bw summarized pat files
        bw_game_summarize = partial_right(process_game,
                                          partial_right(raw_patternscan_game, spatial_dict),
                                          [ partial_right(transform_rawpatfile,
                                                          #transform={ 'border':partial_right(minus, 1) },
                                                          ignore=['border', 'cont', 'capture']),
                                            summarize_rawpat_file
                                            ])
        all_pat = make_all_pat(ALL_PAT_OSL, bw_game_summarize)
        logging.info('all_pat made:\n %s\n -> %s'%(repr(ALL_PAT_OSL), repr(all_pat)))

    # Process One Side List
    gen_n_merge = [ ## Pattern features
                    (BWPatternVectorGenerator( bw_game_summarize,
                                               PatternVectorMaker(all_pat, N) ),
                     merger_fac() )
                    for N, merger_fac in itertools.product(
                        [200, 400, 600 , 800, 1000],
                        [
                            lambda : VectorApply(VectorSumMerger(), finish_fc=natural_rescale),
                            lambda : VectorApply(VectorSumMerger(), finish_fc=linear_rescale),
                            lambda : VectorArithmeticMeanMerger()
                        ]
                    )
                   ] + [
                    ## local sequences
                    ( BWLocalSeqVectorGenerator(omega), VectorArithmeticMeanMerger())
                        for omega in range(5, 16)
                   ] + [
                    ## BWBdist
                    (BWBdistVectorGenerator(by_moves=[A, B, C]), VectorArithmeticMeanMerger()) 
                    for A, B, C in itertools.product(
                        [10, 16], 
                        [44, 54, 64],
                        [160, 200, 240]
                    )
                   ] + [
                    ## BWCapture
                    (BWCaptureVectorGenerator(by_moves=[A, B]), VectorArithmeticMeanMerger()) 
                    for A, B in itertools.product(
                        [40, 60, 80],
                        [160, 200, 240]
                    )
                   ] + [
                    ## win stat
                    (BWWinStatVectorGenerator(), VectorArithmeticMeanMerger()),
                    (BWWinPointsStatVectorGenerator(), VectorArithmeticMeanMerger())
                   ]
    
    best_str = [
        (BWPatternVectorGenerator( bw_game_summarize,
                                   PatternVectorMaker(all_pat, 1000) ), VectorArithmeticMeanMerger()),
        (BWLocalSeqVectorGenerator(10), VectorArithmeticMeanMerger()), 
        (BWBdistVectorGenerator(by_moves=[10, 64, 200]), VectorArithmeticMeanMerger()), 
        (BWCaptureVectorGenerator(by_moves=[60, 240]), VectorArithmeticMeanMerger()),
        
        (BWWinStatVectorGenerator(), VectorArithmeticMeanMerger()),
        (BWWinPointsStatVectorGenerator(), VectorArithmeticMeanMerger()), 
    ]
    
    best_sty = [
        (BWPatternVectorGenerator( bw_game_summarize,
                                   PatternVectorMaker(all_pat, 600) ),
                                   VectorApply(VectorSumMerger(), finish_fc=linear_rescale)), 
        (BWLocalSeqVectorGenerator(5), VectorArithmeticMeanMerger()), 
        (BWBdistVectorGenerator(by_moves=[16, 64, 160]), VectorArithmeticMeanMerger()), 
        (BWCaptureVectorGenerator(by_moves=[40, 160]), VectorArithmeticMeanMerger()),
        
        (BWWinStatVectorGenerator(), VectorArithmeticMeanMerger()),
        (BWWinPointsStatVectorGenerator(), VectorArithmeticMeanMerger()), 
    ]
    
    gen_n_merge = best_sty
    
    return gen_n_merge
    
def get_pathway(SPATIAL_dict_data, ALL_PAT_OSL, **kwargs):
    fe = get_feature_extractors(SPATIAL_dict_data, ALL_PAT_OSL, **kwargs)
    for num, f in enumerate(fe):
        print num, f
    
    vg_osl = OSLVectorGenerator(fe)
    
    return vg_osl

def main():
    t =  timer.Timer()
    ## import'n'init

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # log into file
    ch = handlers.WatchedFileHandler('LOG', mode='w')
    logger.addHandler(ch)
    # and on the console as well
    st = logging.StreamHandler()
    logger.addHandler(st)

    #db_cache.init_cache(filename='/media/ramdisk/CACHE_kgs_wide_60.db')
    #s = my_session_maker(filename='GODB.db')

    ## Prepare data

    with t(log=True):
        #choice = 'gokifu'
        #choice = 'year'
        #choice = 'GTL'
        choice = 'GoGoD1'
        #choice = 'KGS_wide_120'
        if choice ==  'KGS_wide_120':
            # this should be left the same
            s = my_session_maker(filename='GODB_kgs_wide_120.db')
            db_cache.init_cache(filename='/media/VFS2/CACHE_kgs_wide.db')
            assert config.OUTPUT_DIR =='/media/VFS2/OUT_KGS_wide'
            
            KGS = s.query(GameList).filter(GameList.name == 'KGS wide 120').one()
            SPATIAL_dict_data = KGS
            
            dm_name = cl_strength_by_player.get_datamap_name(KGS)
            DATAMAP = s.query(DataMap).filter(DataMap.name == dm_name).one()
            ALL_PAT_OSL = s.query(OneSideList).filter(OneSideList.name == dm_name + ' - OSL merged, 20% sample').one()
            
        elif choice == 'GoGoD1':
            s = my_session_maker(filename='GODB.db')
            db_cache.init_cache(filename='/media/VFS2/CACHE_gostyle.db')
            assert config.OUTPUT_DIR == '/media/VFS2/OUT_GOGOD'
            
            # style
            GOGOD = s.query(GameList).filter(GameList.name == 'GoGoD').one()

            # datamap:    OSL with games -> style vector
            dm_name = cl_style.get_datamap_name(GOGOD, 16, 12)
            DATAMAP = s.query(DataMap).filter(DataMap.name == dm_name).one()

            ALL_PAT_OSL = s.query(OneSideList).filter(OneSideList.name == dm_name + ' - OSL merged').one()
            SPATIAL_dict_data = s.query(GameList).filter(GameList.name == dm_name + ' - Spatial Dict').one()
            
        elif choice == 'GoGoD2':
            s = my_session_maker(filename='GODB.db')
            db_cache.init_cache(filename='/media/VFS2/CACHE_gostyle.db')
            assert config.OUTPUT_DIR == '/media/VFS/OUT_GOGOD'
            
            # style
            GOGOD = s.query(GameList).filter(GameList.name == 'GoGoD').one()

            # datamap:    OSL with games -> style vector
            dm_name = cl_style.get_datamap_name(GOGOD, 192, 1)
            DATAMAP = s.query(DataMap).filter(DataMap.name == dm_name).one()

            ALL_PAT_OSL = s.query(OneSideList).filter(OneSideList.name == dm_name + ' - OSL merged').one()
            SPATIAL_dict_data = s.query(GameList).filter(GameList.name == dm_name + ' - Spatial Dict').one()
            
        elif choice ==  'KGS_wide_60':
            db_cache.init_cache(filename='/media/ramdisk/CACHE_kgs_wide_60.db')
            s = my_session_maker(filename='GODB_kgs_wide_60.db')
            
            KGS = s.query(GameList).filter(GameList.name == 'KGS wide').one()
            SPATIAL_dict_data = KGS
            
            dm_name = cl_strength_by_player.get_datamap_name(KGS)
            DATAMAP = s.query(DataMap).filter(DataMap.name == dm_name).one()
            ALL_PAT_OSL = s.query(OneSideList).filter(OneSideList.name == dm_name + ' - OSL merged, 30% sample').one()
            
        elif choice ==  'GTL':
            # strength
            GTL = s.query(GameList).filter(GameList.name == 'Go Teaching Ladder').one()
            
            dm_name = cl_strength.get_datamap_name(GTL, 5, 5, 24)
            SPATIAL_dict_data = s.query(GameList).filter(GameList.name == 'Spatial Dict Games').one()
            ALL_PAT_OSL = s.query(OneSideList).filter(OneSideList.name == 'Go Teaching Ladder - all_pat OSL').one()
            DATAMAP = s.query(DataMap).filter(DataMap.name == dm_name).one()

            
        elif choice == 'gokifu':

            GOKIFU = s.query(GameList).filter(GameList.name == 'Gokifu KGS + Pro').one()

            SPATIAL_dict_data = GOKIFU
            ALL_PAT_OSL = s.query(OneSideList).filter(OneSideList.name == GOKIFU.name + ' - all_pat OSL').one()

            DATAMAP = s.query(DataMap).filter(DataMap.name == cl_strength.get_datamap_name(GOKIFU, 100, 1)).one()

        elif choice ==  'year':
            GOGOD = s.query(GameList).filter(GameList.name == 'GoGoD').one()

            DATAMAP = s.query(DataMap).filter(DataMap.name == cl_year.get_datamap_name(GOGOD, 20, 500)).one()

            ALL_PAT_OSL = s.query(OneSideList).filter(OneSideList.name == DATAMAP.name + ' - OSL merged, sampled 33%').one()
            SPATIAL_dict_data = s.query(GameList).filter(GameList.name == DATAMAP.name + ' - Spatial Dict, sampled 50%').one()
        else:
            assert False


        logging.info('data loaded')

    features_on_their_own = True
    
    ## pathway - features together
    fes = get_feature_extractors(SPATIAL_dict_data, ALL_PAT_OSL, t=t)
    for num, f in enumerate(fes):
        print num, f
    vg_osl= OSLVectorGenerator(fes)

    with t(log=True):
        tab = make_tab_file(DATAMAP,  vg_osl )
        logging.info('tab file written:\n %s\n -> %s'%(repr(DATAMAP), tab))
        
    ## pathway - features one by one
    if features_on_their_own:
        with t(log=True):
            for num, fe in enumerate(fes):
                vg_osl = OSLVectorGenerator([fe])
                with t(log=True):
                    tab = make_tab_file(DATAMAP,  vg_osl )
                    logging.info('tab file for feature written:\n %d\n %s\n -> %s'%(num, repr(DATAMAP), tab))
        

if __name__ == '__main__':
    main()
