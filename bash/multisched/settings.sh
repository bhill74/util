export PATH=${HOME}/util/multisched:$PATH
export PYTHONPATH=${HOME}/lib/multisched:$PYTHONPATH
export PERL5LIB=${HOME}/lib/multisched:$PERL5LIB
export MULTISCHEDHOME=${HOME}/lib/multisched

function sched_set_param() {
    export MULTISCHEDCONFIG=$(sched_set_param $1 $2)
}

function sched_remove_param() {
    export MULTISCHEDCONFIG=$(sched_remove_param $1 $2)
}

