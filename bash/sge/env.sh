function qenv() {
    local cell=$1
    local debug=0
    if [ ! -z "$2" ] && [ $2 -gt 0 ]; then
        debug=1
    fi
    local reload=0
    if [ -z "$cell" ]; then
        if [ ! -z "$SGE_CELL" ]; then
	    if [ $debug -eq 1 ]; then
		echo "NULL cell, using $SGE_CELL" 
            fi
            cell=$SGE_CELL
	else
	    if [ $debug -eq 1 ]; then
		echo "NULL cell, using snps" 
            fi
	    cell=snps
	    reload=1
	fi
    else
        if [ "$cell" != "$SGE_CELL" ]; then
	    if [ $debug -eq 1 ]; then
		echo "Mismatch, using $cell" 
            fi
	    reload=1
        fi
    fi
    local tpath=$(echo /remote/sge/default/${cell//default\//})   
    local target=$(readlink -f ${tpath})    
    if [ -z "$target" ]; then
       target=${tpath}
    fi    
    local tdir=$(dirname $target)    
    local qpath=$(which qstat 2>/dev/null)
    if [[ $qpath != "$tdir"* ]]; then
        if [ $debug -eq 1 ]; then
	    echo "Missing paths" 
        fi
	reload=1
    fi
    if [ $reload -eq 1 ]; then
	if [ $debug -eq 1 ]; then
	    echo "Reloading $cell ..."
	fi
        . ${target}/common/settings.sh 2>/dev/null
    fi
}
