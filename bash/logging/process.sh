
#**************************************************
#FUNCTION: process
# Used to process the parent command (calling)
#%ARGUMENTS
# None
#%RETURNS
# Nothing, but the environment will be changed.
#**************************************************
function process {
   # No process has been logged and this is a 2nd level function.   
   if [ -z "$_process" ] && [ ${#FUNCNAME[@]} -eq 2 ]; then      
      args=$@
      ${HOME}/util/process/process_cmd -P $$ -c ${FUNCNAME[1]} -a ${BASH_SOURCE[1]} -p "<function>" -a "$args" 2>/dev/null
      export _process=done
      return
   fi
   # No process has ben logged and this is a top-level function.
   if [ -z "$_process_" ] && [ ${#FUNCNAME[@]} -eq 1 ] ; then      
      ${HOME}/util/process/process_cmd -P $$ 2>/dev/null
      export _process=done
      return
   fi
}

#**************************************************
#FUNCTION: pend
# Used to signify the end of a function.
#%ARGUMENTS
# None
#%RETURNS
# Nothing, but the environment will be changed.
#**************************************************
function pend {
    unset _process
}
