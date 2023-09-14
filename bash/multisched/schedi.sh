base=$(cd $(dirname $BASH_SOURCE) && pwd)
util_path=$(cd ${base}/../utils && pwd)
PATH=$util_path:$PATH

function sched_startup() {
    export SCHED_PORT=$(sched_port)
    sched_serve &
    sleep 1
}

sched_startup
