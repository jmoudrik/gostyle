
def get_interval(boundaries, element):
    assert boundaries
    if not element:
        return None
    # skip
    if element < boundaries[0]:
        return None

    prev = boundaries[0]
    for ref in boundaries[1:]:
        if element < ref:
            return prev, ref
        prev = ref

    return None

# cb = [ 1, 2, 3]
# <1, 2), <2, 3)
class_boundaries = ([
    1600,
    # old times
    1700, 1750, 1800, 1825, 1850, 1875, 1900,
    # Pre-war
    1920,
    1930, 1933, 1936, 1940,
    # war'n'after war
    1950, 1955, 1960, 1963, 1966, 1969, 1971, 1973, 1975, 1977, 1979, 1980]
    #1975, 1980, 1982, 1984, 1986, 1988]
    + range(1981,2012))

def get_class(year):
    interval = get_interval(class_boundaries, year)
    if interval:
        a, b = interval
        return (a + b) / 2.0
    else:
        return None

def get_all_intervals():
    return [ get_interval(class_boundaries, lower) for lower in class_boundaries[:-1] ]

if __name__ == '__main__':
    cnt_d = {}

    with open('../data/GoGoD/Database/year_plot', 'r') as fin:
        for line in fin:
            year, count = map(int, line[:-1].split())

            cls = get_class(year)
            if cls:
                cnt_d[cls] = cnt_d.get(cls, 0) + count

    for cls, cnt in sorted(cnt_d.iteritems()):
        interval = get_interval(class_boundaries, cls)
        a,b = interval
        print interval, "\t", b-a, cnt

    print len(cnt_d)

    print get_all_intervals()
