# Remote machines
. ${HOME}/util/process/process.sh

# Perform a remote shell but keep the DISPLAY
# environment setting.
function rsh_d {   
   process $@
   DISPLAY=`display`
   ${CELLGEN}/bin/setEnv DISPLAY
   rsh $*
   pend
}

alias jp01host="${CELLGEN}/bin/machine -s jp01 -1 -c all"
alias am04host="${CELLGEN}/bin/machine -s am04 -1 -c all"
alias cn42host="${CELLGEN}/bin/machine -s cn42 -1 -c all"
alias us01host="${CELLGEN}/bin/machine -s us01 -1 -c all"
alias ca09host="${CELLGEN}/bin/machine -s ca09 -1 -c all"
alias in01host="${CELLGEN}/bin/machine -s in01 -1 -c all"

alias rsh_jp01="rsh_d `${CELLGEN}/bin/machine -s jp01 -1 -c all`"
alias rsh_am04="rsh_d `${CELLGEN}/bin/machine -s am04 -1 -c all`"
alias rsh_cn42="rsh_d `${CELLGEN}/bin/machine -s cn42 -1 -c all`"
alias rsh_us01='rsh_d `${CELLGEN}/bin/machine -s us01 -1 -c all`'
alias rsh_ca09='rsh_d `${CELLGEN}/bin/machine -s ca09 -1 -c all`'
alias rsh_in01='rsh_d `${CELLGEN}/bin/machine -s in01 -1 -c all`'
function rsh_s {
   process $@
   m="${CELLGEN}/bin/machine -s $1 -1 -c all"
   rsh_d `$m`
   pend
}
