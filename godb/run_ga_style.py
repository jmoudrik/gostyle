#coding: utf-8

import sys
import os
import logging
import db_cache
import copy
import multiprocessing
import time
import numpy

from functools import wraps
import random

import Orange
from Orange.evaluation.testing import cross_validation,  proportion_test
from Orange.distance import Euclidean, Manhattan

from orange_hacks.fann_neural import FannNeuralLearner
from orange_hacks.stacking import StackedClassificationLearner
from orange_hacks.stacking_featurewise import FeaturewiseStackedClassificationLearner
from orange_hacks.knn_weighted import KnnWeightedLearner
import timer

import data_about_players



from base_learners import base_learners

basedir = '../TABS/style2_16_12_final_best_all'

TRAIN_DATA= os.path.join(basedir, 'results.tab')
#TRAIN_DATA= os.path.join(basedir, 'feature_1.tab')

random.seed(10)

TRAIN_TABLE = Orange.data.Table(TRAIN_DATA)

def init():
    logging.getLogger().setLevel(logging.INFO)
    db_cache.init_cache(filename='./CACHE_EVAL_STYLE.db') #,  log=True)
    print os.getpid()

print len(TRAIN_TABLE)

def print_BI(BI):
    print "base learners:", sorted(BI)
    sys.stdout.flush()

def i2bl(indices):
    r = []
    for i in indices:
        r.append(base_learners[i])
    return r

get_stacknn = lambda BL, ML, folds : StackedClassificationLearner(BL,
                                         meta_learner=ML,
                                         folds=folds,
                                         name='stacking neural')

def print_sep():
    print "-------------"

def BI2sortedlist(f):
    @wraps(f)
    def g((key, (I, v))):
        return f((key, (I, sorted(v))))
    return g

def get_learner(guy):
    (I, folds), v = guy
    BL = i2bl(sorted(v))
    return get_stacknn(BL, base_learners[I], folds)


@BI2sortedlist
@db_cache.cache_result
@db_cache.declare_pure_function
#def evaluate((key, guy), prop=None, folds=5):
def evaluate((key, guy), prop=0.7, folds=None):
    (I, sfolds), BI = guy
    print key

    BL = i2bl(BI)
    ML = base_learners[I]

    snn = get_stacknn(BL, ML, sfolds)

    assert prop or folds
    assert not ( prop and folds )
    results = []
    class_doms = [ TRAIN_TABLE.domain[x] for x in
                   data_about_players.Data.questionare_annotations]
    for class_dom in class_doms:
        new_domain = Orange.data.Domain(TRAIN_TABLE.domain.features + [class_dom])
        train_table = Orange.data.Table(new_domain, TRAIN_TABLE)

        train_table =  TRAIN_TABLE
        if prop:
            res = proportion_test( [snn], train_table, prop, 1, random_generator=key )
        if folds:
            res = cross_validation( [snn], train_table, folds=folds )
        results.append(res)

    scores = list(sum(map(numpy.array,
                          map( Orange.evaluation.scoring.RMSE, results )))
                  / 4.0)

    return scores[0]

def crossover_pos(pos, father, mother):
    I_f, v_f = father
    I_m, v_m = mother

    from_father = [ g for g in v_f if g <= pos ]
    from_mother = [ g for g in v_m if g > pos ]

    return (I_f, set(from_father + from_mother))

def crossover_double(father, mother):
    pos = random_position()
    guy1 = crossover_pos(pos, father, mother)
    guy2 = crossover_pos(pos, mother, father)

    return guy1,  guy2

def lenghten(guy,  retries=10):
    ret = copy.copy(guy)
    newi = random_position()
    ret.add(newi)
    if retries and guy == ret:
        return lenghten(guy,  retries - 1)
    return ret

def random_position():
    return random.randint(0, len(base_learners) - 1)

def mutate_I(guy):
    (I, folds), v = guy

    if 0.5 < random.random():
        I = random_position()
    else:
        folds = random.randint(2, 6)

    return ((I, folds), v)

def mutate_v(guy):
    I, v = guy
    ret = copy.copy(v)
    newi = random_position()
    if newi in ret:
        ret.remove(newi)
    else:
        ret.add(newi)

    if not ret:
        ret = set([random_position()])

    return (I, ret)

def print_popev(popev,  top=3):
    for ev, guy in popev[:top]:
        I, v = guy

        print "  %.3f" % ev,  (I, list(sorted(v)))


class ParEv:
    def __init__(self, nworkers):
        self.nworkers = nworkers
        self.pool = multiprocessing.Pool(initializer=init, processes=nworkers)
        self.timer = timer.Timer()
        self.it = 0

    def __call__(self, pop):
        self.it += 1

        frozen_pop = [ (I, frozenset(v)) for (I, v) in pop ]
        uniq_pop = [ (self.it, (I, set(v))) for (I, v) in set(frozen_pop) ]
        

        self.timer.start()
        # run in parallel, results cached

        res = self.pool.map_async(evaluate, uniq_pop).get(60*60*20)
        #res = self.pool.map_async(evaluate, uniq_pop).get(5)
        #res = map(evaluate, uniq_pop)

        self.timer.stop_n_log()
        # run normally, everything cached now
        key_pop = [(self.it,  guy) for guy in pop]
        ev = map(evaluate, key_pop)
        return ev


import random, math

for i,  bl in enumerate(base_learners):
    print i,  bl


k_max = 100
k = 0
popsize = 16
elite_size = 1
prob_mut_I = 0.2
prob_mut_v = 0.5

e_best = 10000
best = (None,  [1, 2, 3])

pop = [
    ((44, 4), set([0, 2, 28, 36, 57 ]))
        ]
#pop = [ set([0, 2, 18]),
#        set([0, 2, 5])
#        ]


assert all( 0 <= len(p) < len(base_learners) for p in pop )

import subprocess

def bark():
    pass
    #subprocess.call('bark', shell=True)

if __name__ == "__main__":

    print "MAIN:,",
    init()
    parev = ParEv(8)
    time.sleep(0.1)

    import sys

    try:
        while True:
            print_sep()
            k += 1
            print "%d. ITERATION" % k
            sys.stdout.flush()

            # eval pop
            ev = parev(pop)
            #print ev

            # print best 3
            popev = sorted(list( zip(ev, pop) ))
            print_popev(popev, 100)
            if popev[0][0] < e_best:
                bark()
                e_best, best = popev[0]

            # fitness
            eshift = [ 1 / e for e in ev]
            summ = sum(eshift)
            fitness = [ e / summ for e in eshift ]

            # sort by decreasing fittness

            popsortfit = list(reversed(sorted(zip(fitness, pop))))

            # elitism
            elite = [ guy[1] for guy in popev[:elite_size] ]
            assert elite[0] == popsortfit[0][1]

            pop_inter = []
            # selection
            for a in xrange(popsize):
                rnd = random.random()
                s = 0
                i = 0
                while True:
                    s += popsortfit[i][0]
                    if s >= rnd:
                        break
                    i += 1
                pop_inter.append(popsortfit[i][1])

            # breeding
            pop_new = []

            for i in xrange(popsize / 2):
                father,  mother = pop_inter[2 * i], pop_inter[2 * i + 1]
                ch1, ch2 = crossover_double(father, mother)
                pop_new.append(ch1)
                pop_new.append(ch2)

            # mutate
            pop_mut = []
            for guy in pop_new:

                if random.random() < prob_mut_I:
                    guy = mutate_I(guy)

                if random.random() < prob_mut_v:
                    guy = mutate_v(guy)

                pop_mut.append(guy)

            # pop out
            pop = elite + pop_mut[:popsize - elite_size]

            print
            print_popev(zip([0.0 for _ in xrange(100)], pop), 100)

            if k > k_max:
                break

    except Exception as e:
        parev.pool.terminate()
        raise

    finally:
        print_sep()
        print "best",
        print_popev([(e_best, best)])


