. ${HOME}/util/process/process.sh

#**************************************************
#%FUNCTION: sourcedir
#%DESCRIPTION: Sources an entire directory of files
#%ARGUMENTS:
# [h/help] To display the usage information.
#%RETURNS:
# Nothing unless the verbose command is used and
# if sourcing any of the files results in output.
#**************************************************
function sourceDir {
   process $@
   eval `${PWD}/sourceFiles_base $@`
   pend
}

# Map aliases
alias ottawaMap='map -country CA -province ON -city Ottawa -big -zoom 7'
alias torontoMap='map -country CA -province ON -city Toronto -big -zoom 7'

# History shortcut
alias h='history 25'

# LS shortcuts
alias ll='ls -l \!* | more'
alias la='ls -la  \!*| more'
alias lt='ls -lt  \!*| more'
