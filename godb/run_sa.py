#coding: utf-8

import sys

from functools import wraps

import Orange

from Orange.evaluation.testing import cross_validation,  proportion_test

from Orange.distance import Euclidean, Manhattan

from orange_hacks.fann_neural import FannNeuralLearner
from orange_hacks.stacking import StackedClassificationLearner
from orange_hacks.stacking_featurewise import FeaturewiseStackedClassificationLearner
from orange_hacks.knn_weighted import KnnWeightedLearner

def pca_preprocess_lt(learn_set, test_set):
    
    pca = Orange.projection.linear.PCA(learn_set) #, standardize=True)
    
    return pca(learn_set),  pca(test_set)

#def main( TRAIN_DATA='TABS/KGS_wide_by_player_60/results.tab' ):

if __name__ == "__main__":
    basedir = 'TABS/KGS_wide_by_player_60_featurewise/'
    #basedir = 'TABS/KGS_wide_by_player_60_featurewise_log/'
    #basedir = 'TABS/KGS_wide_by_player_120_fw/'
    basedir = 'TABS/KGS_wide_by_player_120_winstat_fw/'
    #for extension in ['results.tab']: # + ['feature_%d.tab' % fnum for fnum in xrange(9) ]:
    #for extension in ['feature_%d.tab' % fnum for fnum in xrange(9) ]:
    for extension in ['results.tab']:
        TRAIN_DATA=basedir+extension
    
            
        train_table = Orange.data.Table(TRAIN_DATA)
        
        nn_nor = FannNeuralLearner( name='nn_standard 8',
                                    autorescale_output=True, 
                                    hidden_layers=[8],
                                    #desired_error=0.003,
                                    desired_error=0.02,
                                    iterations_between_reports=0, 
                                    max_epochs=50 )
        
        nn_nor2 = FannNeuralLearner( name='nn_standard 10,100,0.001',
                                    autorescale_output=True, 
                                    hidden_layers=[10],
                                    desired_error=0.005,
                                    #desired_error=0.02,
                                    iterations_between_reports=0, 
                                    max_epochs=100 )
        
        nn_cas1 = FannNeuralLearner(name='nn_cascade ',
                                    nn_type='cascade', 
                                    max_neurons=2,
                                    neurons_between_reports=0, # 0 turns it off
                                    desired_error=0.03,
                                    autorescale_output=True )
        
        nn_meta = FannNeuralLearner( name='nn_meta',
                                    autorescale_output=True, 
                                    hidden_layers=[10],
                                    desired_error=0.005,
                                    iterations_between_reports=0, 
                                    max_epochs=100 )
        
        base_learners = [
                ## do not delete
                Orange.regression.mean.MeanLearner(name='mean'), 
                
                Orange.regression.pls.PLSRegressionLearner(n_comp=2, name='pls2'), 
                ## best
                Orange.regression.pls.PLSRegressionLearner(n_comp=3, name='pls3'), 
                Orange.regression.pls.PLSRegressionLearner(n_comp=4, name='pls4'), 
                Orange.regression.pls.PLSRegressionLearner(n_comp=5, name='pls5'), 
                Orange.regression.pls.PLSRegressionLearner(n_comp=6, name='pls6'), 
                
                Orange.regression.linear.LinearRegressionLearner(name='linear'), 
                Orange.regression.lasso.LassoRegressionLearner(name='lasso'), 
                Orange.regression.earth.EarthLearner(name='earth'), 
                Orange.regression.tree.TreeLearner(name='tree'), 
                Orange.regression.tree.SimpleTreeLearner(name='simple tree'), 
                
                Orange.classification.knn.kNNLearner(k=40, name='knn 40, rw=False',  rank_weight=False), 
                Orange.classification.knn.kNNLearner(k=50, name='knn 50, rw=False',  rank_weight=False), 
                Orange.classification.knn.kNNLearner(k=50, distance_constructor=Manhattan(), name='knn 50, rw=False, p1', rank_weight=False), 
                Orange.classification.knn.kNNLearner(k=50, distance_constructor=Manhattan(), name='knn 50, rw=True, p1', rank_weight=True), 
                Orange.classification.knn.kNNLearner(k=60, name='knn 60, rw=False',  rank_weight=False), 
                Orange.classification.knn.kNNLearner(k=50, name='knn 50, rw=True',  rank_weight=True), 
               
                KnnWeightedLearner( k=30, alpha=20, distance_constructor=Manhattan(),
                                    name=u'wknn k=%d, α=%d, %s'%(30, 20, 'p1' ) ), 
                
                ## best
                KnnWeightedLearner( k=50, alpha=20, distance_constructor=Manhattan(),
                                    name=u'wknn k=%d, α=%d, %s'%(50, 20, 'p1' ) ), 
                
                KnnWeightedLearner( k=100, alpha=20, distance_constructor=Manhattan(),
                                    name=u'wknn k=%d, α=%d, %s'%(100, 20, 'p1' ) ), 
                
                KnnWeightedLearner( k=30, alpha=2, name='weighted knn 30,2' ),
                
                nn_cas1,
                ## best
                nn_nor,
                nn_nor2,
                
                Orange.ensemble.forest.RandomForestLearner(trees=5, name='random forrest 5'), 
                Orange.ensemble.forest.RandomForestLearner(trees=10, name='random forrest 10'), 
                Orange.ensemble.forest.RandomForestLearner(trees=25, name='random forrest 25'), 
                Orange.ensemble.forest.RandomForestLearner(trees=50, name='random forrest 50'), 
                Orange.ensemble.forest.RandomForestLearner(trees=100, name='random forrest 100'), 
                ##best
                Orange.ensemble.forest.RandomForestLearner(trees=200, name='random forrest 200'), 
                Orange.ensemble.forest.RandomForestLearner(trees=300, name='random forrest 300'), 
                
                ## svm sucks
                Orange.classification.svm.SVMLearner(name='svm'), 
        Orange.regression.pls.PLSRegressionLearner(n_comp=7, name='pls7'), 
        Orange.regression.pls.PLSRegressionLearner(n_comp=8, name='pls8'), 
        Orange.regression.pls.PLSRegressionLearner(n_comp=9, name='pls9'), 
        Orange.regression.pls.PLSRegressionLearner(n_comp=10, name='pls10'), 
        ]
        ##
        ##  chtel jsem otestovat jak se bude chovat stacknn, kdyz se nn_2 poradne nauci, (vic epoch)
        ##
        
        get_stacknn = lambda BL : StackedClassificationLearner(BL, 
                                                 meta_learner=nn_meta, 
                                                 folds=4, 
                                                 name='stacking neural')
        import logging
        logging.getLogger().setLevel(logging.INFO)
        
        import copy
        import db_cache
        db_cache.init_cache(filename='./CACHE_EVAL.db') #,  log=True)
        
        def print_BI(BI):
            print "base learners:", sorted(BI)
            sys.stdout.flush()
            
        def i2bl(indices):
            r = []
            for i in indices:
                r.append(base_learners[i])
            return r
                
        def print_sep():
            print "-------------"
        
        def BI2sortedlist(f):
            @wraps(f)
            def g(BI):
                return f(sorted(BI))
            return g
        
        @BI2sortedlist
        @db_cache.cache_result
        @db_cache.declare_pure_function
        def evaluate(BI, prop=0.7, folds=None):
            BL = i2bl(BI)
            snn = get_stacknn(BL)
            assert prop or folds
            assert not ( prop and folds )
            if prop:
                res = proportion_test( [snn], train_table, prop, 1 )
            if folds:
                res = cross_validation( [snn], train_table, folds=folds )
        
            return Orange.evaluation.scoring.RMSE(res)[0]
        
        def next_b(BI):
            l = len(BI)
            ret = copy.copy(BI)
            mod = False
            
            if l > 1 and random.random() < 0.6:
                del ret[ random.randint(0, l-1) ]
                mod = True
                
            if random.random() <  0.5:
                newi = random.randint(0, len(base_learners) - 1) 
                if not newi in ret:
                    ret.append(newi) 
                    mod = True
                
            if not mod:
                ret = next_b(BI)
                
            return ret
            
        
        import random, math
        
        for i,  bl in enumerate(base_learners):
            print i,  bl
            
        
        k_max = 500
        k = 0
        
        b = [0, 2, 18, 23, 29]
        e = evaluate(b)
        
        print_sep()
        print "initial e: %.3f" % (e)
        print_BI(b)
        sys.stdout.flush()
        
        b_best = b
        e_best = e
        
        try:
            while True:
                print_sep()
                k += 1
                print "%d. ITERATION" % k
                T = 0.9 ** k
                
                print "current ", 
                print_BI(b)
                print "current e: %.3f" % (e)
                print "next    ", 
                b_next = next_b(b)
                print_BI(b_next)
                sys.stdout.flush()
                e_next = evaluate(b_next)
                print "next    e: %.3f" % (e_next)
                
                # locally better
                if e_next < e:
                    b, e = b_next, e_next
                    print "climbing the hill"
                else:
                    pw = math.exp( (e - e_next) / T )
                    p = random.random()
                    print "with %.2f%% going worse, " % (100 * pw), 
                    # locally worse, but hot enough
                    if p < pw :
                        print  "gone worse"
                        b, e = b_next, e_next
                    else:
                        print  "not yet"
                        
                if e < e_best:
                    print "found global improvement,\n  old e: %.3f\n  new e: %.3f" % (e_best, e)
                    b_best, e_best = b, e
                
                if k > k_max:
                    break
                
        finally:
            print_sep()
            print "best e: %.3f" % (e_best)
            print_BI(b_best)
            
            
            