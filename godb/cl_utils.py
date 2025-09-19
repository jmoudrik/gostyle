import itertools
import random

from models import *
import misc
import utils
            
def get_name_template(name, gl, max_size, min_size, min_splits, equisized, shuffle):
    if max_size and max_size == min_size:
        split_by = 'one split == %d games' % min_size
    elif min_size:
        assert not max_size
        split_by = 'one split >= %d games' % min_size
    elif max_size:
        split_by = 'one split <= %d games' % max_size
    else:
        split_by = 'one split all possible games' % max_size
        
    split_sign = '=='
    
    name = "%s, %s, %s, number of splits %s %s"% (name, repr(gl), split_by, split_sign, min_splits)
    if shuffle:
        name +=  ', Shuffled'
    return name

def grouping_to_onesidelists(iterator, osl_name_factory, max_size=0, min_size=0, min_splits=1, equisized=False, shuffle=False ):
    """
    A grouping is a set (@iterator) of pairs of form (groupname, list of OSLAssociations).
    This method splits the list of OSLAssocs. for each group into multiple subgroups, so that we have
    more training vectors for each group.
    
    it yields (group, one side lists)
    for example running on [ ('group1', [ oa1, oa2, oa3, oa4]), ('group2', [oa5,oa6])] might yield:
    ('group1', OSL([oa1, oa2]))
    ('group1', OSL([oa3, oa4]))
    ('group2', OSL([oa4, oa5]))
    
    max_size = maximum number of games per vector
    min_size = minimum number of games per vector
    
    min_splits = minimum number of vectors
        - other groups (with fewer vectors) will be skipped
    """
    if max_size and min_size and not max_size == min_size:
        raise ValueError("max_size and min_size at once and not the same")
    
    #by_group, other =  misc.filter_both( lambda (g, l) : len(l) >= max_size * min_splits, iterator)
    #if other:
    #    lb,  lo =  len(by_group),  len(other)
    #    logging.info('Skipped %d / %d groups because of small set of games. Decrease the @max_size or @min_splits parameter.'%(lo, lb+lo))
    #    logging.debug( '\n'.join(str(g) for g, l in other ))
    
    by_group = list(iterator)
        
    skip_count = 0
    for group, list_assocs in equisize_grouping(by_group) if equisized else by_group:
        list_assocs = list(list_assocs)
        if shuffle:
            random.shuffle(list_assocs)
            
        if min_size and min_size == max_size:
            splits = list(utils.iter_exact_splits(list_assocs, min_size))
        elif min_size:
            assert not max_size
            splits = list(utils.iter_splits(list_assocs, min_size=min_size))
        elif max_size:
            splits = list(utils.iter_splits(list_assocs, max_size=max_size))
        else:
            splits = [ list_assocs ]
        
        print "%3d : %s"%( len(splits),  group)
        #, %d into %s" % (group,  len(splits), len(list_assocs), map(len, splits))
        
        if min_splits and len(splits) < min_splits:
            #logging.info("Too few splits for group '%s', skipping. Decrease the @min_size, @max_size or @min_splits parameter."%(repr(group)))
            logging.info("skipping '%s', have %d, need %d"%(repr(group),
                                                            len(splits),
                                                            min_splits
                                                            ))
            skip_count += 1
            continue
        
        
        for num, split in enumerate(splits):
            yield group, OneSideList(osl_name_factory(group, num), assocs=split)
            
    if skip_count:
        logging.info('Skipped %d / %d groups because of small set of games.'
                     'Decrease the @max_size or @min_splits parameter.'
                        %(skip_count, len(by_group)))

def equisize_grouping(iterator):
    """
    crops the lists of OSLAssociations so that each group has exactly
    the same number of associations (the rest is thrown away).
    """
    gr_list =  list(iterator)
    minsize = min( len(l) for g, l in gr_list )
    for g, l in gr_list:
        # take only so much, that all the groups have the same
        yield g, l[:minsize]
