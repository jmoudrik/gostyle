import Orange


t = Orange.data.Table('./test.tab')


kl = Orange.classification.knn.kNNLearner(k=2, rank_weight=False)

k = kl(t)



def get_inst(X):
   return Orange.data.Instance(Orange.data.Domain(t.domain.features),[X])

def run(X):
    print k(get_inst(X))