# Auto Completion
. ${HOME}/util/util/completion.sh

#***************************************************************************
# %DESCRIPTION:
# Returns the lib.defs file that should be used by the current command line
# being expanded. 
# %ASSUMPTIONS:
# If explicitly specified then there is a -libdefs parameter, or implicitly
# through a -dir parameter.
# %RETURNS:
# The path to teh lib.defs file whether explicitly, implicitly or not defined.
#***************************************************************************
_get_lib_defs() 
{
    local libdefs=$(_get_arg_value -libdefs)
    if [ -z "$libdefs" ]; then
	local dir=$(_get_arg_value -dir)
	if [ -z "$dir" ]; then
	    dir="."
	fi
	echo "${dir}/lib.defs"
    fi
    tmp=$(readlink -f $libdefs 2>/dev/null)
    if [ ! -z "$tmp" ]; then
	libdefs=$tmp
    fi
    echo $libdefs
}

#***************************************************************************
# %DESCRIPTION:
# Returns the list of possible lib.defs files that can be found under the
# current directory. 
# Note; To limit the number of possibilities the search will only decend 
# a level of 3 (3 directories deep).
# %RETURNS
# The list of possible lib.defs
#***************************************************************************
_oa_lib_defs_core() 
{
    find . -maxdepth 3 -name lib.defs
}

_oa_lib_defs()
{
    _get_cached_by_life_cycle @OA_LIB_DEFS 86400 _oa_lib_defs_core
}
_reset_cache @OA_LIB_DEFS _oa_lib_defs_core

#***************************************************************************
# %DESCRIPTION:
# Returns the list of possible working directories that can be found under the
# current directory. 
# Note: The search will be limited for efficiency by the same  filtering 
# criteria as the lib.defs.
# %RETURNS
# The list of possible directories
#***************************************************************************
_oa_lib_dirs_core()
{
    _oa_lib_defs_core | sed "s|/lib.defs||"
}

_oa_lib_dirs()
{    
    _get_cached_by_life_cycle @OA_LDIRS 86400 _oa_lib_dirs_core
}
_reset_cache @OA_LDIRS _oa_lib_dirs_core

# The OA Libraries
_oa_libs_core()
{
    local libdefs=$(_get_lib_defs)    
    ${HOME}/util/oa/oaLibs -libdefs $libdefs 2>/dev/null   
}

_oa_libs()
{
    local libdefs=$(_get_lib_defs)    
    _get_cached_by_file_timestamp @OA_LIBS $libdefs _oa_libs_core
}
_reset_cache @OA_LIBS _oa_libs_core

# The OA Rules
_oa_rules_core()
{
    local libdefs=$(_get_lib_defs)
    local libName=$(_get_arg_value -libName)    
    if [ -z $libName ]; then
	return
    fi    
    ${HOME}/util/oa/oaRules -libdefs $libdefs -libName $libName 2>/dev/null
}

_oa_rules()
{
    local libdefs=$(_get_lib_defs)
    local libName=$(_get_arg_value -libName)
    if [ ! -z "$libName" ]; then
	local techTime$(${PWD}/oaTechTimestamp -libdefs $libdefs -libName $libName)
	_get_cached_by_timestamp "@OA_RULES${libName}" "${techTime}"  _oa_rules_core
    fi
}
_reset_cache @OA_RULES oa_rules_core

# The LCV 
_oa_lcv_core()
{
    local libName=$1
    local libdefs=$(_get_lib_defs)
    ${PWD}/oaLCV -libdefs $libdefs "^${libName}\$/*/*"
}

_oa_lib_timestamp() 
{
    local libdefs=$(_get_lib_defs)
    local libName=$1
    local libPath=$(${PWD}/oaLibPath -libdefs $libdefs -libName $libName)
    if [ ! -d $libPath ]; then
	echo -1
	return
    fi
    fileTimestamp $libPath
}

_oa_lib_cell_timestamp()
{
    local libdefs=$(_get_lib_defs)
    local libName=$1
    local libPath=$(${PWD}/oaLibPath -libdefs $libdefs -libName $libName)
    local cellPath=$(ls -t ${libPath}/*/*/*.oa 2>/dev/null | head -1 | rev | cut -f3- -d/ | rev)    
    if [ ! -d "$cellPath" ]; then
	fileTimestamp $libPath
	return
    fi
    fileTimestamp $cellPath
}

_oa_lib_cell_view_timestamp()
{
    local libdefs=$(_get_lib_defs)
    local libName=$1
    local libPath=$(${PWD}/oaLibPath -libdefs $libdefs -libName $libName)
    local viewPath=$(/bin/ls -t ${libPath}/*/*/*.oa 2>/dev/null | /usr/bin/head -1)   
    if [ ! -e "$viewPath" ]; then
	fileTimestamp $libPath
	return
    fi
    fileTimestamp $viewPath
}

filter_lcv_column() 
{
    local c=$1
    local p=$2
    if [ "$p" == "" ] || [ "$p" == "*" ]; then	
	cat
    else
	awk -F "/" "\$${c} ~ /${p}/"
    fi 
}	

_oa_lcv()
{
    local libdefs=$(_get_lib_defs)
    local pattern=$1
    local libPattern=$(echo $pattern | cut -f1 -d/)
    local cellPattern=$(echo $pattern | cut -f2 -d/)
    local viewPattern=$(echo $pattern | cut -f3 -d/)
    local libNames=$(_oa_libs | tr " " "\n" | filter_lcv_column 1 "${libPattern}")
    for libName in $libNames; do
	local ltime=$(_oa_lib_cell_view_timestamp $libName)
	_get_cached_by_timestamp "@OA_LCV${libName}" "${ltime}" _oa_lcv_core "${libName}" | \
	    tr " " "\n" | \
	    filter_lcv_column 2 "${cellPattern}" | \
	    filter_lcv_column 3 "${viewPattern}"
    done
}

# --- Completion Functions ---

# The following detail the argument completion for
# oaLibs
# oaCells
# oaLCV
# oaRules
# oaTechTimestamp

# Argument completion for the set of cells found in the specified OA Library
_oa_oaCells() 
{
    local cmd=${COMP_WORDS[0]}
    local cur prev
    local unused=$(_get_unused "-libdefs -dir -libName -verbose")
    _get_cword cur
    _get_pword prev
    case "$prev" in
	-libdefs)
             completions=$(_oa_lib_defs)
	     ;;
        -dir)
             completions=$(_oa_lib_dirs)
	     ;;
        -libName)
             completions=$(_oa_libs)
	     ;;
	*)
	     completions=$unused
	     ;;
     esac
     COMPREPLY=( $(compgen -W "$completions" -- $cur) )
}    
complete -o default -F _oa_oaCells oaCells

# Argument completion for the set of OA Library names from a specified (or implied) lib.defs file.
_oa_oaLibs() 
{
    local cmd=${COMP_WORDS[0]}
    local cur prev
    local unused=$(_get_unused "-libdefs -dir -verbose")
    _get_cword cur
    _get_pword prev
    case "$prev" in
	-libdefs)
             completions=$(_oa_lib_defs)
	     ;;
        -dir)
             completions=$(_oa_lib_dirs)
	     ;;
	*)
	     completions=$unused
	     ;;
     esac
     COMPREPLY=( $(compgen -W "$completions" -- $cur) )
}    
complete -o default -F _oa_oaLibs oaLibs

# Argument completion for the set of rule IDs found in the OA Library technology.
_oa_oaRules() 
{
    local cmd=${COMP_WORDS[0]}
    local cur prev
    local unused=$(_get_unused "-libdefs -dir -libName -verbose")
    _get_cword cur
    _get_pword prev
    case "$prev" in
	-libdefs)
             completions=$(_oa_lib_defs)
	     ;;
        -dir)
             completions=$(_oa_lib_dirs)
	     ;;
        -libName)
             completions=$(_oa_libs)
	     ;;
	*)
	     completions=$unused
	     ;;
     esac
     COMPREPLY=( $(compgen -W "$completions" -- $cur) )
}    
complete -o default -F _oa_oaRules oaRules
