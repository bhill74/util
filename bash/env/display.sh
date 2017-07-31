rshdisplay() {
   local MYPTS=`ps | grep pts | awk '{print $2}' | sort | uniq`
   local MYMACHINE=`who | awk "{if(\\$2==\\"$MYPTS\\") print}" | /bin/sed -e "s/^.*(\(.*\)).*/\1/"`
   echo "${MYMACHINE}:0.0"
}
