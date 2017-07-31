# Auto Completion
. ${HOME}/util/util/completion.sh
if [ "$_no_completion" == "1" ]; then
    return
fi

# Perforce Changelists
_p4_my_changelists()
{
    local dir=$1
    if [ -z "$dir" ]; then
	dir=...
    fi
    p4 changes "${dir}" 2>/dev/null | awk '{print $2}'
}

_p4_my_open_changelists()
{
    local dir=$1
    if [ -z "$dir" ]; then
	dir=...
    fi
    p4 opened "${dir}" 2>/dev/null | grep -v default | awk '{print $(NF-1)}' | sort | uniq
}

# Perforce Branches
_p4_get_branches_core()
{
    p4 branches 2>/dev/null | awk 'NF>3 {print $2}'
}

_p4_get_branches() {
    _get_cached_by_life_cycle @P4 86400 _p4_get_branches_core 
}
_reset_cache @P4 _p4_get_branches_core

# Perforce Users
_p4_get_users_core()
{    
    p4 users 2>/dev/null | awk 'NF>3 {print $1}'
}

_p4_get_users() {
    _get_cached_by_life_cycle @P4 86400 _p4_get_users_core 
}
_reset_cache @P4 _p4_get_users_core

# Perforce Commands
_p4_get_commands_core()
{   
    p4 help commands 2>/dev/null | awk 'NF>3 {print $1}'
}
_p4_get_commands() {
    _get_cached_by_file_timestamp @P4 `which p4` _p4_get_commands_core 
}
_reset_cache @P4 _p4_get_commands_core

# Perforce Path Completion
function _p4_get_depot_completion()
{
    local completions
    local dirs
    echo $(
        # in case someone actually has /[/]depot/ on their file system
        # and have enabled globastar, we disable it here just to be
        # safe.
        #shopt -u globstar
        completions=$(p4 files ${1}* 2>/dev/null | sed 's/#[0-9]\+ - .*$//')
        dirs=$(p4 dirs ${1}* 2>/dev/null | sed 's/.*/\0\//')
        # If there is only one dir that matches make it two
        # entries so it will complete to using the single trailing /
        if [[ ""=$completions ]] && [ 1 -eq $(echo $dirs| wc -w) ] ; then
                dirs="${dirs} ${dirs}/"
        fi
        completions=${completions}" "${dirs}
        echo $completions
    )
}

_p4_commands()
{
    local cur=${COMP_WORDS[COMP_CWORD]}
    local prev=${COMP_WORDS[COMP_CWORD-1]}

    commands=$(_p4_get_commands)

    # default completions is the list of commands
    completions=$commands

    case "$prev" in
        add)
            completions="-c -f -n -t"
            ;;
        annotate)
            completions="-a -c -i -q -d -dw"
            ;;
        branch)
            completions="-f -d -o -i $(_p4_get_branches)"
            ;;
        change)
            completions="-f -s -d -o -i"
            ;;
        changes)
            completions="-i -t -l -L -c -m -s -u"
            ;;
        changelist)
            completions="-f -s -d -o -i"
            ;;
        changelists)
            completions="-i -t -l -L -c -m -s -u"
            ;;
        client)
            completions="-f -t -d -o -i"
            ;;
        counter)
            completions="-f -d"
            ;;
        delete)
            completions="-c -n"
            ;;
        depot)
            completions="-d -o -i"
            ;;
        describe)
            completions="-dn -dc -ds -du -db -dw -s"
            ;;
        diff)
            completions="... -dn -dc -ds -du -db -dw -dl -f -sa -sd -se -sr -t"
            ;;
        edit)
            completions="-c -n -t"
            ;;
        integrate)
            completions="-c -d -Dt -Ds -Di -f -h -i -I -o -r -t -v -b -s -n"
            ;;
        resolve)
            completions="-af -am -as -at -ay -db -dw -f -n -o -t -v"
            ;;
        resolved)
            completions="-o"
            ;;
        revert)
            completions="-a -n -k -c ..."
            ;;
        sync)
            completions="-f -n -k"
            ;;
        -s)
            completions="@"
            ;;
        -t)
            # file types
            base_types="text binary symlink apple apple resource unicode utf16"
            modifiers="w x ko k l C D F S Sn m X"
            completions=""
            for el in $base_types; do
                for ele in $modifiers; do
                    completions=$completions" "${el}"+"${ele}
                done
            done
            
            ;;
        -b)
            completions=$(_p4_get_branches)
            ;;
        changes)
            completions="... -u"
            ;;
        -u)
            completions=$(_p4_get_users)
            ;;
        user)
            completions=$(_p4_get_users)
            ;;
    esac

    if [[ "$cur" == //* && -z "$P4_DISABLE_DEPOT_COMPLETION" ]]; then
        completions=$(_p4_get_depot_completion $cur)
    fi
    
    COMPREPLY=( $(compgen -W "$completions" -- $cur) )
}

complete -o default -F _p4_commands p4
