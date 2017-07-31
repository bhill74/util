alias p4pwd="p4 where | awk '{print \$1}'"
alias p4new="find . -name '*.lib.cells' -prune -o -name '*.[ao]' -prune -o -type f -exec p4 fstat {} \; 2>&1 | grep 'no such file' | awk '{print \$1}'"
