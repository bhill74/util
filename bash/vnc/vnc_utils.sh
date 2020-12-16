#!/bin/bash

function vnc_get_port() {
	local pattern="rfbport ([[:digit:]]+)"
	if [[ $1 =~ $pattern ]]; then
		echo ${BASH_REMATCH[1]}
	fi
}

function vnc_get_disp() {
	local pattern=" :([[:digit:]]+) "
	if [[ $1 =~ $pattern ]]; then
		echo ${BASH_REMATCH[1]}
	fi
}
