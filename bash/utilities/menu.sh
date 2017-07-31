function acontains () {
  local e
  for e in "${@:2}"; do 
      if [[ "$e" == "$1" ]]; then 
	  echo TRUE; return
      fi
  done
  echo FALSE
}

function aindex() {
  local e
  local n=0
  for e in "${@:2}"; do 
      if [[ "$e" == "$1" ]]; then 
	  return $n
      fi
      let n=n+1
  done
  return -1
}


function menu() {    
    local cmd
    cmd=("${cmd[@]}" /usr/bin/zenity --list);
    local def
    local OPTIND
    while getopts "smc:t:w:d:D:" opt
    do
       case $opt in
          s) echo S;cmd=("${cmd[@]}" --radiolist --column Selected --column Item);;
          m) echo M;cmd=("${cmd[@]}" --checklist --column Chosen --column Item);;
	  D) echo D;while IFS=',' read -ra ops; do
	          def=("${def[@]}" "${ops[@]}")
	     done <<< "$OPTARG";;
          c) while IFS=',' read -ra ops; do
		  for op in "${ops[@]}"; do		     
		      cmd=("${cmd[@]}" $(acontains "$op" "${def[@]}") "$op")
		  done
	     done <<< "$OPTARG";;
          t) cmd=("${cmd[@]}" --title "$OPTARG");;
          w) cmd=("${cmd[@]}" --text "$OPTARG");;
	  d) cmd=("${cmd[@]}" --separator "$OPTARG");;
        esac
    done  
    echo "${cmd[@]}"
"${cmd[@]}"
}
