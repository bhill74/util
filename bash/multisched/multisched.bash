base=$(cd $(dirname $BASH_SOURCE) && pwd)
#util_path=$(cd ${base}/../utils && pwd)
#PATH=$util_path:$PATH


SERVER_PID=-1

function _sched_shutdown() {
    if [[ $SERVER_PID -eq 0 ]]
    then
        return
    fi

    sched_shutdown
    wait $SERVER_PID
    SERVER_PID=0
}

function sched_startup() {
    export MULTISCHED_PORT=$(sched_port)
    sched_serve &
    SERVER_PID=$!
    sleep 1
    trap _sched_shutdown EXIT;
}

sched_startup
