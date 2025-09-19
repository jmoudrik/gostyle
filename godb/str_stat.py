import os

import Orange

if __name__ == "__main__":
    basedir = 'TABS/KGS_wide_by_player_10_100_120_simple'
    basedir = 'TABS/KGS_wide_10_100_120'
    #for extension in ['results.tab']: # + ['feature_%d.tab' % fnum for fnum in xrange(9) ]:
    #for extension in ['feature_%d.tab' % fnum for fnum in xrange(9) ]:
    extension =  'results.tab'
    TRAIN_DATA= os.path.join(basedir, extension)
    train_table = Orange.data.Table(TRAIN_DATA)
    
    d = {}    
    
    for ins in train_table:
        cls = float(ins.get_class())
        d[cls] = d.get(cls , 0) +  1
    
    for key, val in sorted(d.items()):
        print key, val
        