function addColor {
    echo "\e[${1}m${2}\e[m"
}

function addTitle {
    case $TERM in
	xterm*)
            echo "\[\033]0;${1}\007\]"
	    ;;
	*)
            ;;
   esac
}
