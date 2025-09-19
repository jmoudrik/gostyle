#coding: utf-8

import sys
import os
import Orange

from Orange.evaluation.testing import cross_validation,  proportion_test

from Orange.distance import Euclidean, Manhattan

from orange_hacks.fann_neural import FannNeuralLearner
from orange_hacks.stacking import StackedClassificationLearner
from orange_hacks.stacking_featurewise import FeaturewiseStackedClassificationLearner
from orange_hacks.knn_weighted import KnnWeightedLearner

#import run_ga

def get_pca_prep(N):
    def pca_preprocess_lt(learn_set, test_set):
        pca = Orange.projection.linear.PCA(learn_set, max_components=N, use_generalized_eigenvectors=True) #, standardize=True)
        
        return pca(learn_set),  pca(test_set)
    return pca_preprocess_lt

#def main( TRAIN_DATA='TABS/KGS_wide_by_player_60/results.tab' ):

if __name__ == "__main__":
    basedir = 'TABS/KGS_wide_final_best'
    basedir = 'TABS/style2_16_12_final_best_two'
    #extension = 'feature_0.tab'
    #extension = 'results.tab'
    for extension in ['results.tab'] :
    #for extension in ['feature_%d.tab' % fnum for fnum in xrange(55) ]:
    #for extension in ['feature_%d.tab' % fnum for fnum in [54] ]:
        TRAIN_DATA = os.path.join(basedir, extension)
        
        TRAIN_TABLE = Orange.data.Table(TRAIN_DATA)
        
        nn_nor2 = FannNeuralLearner( name='nn_standard 10,100,0.001',
                                    autorescale_output=True, 
                                    hidden_layers=[10],
                                    desired_error=0.001,
                                    #desired_error=0.02,
                                    iterations_between_reports=0, 
                                    max_epochs=100 )
        
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
                #Orange.regression.pls.PLSRegressionLearner(n_comp=3, name='pls3'), 
                ## best sa
                #Orange.regression.pls.PLSRegressionLearner(n_comp=4, name='pls4'), 
                #Orange.regression.pls.PLSRegressionLearner(n_comp=5, name='pls5'), 
                #Orange.regression.pls.PLSRegressionLearner(n_comp=6, name='pls6'), 
                
                #Orange.regression.tree.SimpleTreeLearner(name='simple tree'), 
                #Orange.regression.linear.LinearRegressionLearner(name='linear'), 
                ## best sa
                #Orange.regression.earth.EarthLearner(name='earth'), 
                #Orange.regression.lasso.LassoRegressionLearner(name='lasso'), 
                
                #Orange.classification.knn.kNNLearner(k=40, name='knn 40, rw=False',  rank_weight=False), 
                ## best sa
                #Orange.classification.knn.kNNLearner(k=50, name='knn 50, rw=False',  rank_weight=False), 
                #Orange.classification.knn.kNNLearner(k=50, distance_constructor=Manhattan(), name='knn 50, rw=False, p1', rank_weight=False), 
                #Orange.classification.knn.kNNLearner(k=50, distance_constructor=Manhattan(), name='knn 50, rw=False, p1', rank_weight=True), 
                #Orange.classification.knn.kNNLearner(k=60, name='knn 60, rw=False',  rank_weight=False), 
                #Orange.classification.knn.kNNLearner(k=50, name='knn 50',  rank_weight=True), 
                
                #KnnWeightedLearner( k=30, alpha=20, distance_constructor=Manhattan(),
                #                    name=u'wknn k=%d, α=%d, %s'%(30, 20, 'p1' ) ), 
                
                ## best
                KnnWeightedLearner( k=50, alpha=20, distance_constructor=Manhattan(),
                                    name=u'wknn k=%d, α=%d, %s'%(50, 20, 'p1' ) ), 
                
                ## best sa
                #KnnWeightedLearner( k=100, alpha=20, distance_constructor=Manhattan(),
                #                    name=u'wknn k=%d, α=%d, %s'%(100, 20, 'p1' ) ), 
                
                #KnnWeightedLearner( k=30, alpha=2, name='weighted knn 30,2' ),
                
                #nn_cas,
                ## best
                ## best sa
                #nn_nor2,
                
                Orange.ensemble.forest.RandomForestLearner(trees=50, name='random forrest 50'), 
                #Orange.ensemble.forest.RandomForestLearner(trees=100, name='random forrest 100'), 
                ##best
                #Orange.ensemble.forest.RandomForestLearner(trees=200, name='random forrest 200'), 
                #Orange.ensemble.forest.RandomForestLearner(trees=300, name='random forrest 300')
                
                ## svm sucks
                #Orange.classification.svm.SVMLearner(name='svm easy'),
                ] + [
                ##best
                Orange.ensemble.bagging.BaggedLearner(nn, t=t, name='bagged %d x '%t + nn.name) for nn in [ nn_nor2 ] for t in [20]
                ]
        
        learners = base_learners
        
        """
        for k in xrange(22, 31): #[20, 20, 22]:
            for alpha in xrange(18, 24): #[2, 3, 4, 5, 6]:
                for dist in [ Manhattan() ]: #Euclidean(), 
                    base_learners.append(
                        KnnWeightedLearner( k=k,
                                            alpha=alpha,
                                            distance_constructor=dist, 
                                            name=u'wknn k=%d, α=%d, %s'%(k, alpha, dist.__name__)) )
                    
        """
        ##
        ##  chtel jsem otestovat jak se bude chovat stacknn, kdyz se nn_2 poradne nauci, (vic epoch)
        ##
        
        stacknn = StackedClassificationLearner(base_learners, 
                                                 meta_learner=nn_meta, 
                                                 folds=4, 
                                                 name='stacking neural')
        
        
        learners =  base_learners + [ stacknn ] #, stacktree ]
        
        
        def print_stat():
            print 'fold'
            
        results = []
        for class_dom in [TRAIN_TABLE.domain.class_var] + [ TRAIN_TABLE.domain[x] for x in [-5, -4, -3] ]:
            new_domain = Orange.data.Domain(TRAIN_TABLE.domain.features + [class_dom])
            train_table = Orange.data.Table(new_domain, TRAIN_TABLE)
            
            train_table =  TRAIN_TABLE
            res = cross_validation( learners, train_table, folds=5,
            #res = proportion_test( learners, train_table, 0.1, 1,
                                     #store_classifiers=True,
                                     #store_examples=True,
                                     #preprocessors=(('LT', get_pca_prep(n_comp)),
                                     #callback=print_stat, 
                                     )
            results.append(res)
        
        print
        print TRAIN_DATA
        #print "PCA ",  n_comp
        
        def print_lsc(learner,  rmse, mean_rmse):
            s = "%25s: %5.3f (%.3f x better than 'mean')" % (learner.name, rmse, mean_rmse / rmse )
            print s.encode('utf-8')
            
        class mean_cmp:
            name = 'mean cmp'
        import numpy
            
        scores = list(sum(map(numpy.array,
                              map( Orange.evaluation.scoring.RMSE, results )))
                      / 4.0)
        
        assert learners[0].name ==  'mean'
        min_err, minl = scores[0],  learners[0]
        for rmse, learner in zip(scores, learners):
            if rmse < min_err:
                min_err = rmse
                minl = learner
            print_lsc(learner, rmse, scores[0])
        print "---- best ----"
        print_lsc(minl, min_err, scores[0])
        print
                
