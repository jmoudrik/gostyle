

set term post eps
set output 'str_sizedist.eps'
set style data boxplot
set style boxplot nooutliers fraction 0.95

set yrange [8:52]
set ytics 10

#plot './class_diff_guess_size_5.dat' using (0.5):4:(0.5):1
plot './diff_class_datasize_10_50_120.dat' using (0.5):3:(0.5):2 notitle