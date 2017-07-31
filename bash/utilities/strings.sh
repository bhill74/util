. ${HOME}/util/process/process.sh

#**************************************************
#%FUNCTION: trim
#%DESCRIPTION: Removes leading and trailing whitespace
#%ARGUMENTS:
# string -- String to process
#%RETURNS:
# The trimmed string.
#**************************************************
trim()
{
    process $@
    local var=$@
    var="${var#"${var%%[![:space:]]*}"}"   # remove leading whitespace characters
    var="${var%"${var##*[![:space:]]}"}"   # remove trailing whitespace characters
    echo -n "$var"
}

#**************************************************
#%FUNCTION: prefix 
#%DESCRIPTION: Adds a prefix to every word in the 
# given string
#%ARGUMENTS:
# prefix -- The prefix to add
# var -- The string to process
#%RETURNS:
# The modified string.
#**************************************************
prefix()
{
    process $@
    local prefix=$1 var=$2
    var=$(trim $var | sed "s|[[:space:]]| $prefix|g") 
    echo -n "${prefix}${var}"
    #echo -n "$prefix${var//[[:space:]]/ $prefix}"
}

#**************************************************
#%FUNCTION: suffix 
#%DESCRIPTION: Adds a suffix to every word in the 
# given string
#%ARGUMENTS:
# suffix -- The suffix to add
# var -- The string to process
#%RETURNS:
# The modified string.
#**************************************************
suffix()
{
    process $@
    local suffix=$1 var=$2
    var=$(trim $var | sed "s|[[:space:]]|$suffix |g") 
    echo -n "${var}${suffix}"
    #echo -n "${var//[[:space:]]/$suffix }$suffix"
}

#**************************************************
#%FUNCTION: rev
#%DESCRIPTION: Reverses the characters in a given 
# string or pipe
# Note: Only defined if not already existing.
#%ARGUMENTS:
# [string] -- string to reverse
#%RETURNS:
# The modified strings
#**************************************************
type rev >/dev/null 2>&1 || {
    rev() {
	process $@
	_rev() {
	    local str=$1
	    len=${#str}
    	    for ((i=1;i<len;i++)); do str=$str${str: -i*2:1}; done; str=${str:len-1}
	    echo $str
	}	

	if [ ! -t 0 ]; then
	    while read line; do
		_rev $line
	    done
	else
            if [ "$1" != "-t" ]; then
		_rev $1
	    fi
	fi
    }
}
