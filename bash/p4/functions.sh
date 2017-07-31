. ${HOME}/util/process/process.sh

set -a
P4CODEBASE=//cosmos/cadabra

#**************************************************
#%FUNCTION: p4branch
#%DESCRIPTION: Determines which branch of the code
# base is currently being used.
#%ARGUMENTS:
# [h/help] To display the usage information.
#%RETURNS:
# The current branch.
#**************************************************
function p4branch {
    process $@
    if [ "$1" == "-h" ] || [ "$1" == "-help" ]; then
       echo "Determines which branch of the code base is currently being used"
       echo "  -h/help -- Display this information"
       echo "usage: p4branch"
       pend
       return
    fi  

    P4PWD=`p4pwd`
    BRANCH=`echo $P4PWD | perl -p -e "s|.*/(.*?)/src.*|\\$1|g;"`
    BRANCH=`echo $BRANCH | perl -p -e "s|.*/cae/(.*?)/.*|\\$1|g;"`
    echo $BRANCH
    pend
}

#**************************************************
#%FUNCTION: p4branches
#%DESCRIPTION: Determines which branches currently 
# exist in perforce.
#%ARGUMENTS:
# [h/help] To display the usage information.
# [s] -- Subdirectory to add to the base path when examining.
# [o] -- To display only the 'other' branches.
#%RETURNS:
# The existing branches.
#**************************************************
function p4branches {
    process $@
    if [ "$1" == "-h" ] || [ "$1" == "-help" ]; then
       echo "Determines the set of branches of the code base"
       echo "  -h/help -- Display this information"
       echo "  -s -- Subdirectory to examine from the base"
       echo "  -o -- Remove the current branch being used"
       echo "usage: p4branches"
       pend
       return
    fi 

    SUB=""
    OTHER=0
    OPTIND=1
    while getopts "s:o" opt; do     
      case $opt in
	 s) SUB="$OPTARG/";;
         o) OTHER=1;;         
      esac
    done

    if [ $OTHER -gt 0 ]; then
       branch=`p4branch`	
       BRANCHES=`p4 dirs $P4CODEBASE/${SUB}* | grep -v -- "$branch" | grep -- '-branch' | sort`;
    else 
       BRANCHES=`p4 dirs $P4CODEBASE/${SUB}* | grep -- '-branch' | sort`;	
    fi   
    BRANCHES=`echo $BRANCHES | perl -pe "s|$P4CODEBASE/${SUB}||g;"`

    echo $BRANCHES
    pend
}

#**************************************************
#%FUNCTION: p4toMAIN
#%DESCRIPTION: Used to integrate a change from another
# branch to the MAIN branch.
#! Assuming you are in a client that has access to main.
#%ARGUMENTS:
# id -- The perforce changelist number.
# [h/help] To display the usage information.
#%RETURNS:
# Nothing.
#**************************************************
function p4toMAIN {
    process $@
    if [ "$1" == "-h" ] || [ "$1" == "-help" ]; then
       echo "Integrates a change from another chosen branch to the MAIN branch currently being used"      
       echo "  id -- The perforce changelist number"
       echo "  -h/help -- Display this information"
       echo "usage: p4toMAIN <id>"
       pend
       return
    fi 

    if [ -z "$1" ]; then
       echo "A perforce changelist number must be provided"
       pend
       return
    fi

    select BRANCH in `p4branches`; do
       echo $BRANCH	
       p4 integrate -b $BRANCH -s $P4CODEBASE/$BRANCH/...@$1,$1 $P4CODEBASE/main/src/...
       break
    done
    pend
}

#**************************************************
#%FUNCTION: p4fromBranch
#%DESCRIPTION: Used to integrate a change from another
# branch to the current branch.
#%ARGUMENTS:
# id -- The perforce changelist number.
# [h/help] To display the usage information.
#%RETURNS:
# Nothing.
#**************************************************
function p4fromBranch {
    process $@
    if [ "$1" == "-h" ] || [ "$1" == "-help" ]; then
       echo "Integrates a change from another chosen branch to the branch currently being used"      
       echo "  id -- The perforce changelist number"
       echo "  -h/help -- Display this information"
       echo "usage: p4fromBranch <id>"
       pend
       return
    fi 

    if [ -z "$1" ]; then
       echo "A perforce changelist number must be provided"
       pend
       return
    fi

    branch=`p4branch`
    select BRANCH in `p4branches -o`; do
       echo $BRANCH	
       p4 integrate -b $BRANCH -s $P4CODEBASE/$BRANCH/...@$1,$1 $P4CODEBASE/$branch/src/...
       break
    done
    pend
}

#**************************************************
#%FUNCTION: p4fromRSKBranch
#%DESCRIPTION: Used to integrate a change from another
# branch to the current branch within the RSK structure
#%ARGUMENTS:
# id -- The perforce changelist number.
# [h/help] To display the usage information.
#%RETURNS:
# Nothing.
#**************************************************
function p4fromRSKBranch {
    process $@
    if [ "$1" == "-h" ] || [ "$1" == "-help" ]; then
       echo "Integrates a change from another chosen branch to the branch currently being used"      
       echo "  id -- The perforce changelist number"
       echo "  -h/help -- Display this information"
       echo "usage: p4fromRSKBranch <id>"
       return
    fi 

    if [ -z "$1" ]; then
       echo "A perforce changelist number must be provided"
       pend
       return
    fi

    branch=`p4branch`
    select BRANCH in `p4branches -o`; do
       echo $BRANCH	
       p4 integrate $P4CODEBASE/cae/$BRANCH/...@$1,$1 $P4CODEBASE/cae/$branch/...
       break
    done
    pend
}

#**************************************************
#%FUNCTION: p4fromMAIN
#%DESCRIPTION: Used to integrate a change from MAIN to
# the branch of the client you are using.
#%ARGUMENTS:
# id -- The perforce changelist number.
# [h/help] To display the usage information.
#%RETURNS:
# Nothing.
#**************************************************
function p4fromMAIN {
    process $@
    if [ "$1" == "-h" ] || [ "$1" == "-help" ]; then
       echo "Integrates a change from the MAIN branch to the other branch currently being used"
       echo "  id -- The perforce changelist number"
       echo "  -h/help -- Display this information"
       echo "usage: p4fromMAIN <id>"
       return
    fi

    if [ -z "$1" ]; then
       echo "A perforce changelist number must be provided"
       pend
       return
    fi

    BRANCH=`p4branch`	
    p4 integrate -f $P4CODEBASE/main/src/...@$1,$1 $P4CODEBASE/$BRANCH/src/...
    pend
}
