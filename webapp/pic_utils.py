import subprocess
import os

import config
import misc

def _generate_pic(basedir, value, sigma, min_v, max_v, template):
    head_name = misc.unique_hash(10) + '.png'
    img_outfile = os.path.join(basedir, head_name)
    
    middle = min(max_v, max(min_v, value))
    left = max(min_v, middle - sigma)
    right = min(max_v, middle + sigma)
    
    script = template%(    img_outfile,
                           left, left,
                           middle, middle,
                           right, right,
                           img_outfile
                        )

    retcode = subprocess.call(script,  shell=True)
    if retcode:
        raise RuntimeError('Picture generation failed.')
    return head_name


def generate_str_pic(basedir, value, sigma):
    return _generate_pic(basedir, value, sigma, -5, 20, """
cat << EOF | gnuplot
reset

set terminal png size 500, 75 transparent
#set terminal png size 470, 60 transparent

set output '%s'
set border lw 2

unset ytics
set yrange[0:2]

unset xtics
set xrange[-5.5 : 20.5]
set xtics ( "20k" 20,\
"18k" 18,\
"16k" 16,\
"14k" 14,\
"12k" 12,\
"10k" 10,\
"8k" 8,\
"6k" 6,\
"4k" 4,\
"2k" 2,\
"1d" 0,\
"3d" -2,\
"5d" -4 )
set arrow from %f,graph(0,0) to %f,graph(1,1) nohead lc rgb "blue" lw 2
set arrow from %f,graph(0,0) to %f,graph(1,1) nohead lc rgb "red" lw 2
set arrow from %f,graph(0,0) to %f,graph(1,1) nohead lc rgb "blue" lw 2


plot 1/0 notitle
EOF

mogrify -shave 10x10 '%s'
""")

def generate_style_pic(basedir, value, sigma):
    return _generate_pic(basedir, value, sigma, 1, 10, """
cat << EOF | gnuplot
reset

set terminal png size 500, 75 transparent

set output '%s'
set border lw 2

unset ytics
set yrange[0:2]

set xrange[0.5 : 10.5]
set xtics 1,1,10

set arrow from %f,graph(0,0) to %f,graph(1,1) nohead lc rgb "blue" lw 2
set arrow from %f,graph(0,0) to %f,graph(1,1) nohead lc rgb "red" lw 2
set arrow from %f,graph(0,0) to %f,graph(1,1) nohead lc rgb "blue" lw 2

plot 1/0 notitle
EOF

mogrify -shave 10x10 '%s'
""")

def generate_rel_freq_pic(basedir, left,  middle, right):
    assert left <= middle <= right
    
    head_name = misc.unique_hash(6) + '.png'
    img_outfile = os.path.join(basedir, head_name)
    
    script = """
cat << EOF | gnuplot
reset

set terminal png size 600, 110 transparent

set output '%s'
set border lw 2

unset ytics
set yrange[0:2]

set xrange[%.2f : %.2f]

set title "Strong player       This pattern is played every X games          Weak player" 

set arrow from %f,graph(0,0) to %f,graph(1,1) nohead lc rgb "red" lw 2

plot 1/0 notitle
EOF
    
    """%(    img_outfile,
             left, right,
             middle, middle)

    retcode = subprocess.call(script,  shell=True)
    if retcode:
        raise RuntimeError('Picture generation failed.')
    return head_name

if __name__ == '__main__':
    
    #print generate_str_pic('./OUTPUT', 10, 2.2)
    print generate_style_pic('./', 9.8, 2.2)
    #print generate_rel_freq_pic('./OUTPUT', 1,  20,  100)
    
    