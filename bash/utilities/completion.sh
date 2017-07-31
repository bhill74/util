. ${HOME}/util/util/upvar.sh
. ${HOME}/util/util/strings.sh

# Completion is only relevant for BASH shells
ver=`echo $0 | rev | cut -f1 -d/ | rev | sed "s/[^a-z]//g"`
if [ "$ver" != "bash" ]; then
    export _no_completion=1
    return
fi
unset _no_completion

_get_cword() 
{
    if [ ! -z "$1" ]; then
	local "$1" && upvar $1 ${COMP_WORDS[COMP_CWORD]}
	return
    fi
    echo ${COMP_WORDS[COMP_CWORD]}
}

_get_pword()
{
    if [ ! -z "$1" ]; then
	local "$1" && upvar $1 ${COMP_WORDS[COMP_CWORD-1]}
	return
    fi
    echo ${COMP_WORDS[COMP_CWORD-1]}
}

_get_words()
{
    local c=$(_get_cword)
    local p=$(_get_pword)
    if local "$1" "$2"; then
	upvar $1 $c
	upvar $2 $p
    fi
}    

_get_cmd()
{
    if [ ! -z "$1" ]; then
	local "$1" && upvar $1 ${COMP_WORDS[0]}
	return
    fi
    echo ${COMP_WORDS[0]}
}

_get_all()
{
    local all=$(IFS=' '; echo "${COMP_WORDS[*]}")
    if [ ! -z "$1" ]; then
	local "$1" && upvar $1 "$all"
	return
    fi
    echo $all
}

_is_within() 
{
    local all item
    all=" $2 "
    item=$1
    if [ "${all/ $item //}" != "$all" ]; then
	echo 1
	return
    fi
    echo 0
}

_get_unused()
{
    a=$1
    b=$2
    if [ -z "$b" ]; then
	_get_all b
    fi
    r=''
    for l in $a; do
        if [[ ! $b =~ $l ]]; then
           r="$r $l"
        fi
    done
    echo $r
}

_get_arg_value()
{
    local param=$1
    local count=0
    local size=${#COMP_WORDS[@]}
    while [ $count -lt $size ]; do
	let count=count+1	
        if [ "${COMP_WORDS[$count]}" == "$param" ]; then
	    echo ${COMP_WORDS[$count+1]}
	    return
        fi
    done
}

_get_last_value()
{
    eval eval args=( $(history | cut -f4- -d" " | egrep "^${1}" | tail -1) );
    local a
    local n=1
    local values=()
    for a in "${args[@]}"; do
	if [ "$a" = "$2" ]; then
	    values=("${values[@]}" ${args[$n]})
	fi
	let n=n+1
    done
    echo $(IFS=$3; echo "${values[*]}")
}

_process_tag() {
    local tag=$1 use_flag=0
    if [ ${tag:0:1} == "@" ]; then
	use_file=1
	tag=${tag:1:${#tag}}
    fi
    upvar $2 $use_file
    upvar $3 $tag
}

_get_cache_var() {
    echo __${1}_2_${2}_3_${3}
}

_get_cache_stamp() {
    _get_cache_var "$1" "$2" TSTMP
}

_get_cache_value() {
    _get_cache_var "$1" "$2" VALUE
}

_get_cache_reference() {
    _get_cache_var "$1" "$2" REF
}

_get_tmp() {
    local ltmp=${TMP}
    if [ -z "$ltmp" ] || [ ! -d "$ltmp" ] || [ ! -w "$ltmp" ]; then
	ltmp=/tmp
    fi  
    echo $ltmp
}

_get_cache_file() {
    local ltmp=$(_get_tmp) 
    echo ${ltmp}/$(_get_cache_var "$1" "$2" FILE)
}

_reset_cache() {
    local tag="$1" 
    local func=$2
    local use_file=0
    _process_tag $tag use_file tag
    if [ $use_file -eq 1 ]; then
        local ltmp=$(_get_tmp) 
	for var in $(ls ${ltmp}/__${tag}* 2>/dev/null); do	   
	    var=$(basename $var)	   
	    var=${var:2}	    
	    var=${var%_2_*}	    
	    if [ -e $(_get_cache_file "$var" "$func") ]; then		
		unset $(_get_cache_stamp "$var" "$func")
		unset $(_get_cache_value "$var" "$func")
		unset $(_get_cache_reference "$var" "$func")	    
		rm -f $(_get_cache_file "$var" "$func") 2>/dev/null
	    fi
	done
    else
	for var in $(set -o posix; set | egrep "^__${tag}" | cut -f1 -d= | cut -f1 -d\#); do
	    var=${var:2}
	    var=${var%=*}
	    var=${var%_2_*}
	    unset $(_get_cache_stamp "$var" "$func")
	    unset $(_get_cache_value "$var" "$func")
	    unset $(_get_cache_reference "$var" "$func")
	done
    fi
}

_set_cache_value() {
    local tag=$1 func=$2 value=$3
    local var=$(_get_cache_value $tag $func)
    export $var=$value
}

_reset_cache_time() {
    local tag=$1 func=$2 
    local var=$(_get_cache_stamp $tag $func)
    export $var=$(date "+%s")
}

_get_cached_by_life_cycle() {
    # Arguments
    local tag=$1 life=$2 func=$3 args=$4 var=$5
    # Current timestamp
    local now=$(date '+%s')
    # Process TAG
    local use_file=0
    _process_tag $tag use_file tag
    # Unique Variable Names
    local var_timestamp=$(_get_cache_stamp $tag $func)
    local var_value=$(_get_cache_value $tag $func)
    local file_name=$(_get_cache_file $tag $func)
    # -- dereferenced values --
    local timestamp=$(eval echo \$${var_timestamp})
    local value=$(eval echo \$${var_value})
    if [ $use_file ] && [ -e "$file_name" ]; then
	timestamp=$(sed -n '1p' $file_name | cut -f2 -d:)
	value=$(tail -n +2 $file_name)
    fi 
    # Compare against previous values
    if [ -z "${timestamp}" ] || \
	[ $(($now - ${timestamp})) -gt $life ] || \
	[ -z "${value}" ] ; then
	# Resolve output and store
	local output=`$func $4`
        export ${var_value}="$output"
	value=$(eval echo \$$var_value)
	export ${var_timestamp}=$(echo $now)
	if [ $use_file ]; then
	    echo "Timestamp:$now" > $file_name
	    echo $value >> $file_name
	fi
    fi 

    if [ ! -z "$var" ]; then
	local "$var" && upvar $var $value
	return
    fi

    echo $value
}

fileTimestamp() {
    local file=$1
    if [ ! -e "$file" ]; then
	return
    fi
    local ftime=$(stat --print=%y $1 | cut -f1 -d.)
    date -d"${ftime}" '+%s'
}

_get_cached_by_timestamp() {
    # Arguments
    local tag=$1 rtime=$2 func=$3 args=$4 var=$5
    # Current timestamp
    local now=$(date '+%s')    
    # Process TAG
    local use_file=0
    _process_tag $tag use_file tag
    # Unique Variable Names
    local var_timestamp=$(_get_cache_stamp $tag $func)
    local var_value=$(_get_cache_value $tag $func)
    local file_name=$(_get_cache_file $tag $func)
    # -- dereferenced values --
    local timestamp=$(eval echo \$$var_timestamp)    
    local value=$(eval echo \$$var_value)
    if [ $use_file ] && [ -e "$file_name" ]; then
	timestamp=$(sed -n '1p' $file_name | cut -f2 -d:)
	value=$(tail -n +2 $file_name)
    fi
    if [ -z "$timestamp" ]; then
	timestamp=0
    fi
    if [ -z "$rtime" ]; then
	rtime=-1
    fi

    # Compare against previous values
    if [ $rtime -eq -1 ] || \
	[ $rtime -gt $timestamp ] || \
	[ -z "${value}" ]; then
	# Resolve output and store
	local output=`$func $4`
	export $var_value="$output"
	value=$(eval echo \$$var_value)
	export $var_timestamp=$(echo $now)	
	if [ $use_file ]; then
	    echo "Timestamp:$now" > $file_name	    
	    echo $value >> $file_name
	fi
    fi
    if [ ! -z "$var" ]; then
	local "$var" && upvar $var $value
	return
    fi
    echo $value
}

_get_cached_by_file_timestamp() {
    # Arguments
    local tag=$1 ref=$2 func=$3 args=$4 var=$5
    # Current timestamp
    local now=$(date '+%s')
    # Reference file timestamp
    local rtime=$(fileTimestamp $ref)
    # Process TAG
    local use_file=0
    _process_tag $tag use_file tag
    # Unique Variable Names
    local var_timestamp=$(_get_cache_stamp $tag $func)
    local var_reference=$(_get_cache_reference $tag $func)
    local var_value=$(_get_cache_value $tag $func)
    local file_name=$(_get_cache_file $tag $func)
    # -- dereferenced values --
    local timestamp=$(eval echo \$$var_timestamp)
    local reference=$(eval echo \$$var_reference)
    local value=$(eval echo \$$var_value)
    if [ $use_file ] && [ -e "$file_name" ]; then
	timestamp=$(sed -n '1p' $file_name | cut -f2 -d:)
	reference=$(sed -n '2p' $file_name | cut -f2 -d:)
	value=$(tail -n +3 $file_name)
    fi
    if [ -z "$timestamp" ]; then
	timestamp=0
    fi

    # Compare against previous values
    if [ $rtime -eq -1 ] || \
	[ $rtime -gt $timestamp ] || \
	[ -z "${reference}" ] || \
	[ "$reference" != "$ref" ] || \
	[ -z "${value}" ]; then
	# Resolve output and store
	local output=`$func $4`
	export $var_value="$output"
	value=$(eval echo \$$var_value)
	export $var_timestamp=$(echo $now)
	export $var_reference=$(echo $ref)
	if [ $use_file ]; then
	    echo "Timestamp:$now" > $file_name
	    echo "Reference:$ref" >> $file_name
	    echo $value >> $file_name
	fi
    fi

    if [ ! -z "$var" ]; then
	local "$var" && upvar $var $value
	return
    fi

    echo $value
}
