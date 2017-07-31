. ${HOME}/util/process/process.sh

function preserveEnv () {   
   process $@
   ENVFILE=/tmp/bhill.env
   HOST=`${CELLGEN}/bin/remoteHost`
   if [ ! -z "$HOST" ]; then
      RES=`${CELLGEN}/bin/getEnv ${HOST} 1 $ENVFILE export`
      if [ -e "$ENVFILE" ]; then
	 if [ "$1" == "-v" ]; then
	    echo "ENV from $HOST"
            more $ENVFILE
         fi        
         source $ENVFILE
      fi 
   fi
   pend
}
