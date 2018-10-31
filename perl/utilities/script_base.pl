# Define some constants.

# Define some arguments.
push( @optionList, "csh!" );

# SITE -- Get the current network site code.
( $site ) = `/usr/local/bin/siteid` unless ( $opt_site );
chomp $site;

#**************************************************
#%FUNCTION: process_base_msg
#%DESCRIPTION: Used to convert a string to a series
# of echo statements to be used in a 'base' script.
#%ARGUMENTS:
# text -- The text string to convert.
#%RETURNS:
# The adjusted string as a series of echo commands.
#**************************************************
sub process_base_msg {
  my( $text ) = shift;
  $text =~ s/\n/\";echo \"/g;
  return "echo \"${text}\"";
}

1;
