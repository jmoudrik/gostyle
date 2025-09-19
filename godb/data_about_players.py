#!/usr/bin/python

import numpy
import math

import load_questionare

def questionare_average(questionare_list, silent=False, tex=False, cnt_limit=1):
# Otake Hideo          & $4.3 \pm 0.5$ & $3.0 \pm 0.0$ & $4.6 \pm 1.2$ & $3.6 \pm 0.9$ \\
    total={}
    count={}	
    for questionare in questionare_list:
        for name in questionare.keys():
            if name in count:
                count[name] += 1
            else:
                count[name] = 1
                total[name] = []
            total[name].append(questionare[name])

    l=[]
    for name, counter in count.items():
        l.append( (counter, name) )
    l.sort()
    l.reverse()
    variance=[]
    result={}
    
    for counter, name in l:
        if counter >= cnt_limit:
            means=[]
            if not silent:
                print "%d: %20s"%(counter, name),
                    
            a = numpy.array(total[name]).transpose()
            for b in a:
                means.append(b.mean())
                if not silent:
                    if not tex:
                        print u"%2.3f \u00B1 %2.3f  "%(b.mean(), numpy.sqrt(b.var())),
                    else:
                        print u"& $%2.1f \pm %2.1f$"%(b.mean(), numpy.sqrt(b.var())),
                    variance.append(numpy.sqrt(b.var()))
            if not silent:
                if not tex:
                    print
                else:
                    print "\\\\"
                variance.append(numpy.sqrt(b.var()))
            result[name] = means
            
    if not silent:
        if not tex:
            print "Mean standard deviation is: %2.3f"%(numpy.array(variance).mean(),)
    return result

def questionare_average_raw(questionare_list):
    import numpy
    total={}
    count={}	
    for questionare in questionare_list:
        for name in questionare.keys():
            if name in count:
                count[name] += 1
            else:
                count[name] = 1
                total[name] = []
            total[name].append(questionare[name])

    l=[]
    for name, counter in count.items():
        l.append( (counter, name) )
    l.sort()
    l.reverse()
    variance=[]
    result={}
    for counter, name in l:
        if counter > 1:
            means=[]
            print "%s, %d,"%(name, counter),
            a = numpy.array(total[name]).transpose()
            for b in a:
                means.append(b.mean())
                print u"%2.3f,"%(b.mean()),
            print
            result[name] = means
    return result

class Data:
    ### Explicit list of players
    
    ### commented out, use the method get_all_player_names instead
    """players_all = set(['Miyazawa Goro', 'Cho Tae-hyeon', 'Yi Se-tol', 'Fujisawa Hideyuki', 'Yamashita Keigo',
         'Shao Zhenzhong', 'Luo Xihe', 'Yasuda Shusaku', 'Yuki Satoshi', 'Suzuki Goro', "Yi Ch'ang-ho",
         'Kato Masao', 'Honinbo Shusaku', 'Cho U', 'Cho Chikun', 'Honinbo Shuwa', 'Jie Li', 'Gu Li',
         'Nie Weiping', "Yi Ch'ang-ho", 'O Meien', 'Ma Xiaochun', 'Sakata Eio', 'Rui Naiwei', 'Honinbo Dosaku',
         'Hane Naoki', 'Kuwahara Shusaku', 'Kobayashi Koichi', 'Otake Hideo', 'Chen Zude', 'Chen Yaoye',
         'Takemiya Masaki', 'Ishida Yoshio', 'Yoda Norimoto', 'Takao Shinji', 'Wu Songsheng', 'Go Seigen'])
        """
    
    #players_all = ['Takemiya Masaki', 'Cho Tae-hyeon', 'Yoda Norimoto', 'Chen Zude', 'Sakata Eio', 'Luo Xihe', 'Gu Li', 'Jie Li', 'Cho Chikun', 'Cho U', 'Suzuki Goro', 'O Meien', 'Miyazawa Goro', 'Wu Songsheng', 'Ma Xiaochun', 'Yasuda Shusaku', 'Kuwahara Shusaku', 'Honinbo Shusaku', 'Go Seigen', 'Shao Zhenzhong', "Yi Ch'ang-ho", 'Ishida Yoshio', 'Kobayashi Koichi', 'Rui Naiwei', 'Yi Se-tol', 'Kato Masao', 'Nie Weiping']
    #players_all = ['Chen Yaoye', 'Chen Zude', 'Cho Chikun', 'Cho Tae-hyeon', 'Cho U', 'Fujisawa Hideyuki', 'Go Seigen', 'Gu Li', 'Hane Naoki', 'Honinbo Dosaku', 'Honinbo Shusaku', 'Honinbo Shuwa', 'Huang Longshi', 'Ishida Yoshio', 'Jie Li', 'Kato Masao', 'Kato Shin', 'Kobayashi Koichi', 'Kuwahara Shusaku', 'Luo Xihe', 'Ma Xiaochun', 'Miyazawa Goro', 'Nie Weiping', 'O Meien', 'Otake Hideo', 'Rui Naiwei', 'Sakata Eio', 'Shao Zhenzhong', 'Suzuki Goro', 'Takao Shinji', 'Takemiya Masaki', 'Wu Songsheng', 'Yamashita Keigo', 'Yasuda Shusaku', "Yi Ch'ang-ho", 'Yi Se-tol', 'Yoda Norimoto', 'Yuki Satoshi']
    # Set-in-paper:
    #players_all = [ 'Yoda Norimoto', 'Yi Se-tol', "Yi Ch'ang-ho", 'Takemiya Masaki', 'Sakata Eio', 'Rui Naiwei', 'Otake Hideo', 'O Meien', 'Ma Xiaochun', 'Luo Xihe', 'Ishida Yoshio', 'Gu Li', 'Cho U', 'Cho Chikun', 'Yuki Satoshi', 'Yamashita Keigo', 'Takao Shinji', 'Miyazawa Goro', 'Kobayashi Koichi', 'Kato Masao', 'Hane Naoki', 'Go Seigen', 'Fujisawa Hideyuki', 'Chen Yaoye' ]

    ### Thist is used for StrategyOutputVectorGenerator (see gostyle.py)
    """
    strategy_players = {
    }
    player_strategy = {}
    for cl, pls in strategy_players.iteritems():
        for pl in pls:
            player_strategy.setdefault(pl, []).append(cl)
    """
    
    ###
    ###	Following code consist of expert based knowledge kindly supplied by 
    ###      Alexander Dinerstein 3-pro, Motoki Noguchi 7-dan and Vit Brunner 4-dan)

    ### The vector at each name corresponds with 
    ### ( 
    questionare_annotations =  ['territory', 'orthodox', 'aggressiveness', 'thickness']
    
    questionare_directory = './QUESTIONARE'
    questionare_list = [ 
    #questionare_vit_brun
        {
            "Chen Yaoye": (7, 5, 7, 6),
            "Cho Chikun": (9, 7, 7, 9),
            "Cho U": (4, 6, 7, 4),
            "Gu Li": (5, 6, 9, 5),
            "Ishida Yoshio": (6, 3, 5, 5),
            "Luo Xihe": (8, 4, 7, 7),
            "Ma Xiaochun": (5, 7, 7, 7),
            "O Meien": (3, 9, 6, 5),
            "Otake Hideo": (4, 3, 6, 5),
            "Rui Naiwei": (5, 6, 8, 5),
            "Sakata Eio": (6, 4, 8, 6),
            "Takemiya Masaki": (1, 4, 7, 2),
            #"Yi Ch'ang-ho 2004-": (7, 6, 4, 4),
            #"Yi Ch'ang-ho 2005+": (7, 6, 6, 4),
            "Yi Ch'ang-ho": (7, 6, 6, 4),
            "Yi Se-tol": (6, 5, 9, 5),
            "Yoda Norimoto": (4, 4, 7, 3)
        }, 
    # questionare_motoki_noguchi
        {
            "Cho Chikun": (8, 9, 8, 8 ),
            "Cho U": (9, 7, 6, 8),
            "Gu Li": (7, 8, 10, 4 ),
            "Ishida Yoshio": (9, 6, 2, 6),
            "Luo Xihe": (6, 8, 9, 7 ),
            "Ma Xiaochun": (9, 6, 7, 8),
            "O Meien": (1, 10, 10, 2 ),
            "Otake Hideo": (4, 3, 5, 3),
            "Rui Naiwei": (6, 6, 10, 2),
            "Sakata Eio": (10, 5, 6, 10),
            "Takemiya Masaki": (2,6, 6, 1),
            #"Yi Ch'ang-ho 2004-": (8, 3, 2, 3),
            # P: udelal jsem to z 2004-
            "Yi Ch'ang-ho": (8, 3, 2, 3),
            "Yi Se-tol": (5, 10, 10, 8 ),
            "Yoda Norimoto": (8, 2, 2, 5),
            "Fujisawa Hideyuki": (4, 8, 7, 4 ),
            "Go Seigen": (8, 10, 9, 6),
            "Hane Naoki": (8, 2, 4, 6 ),
            "Honinbo Dosaku": (2, 10, 8, 5 ),
            "Honinbo Shusaku": (8, 3, 2, 6),
            "Honinbo Shuwa": (10, 8, 2, 10),
            "Kato Masao": (2,3, 9, 4),
            "Kobayashi Koichi": (8, 3, 3, 6),
            "Miyazawa Goro": (1, 10, 10, 3),
            "Takao Shinji": (4, 3, 7, 4 ),
            "Yamashita Keigo": (2, 8, 10, 4 ),
            "Yuki Satoshi": (2, 8, 10, 4)
        }, 
    #questionare_alex_dinner
        {
            "Chen Yaoye": (5, 3, 5, 5), 
            "Cho Chikun": (10, 7, 5, 10), 
            "Cho U": (9, 5, 3, 7), 
            "Gu Li": (5, 7, 8, 3), 
            "Ishida Yoshio": (9, 6, 3, 5), 
            "Luo Xihe": (8, 10, 7, 4), 
            "Ma Xiaochun": (10, 6, 3, 9), 
            "O Meien": (4, 10, 9, 4), 
            "Otake Hideo": (5, 3, 3, 3), 
            "Rui Naiwei": (3, 5, 9, 3), 
            "Sakata Eio": (7, 5, 8, 8), 
            "Takemiya Masaki": (1, 9, 8, 1), 
            #"Yi Ch'ang-ho 2004-": (6, 6, 2, 1), 
            #"Yi Ch'ang-ho 2005+": (5, 4, 5, 3), 
            # commented because duplicates 2005+
            "Yi Ch'ang-ho": (5, 4, 5, 3),
            "Yi Se-tol": (5, 5, 9, 7), 
            "Yoda Norimoto": (7, 7, 4, 2), 
            "Chen Zude": (3, 8, 6, 5), 
            "Cho Tae-hyeon": (1, 4, 4, 2), 
            "Fujisawa Hideyuki": (3, 10, 7, 4), 
            "Go Seigen": (4, 8, 7, 4), 
            "Hane Naoki": (7, 3, 4, 3), 
            "Jie Li": (5, 3, 5, 4), 
            "Kato Masao": (3, 6, 10, 4), 
            "Kobayashi Koichi": (10, 2, 2, 5), 
            "Miyazawa Goro": (2, 10, 9, 5), 
            "Nie Weiping": (3, 7, 8, 4), 
            "Shao Zhenzhong": (4, 5, 5, 4), 
            "Suzuki Goro": (4, 7, 5, 5), 
            "Takao Shinji": (6, 4, 4, 5), 
            "Wu Songsheng": (2, 10, 7, 4), 
            "Yamashita Keigo": (2, 10, 9, 2), 
            "Yuki Satoshi": (4, 9, 8, 5), 
            #"breakfast": (7, 7, 3, 4), 
            #"rapyuta/daien": (4, 7, 6, 5), 
            #"MilanMilan": (5, 5, 6, 4), 
            #"roln111-": (6, 5, 7, 5), 
            #"somerville": (4, 5, 5, 6), 
            #"artem92-": (7, 4, 3, 2), 
            #"TheCaptain": (3, 8, 7, 6)
        }
        ## + guys from the online questionare
        ] + load_questionare.scan_d(questionare_directory)
    
    questionare_total = questionare_average(questionare_list, silent=True)
    
    players_recommend = set([
 'Chen Yaoye',
 'Chen Zude',
 'Cho Chikun',
 #'Cho Tae-hyeon',
 'Cho U',
 'Fujisawa Hideyuki',
 'Go Seigen',
 'Gu Li',
 'Hane Naoki',
 'Honinbo Dosaku',
 'Honinbo Shusaku',
 'Honinbo Shuwa',
 'Ishida Yoshio',
 'Kato Masao',
 'Kobayashi Koichi',
 'Luo Xihe',
 'Ma Xiaochun',
 'Miyazawa Goro',
 'Nie Weiping',
 'O Meien',
 'Otake Hideo',
 'Rui Naiwei',
 'Sakata Eio',
 'Shao Zhenzhong',
 #'Suzuki Goro',
 'Takao Shinji',
 'Takemiya Masaki',
 u'Iyama Yuta',
 'Wu Songsheng',
 'Yamashita Keigo',
 "Yi Ch'ang-ho",
 'Yi Se-tol',
 'Yoda Norimoto',
 'Yuki Satoshi',
    ])
    
def pro_name2web(name):
    exceptions = {
        'Iyama Yuta' : 'http://ps.waltheri.net/database.html#/player/Iyama Yuuta',
        'Yi Se-tol' : 'http://ps.waltheri.net/database.html#/player/Lee Sedol',
        
    }
    
    if name in exceptions:
        return exceptions[name]
    
    return 'http://ps.waltheri.net/database.html#/player/' + name
    
def get_all_player_names(limit=1):
    pc = {}
    
    for q in Data.questionare_list:
        for p in q.keys():
            pc[p] = pc.get(p, 0) + 1
    
    ps = set( p for p in pc.keys() if pc[p] >= limit )
    
    return ps

def get_interesting_pros(style, top, bottom, without_dist=True):
    style_vec = numpy.array(style)
    
    dist = []
    for pro_name, pro_style in Data.questionare_total.iteritems():
        if pro_name in Data.players_recommend:
            dist.append(
                ( math.sqrt( sum(numpy.power(style_vec - numpy.array(pro_style),  2))), 
                  (pro_name, pro_name2web(pro_name))
                )   
            )
    dist.sort()
    if not without_dist:
        return dist[:top], dist[-bottom:]
    
    def second((a, b)):
        return b
    
    return map(second, dist[:top]), map(second, dist[-bottom:]) 

if __name__ == '__main__':
    def main():
        print get_all_player_names(4)
    
        tex = True
        
        questionare_total = questionare_average(Data.questionare_list, cnt_limit=2, silent=False, tex=tex)
        
        pa = get_all_player_names(2)
        
        vals = numpy.array([ va for pn, va in questionare_total.iteritems() if pn in pa ])
        print vals.shape
        
        key2vec = {}
        for desc, num in zip(Data.questionare_annotations, range(4)):
            sli = vals[:, num]
            key2vec[desc] = sli
            if not tex:
                print u"%s\n  mean: %2.3f \u00B1 %2.3f"%(desc, sli.mean(),  sli.std())
            else:
                print u"%s & %2.3f \\pm %2.3f \\"%(desc, sli.mean(),  sli.std())
            
        import analyze_attributes
                
        qa = Data.questionare_annotations
        print '', 
        print " | ".join("%15s"%an for an in (['']+qa))
        for i in xrange(len(qa)):
            print "%15s | " % qa[i], 
            for j in xrange(len(Data.questionare_annotations)):
                if i > j:
                    print "%15s |" % ('' ), 
                else:
                    p = analyze_attributes.pearson_coef(key2vec[qa[i]],
                                                        key2vec[qa[j]])
                    print "%15s |" % ( "%.3f" % p ), 
            print
    
    main()
        
    ##
    ##

    def test_style(style):
        near, dist = get_interesting_pros(style,  3, 3) 
        print "similar"
        for p in near:
            print p
        print
        print "distant"
        for p in dist:
            print p
           
    #test_style([1, 2, 3, 4])
    
        

