base=$(cd $(dirname $BASH_SOURCE) && pwd)


function _check_regs() {
    local cur=${COMP_WORDS[COMP_CWORD]}
    COMPREPLY=( $(compgen -W "$(${base}/branch_regs)" -- $cur))
}
complete -F _check_regs check_regs
