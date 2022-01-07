. ${HOME}/util/paths/settings.sh

#**************************************************
#%FUNCTION: pythonpath_append
#%DESCRIPTION: A utility for appending sections
# to the main PYTHONPATH environment variable
#%ARGUMENTS
# The segments to append to the PYTHONPATH.
#%RETURNS
# Nothing, but the environment will be changed.
#**************************************************
function pythonpath_append {
    eval `${HOME}/util/paths/path_modify_base -mode append -name PYTHONPATH $* `
}

#**************************************************
#%FUNCTION: pythonpath_prepend
#%DESCRIPTION: A utility for prepending sections
# to the main PYTHONPATH environment variable
#%ARGUMENTS
# The segments to prepend to the PYTHONPATH.
#%RETURNS
# Nothing, but the environment will be changed.
#**************************************************
function pythonpath_prepend {
    eval `${HOME}/util/paths/path_modify_base -mode prepend -name PYTHONPATH $* `
}

#**************************************************
#%FUNCTION: pythonpath_insert
#%DESCRIPTION: A utility for inserting sections
# to the main PYTHONPATH environment variable
#%ARGUMENTS
# [before <segments>] -- The segments to insert before
# [after <segments>] -- The segments to insert after
# <segments> -- The segments to insert to the PYTHONPATH
#%RETURNS
# Nothing, but the environment will be changed.
#**************************************************
function pythonpath_insert {
    eval `${HOME}/util/paths/path_modify_base -mode insert -name PYTHONPATH $* `
}

#**************************************************
#%FUNCTION: pythonpath_dominant
#%DESCRIPTION: A utility for making sure the path to
# the file given will be the dominant one in the 
# PYTHONPATH environment variable.
#%ARGUMENTS
# The location of the file to be dominant.
#%RETURNS
# Nothing, but the environment will be changed.
#**************************************************
function pythonpath_dominant {
    eval `${HOME}/util/paths/path_modify_base -mode dominant -name PYTHONPATH $*`
}
