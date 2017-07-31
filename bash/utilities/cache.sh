. ${HOME}/util/util/utilities.sh

#**************************************************
#%FUNCTION: _makeCacheVariable
#%DESCRIPTION: Merge the variables into a single
# string name.
#%ARGUMENTS:
# tag -- The tag to group the variables together
# type -- The type of variable being created.
#%RETURNS:
# The variable name.
#**************************************************
_makeCacheVariable() {
    echo __$(${HOME}/util/util/join -delim _ -trim "$@")
}

#**************************************************
#%FUNCTION: _makeCacheTimestampVariable
#%DESCRIPTION: Combine string to form a variable
# name used for timestamp information.
#%ARGUMENTS:
# tag -- The tag to group the variables together
#%RETURNS:
# The variable name.
#**************************************************
_makeCacheTimestampVariable() {
    _makeCacheVariable "$1" TSTMP
}

#**************************************************
#%FUNCTION: _makeCacheValueVariable
#%DESCRIPTION: Combine string to form a variable
# name used for value information.
#%ARGUMENTS:
# tag -- The tag to group the variables together
#%RETURNS:
# The variable name.
#**************************************************
_makeCacheValueVariable() {
    _makeCacheVariable "$1" VALUE
}

#**************************************************
#%FUNCTION: _makeCacheReferenceVariable
#%DESCRIPTION: Combine string to form a variable
# name used for reference information.
#%ARGUMENTS:
# tag -- The tag to group the variables together
#%RETURNS:
# The variable name.
#**************************************************
_makeCacheReferenceVariable() {
    _makeCacheVariable "$1" REF
}

#**************************************************
#%FUNCTION: _makeCacheFile
#%DESCRIPTION: Combine string to form a file name
# for storing cached information.
#%ARGUMENTS:
# tag -- The tag to group the variables together
#%RETURNS:
# The variable name.
#**************************************************
_makeCacheFile() {
    echo $TMP/$(_makeCacheValueVariable $1).ch
}

#**************************************************
#%FUNCTION: _getCacheType
#%DESCRIPTION: Determine what type of caching should
# be done for a given tag.
#%ARGUMENTS:
# tag -- The tag to group the variables together
#%RETURNS:
# 'file' for file based cachine, and 'env' for environment
# variable caching.
#**************************************************
_getCacheType() {
    local tag=$1
    local var=_cacheType_${tag}
    local cache_var=$(eval echo \$$var)
    if [ ! -z "$cache_var" ] && [ "$cache_var" == "file" ]; then
	echo file
	return
    fi

    if [ ! -z "$_cacheType" ] && [ "$_cacheType" == "file" ]; then
	echo file
	return
    fi
    
    echo env
}

#**************************************************
#%FUNCTION: _clearCache
#%DESCRIPTION: Clears all cache information for a given 
# tag.
#%ARGUMENTS:
# tag -- The tag to group the variables together
#%RETURNS:
# Nothing.
#**************************************************
_clearCache() {
    local tag=$1 
    unset `_makeCacheTimestampVariable $tag`
    unset `_makeCacheValueVariable $tag`
    unset `_makeCacheReferenceVariable $tag`   
    rm -f `_makeCacheFile $tag`
}

#**************************************************
#%FUNCTION: _resetCacheTimestamp
#%DESCRIPTION: Clears all cache information for a given 
# tag.
#%ARGUMENTS:
# tag -- The tag to group the variables together
#%RETURNS:
# Nothing.
#**************************************************
_resetCacheTimestamp() {
    local tag=$1
    if [[ "$(_getCacheType $tag)" == "env" ]]; then	
	local var=$(_makeCacheTimestampVariable $tag)
	export $var=$(date "+%s")
    else 
	touch $(_makeCacheFile $tag)
    fi
}

#**************************************************
#%FUNCTION: _setCacheValue
#%DESCRIPTION: Sets the related cache with a given
# value.
#%ARGUMENTS:
# tag -- The tag to group the variables together
#%RETURNS:
# Nothing.
#**************************************************
_setCacheValue() {
    local tag=$1 value=$2
    if [[ "$(_getCacheType $tag)" == "env" ]]; then	
	local var=$(_makeCacheValueVariable $tag)
	export $var=$value
	_resetCacheTimestamp $tag
    else
	echo $value > $(_makeCacheFile $tag)
	_resetCacheTimestamp $tag
    fi
}

#**************************************************
#%FUNCTION: _getCacheValue
#%DESCRIPTION: Retrieves the related cache with a given
# value.
#%ARGUMENTS:
# tag -- The tag to group the variables together
# [life] -- The limit on how old the data can be for 
# retrieval
# [var] -- The name of the variable to populate.
#%RETURNS:
# Nothing.
#**************************************************
_getCacheValue() {
    local tag=$1 life=$2   
    # Current timestamp
    local now=$(date "+%s")
    local timestamp value

    if [[ "$(_getCacheType $tag)" == "env" ]]; then	
	local var_value=$(_makeCacheValueVariable $tag)
	value=$(eval echo \$$var_value)
	local var_timestamp=$(_makeCacheValueVariable $tag)
	timestamp=$(eval echo \$${var_timestamp})
    else
	local file_value=$(_makeCacheFile $tag)
	timestamp=$(stat --printf=%Y $file_value 2>/dev/null)
	value=$(cat $file_value 2>/dev/null)
    fi

    if [ ! -z "$life" ]; then
	if [ -z "${timestamp}" ] || \
	    [ $(($now - ${timestamp})) -gt $life ]; then
	    return
	fi
    fi
    
    if [ ! -z "$3" ]; then
	local "$3" && upvar $3 $value
	return
    fi

    echo $value
}   

_getCachedByLifeCycle() {
    # Arguments
    local tag=$1 life=$2 func=$3 args=$4 var=$5
    # Current timestamp
    local now=$(date "+%s")
    # Unique Variable Names
    local var_timestamp=$(_makeCacheTimestampVariable $tag)
    local var_value=$(_makeCacheValueVariable $tag)
    local file_value=$(_makeCacheFile $tag)
    # -- dereferenced values --
    local timestamp value
    if [[ "$(_getCacheType $tag)" == "env" ]]; then	
	timestamp=$(eval echo \$${var_timestamp})
	value=$(eval echo \$${var_value})
    else
	timestamp=$(stat --printf=%Y $file_value 2>/dev/null)
	value=$(cat $file_value 2>/dev/null)
    fi
    # Compare against previous values
    if [ -z "${timestamp}" ] || \
	[ $(($now - ${timestamp})) -gt $life ] || \
	[ -z "${value}" ] ; then
	# Resolve output and store
	local output=`$func $4`  
	value=$(echo $output)
	if [[ "$(_getCacheType $tag)" == "env" ]]; then
	    export ${var_value}="$output"
	    value=$(eval echo \$$var_value)
	    export ${var_timestamp}=$(date "+%s")
	else
	    echo $output > $file_value
	    value=$(cat $file_value)
	fi
    fi 

    if [ ! -z "$var" ]; then
	local "$var" && upvar $var $value
	return
    fi

    echo $value
}

_getCachedByFileTimestamp() {
    # Arguments
    local tag=$1 ref=$2 func=$3 args=$4 var=$5
    # Current timestamp
    local now=$(date "+%s")
    # File timestamp
    local rtime=$(stat --print=%Y $ref | cut -f1 -d.)
    rtime=$(date -d"${rtime}" "+%s")
    # Unique Variable Names
    local var_timestamp=$(_makeCacheTimestampVariable $tag)
    local var_reference=$(_makeCacheReferenceVariable $tag)
    local var_value=$(_makeCacheValueVariable $tag)
    local file_value=$(_makeCacheFile $tag)
    # -- dereferenced values --
    local timestamp reference value
    if [[ "$(_getCacheType $tag)" == "env" ]]; then	
	timestamp=$(eval echo \$$var_timestamp)
	reference=$(eval echo \$$var_reference)
	value=$(eval echo \$$var_value)
    else
	timestamp=$(stat --printf=%Y $file_value)
	value=$(cat $file_value)
    fi
    # Compare against previous values
    if [ -z "${timestamp}" ] || \
	[ -z "${reference}" ] || \
	[ $now -lt $rtime ] || \
	[ "$reference" != "$ref" ] || \
	[ -z "${value}" ]; then
	# Resolve output and store
	local output=`$func $4`
	export $var_value="$output"
	value=$(eval echo \$$var_value)
	export $var_timestamp=$(echo $now)
	export $var_reference=$(echo $ref)
    fi

    if [ ! -z "$var" ]; then
	local "$var" && upvar $var $value
	return
    fi

    echo $value
}
