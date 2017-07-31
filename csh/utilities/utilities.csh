#**************************************************
#%FUNCTION: sourcedir
#%DESCRIPTION: Sources an entire directory of files
#%ARGUMENTS:
# [h/help] To display the usage information.
# [v/verbose] To be verbose for every file name.
#%RETURNS:
# Nothing unless the verbose command is used and
# if sourcing any of the files results in output.
#**************************************************
alias sourceDir 'eval `sourceFiles_base \!*`'
