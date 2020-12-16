#!/bin/sh

function color_esc() {
    printf '\033'
}

function color_replace() {
   esc=$(color_esc)
   pattern=$1
   code=$2
   cmd="s,\\(${pattern}\\),${esc}[${code}m\\1${esc}[m,"
   sed $cmd
}

function color_wrap() {
   esc=$(color_esc)
   text=$1
   code=$2
   echo "${esc}[${code}m${text}${esc}[m"
}
