 function repeat() {
     printf -- "${1}%.0s" $(eval echo {1..$2})
 }
