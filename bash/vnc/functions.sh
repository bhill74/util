. ${HOME}/util/process/process.sh

function vncrecord {
   process $@
   NAME=$1
   vnc2swf ${NAME}.swf ${VNCDEMO} -depth 8 > ${NAME}.html
   pend
}
