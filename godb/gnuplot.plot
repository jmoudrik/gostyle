reset
n=20	#number of intervals
max=10.	#max value
min=-10.	#min value
width=(max-min)/n	#interval width
invsqrt2pi = 0.398942280401433
normal(x,mu,sigma)=sigma<=0?1/0:invsqrt2pi/sigma*exp(-0.5*((x-mu)/sigma)**2)
#function used to map a value to the intervals
hist(x,width)=width*floor(x/width)+width/2.0
set term png	#output terminal and file
set output "histogram.png"
set xrange [min:max]
set yrange [0:]
#to put an empty boundary around the
#data inside an autoscaled graph.
set offset graph 0.05,0.05,0.05,0.0
set xtics min,(max-min)/5,max
set boxwidth width*0.9
set style fill solid 0.5	#fillstyle
set tics out nomirror
set xlabel "x"
set ylabel "Frequency"
#count and plot
plot "residuals_class_size_mean.dat" u (hist($1,width)):(1.0) smooth freq w boxes lc rgb"green" notitle, 1000 * normal(x, 0, 2.7)


# cat residuals_class_size_abs.dat | sed 's/ .*//' > res.dat
