. ${HOME}/util/paths/settings.sh

homedir=/home2/bhill
path_append ${homedir}/.gem/ruby/2.3.0/bin

eval `${HOME}/util/paths/path_modify_base -mode append -name GEM_PATH ${homedir}/.gem/ruby/2.3.0`
