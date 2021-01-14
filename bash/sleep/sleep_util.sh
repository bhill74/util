function remain() {
    local v=$1
    local d=$(($v/(3600*24)))
    local r=$(($v-$d*3600*24))
    local h=$(($r/3600))
    r=$(($r-$h*3600))
    local m=$(($r/60))
    r=$(($r-$m*60))
    local s=$r
   
    if [[ $d -gt 1 ]]; then
        printf -- "%i Days %02i:%02i:%02i        \r" $d $h $m $s 
    elif [[ $d -gt 0 ]]; then
        printf -- "%i Day %02i:%02i:%02i         \r" $d $h $m $s 
    else
        printf -- "%02i:%02i:%02i                \r" $h $m $s 
    fi
}

function countdown() {
    local v=$1
    local d=${2:-1}

    while [[ $v -gt 0 ]]
    do
        remain $v
        v=$(($v-$d))
        sleep $d
    done
    remain 0
    echo
}
