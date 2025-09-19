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

import run_ga

def get_pca_prep(N):
    def pca_preprocess_lt(learn_set, test_set):
        pca = Orange.projection.linear.PCA(learn_set, max_components=N, use_generalized_eigenvectors=True) #, standardize=True)
        
        return pca(learn_set),  pca(test_set)
    return pca_preprocess_lt

#def main( TRAIN_DATA='TABS/KGS_wide_by_player_60/results.tab' ):

if __name__ == "__main__":
    basedir = 'TABS/KGS_wide_final_all_feat'
    basedir = 'TABS/KGS_wide_final_pat_aver'
    basedir = 'TABS/KGS_wide_final_best'
    #basedir = 'TABS/style2_16_12'
    #extension = 'feature_0.tab'
    #extension = 'results.tab'
    for extension in ['results.tab'] :
    #for extension in ['feature_%d.tab' % fnum for fnum in xrange(49) ]:
    #for extension in ['feature_%d.tab' % fnum for fnum in [0, 1] ]:
    #for extension in ['results.tab'] + ['feature_%d.tab' % fnum for fnum in xrange(8) ]:
    #for n_comp in range(4):
    #for n_comp in range(0, 45, 5):
    #for class_dom in [TRAIN_TABLE.domain.class_var] + [ TRAIN_TABLE.domain[x] for x in [-5, -4, -3] ]:
        TRAIN_DATA = os.path.join(basedir, extension)
        TRAIN_TABLE = Orange.data.Table(TRAIN_DATA)
        #new_domain = Orange.data.Domain(TRAIN_TABLE.domain.features + [class_dom])
        #train_table = Orange.data.Table(new_domain, TRAIN_TABLE)
        #print class_dom
        
        train_table =  TRAIN_TABLE
        
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
                                    desired_error=0.001,
                                    #desired_error=0.02,
                                    iterations_between_reports=0, 
                                    max_epochs=100 )
        
        nn_nor3 = FannNeuralLearner( name='nn_standard 10,100,0.005',
                                    autorescale_output=True, 
                                    hidden_layers=[10],
                                    desired_error=0.005,
                                    #desired_error=0.02,
                                    iterations_between_reports=0, 
                                    max_epochs=100 )
        
        nn_nor4 = FannNeuralLearner( name='nn_standard 4,4,200,0.005',
                                    autorescale_output=True, 
                                    hidden_layers=[4, 4],
                                    desired_error=0.005,
                                    #desired_error=0.02,
                                    iterations_between_reports=0, 
                                    max_epochs=200 )
        
        nn_cas1 = FannNeuralLearner(name='nn_cascade ',
                                    nn_type='cascade', 
                                    max_neurons=2,
                                    neurons_between_reports=0, # 0 turns it off
                                    desired_error=0.03,
                                    autorescale_output=True )
        
        nn_cas2 = FannNeuralLearner(name='nn_cascade ',
                                    nn_type='cascade', 
                                    max_neurons=5,
                                    neurons_between_reports=0, # 0 turns it off
                                    desired_error=0.01, 
                                    autorescale_output=True )
        
        nn_meta = FannNeuralLearner( name='nn_meta',
                                    autorescale_output=True, 
                                    hidden_layers=[10],
                                    desired_error=0.005,
                                    iterations_between_reports=0, 
                                    max_epochs=100 )
        
        knnw = KnnWeightedLearner( k=50, alpha=20, distance_constructor=Manhattan(),
                                    name=u'wknn k=%d, α=%d, %s'%(50, 20, 'p1' ) )
        
        base_learners = [
                ## do not delete
                Orange.regression.mean.MeanLearner(name='mean'), 
                
                #Orange.regression.pls.PLSRegressionLearner(n_comp=2, name='pls2'), 
                ## best
                Orange.regression.pls.PLSRegressionLearner(n_comp=3, name='pls3'), 
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

        nn_test = lambda X : FannNeuralLearner( name='nn_standard %.1f 10,100,0.001'%(X),
                                autorescale_output=True, 
                                autorescale_lower_bound=-X, 
                                autorescale_upper_bound=X, 
                                hidden_layers=[10],
                                desired_error=0.001,
                                #desired_error=0.02,
                                iterations_between_reports=0, 
                                max_epochs=100 )
        
        base_learners_nn =  [
            Orange.regression.mean.MeanLearner(name='mean'), 
        ] + [ nn_test(X) for X in [0.9, 0.95, 1.0, 1.05, 1.1, 1.15] ]
        
        
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
        
        fw_stacknn = FeaturewiseStackedClassificationLearner(
                                                 base_learners, 
                                                 meta_learner=nn_nor2, 
                                                 folds=10, 
                                                 name='fw stacking neural')
        
        stacktree = StackedClassificationLearner(base_learners, 
                                                 meta_learner=Orange.ensemble.forest.RandomForestLearner(trees=100, name='meta random forrest'), 
                                                 folds=4, 
                                                 name='stacking tree')
        
        fw_stacktree = FeaturewiseStackedClassificationLearner(
                                                 base_learners, 
                                                 meta_learner=Orange.ensemble.forest.RandomForestLearner(trees=100, name='meta random forrest'), 
                                                 folds=4, 
                                                 name='fw stacking tree')
        
        
        #learners =  base_learners +  [ stacknn, stacktree ]
        #learners =  base_learners + [ stacknn ] #, stacktree ]
        #learners =  base_learners #+  [ fwstack_tree ]
        learners = base_learners_nn
        #learners = [ base_learners[0] , 
        #             stacknn, 
        #             run_ga.get_learner(((67, 4), [0, 2, 23, 25, 28, 33, 36, 57, 86]))
        #]
        
        def print_stat():
            print 'fold'
            
        res = cross_validation( learners, train_table, folds=5,
        #res = proportion_test( learners, train_table, 0.7, 1,
                                 #store_classifiers=True,
                                 #store_examples=True,
                                 #preprocessors=(('LT', get_pca_prep(n_comp)),
                                 callback=print_stat, 
                                 )
        
        print
        print TRAIN_DATA
        #print "PCA ",  n_comp
        
        def print_lsc(learner,  rmse, mean_rmse):
            s = "%25s: %5.3f (%.3f x better than 'mean')" % (learner.name, rmse, mean_rmse / rmse )
            print s.encode('utf-8')
            
        class mean_cmp:
            name = 'mean cmp'
            
        scores = Orange.evaluation.scoring.RMSE(res)
        #scores =  [9.307] +  scores
        #learners =  [mean_cmp()] +  learners
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
        
        #print res.examples[0][0].get_metas()
        
        #if True:
        if False:
            assert len(res.examples[0]) == len(res.results)
            print res.examples[0][0].get_metas()
            
                
            d = {}
            for ex, re in zip(res.examples[0], res.results):
                assert ex[-1] == re.actual_class
                
                datasize = float(ex.get_metas()[-4])
                for i, guess in enumerate(re.classes):
                    diff = re.actual_class - guess
                    d.setdefault(i, []).append((re.actual_class, diff, guess, datasize))
            
            for i, l in d.items():
                fn = 'OUT/class_diff_guess_size_%d.dat' % i
                with open(fn, 'w') as fout:
                    for tup in sorted(l):
                        fstr = "%s " * len(tup) + "\n"
                        fout.write(fstr % tup)
                

#gnuplot> set style data boxplot
#gnuplot> set style boxplot nooutliers sorted
#gnuplot> plot './residuals_class_size_mean.dat' using (0.5):3:(0.5):2
