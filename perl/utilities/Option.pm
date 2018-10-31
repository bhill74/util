
package Option;

use Getopt::Long;

our @options;
our %description;
our %default;
our %alternatives;

our $programName;
our $description;

#**************************************************
#%FUNCTION: getName
#%DESCRIPTION: Used to extract the argument name
# from the name-syntax string.
#%ARGUMENTS:
# [string] - The name-syntax string to process.
#%RETURNS:
# The argument name.
#**************************************************
sub getName {
  my( $name ) = shift;
  $name =~ s/\W.*$//g;
  return $name;
}

#**************************************************
#%FUNCTION: description
#%DESCRIPTION: Used to set/retrieve the description
# that should be included in the help text.
#%ARGUMENTS:
# [description] - The new description to use.
#%RETURNS:
# The stored description.
#**************************************************
sub description {
  if ( scalar(@_) > 0 ) {
    $description = shift;
  }
  return $description;
}

#**************************************************
#%FUNCTION: programName
#%DESCRIPTION: Used to set/retrieve the program
# name that should be included in the help
# text.
#%ARGUMENTS:
# [programName] - The new program name to use.
#%RETURNS:
# The stored program name.
#**************************************************
sub programName {
  if ( scalar(@_) > 0 ) {
    $programName = shift;
  }
  return $programName;
}

#**************************************************
#%FUNCTION: add
#%DESCRIPTION: Used to add an option to the
# possible command arguments.
#%ARGUMENTS:
# name -- The option name and format
# description -- The descriptoin of the arguments.
# [default] -- The default value.
#%RETURNS:
# The option name.
#**************************************************
sub add {
  my( $name, $description, $default ) = @_;
  push( @main::optionList, $name );
  $name = getName( $name );
  push( @options, $name );
  $description{$name} = $description;
  if ( $default ne '' || scalar(@_) > 2 ) {
    $default{$name} = $default;
  }
}

#**************************************************
#%FUNCTION: alternatives
#%DESCRIPTION: Used to set/retrieve the alternatives
# for a given argument name. Alternatives will have the
# same syntax as the main argument.
#%ARGUMENTS:
# name -- The argument name.
# [alternatives] -- The argument alternatives to use.
#%RETURNS:
# The stored alternatives.
#**************************************************
sub alternatives {
  my( $name ) = shift;
  $name = getName( $name );
  push( @{$alternatives{$name}}, @_ );
  foreach $option ( @main::optionList ) {
    if ( getName( $option ) eq $name ) {
      my( $syntax ) = ( $option =~ /$name(.*)/ );
      foreach $alternative ( @_ ) {
	push( @main::optionList, "${alternative}${syntax}" );
      }
    }
  }
  return @{$alternatives{$name}};
}

#**************************************************
#%FUNCTION: byLength
#%DESCRIPTION: Used for sorting strings by their
# length.
#%ARGUMENTS:
# a, b - Two strings to compare.
#%RETURNS:
# The comparison value.
#**************************************************
sub byLength {
  return ( length($a) - length($b) );
}

#**************************************************
#%FUNCTION: combine
#%DESCRIPTION: Used to combine an argument and it's
# alternatives into a single string for the help
# text.
#%ARGUMENTS:
# names -- The array of names to combine.
#%RETURNS:
# The combined value.
#**************************************************
sub combine {
  my @names = ( @_ );
  push( @names, @{$alternatives{$name}} );
  @names = sort byLength @names;
  if( scalar( @names ) == 2 ) {
    if ( $names[1] =~ /^$names[0]/ ) {
      my $remainder = $';
      return "$names[0]\[$remainder\]";
    }
  }
  return join( "/", @names );
}

#**************************************************
#%FUNCTION: process
#%DESCRIPTION: Used to process the command line
# arguments, combine the alternatives and generate
# a help message if necessary.
#%ARGUMENTS:
# None.
#%RETURNS:
# The generated help message (if appropriate).
#**************************************************
sub process {
  GetOptions( @main::optionList );

  foreach $name ( @options ) {
    my $value = ${"opt_$name"};
    if ( $value eq '' ) {
      foreach $alternative ( @{$alternatives{$name}} ) {
	my $alt_value = ${"opt_$alternative"};
	if ( $alt_value ne '' ) {
	  ${"main::opt_$name"} = $alt_value;
	  last;
	}
      }
    } else {
      ${"main::opt_$name"} = $value;
    }
  }

  my $message = "";

  if ( $main::opt_help ) {
    $message .= "  $description\nOptions:\n";
    my %tags = ();
    my $maxLength = 0;
    foreach $name ( @options ) {
      $tags{$name} = combine( $name );
      $length = length( $tags{$name} );
      if ( $length > $maxLength ) {
	$maxLength = $length;
      }
    }

    foreach $name ( @options ) {
      my $default = $default{$name};
      if ( $default ne '' ) {
	$default = ", and is '${default}' by default";
      }
      $message .= sprintf( "  %-${maxLength}s -- %s%s\n", $tags{$name}, $description{$name}, $default );
    }
    $message .= "Usage: $programName\n";
  }

  return $message;
}

# Add the option defaults.
add( 'help!', 'Displays this help menu' );
alternatives( 'help', 'h' );
( $programName ) = ( $0 =~ /(\w+)$/ );
$description = '<Empty Description>';

1;
