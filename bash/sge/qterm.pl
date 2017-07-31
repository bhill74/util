#!/bin/env perl

# ----------------------------------------
# ---- Session Settings
# Collect information about the current
# session and environment.
my( $site ) = `/usr/local/bin/siteid`;
chomp $site;

my( $display ) = `$ENV{HOME}/util/remote/display`;
chomp $display;

my( $host ) = ( `hostname` =~ /^(\w+)/ );

my @info = split( ':', `ypcat -k passwd | grep " $ENV{USER}:"` );
print "I " . join( "!", @info ) . "\n";
my( $shell ) = ( $ENV{SGE_DEFAULT_SHELL} ) ? $ENV{SGE_DEFAULT_SHELL} : $info[6];

# ----------------------------------------
# ---- Command Line Arguments
# Process the command line arguments

my( $project ) = ( $opt_P || 'ilight' );
my( $title )=( $opt_title || "Term window for $info[4] ($ENV{USER})" );
my( $rsite )=( $opt_rsite || $site );
$rsite =~ tr/A-Z/a-z/g;
my $sendenv = join( ',', grep( /\S/, split( ',', $ENV{SGE_TERM_SENDENV} . ',' . $opt_sendenv )));
my $verbose = $opt_verbose;

# ----------------------------------------
# ---- Remote Host
if ( $rsite ne $site ) {
  my( $dir ) = `rfs $rsite resolve ~`;
  my( $var ) = ${rsite}_SGE_HOST
  $var =~ tr/a-z/A-Z/g;
  my $host  = $ENV{$var};
  if ( ! $host ) {
    ( $host ) = `machineInfo -s | grep $rsite | head -1 | cut -f1 -d,`
  }

  if ( ! $host ) {
    die "No host is known for $rsite";
  }

  my $cmd = join( " ", "$dir/util/sge/qterm", @ARGS );
  rsh $host $cmd;
  exit
}

# ----------------------------------------
# ---- Utility Functions
# Useful utility functions for processing information

#%FUNCTION: tmpName
#%DESCRIPTION: Create the temporary file name.
function tmpName {
   echo /tmp/${1}.`date +%Y%m%d%H%M%S`.txt
}

# ----------------------------------------
# ---- SunGrid
# Access the appropriate SunGrid

# The AMSG grid farm is available in most sites
# but the desired grid should be specified
if [ ! -e "/remote/sge/${SGE_BASE}/common/settings.sh" ]; then
   if [ $VERBOSE == 1 ]; then
      echo "$SGE_BASE not found, using default"
   fi
   SGE_BASE=cells/snps
fi

source /remote/sge/${SGE_BASE}/common/settings.sh
if [ $VERBOSE == 1 ]; then
   echo "Using $SGE_CELL grid"
fi

# Define a function to determine the VALID hosts that are
# available on the FARM.
function valid {
   FILTER="cat"
   if [ "$1" == "1" ]; then
      FILTER="grep -v '(0)'"
   fi
   quser -u $USER ${OPTIONS} 2>&1 | grep ${PROJECT} | grep Y | ${FILTER} | cut -f1 -d' ' | cut -f2 -d@
}

# If this window is already taking up a slot in the queue then
# attempt to track down the appropriate machine for launching
# another window without taking up another slot. Determine
# the appropriate HOST and whether it is the SAME session.
XTERMHOST=""
SAME=0
if [ ! -z "$RELATED_JOB_ID" ]; then
   JOB_ID=$RELATED_JOB_ID
fi

if [ ! -z "$JOB_ID" ]; then
   if [ ! -z "$SGE_O_SHELL" ]; then
      SHELL=$SGE_O_SHELL
   fi

   # Determine which hosts are applicable for this
   # type of session.
   VALID_HOSTS=`tmpName hosts`
   valid > $VALID_HOSTS

   # Collect all the interactive JOB ids.
   ID_TMP=`tmpName ids`
   IDS=$JOB_ID
   qstat -u $USER 2>&1 | grep INTERACTIV | grep -v $JOB_ID | cut -f2 -d' ' > $ID_TMP
   while read ID; do
      IDS="$IDS $ID"
   done < $ID_TMP
   rm -rf $ID_TMP 2>/dev/null

   # Find the appropriate job ID, starting with the current one.
   for ID in $IDS; do
      JOB_PROJECT=`qstat -j $ID 2>&1 | grep 'project:' | cut -f2 -d: | sed "s/ //g"`
      if [ "$PROJECT" != "$JOB_PROJECT" ]; then
         continue
      fi

      if [ $JOB_ID = $ID ]; then
         SAME=1
         XTERMHOST=$HOST
      else
         XTERMHOST=`qstat -u $USER | grep $ID | awk '{print $8}' | cut -f2 -d@ | cut -f1 -d.`
      fi

      VALID_HOST=`grep $XTERMHOST $VALID_HOSTS`
      if [ -z "${VALID_HOST}" ]; then
         SAME=0
         XTERMHOST=''
         continue
      fi

      JOB_ID=$ID
      break
   done

   rm -rf $VALID_HOSTS 2>/dev/null
fi

# If there are NO available hosts on the FARM or if
# the preferred host is not part of the FARM then
# use an explicit xterm command.
AVAIL_HOSTS=`valid 1`
IS_PREFER_AVAIL=1
if [ ! -z "$SGETERM_PREFER" ]; then
   IS_PREFER_AVAIL=`qhost -h $SGETERM_PREFER | grep $SGETERM_PREFER | wc | awk '{print $1}'`
fi

if [ "$IS_PREFER_AVAIL" == "0" ]; then
   if [ $VERBOSE == 1 ]; then
      echo "Using desired non-SGE host $SGETERM_PREFER"
   fi
   XTERMHOST=$SGETERM_PREFER
   JOB_ID=UNDEFINED
else
   if [ "$AVAIL_HOSTS" == "" ]; then
      if [ $VERBOSE == 1 ]; then
         echo "No available SunGrid hosts"
      fi

      CMD="${CELLGEN}/bin/machine -1 "
      PATTERN='s/^.*qsc=(\w+).*$/$1/g;'
      QSC=`echo $OPTIONS | perl -p -e "${PATTERN}"`
      if [ ! -z "$QSC" ]; then
         if [ ${#QSC} -lt 2 ]; then
            CMD="${CMD} -q ${QSC}"
         fi
      fi
      PATTERN='s/^.*os_version=(\S+).*$/$1/g;'
      OS=`echo $OPTIONS | perl -p -e "${PATTERN}"`
      if [ ! -z "$OS" ]; then
         if [ ${#OS} -lt 6 ]; then
            CMD="${CMD} -S ${OS}"
         fi
      fi

      XTERMHOST=`${CMD}`
      if [ -z "$XTERMHOST" ]; then
         echo "No known host could be found"
         exit
      fi

      if [ $VERBOSE == 1 ]; then
         echo "Using first non-SGE host $XTERMHOST"
      fi
      JOB_ID=UNDEFINED
   fi
fi

# If we should be using the same SunGrid slot then
# simply open an Xterm window.
if [ ! -z "$XTERMHOST" ]; then
   if [ $SAME == 1 ]; then
      if [ $VERBOSE == 1 ]; then
         echo "Using same SGE slot ($XTERMHOST:$JOB_ID)"
      fi
      export RELATED_JOB_ID=$JOB_ID
      unset JOB_ID
      export SGE_BASE
      xterm -ls -display $R_DISPLAY -T "$TITLE [C]" -e $SHELL &
      exit
   fi

   if [ $VERBOSE == 1 ]; then
      if [ "$JOB_ID" == "UNDEFINED" ]; then
	 if [ "$XTERMHOST" == "$HOSTNAME" ]; then
            echo "Using local machine ($XTERMHOST)"
         else
            echo "Using machine ($XTERMHOST)"
         fi
      else
         echo "Using existing SGE slot ($XTERMHOST:$JOB_ID)"
      fi
   fi

   VARS=`echo $SENDENV | sed "s/,/ /g"`

   COMMAND=$SHELL
   if [ "$SHELL" == "/bin/bash" ] || [ "$SHELL" == "/bin/sh" ]; then
      COMMAND="$COMMAND;export RELATED_JOB_ID=$JOB_ID"
      for NAME in $VARS; do
         if [ -z "$NAME" ]; then
            next
         fi
         COMMAND="$COMMAND;export $NAME='${!NAME}'"
      done
   fi

   if [ "$SHELL" == "/bin/csh" ] || [ "$SHELL" == "/bin/tcsh" ]; then
      COMMAND="$COMMAND;setenv RELATED_JOB_ID $JOB_ID"
      for NAME in $VARS; do
         if [ -z "$NAME" ]; then
            next
         fi
         COMMAND="$COMMAND;setenv $NAME '${!NAME}'"
      done
   fi

   echo $COMMAND

   rsh $XTERMHOST "$COMMAND;xterm -ls -display $R_DISPLAY -title '$TITLE [C]' -e '$SHELL'" 2> /dev/null &
   exit
fi

# Set up the SunGrid command.

if [ ! -z "$SGETERM_PREFER" ]; then
   PREFER=`echo $SGETERM_PREFER | sed "s/,/|/g"`
   PREFER="-l 'hostname=(${PREFER})'"
fi

if [ ! -z "$SGETERM_AVOID" ]; then
   AVOID=`echo $SGETERM_AVOID | sed "s/,/|/"`
   AVOID="-l 'hostname=!(${AVOID})'"
fi
OPTIONS="${OPTIONS} -soft ${PREFER} ${AVOID} ${SOFT_OPTIONS}"
OPTIONS=`echo $OPTIONS | sed "s|\([_a-z]*=[^ ]*\)|'\\1'|g"`

if [ ! -z "$SENDENV" ]; then
   VARS=`echo $SENDENV | sed "s/,/ -v /g"`
   VARS="-v $VARS"
fi
QSH="qsh -S $SHELL $VARS -display $R_DISPLAY -P $PROJECT $OPTIONS -- -T \"$TITLE [M]\" -bd red -ms blue"

if [ $VERBOSE == 1 ]; then
   echo $QSH
fi

eval $QSH
