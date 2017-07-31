. ${HOME}/util/util/upvar.sh
. ${HOME}/util/sge/env.sh
. ${HOME}/util/sge/completions.sh

function _qinit() {
   # Derive the JOB id.
   local id=`echo $1 | cut -f1 -d'@'`
   if [ -z "$id" ] || [ "$id" = "SAME" ]; then
       id=$JOB_ID
   fi
   local _jid=`echo $id | cut -f1 -d/`  
   if local "$2"; then
       upvar $2 $_jid
   fi
   # Derive the appropriate SGE cell.
   local cell=`echo "$id/" | cut -f2 -d/`
   qenv "$cell"
   # Derive the appropriate host
   local _rhost=`echo $1@ | cut -f2 -d'@'` 
   local host=`/bin/hostname`
   if [ -z "$_rhost" ]; then
       _rhost=`_sge_get_hosts 2>/dev/null | grep $host`
   fi
   if [ -z "$_rhost" ]; then
       _rhost=`_sge_get_hosts 2>/dev/null | head -1`
   else 
       if [ "$_rhost" = "$host" ]; then
	   _rhost=''
       fi
   fi
   if [ ! -z "$3" ] && local "$3"; then
      upvar $3 $_rhost
   fi
}
