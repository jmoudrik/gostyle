reset

set terminal png size 500, 75 transparent

set output 'out.png'
set border lw 2

unset ytics
set yrange[0:2]

#set xlabel "Strength"
unset xtics
set xrange[-5 : 20]
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
#"6d" -5 )

#"1k" 1,\
#"19k" 19,\
#"17k" 17,\
#"15k" 15,\
#"13k" 13,\
#"5k" 5,\
#"3k" 3,\
#"9k" 9,\
#"11k" 11,\
#"7k" 7,\
#"2d" -1,\
#"4d" -3,\
#"6d" -5 )

set arrow from -2,graph(0,0) to -2,graph(1,1) nohead lc rgb "red" lw 2
set arrow from -4.7,graph(0,0) to -4.7,graph(1,1) nohead lc rgb "blue" lw 2
set arrow from 0.7,graph(0,0) to 0.7,graph(1,1) nohead lc rgb "blue" lw 2


plot 1/0 notitle
