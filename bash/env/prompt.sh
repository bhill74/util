. ${PWD}/prompt_util.sh

PS1="$(addTitle \$\(qsc\)/\$\(siteid\):\\H-\\W\$TINFO)\
$(addColor '0;32' \$DEV_MODE)\
/$(addColor '0;35' \$\(~/util/util/devModeInfo\))\
 [\h] \W \! \$ "
