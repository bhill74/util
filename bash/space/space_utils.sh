#!/bin/bash

set -a

source ${HOME}/util/text/formatting.sh

kramdown=0
verbose=0
level=3
user_pattern=*
function space_args() {
    local OPTIND opt
    while getopts "kvl:u:" opt; do
        case ${opt} in
            k)
                kramdown=1
                ;;
            v)
                verbose=1
                ;;
            l)
                level=$OPTARG
                ;;
            u)
                user_pattern=$OPTARG
                ;;
        esac
    done
}

function toMB() {
    echo "$(($1 / 1024))MB"
}

function header() {
    if [[ $kramdown > 0 ]]; then echo -n "$(repeat '#' $1) "; fi
    echo -n $2 
    echo
}

function table_header() {
    d=$(if [[ $kramdown > 0 ]]; then echo "|"; else echo " "; fi)
    if [[ $kramdown > 0 ]]; then echo; fi

    if [[ $level == 1 ]]; then
        printf "${d}%25s${d}%10s${d}\n" "Name" "% of Disk"
        printf "${d}:%s${d}:%s${d}\n" $(repeat - 24) $(repeat - 9)
    else 
        printf "${d}%25s${d}%12s${d}%10s${d}%10s${d}\n" "Name" "Size" "% of Group" "% of Disk"
        printf "${d}:%s${d}:%s${d}:%s${d}:%s${d}\n" $(repeat - 24) $(repeat - 11) $(repeat - 9) $(repeat - 9)
    fi
}

function table_footer() {
    if [[ $kramdown > 0 ]]; then echo; fi
}

function cal_percent() {
    echo "(${1}.0/${2})*100" | bc -l
}

function report() {
    per_grp=$(cal_percent $2 $3);
    per_dsk=$(cal_percent $2 $4);
    d=$(if [[ $kramdown > 0 ]]; then echo "|"; else echo " "; fi)
    f=$(if [[ $kramdown > 0 ]]; then echo "**"; else echo ""; fi)
    s=$(if [[ $kramdown > 0 ]]; then echo ""; else echo "9"; fi)

    if [[ $level == 1 ]]; then
        printf "${d}%25s${d}${f}%${s}.2f%%${f}${d}\n" $1 $per_dsk
    else
        printf "${d}%25s${d}%12s${d}%${s}.2f%%${d}${f}%${s}.2f%%${f}${d}\n" $1 $(toMB $2) $per_grp $per_dsk
    fi
}

declare -A used
function add_used() {
    ref=$1
    while [ "$ref" != "/" ] && [ ! -z $ref ]; do
        ref=$(dirname $ref)
        used[$ref]=1
    done
}

function is_used() {
    if [[ -z "${used[$1]}" ]]; then echo 'N'; else echo 'Y'; fi
}

function get_size() {
    du -s --block-size=k $1 2>/dev/null | awk '{print $1}'
}

function get_used_space() {
    echo $(cd $1;df . | tail -1 | awk '{print $3}')
} 

function check_regressions() {
    base_dir=$1
    if [[ $verbose > 0 ]]; then >&2 echo "Checking regressions in $base_dir"; fi

    if [[ $level -le 0 ]]; then return; fi

    declare -A by_user
    declare -A by_customer
    declare -A by_branch
    used_space=$(get_used_space $base_dir)
    total=0
    tstamp_pattern="[0123456789]*h[0123456789]*m[0123456789]*s\$"
    while read path; do
        base=$(basename $path)
        user=$(basename $(dirname $path))
        customer=$(basename $(dirname $(dirname $path)))
        size=$(get_size $path)
        branch=$(echo $base | sed "s/^regr_//" | sed "s/_${tstamp_pattern}//")
        ubranch=$user/$branch
        tstamp=$(echo $base | sed "s/_\(${tstamp_pattern}\)/\\1/")
        #echo $base - $user - $branch - $size - $customer
        add_used $path

        new=${size//K/}
        if [ -z "$new" ]; then new=0; fi
        by_user[$user]=$((${by_user[$user]:-0} + $new))
        by_customer[$customer]=$((${by_customer[$customer]:-0} + $new))
        by_branch[$ubranch]=$((${by_branch[$ubranch]:-0} + $new))
        total=$(($total + $new))
        if [[ $verbose > 0 ]]; then >&2 echo "  Found $base in $customer"; fi
    done < <(ls -d ${base_dir}/*/${user_pattern}/regr_*)

    per_dsk=$(cal_percent $total $used_space)
    header 1 "Regression Data Under ${base_dir} $(toMB $total) ($(printf "%.2f%%" $per_dsk) of Disk)"
    echo

    if [[ $level > 0 ]]; then
        header 2 "By User"
        table_header "User"
        for user in "${!by_user[@]}"; do
            report $user ${by_user[$user]} $total $used_space
        done
        echo
    fi

    if [[ $level > 2 ]]; then
        header 2 "By Customer"
        table_header "Customer"
        for customer in "${!by_customer[@]}"; do
            report $customer ${by_customer[$customer]} $total $used_space
        done
        echo
    fi

    if [[ $level > 1 ]]; then
        header 2 "By Branch"
        table_header "User/Branch"
        for branch in "${!by_branch[@]}"; do
            report $branch ${by_branch[$branch]} $total $used_space
        done
        echo
    fi
}

function check_other() {
    base_dir=$2
    if [[ $verbose > 0 ]]; then >&2 echo "Checking in $base_dir"; fi

    if [[ $level -le 1 ]]; then return; fi

    declare -A by_path
    total=0
    used_space=$(get_used_space $base_dir)
    while read path; do
        if [ $(is_used $path) == "Y" ]; then
            continue
        fi

        size=$(get_size $path)
        add_used $path
        new=${size//K/}
        if [ -z "$new" ]; then new=0; fi
        by_path[$path]=$((${by_path[$path]:-0} + $new))
        total=$(($total + $new))
        if [[ $verbose > 0 ]]; then >&2 echo "  Found $path"; fi
    done < <(ls -d ${base_dir}/*)

    per_dsk=$(cal_percent $total $used_space)
    header 1 "$1 Data Under ${base_dir} $(toMB $total) ($(printf "%.2f%%" $per_dsk) of Disk)"
    echo 

    header 2 "Other Paths"
    table_header "Path"
    for path in "${!by_path[@]}"; do
        report $path ${by_path[$path]} $total $used_space
    done
    echo
}
