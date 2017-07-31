#**************************************************
#%FUNCTION: path_append
#%DESCRIPTION: A utility for appending sections
# to the main PATH environment variable
#%ARGUMENTS
# The segments to append to the PATH.
#%RETURNS
# Nothing, but the environment will be changed.
#**************************************************
alias path_append 'eval `${HOME}/util/paths/path_modify_base -csh -mode append -name PATH \!* `'



#**************************************************
#%FUNCTION: path_prepend
#%DESCRIPTION: A utility for prepending sections
# to the main PATH environment variable
#%ARGUMENTS
# The segments to prepend to the PATH.
#%RETURNS
# Nothing, but the environment will be changed.
#**************************************************
alias path_prepend 'eval `${HOME}/util/paths/path_modify_base -csh -mode prepend -name PATH \!* `'



#**************************************************
#%FUNCTION: path_insert
#%DESCRIPTION: A utility for inserting sections
# to the main PATH environment variable
#%ARGUMENTS
# [before <segments>] -- The segments to insert before
# [after <segments>] -- The segments to insert after
# <segments> -- The segments to insert to the PATH
#%RETURNS
# Nothing, but the environment will be changed.
#**************************************************
alias path_insert 'eval `${HOME}/util/paths/path_modify_base -csh -mode insert -name PATH \!* `'



#**************************************************
#%FUNCTION: path_dominant
#%DESCRIPTION: A utility for making sure the path to
# the file given will be the dominant one in the 
# PATH environment variable.
#%ARGUMENTS
# The location of the file to be dominant.
#%RETURNS
# Nothing, but the environment will be changed.
#**************************************************
alias path_dominant 'eval `${HOME}/util/paths/path_modify_base -csh -mode dominant -name PATH \!* `'
