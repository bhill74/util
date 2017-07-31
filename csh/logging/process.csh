
#**************************************************
#%ALIAS: process
# Used to process the parent command (calling)
#%ARGUMENTS
# None
#%RETURNS
# Nothing, but the environment will be changed.
#**************************************************
alias process 'set ARGS="\!*" \
   if ( $?_process_ == 0 ) then \
      ${HOME}/util/process/process_cmd -P $$ >& /dev/null \
      setenv _process_ done \
   endif \
'
