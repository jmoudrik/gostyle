#!/bin/sh


parse_resfile () {
    echo "$1" | sed "s/^-> ResultFile('\(.*\)')$/\1/"
}

dir=$1

[ -z "$1" ] && { echo "usage: $0 directory" ; exit 1 ; }

[ -d "$dir" ] || { echo "Creating directory $dir" ; mkdir $dir ; } 


git_hash="$(git rev-parse --verify HEAD)"

echo $git_hash > $dir/git_hash
echo The latest git commit is $git_hash
cp pokus.py $dir
echo "Copying pokus.py"

while read a; do
    if ( echo $a | grep 'spatial dict made' > /dev/null ) ; then
        read gl
        read res_file
        filename=$(parse_resfile "$res_file")
        cp $filename $dir/patterns.spat

        echo "Copyed patterns.spat"
        echo "    from " $filename
    fi
    if ( echo $a | grep 'all_pat made' > /dev/null ) ; then
        read gl
        read res_file
        filename=$(parse_resfile "$res_file")
        cp $filename $dir/all.pat

        echo "Copyed all.pat"
        echo "    from " $filename
    fi
    if ( echo $a | grep 'tab file written' > /dev/null ) ; then
        read gl
        read res_file
        filename=$(parse_resfile "$res_file")
        cp $filename $dir/results.tab

        echo "Copyed results.tab"
        echo "    from " $filename
    fi
    if ( echo $a | grep 'tab file for feature written' > /dev/null ) ; then
        read feat_num
        read gl
        read res_file
        filename=$(parse_resfile "$res_file")
        featname="feature_${feat_num}.tab"
        cp $filename $dir/$featname

        echo "Copyed $featname"
        echo "    from " $filename
    fi

done
