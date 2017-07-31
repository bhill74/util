# Auto Completion
. ${HOME}/util/rfs/completions.sh
. ${HOME}/util/p4/completions.sh

if [ "$_no_completion" == "1" ]; then
    return
fi

# The CodeCollaborator Server
_ccollab_server_core()
{
    ccollab info | head -1 | awk '{print $(NF)}'
}

_ccollab_server()
{
    _get_cached_by_file_timestamp @CCOLLAB `which ccollab` _ccollab_server_core
}
_reset_cache @CCOLLAB _ccollab_server_core

# The CodeCollaborator Commands
_ccollab_get_commands_core()
{
    ccollab help --show-all 2>&1 | egrep '^  [a-z]' | awk '{print $1}'
}

_ccollab_get_commands() 
{
    _get_cached_by_file_timestamp @CCOLLAB `which ccollab` _ccollab_get_commands_core
}
_reset_cache @CCOLLAB _ccollab_get_commands_core

# The CodeCollaborator Admin Commands
_ccollab_get_admin_commands_core()
{
    ccollab help admin --show-all 2>&1 | egrep '^  [a-z]' | awk '{print $1}'
}

_ccollab_get_admin_commands() 
{
    _get_cached_by_file_timestamp @CCOLLAB `which ccollab` _ccollab_get_admin_commands_core
}
_reset_cache @CCOLLAB _ccollab_get_admin_commands_core

# The CodeCollaborator Global Options
_ccollab_global_options_core()
{
    ccollab help global-options 2>&1 | egrep -- '^     *--[a-z]' | awk '{print $1}' | sed "s/--//"
}

_ccollab_global_options() 
{
    _get_cached_by_file_timestamp @CCOLLAB `which ccollab` _ccollab_global_options_core
}
_reset_cache @CCOLLAB _ccollab_global_options_core

# My Reviews
_ccollab_my_reviews_core() 
{
    ${PWD}/ccreviews -creator=${USER} -active 2>&1 | cut -f1 -d,
}

_ccollab_my_reviews()
{
    _get_cached_by_life_cycle @CCOLLAB 86400 _ccollab_my_reviews_core
}
_reset_cache @CCOLLAB _ccollab_my_reviews_core

_ccollab_reviews()
{
    echo "new last ask $(_ccollab_my_reviews)"
}

# Local Users
_ccollab_local_users_core()
{
    ${PWD}/ccusers -level 2 -user=${USER} 2>&1 
}

_ccollab_local_users()
{
    _get_cached_by_life_cycle @CCOLLAB 86400 _ccollab_local_users_core
}
_reset_cache @CCOLLAB _ccollab_local_users_core

# Groups
_ccollab_groups_core()
{
    ${PWD}/ccgroups -simple 2>&1 | sed "s/ /\\\\ /g"
}

_ccollab_groups()
{
    _get_cached_by_life_cycle @CCOLLAB 86400 _ccollab_groups_core
}
_reset_cache @CCOLLAB _ccollab_groups_core

_ccollab_commands()
{
    local index=${#COMP_WORDS[@]}
    local cmd=${COMP_WORDS[1]}
    local cur
    _get_cword cur
    _get_pword prev

    commands=$(_ccollab_get_commands)

    # default completions is the list of commands
    completions=$commands

    case "$cmd" in
	help)
           completions="$commands --show-all global-options"
           ;;
	info)
           completions=""
	   ;;
        login)
           if [ $index -eq 3 ]; then
	        completions=$(_ccollab_server)
           elif [ $index -eq 4 ]; then
                completions=$USER
           elif [ $index -eq 5 ]; then
                completions=""
           else
                completions=""
           fi
	   ;;
        logout)
           completions=""
	   ;;
        set)
           if [ $index -eq 3 ]; then
	        completions=$(_ccolab_global_options)
           else
                completions=""
           fi
	   ;;
        addfiles)
	   if [ $index -eq 3 ]; then # <review>
	        completions=$(_ccollab_reviews)
           elif [ "${prev:0:2}" == "--" ]; then
                completions=""           
           else
                completions="--relative-to --separate-changelists --upload-comment"
           fi
	   ;;
        addchangelist)
           if [ $index -eq 3 ]; then
                completions=$(_ccollab_reviews)
	   elif [ $index -eq 4 ]; then
	        completions=$(_p4_my_open_changelists)
	   else
	        completions=""
           fi
	   ;;
        adddiffs)
	   if [ $index -eq 3 ]; then # <review>
	        completions=$(_ccollab_reviews)
	   elif [ $index -eq 4 ]; then # <before>
	        completions=""
           elif [ "${prev:0:2}" == "--" ]; then
                completions=""           
           else
                completions="--relative --upload-comment"
           fi
	   ;;
        addp4diffs)
	   if [ $index -eq 3 ]; then # <review>
	        completions=$(_ccollab_reviews)
           elif [ "${prev:0:2}" == "--" ]; then
                completions=""           
           else
                completions="--upload-comment"
           fi
	   ;;
        addversions)
	   if [ $index -eq 3 ]; then # <review>
	        completions=$(_ccollab_reviews)
           elif [ "${prev:0:2}" == "--" ]; then
                completions=""           
           else
                completions="--version-spec --upload-comment"
           fi
	   ;;
        actionitems)
           completions=""
	   ;;
        browse)
           if [ "$prev" == "--review" ]; then
                completions=$(_ccollab_reviews)
           else
                completions="--review"
           fi 
	   ;;
        commit)
	   if [ $index -eq 3 ]; then # <review>
	        completions=$(_ccollab_reviews)
           elif [ "${prev:0:2}" == "--" ]; then
                completions=""           
           else
                completions="--comment --dismiss-only --force"
           fi
	   ;;
        addp4job)
	   if [ $index -eq 3 ]; then # <review>
	        completions=$(_ccollab_reviews)         
           else
                completions=""
           fi
	   ;;
        addurls)
	   if [ $index -eq 3 ]; then # <review>
	        completions=$(_ccollab_reviews)         
           elif [ "${prev:0:2}" == "--" ]; then
                completions=""  
           else
                completions="--upload-comment"
           fi
	   ;;
        admin)
           if [ $index -eq 3 ]; then # <sub-command>
	        completions=$(_ccollab_get_admin_commands)
	   fi
	   ;;
    esac

    COMPREPLY=( $(compgen -W "$completions" -- $cur) )
}
complete -o default -F _ccollab_commands ccollab

_ccpeople_commands() {
    local cmd=${COMP_WORDS[1]}
    local cur prev
    local unused=$(_get_unused "-review -all -author -reviewer -observer -query")
    _get_cword cur
    _get_pword prev
    case "$prev" in 
	-review)
             completions=$(_ccollab_my_reviews)
	     ;;
	#-all)
	#-author)
	#-reviewer)
	#-observer)
	#-query)
	*)
	     completions=$unused
	     ;;
    esac
    COMPREPLY=( $(compgen -W "$completions" -- $cur) )
}
complete -o default -F _ccpeople_commands ccpeople

_ccreviews_commands() {
    local cmd=${COMP_WORDS[1]}
    local cur prev
    local unused=$(_get_unused "-me -involved -user -creator -author -reviewer -moderator -observer -active -query")
    _get_cword cur
    _get_pword prev
    case "$prev" in 
	-me)
             completions="creator author reviewer moderator observer"
	     ;;
	-user|-creator|-author|-reviewer|-moderator|-observer)
	     completions=$(_ccollab_local_users)
	     ;;
	#-active)
	#-query)
	*)
	     completions=$unused
	     ;;
    esac
    COMPREPLY=( $(compgen -W "$completions" -- $cur) )
}
complete -o default -F _ccreviews_commands ccreviews

_ccusers_commands() {
    local cmd=${COMP_WORDS[1]}
    local cur=$2 icur prev    
    local unused=$(_get_unused "-group -level -user -query")
    _get_cword icur    
    _get_pword prev
    case "$prev" in 
	-group) 
              let i=0
	      compgen -W "$(_ccollab_groups)" -- "$cur" > ${TMP}/a.lck
              while read line
	      do
		  if [[ "${icur:0:1}" == "'" ]]; then 
		      COMPREPLY[i]="'${line}'"
                  elif [[ "${icur:0:1}" == "\"" ]]; then
		      COMPREPLY[i]="\"${line}\""
		  else
		      COMPREPLY[i]=$(printf "%q" "${line}")
		  fi                 
		  ((++i))
	      done < ${TMP}/a.lck
	      rm ${TMP}/a.lck
	      return 
	      ;;
	-level)
	      completions="1 2 3 4 -1 -2 -3 -4"
	      ;;
	-user)
	      completions=$(_ccollab_local_users)
	      ;;
	#-query)
	*)
	      completions=$unused
	      ;;
    esac
    COMPREPLY=( $(compgen -W "$completions" -- $cur) )
}
complete -o default -F _ccusers_commands ccusers

_ccgroups_commands() {
    local cmd=${COMP_WORDS[1]}
    local cur=$2 icur prev    
    local unused=$(_get_unused "-linked -simple -user -indent -query")
    _get_cword icur    
    _get_pword prev
    case "$prev" in 
	-user)
	      completions=$(_ccollab_local_users)
	      ;;
        #-linked)
	#-simple
	#-user
	#-indent
	#-query
        *)
	      completions=$unused
	      ;;
    esac
    COMPREPLY=( $(compgen -W "$completions" -- $cur) )
}
complete -o default -F _ccgroups_commands ccgroups
