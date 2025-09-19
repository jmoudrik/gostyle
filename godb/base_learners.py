#coding: utf-8

import itertools
import sys

import Orange
from Orange.distance import Euclidean, Manhattan

from orange_hacks.fann_neural import FannNeuralLearner
from orange_hacks.stacking import StackedClassificationLearner
from orange_hacks.knn_weighted import KnnWeightedLearner

NN_learners = [
FannNeuralLearner( name='nn_standard, hidden=%d, error=%f, max epochs=%d'%(hidden, error, max_e), 
            autorescale_output=True, 
            hidden_layers=[hidden],
            desired_error=error,
            iterations_between_reports=0, 
            max_epochs=max_e ) for hidden, error, max_e in itertools.product(
                    [10, 20], 
                    [0.001, 0.005], 
                    [50, 100, 200, 500]
            )
]

base_learners = [
        ## Mean regression
        Orange.regression.mean.MeanLearner(name='mean'), 
        ] + [
        ## PLS
        Orange.regression.pls.PLSRegressionLearner(n_comp=n_comp, name='pls %d'%n_comp)
                for n_comp in xrange(2, 11)
        ] + [
        ## KNN
        KnnWeightedLearner( k=k, alpha=alpha, distance_constructor=dist(), 
                            name=u'wknn k=%d, α=%d, %s'%( k,  alpha, dist) )
            for k, alpha, dist in itertools.product(
                [10, 20, 30, 40,  50, 60], 
                [10, 20], 
                [Manhattan, Euclidean]
            )
        ] + [
        ## Random forrest
        Orange.ensemble.forest.RandomForestLearner(trees=n_trees, name='random forrest %d'%(n_trees))
                for n_trees in [10, 25, 50, 100, 200]
        ## Neural networks
        ] + NN_learners + [
        ## Bagged Neural networks
        Orange.ensemble.bagging.BaggedLearner(nn, t=t, name='bagged %d x '%t + nn.name)
            for nn, t in itertools.product(
                NN_learners,
                [20, 40]
            )
        ]

def i2bl(indices):
    r = []
    for i in indices:
        r.append(base_learners[i])
    return r

get_stacknn = lambda BL, ML, folds : StackedClassificationLearner(BL, 
                                         meta_learner=ML, 
                                         folds=folds, 
                                         name='stacking neural')

def get_initial_hand_tuned_learner():
    folds = 4
    ML = base_learners[44]
    BL = i2bl([0, 2, 28, 36, 57])
    return get_stacknn(BL, ML, folds)

def print_learners():
    for i,  bl in enumerate(base_learners):
        print i, bl

if __name__ == '__main__':
    print_learners()
    