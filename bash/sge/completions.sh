# Auto completion
. ${HOME}/util/process/process.sh
. ${HOME}/util/util/completion.sh
if [ "$_no_completion" == "1" ]; then
    return
fi

_sge_get_info()
{
    local _cur _prev cmd _usunsed
    _get_cword _cur
    _get_pword _prev   
    _get_cmd cmd
    options=$(_sge_ops "$cmd")
    _unused=$(_get_unused "$options")
    if local "$1" "$2" "$3"; then
	upvar $1 $_cur
	upvar $2 $_prev
	upvar $3 "$_unused"
    fi
}

# Spaces and using square brackets
function _sge_ops1() {
    $1 -help | egrep '^ +\[' | awk '{print $1}' | sed "s/[]]//" | sed "s/[[]//" | tr '\n' ' '
}

# Tab to dash
function _sge_ops2() {
    $1 -help | egrep '^'$'\t''+\-' | awk '{print $1}' | tr '\n' ' '
}

# 3 spaces to dash
function _sge_ops3() {
    $1 -help | egrep '^   \-' | awk '{print $1}' | tr '\n' ' '
}

# Spaces and using dash
function _sge_ops4() {
    $1 -help | egrep '^ +\-' | awk '{print $1}' | tr '\n' ' '
}

function _sge_ops() {
    r=$(_sge_ops1 $1 2>/dev/null)
    if [ ! -z "$r" ]; then
	echo $r
	return
    fi
    r=$(_sge_ops2 $1 2>/dev/null)
    if [ ! -z "$r" ]; then
	echo $r
	return
    fi
    r=$(_sge_ops3 $1 2>/dev/null)
    if [ ! -z "$r" ]; then
	echo $r
	return
    fi
    _sge_ops4 $1 2>/dev/null
}

function _menu_size() {
    local num=$(echo "$1" | grep -o ' ' 2>/dev/null | wc -l)
    num=$((num * 70))
    if [ $num -gt $2 ]; then
	echo $2
	return
    fi
    echo $num
}

function _sge_yes_no() {
    echo "y n"
}

function _sge_get_users()
{
    qconf -suserl 2>/dev/null
}

function _sge_get_run_users()
{
    qstat  2>/dev/null | awk '{print $4}' | sort | uniq
}

function _sge_get_user_lists()
{
    qconf -sul 2>/dev/null
}

function _sge_get_submit_hosts()
{
    qconf -ss  2>/dev/null | cut -f1 -d.
}

function _sge_get_hosts()
{
    { qconf -ss ; qconf -sh ; } | sort | uniq | cut -f1 -d.
}

function _sge_get_projects()
{
    qconf -sprjl 2>/dev/null
}

function _sge_get_parallel()
{
    qconf -spl 2>/dev/null
}

function _sge_get_groups()
{
    qconf -shgrpl 2>/dev/null
}

function _sge_get_resource_names()
{
    qstat -F 2>/dev/null | egrep "(hl:|hf:)" | cut -f2 -d: | cut -f1 -d= | sort | uniq
}

function _sge_get_resource_names_multiple()
{
    local values=$(_sge_get_resource_names | tr '\n' ' ')
    local cmd=$(_get_cmd)
    local last=$(_get_last_value "$cmd" $2)
    ${HOME}/util/util/gGetValues -C "$1" -c "$values" \
	-d , -D "$last" -t "$cmd $2" \
	-w "Please choose one or more resource names" \
	-H $(_menu_size "$values" 600)
}

function _sge_get_last() 
{
    echo $1 | awk -F, '{print $NF}'
}

function _sge_filter()
{
    if [ ! -z "$1" ]; then	
	grep -v "$1"
    else 
	grep -v -e '[^[:print:]]'
    fi
}

function _sge_filter_merge() 
{
    local value=$1
    local full=$2
    egrep "^$value" | sed "s/^$full/$value/"
}

function _sge_get_resource_values()
{
    ${PWD}/qresvalues -start "$1" | uniq
}

function _sge_get_all_resource_values()
{
    ${PWD}/qresvalues -all | uniq
}

function _sge_get_resource_values_multiple()
{
    local cur=$1
    local prefix=${cur/=*/=}
    if [[ $cur =~ , ]]; then
	local values=$(_sge_get_all_resource_values | tr '\n' ' ')
	local cmd=$(_get_cmd)
	cur=$(${PWD}/resourceValuesParse -expand "$cur")
	local result=$(${HOME}/util/util/gGetValues -C "$cur" -c "$values" \
	    -d , -f -t "$cmd $2" \
	    -w "Please choose one or more resource values" \
	    -H $(_menu_size "$values" 700) )
	result=$(${PWD}/resourceValuesParse "$result")
	prefix=$(echo $cur | sed -r "s/=[^=]*\$/=/")
	COMPREPLY=(${result/#$prefix})
    else
	local values=$(_sge_get_resource_values $1 | tr '\n' ' ')
	if [[ $prefix =~ = ]]; then
	    cur=${cur/#$prefix}
	fi
	COMPREPLY=($(compgen -W "$values" -- $cur) )
    fi
}

# Job Identifers
function _sge_get_all_job_ids()
{  
    qstat -u '*' | tail -n+3 | _sge_filter $2 | awk '{print $1}'
}

function _sge_get_run_job_ids()
{
    qstat -u '*' -s r | tail -n+3 | _sge_filter $2 | awk '{print $1}'
}

function _sge_get_my_job_ids()
{  
    qstat -u "$USER" | tail -n+3 | _sge_filter $2 | awk '{print $1}'
}

function _strip_xml 
{
    perl -p -e "s/^\\s+//;s/\\<.*?\\>//g;" | sort -u
}

function _sge_filter_job_names 
{
    grep JB_name | _strip_xml
}

function _sge_get_all_job_names() 
{
    qstat -u '*' -xml | _sge_filter_job_names
}

function _sge_get_run_job_names() 
{
    qstat -u '*' -s r -xml | _sge_filter_job_names
}

function _sge_get_my_job_names()
{
    qstat -u $USER -xml | _sge_filter_job_names
}

function _sge_filter_jobs 
{
    egrep "(JB_name|JB_job_number)" | _strip_xml
}

function _sge_get_all_jobs()
{
    qstat -u '*' -xml | _sge_filter_jobs | _sge_filter $2
}

function _sge_get_run_jobs() 
{
    qstat -u '*' -s r -xml | _sge_filter_jobs
}

function _sge_get_my_jobs()
{
    qstat -u $USER -xml | _sge_filter_jobs
}

function _sge_get_all_jobs_multiple()
{ 
    local jobs=$(_sge_get_all_jobs | tr '\n' ' ')
    local cmd=$(_get_cmd)
    local last=$(_get_last_value "$cmd" $2)  
    ${HOME}/util/util/gGetValues -C "$1" -c "$jobs" \
	-d , -D "$last" -t "$cmd $2" \
	-w "Please choose one or more job identifiers" \
	-H $(_menu_size "$jobs" 400)
}

function _sge_get_run_jobs_multiple()
{
    local jobs=$(_sge_get_run_jobs | tr -'\n' ' ')
    local cmd=$(_get_cmd)
    local last=$(_get_last_value "$cmd" $2)   
    ${HOME}/util/util/gGetValues -C "$1" -c "$jobs" \
	-d , -D "$last" -t "$cmd $2" \
	-w "Please choose one or more job identifiers for these jobs in progress" \
	-H $(_menu_size "$jobs" 400)
}

function _sge_get_my_jobs_multiple()
{
    local jobs=$(_sge_get_my_jobs | tr '\n' ' ')
    local cmd=$(_get_cmd)
    local last=$(_get_last_value "$cmd" $2)
    ${HOME}/util/util/gGetValues -C "$1" -c "$jobs" \
	-d , -D "$last"  -t "$cmd $2" \
	-w "Please choose one or more job identifiers for these jobs owned by <b>'$USER'</b>" \
	-H $(_menu_size "$jobs" 400)
}

function _sge_get_queues()
{
    qconf -sql 2>/dev/null
}

_sge_qtail()
{    
    local cur
    _get_cword cur
    COMPREPLY=( $(compgen -W "$(_sge_get_all_jobs 1 INTERACT)" -- $cur) )
}
complete -o default -F _sge_qtail qtail

_sge_qjobhost()
{
    local cur
    _get_cword cur
    COMPREPLY=( $(compgen -W "$(_sge_get_all_jobs)" -- $cur) )
}
complete -o default -F _sge_qjobhost qjobhost

_sge_qaccess()
{
    local cur prev unused
    _sge_get_info cur prev unused
    case "$prev" in
        -h)
            completions=$(_sge_get_hosts $cur)
	    ;;
	-P)
	    completions=$(_sge_get_projects $cur)
	    ;;
	-u)
            completions=$(_sge_get_users $cur)
	    ;;
	-ul)
            completions=$(_sge_get_user_lists $cur)
	    ;;
        *)
            completions=$unused
	    ;;
    esac
    COMPREPLY=( $(compgen -W "$completions" -- $cur) )
}
complete -o default -F _sge_qaccess qaccess

_sge_qacct()
{
    local cur prev unused
    _sge_get_info cur prev unused
    case "$prev" in
	-g)
	    completions=$(_sge_get_groups $cur)
	    ;; 
        -h)
            completions=$(_sge_get_hosts $cur)
	    ;;
	-j)
	    completions=$(_sge_get_all_jobs $cur)
	    ;;
	-l)
	    _sge_get_resource_values_multiple "$cur" "$prev"
	    return
	    ;;
	-o)
	    completions=$(_sge_get_users $cur)
	    ;;
	-P)
	    completions=$(_sge_get_projects $cur)
	    ;;
	-q)
	    completions=$(_sge_get_queues $cur)
 	    ;;	
        *)
            completions=$unused
	    ;;
    esac
    COMPREPLY=( $(compgen -W "$completions" -- $cur) )
}
complete -o default -F _sge_qacct qacct

_sge_qalter()
{
    local cur prev unused
    _sge_get_info cur prev unused
    case "$prev" in
        -b|-j|-R|-r)
	    completions=$(_sge_yes_no)
	    ;;
        -h)
            completions=$(_sge_get_hosts $cur)
	    ;;
	-P)
	    completions=$(_sge_get_projects $cur)
	    ;;
	-u)
            completions=$(_sge_get_users $cur)
	    ;;
	-w)
            completions="e w n v p"
	    ;;
        *)
            if [ -z "$cur" ] || [ ${cur:0:1} = "-" ]; then 
                completions=$unused
            else
                completions=$(_sge_get_all_jobs $cur)
            fi 
	    ;;
    esac
    COMPREPLY=( $(compgen -W "$completions" -- $cur) )
}
complete -o default -F _sge_qalter qalter

_sge_qconf()
{
    local cur prev unused
    _sge_get_info cur prev unused
    case "$prev" in
        -acal|-dcal|-mcal|-scal)					# calendar related options
	    completions=$(qconf -scall 2>/dev/null)
    	    ;;	
	-ackpt|-dckpt|-mckpt|-sckpt)					# ckpt related options
	    completions=$(qconf -sckptl 2>/dev/null)
 	    ;;
        -aconf|-dconf|-de|-dh|-ds)					# host related options
            completions=$(_sge_get_hosts $cur)
	    ;;
        -ahgrp|-dhgrp|-whgrp|-shgrp|-shgrp_tree|-shgrp_resolved)	# group related options
	    completions=$(qconf -shgrpl 2>/dev/null)
	    ;;
	-ajc|-djc|-mjc|-sjc)						# class related options
	    completions=$(qconf -sjcl 2>/dev/null)
	    ;;
	-am|-ao|-au|-dm|-do|-du|-duser|-suser)				# user related options
            completions=$(_sge_get_users $cur)
	    ;;
	-ap|-dp|-mp|-sp)						# parallel environment related options
	    completions=$(_sge_get_parallel $cur)
	    ;;
	-aprj|-mprj|-sprj)						# project related options	
	    completions=$(_sge_get_projects $cur)
	    ;;
        -mconf|-sconf)							# host related options including global 
	    completions=$(_sge_get_hosts $cur) global
	    ;;
	-me|-se)							# server related options
	    completions=$(qconf -sel 2>/dev/null)
	    ;;
        *)
            completions=$unused
	    ;;
    esac
    COMPREPLY=( $(compgen -W "$completions" -- $cur) )
}
complete -o default -F _sge_qconf qconf

_sge_qdel()
{
    local cur prev unused
    _sge_get_info cur prev unused
    case "$prev" in
	-u)
            completions=$(_sge_get_users $cur)
	    ;;
        *)
            if [ -z "$cur" ] || [ ${cur:0:1} = "-" ]; then 
                completions=$unused
            else
                completions=$(_sge_get_my_jobs_multiple $cur)
            fi 
	    ;;
    esac
    COMPREPLY=( $(compgen -W "$completions" -- $cur) )
}
complete -o default -F _sge_qdel qdel

_sge_qhold()
{
    local cur prev unused
    _sge_get_info cur prev unused
    case "$prev" in
	-h)
	    completion="u s o"
	    ;;
	-u)
            completions=$(_sge_get_users $cur)
	    ;;
        *)
            if [ -z "$cur" ] || [ ${cur:0:1} = "-" ]; then 
                completions=$unused
            else
                completions=$(_sge_get_all_jobs $cur)
            fi 
	    ;;
    esac
    COMPREPLY=( $(compgen -W "$completions" -- $cur) )
}
complete -o default -F _sge_qhold qhold

_sge_qhost()
{
    local cur prev unused
    _sge_get_info cur prev unused
    case "$prev" in
	-F)
	    completions=$(_sge_get_resource_names_multiple "$cur" "$prev")
	    ;;
	-h)
	    completions=$(_sge_get_host $cur)
	    ;;
	-l)	    
	    _sge_get_resource_values_multiple "$cur" "$prev"
	    return
	    ;;
	-u)
            completions=$(_sge_get_users $cur)
	    ;;
        *)
            completions=$unused
	    ;;
    esac
    COMPREPLY=($(compgen -W "$completions" -- $cur) )
}
complete -o default -F _sge_qhost qhost

_sge_qlogin()
{
    local cur prev unused
    _sge_get_info cur prev unused
    case "$prev" in
	-l)
            _sge_get_resource_values_multiple "$cur" "$prev"
	    return
	    ;;
	-now|-pty|-R)
	    completions=$(_sge_yes_no)
	    ;;
	-P)
	    completions=$(_sge_get_projects)
	    ;;
	-w)
            completions="e w n v p"
	    ;;
        *)
            completions=$unused
	    ;;
    esac
    COMPREPLY=( $(compgen -W "$completions" -- $cur) )
}
complete -o default -F _sge_qlogin qlogin

_sge_qstat()
{
    local cur prev unused
    _sge_get_info cur prev unused
    case "$prev" in
        -explain)
            completions="a A c E"
	    ;;
	-F)
	    completions=$(_sge_get_resource_names_multiple "$cur" "$prev")
	    ;;
	-g)
	    completions="c d t"
	    ;; 
        -j) 
            completions=$(_sge_get_all_jobs $cur)
	    ;;
	-l)
	    _sge_get_resource_values_multiple "$cur" "$prev"
	    return
	    ;;
	-q)
	    completions=$(_sge_get_queues $cur)
            ;;
	-qs)
	    completions="a c d o s u A C D E S"
	    ;;
	-u|-U)
            completions=$(_sge_get_users $cur)
	    ;;
        *)
            completions=$unused
	    ;;
    esac
    COMPREPLY=( $(compgen -W "$completions" -- $cur) )
}
complete -o default -F _sge_qstat qstat
 
_sge_qmod()
{
    local cur prev unused
    _sge_get_info cur prev unused
    case "$prev" in
	-log)
	    completions=$(_sge_get_queues $cur)
            ;;
        *)
            completions=$unused
	    ;;
    esac
    COMPREPLY=( $(compgen -W "$completions" -- $cur) )
}
complete -o default -F _sge_qmod qmod

_sge_qmsg()
{
    local cur
    _get_cword cur  
    completions=$(_sge_get_hosts & _sge_get_all_job_ids)
    COMPREPLY=( $(compgen -W "$completions" -- $cur) )
}
complete -o default -F _sge_qmsg qmsg

_sge_qping()
{
    local cur prev unused
    _sge_get_info cur prev unused
    case "$prev" in
        *)
            completions=$unused
	    ;;
    esac
    COMPREPLY=( $(compgen -W "$completions" -- $cur) )
}
complete -o default -F _sge_qping qping

_sge_qquota()
{
    local cur prev unused
    _sge_get_info cur prev unused
    case "$prev" in
	-h)
	    completions=$(_sge_get_hosts $cur)
	    ;;
	-jc)
	    completions=$(qconf -sjcl 2>/dev/null)
	    ;;
	-l)
	    _sge_get_resource_values_multiple "$cur" "$prev"
	    return
	    ;;
	-u)
	    completions=$(_sge_get_users $cur)
	    ;;
	-pe)
	    completions=$(_sge_get_parallel $cur)
	    ;;
	-P)
	    completions=$(_sge_get_projects $cur)
	    ;;
	-q)
	    completions=$(_sge_get_queues $cur)
	    ;;
        *)
            completions=$unused
	    ;;
    esac
    COMPREPLY=( $(compgen -W "$completions" -- $cur) )
}
complete -o default -F _sge_qquota qquota

_sge_qrelease()
{
    local cur prev unused
    _sge_get_info cur prev unused
    case "$prev" in
	-h)
	    completions=$(_sge_get_hosts $cur)
	    ;;
        *)
            completions=$unused
	    ;;
    esac
    COMPREPLY=( $(compgen -W "$completions" -- $cur) )
}
complete -o default -F _sge_qrelease qrelease

_sge_qreserve()
{
    local cur prev unused
    _sge_get_info cur prev unused
    case "$prev" in
	-h)
	    completions=$(_sge_get_hosts $cur)
	    ;;
	-u)
	    completions=$(_sge_get_users $cur)
	    ;;
	-ul)
	    completions=$(_sge_get_user_lists $cur)
	    ;;
        *)
            completions=$unused
	    ;;
    esac
    COMPREPLY=( $(compgen -W "$completions" -- $cur) )
}
complete -o default -F _sge_qreserve qreserve

_sge_qresub()
{
    local cur prev unused
    _sge_get_info cur prev unused
    case "$prev" in
	-h)
	    completions="n u s o U S O"
	    ;;
        *)
            if [ -z "$cur" ] || [ ${cur:0:1} = "-" ]; then 
                completions=$unused
            else
                completions=$(_sge_get_all_jobs $cur)
            fi 
	    ;;
    esac
    COMPREPLY=( $(compgen -W "$completions" -- $cur) )
}
complete -o default -F _sge_qresub qresub

_sge_qrls()
{
    local cur prev unused
    _sge_get_info cur prev unused
    case "$prev" in
	-h)
	    completions="u s o"
	    ;;
        *)
            if [ -z "$cur" ] || [ ${cur:0:1} = "-" ]; then 
                completions=$unused
            else
                completions=$(_sge_get_all_jobs $cur)
            fi 
	    ;;
    esac
    COMPREPLY=( $(compgen -W "$completions" -- $cur) )
}
complete -o default -F _sge_qrls qrls
   
_sge_qsubmit()
{
    local cur prev
    _get_words cur prev   
    local bin=$(_get_cmd)
    local hbin=$bin
    if [ "$bin" = "qtcsh" ]; then
        hbin=qsh
    fi
    local options=$(_sge_ops $hbin)
    if [ "$bin" = "qtcsh" ]; then
        options="$options -A -B -L -R"
    fi
    unused=$(_get_unused "$options")
    completions=''

    case "$prev" in
	-b|-j|-now|-pty|-R|-r|-shell|-sync)
            completions=$(_sge_yes_no)
	    ;;
	-jc)
	    completions=$(qconf -sjcl 2>/dev/null)
	    ;;
	-l)
	    _sge_get_resource_values_multiple "$cur" "$prev"
	    return
	    ;;
	-P)
	    completions=$(_sge_get_projects)
	    ;;
	-q)
	    completions=$(_sge_get_queues $cur)
            ;;
	-v)
            completions=$(comm -3 <(declare | sort) <(declare -f | sort) | cut -f1 -d= | sort | uniq)
	    ;;
	-w)
            completions="e w n v p"
	    ;;
        *)
   	    if [ "$prev" = "qsamesub" ]; then
		completions=$(_sge_get_all_jobs)
            else
                completions=$unused
	    fi
	    ;;
    esac
    COMPREPLY=( $(compgen -W "$completions" -- $cur) )
}
complete -o default -F _sge_qsubmit qlogin
complete -o default -F _sge_qsubmit qsub
complete -o default -F _sge_qsubmit qsh
complete -o default -F _sge_qsubmit qtcsh
complete -o default -F _sge_qsubmit qrsh
complete -o default -F _sge_qsubmit qsamesub

_sge_quser()
{
    local cur prev unused
    _sge_get_info cur prev unused
    case "$prev" in
	-l)
	    _sge_get_resource_values_multiple "$cur" "$prev"
	    return
	    ;;
	-u)
	    completions=$(_sge_get_users $cur)
            ;;
        *)
            completions=$unused
	    ;;
    esac
    COMPREPLY=( $(compgen -W "$completions" -- $cur) )
}
complete -o default -F _sge_quser quser

_sge_qselect()
{
    local cur prev unused
    _sge_get_info cur prev unused
    case "$prev" in
	-l)
	    _sge_get_resource_values_multiple "$cur" "$prev"
	    return
	    ;;
	-U)
	    completions=$(_sge_get_users $cur)
            ;;
	-pe)
	    completions=$(_sge_get_parallel $cur)
            ;;
	-q)
	    completions=$(_sge_get_queues $cur)
            ;;
	-qs)
	    completions="a c d o s u A C D E S"
	    ;;
        *)
            completions=$unused
	    ;;
    esac
    COMPREPLY=( $(compgen -W "$completions" -- $cur) )
}
complete -o default -F _sge_qselect qselect

# --------------------------------------------------
# Advanced Reservation(s)
#
_sge_qrdel()
{
    local cur prev unused
    _sge_get_info cur prev unused    
    case "$prev" in
	-u)
	    completions=$(_sge_get_users $cur)
	    ;;
        *)
            completions=$unused
	    ;;
    esac
    COMPREPLY=( $(compgen -W "$completions" -- $cur) )
}
complete -o default -F _sge_qrdel qrdel

_sge_qrsub()
{
    local cur prev unused
    _sge_get_info cur prev unused
    case "$prev" in
	-he|-now)
	    completions=$(_sge_yes_no $cur)
	    ;;
	-l)
	    _sge_get_resource_values_multiple "$cur" "$prev"
	    return
	    ;;
	-q)
	    completions=$(_sge_get_queues $cur)
            ;;
	-u)
	    completions=$(_sge_get_users $cur)
	    ;;
	-w)
            completions="e v"
	    ;;
        *)
            completions=$unused
	    ;;
    esac
    COMPREPLY=( $(compgen -W "$completions" -- $cur) )
}
complete -o default -F _sge_qrsub qrsub

_sge_qrstat()
{
    local cur prev unused
    _sge_get_info cur prev unused
    case "$prev" in
	-u)
	    completions=$(_sge_get_users $cur)
	    ;;
        *)
            completions=$unused
	    ;;
    esac
    COMPREPLY=( $(compgen -W "$completions" -- $cur) )
}
complete -o default -F _sge_qrstat qrstat
