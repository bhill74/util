# Auto Completion

_gfiledir () {
    local IFS=$'\n'
    local args=(-L)
    if [ ! -z "$cur" ]
    then
        args+=(-l "$cur")
    fi

    local -a toks
    toks=($(fromdrive "${args[@]}"))
    if [[ ${#toks[@]} -ne 0 ]]; then
        compopt -o nospace -o filenames 2>/dev/null
        COMPREPLY+=("${toks[@]}")
    fi
}

function _gdrive_from() {
    local cur prev
    cur=${COMP_WORDS[COMP_CWORD]}
    prev=${COMP_WORDS[COMP_CWORD-1]}
    case "$prev" in
        -l) 
           _gfiledir
            ;;
    esac 
}

function _gdrive_to() {
    local cur prev
    cur=${COMP_WORDS[COMP_CWORD]}
    prev=${COMP_WORDS[COMP_CWORD-1]}
    case "$prev" in
        -l) 
           _gfiledir
            ;;
    esac 
}

complete -F _gdrive_from fromdrive
complete -F _gdrive_to todrive
