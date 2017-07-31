# FILE       : sctrace.sh
# LICENSE    : GPL v2.0 (only)
# PURPOSE    : print the recursive callers' list for a script
#              (sort of a process backtrace)
# USAGE      : [in a script] source sctrace.sh
#
# TESTED ON  :
# - Linux, x86 32-bit, Bash 3.2.39(1)-release

# REFERENCES:
# [1]: http://tldp.org/LDP/abs/html/internalvariables.html#PROCCID
# [2]: http://linux.die.net/man/5/proc
# [3]: http://linux.about.com/library/cmd/blcmdl1_tac.htm

#! /bin/bash

TRACE=""
CP=$$ # PID of the script itself [1]

while true # safe because "all starts with init..."
do
        CMDLINE=$(cat /proc/$CP/cmdline)
        PP=$(grep PPid /proc/$CP/status | awk '{ print $2; }') # [2]
        TRACE="$TRACE [$CP]:$CMDLINE\n"
        if [ "$CP" == "1" ]; then # we reach 'init' [PID 1] => backtrace end
                break
        fi
        CP=$PP
done
echo "Backtrace of '$0'"
echo -en "$TRACE" | tac | grep -n ":" # using tac to "print in reverse" [3]
