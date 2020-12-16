# **************************************************
# Define the package for Menu
package Menu;

my $any_cmd = "$ENV{HOME}/util/menu/any";
my $prompt_cmd = "$ENV{HOME}/util/menu/pr";

# **************************************************
# %FUNCTION:
#  Menu->new
# %DESCRIPTION
#  menu() is used to create a new menu object. This
#  object is used to display options to the screen and
#  allow users to select from them.
# %ARGUMENTS
#  None
# %RETURNS
#  A pointer to a new Menu hash.
# **************************************************
sub new {
    my $type = shift;
    my $self = shift;

    # Values
    $self->{default} = undef;
    $self->{type} = 'single';
    $self->{preMessage} = undef;
    $self->{postMessage} = undef;
    @{$self->{choices}} = undef;

    bless $self, $type;

    return $self;
}

# **************************************************
# %FUNCTION:
#  Menu->default
# %DESCRIPTION
#  default() is used to set and access the
#  default value used by the menu prompt.
# %ARGUMENTS
#  [default] -- The default value to use. Can be
#  any type of data but is assumed to be a string
#  or number.
# %RETURNS
#  The current default value.
# **************************************************
sub default {
  my $self = shift;
  $self->{default} = shift if ( @_ );
  return $self->{default};
}

# **************************************************
# %FUNCTION:
#  Menu->type
# %DESCRIPTION
#  type() is used to set and access the
#  type of menu that should be displayed. There
#  are only certain types allowed.
#   * 'single'
#   * 'multiple'
#   * 'directory'
#   * 'file'
#   * 'yesno'
#   * 'string'
#   * 'number'
# %ARGUMENTS
#  [type] -- The type of menu to create. The
#  default is 'single'.
# %RETURNS
#  The current type of menu.
# **************************************************
sub type {
  my $self = shift;
  $self->{type} = shift if ( @_ );
  return $self->{type};
}

# **************************************************
# %FUNCTION:
#  Menu->preMessage
# %DESCRIPTION
#  preMessage() is used to set and access the
#  message that should be displayed at the top
#  of the menu. The message should not contain the
#  carriage return at the end.
# %ARGUMENTS
#  [preMessage] -- The message string.
# %RETURNS
#  The message string.
# **************************************************
sub preMessage {
  my $self = shift;
  $self->{preMessage} = shift if ( @_ );
  return $self->{preMessage};
}

# **************************************************
# %FUNCTION:
#  Menu->postMessage
# %DESCRIPTION
#  postMessage() is used to set and access the
#  message that should be displayed at the bottom
#  of the menu. The message should not contain the
#  carriage return at the end.
# %ARGUMENTS
#  [postMessage] -- The message string.
# %RETURNS
#  The message string.
# **************************************************
sub postMessage {
  my $self = shift;
  $self->{postMessage} = shift if ( @_ );
  return $self->{postMessage};
}

# **************************************************
# %FUNCTION:
#  Menu->choices
# %DESCRIPTION
#  choices() is used to set and access the list of
#  choices that can be made from the menu.
# %ARGUMENTS
#  [choices] -- The list of choices that can be made.
# %RETURNS
#  The list of choices that will be used.
# **************************************************
sub choices {
  my $self = shift;
  @{$self->{choices}} = @_ if ( @_ );
  return @{$self->{choices}};
}

sub validate {
  my $self = shift;
  my $value = shift;

  # Get the flag indicating that the user should be prompted.
  my $prompt = shift;

  # Get the type of data.
  my $type = $self->type;

  # If the type is a selection.
  if ( $type eq 'single' || $type eq 'multiple' ) {
    # Get the choices.
    my @choices = $self->choices;
    my $choice, $c;
    foreach $c ( 1..$#choices+1 ) {
      if ( $value eq $choices[$c] ) {
	$choice = $c;
      } else {
	$choice = -1;
      }
    }

    return $self->_validate( $choice, $prompt );
  }

  return $self->_validate( $value, $prompt );
}

sub _validate {
  my $self = shift;
  my $value = shift;

  # Get the flag indicating that the user should be prompted.
  my $prompt = shift;

  # Get the choices.
  my @choices = $self->choices;

  # Get the type of data.
  my $type = $self->type;

  # If the type is a selection.
  if ( $type eq 'single' || $type eq 'multiple' ) {
    # If the type is a single selection then make sure a
    # valid option is chosen.
    if ( $value < 0 ||
	 $value eq '0' ) {
      if ( $prompt ) {
	print STDERR "The selection is not valid.\n";
	print STDERR "Please choose the appropriate number.\n";
      }
      return 0;
    }
    # If the type is a single selection then make sure
    # only 1 option is chosen.
    if ( $type eq 'single' &&
	 $value =~ /\D/ ) {
      if ( $prompt ) {
	print STDERR "The selection is not valid.\n";
	print STDERR "Please only choose one option.\n";
      }
      return 0;
    }
    # If the type is a single selection then make sure a
    # valid option is chosen.
    if ( $type eq 'single' &&
	 $value > $#choices + 1 ) {
      if ( $prompt ) {
	print STDERR "The selection is not valid.\n";
	print STDERR "Please choose the appropriate number.\n";
      }
      return 0;
    }
    # If the type is a multiple selection then make sure
    # there are no invalid characters.
    if ( $type eq 'multiple' &&
	 ( $value > $#choices + 2 ||
	   $value =~ /[^0-9\-,]/ ) ) {
      if ( $prompt ) {
	print STDERR "The selection is not valid.\n";
	print STDERR "Please choose one or more of the appropriate numbers.\n";
	print STDERR "ie. 4\n";
	print STDERR "    3,6,8\n";
	print STDERR "    3-6,9,12\n";
      }
      return 0;
    }
  }
  # If the type is a directory then make sure it exists.
  elsif ( $type eq 'directory' && !-d $value ) {
    if ( $prompt ) {
      print STDERR "That directory does not exist.\n";
    }
    return 0;
  }
  # If the type is a file then make sure it exists.
  elsif ( $type eq 'file' && !-e $value ) {
    if ( $prompt ) {
      print STDERR "That file does not exist.\n";
    }
    return 0;
  }
  # If the type is a yes or no question then make sure it is valid.
  elsif ( $type eq 'yesno' && $value !~ /[YN]/i ) {
    if ( $prompt ) {
      print STDERR "Please enter Y (Yes) or N (No).\n";
    }
    return 0;
  }
  # If the type is a number then make sure it is valid.
  elsif ( $type eq 'number' && $value < 1 ) {
    if ( $prompt ) {
      print STDERR "Please enter a positive numerical value.\n";
    }
    return 0;
  }

  return 1;
}

# **************************************************
# %FUNCTION:
#  Menu->prompt
# %DESCRIPTION
#  prompt() is used to create the prompt that the
#  user will use to input a selection. Depending
#  on the type of prompt the user may have a menu
#  of options or have a string to explicitly type in.
# %ARGUMENTS
#  None
# %RETURNS
#  The input from the user.
# **************************************************
sub prompt {
  # Get the object.
  my $self = shift;

  # Get the type of option.
  my $type = $self->type;

  # Get the choices.
  my @choices = grep(/\S/, $self->choices);

  # Get the default value.
  my $default = $self->default;

  # If the default value is NOT set then set it.
  if ( !$default ) {
    # If the type is a selection that includes ALL
    # the options then default to the last one.
    if ( $type eq 'multiple' ) {
      $default = $#choices + 2;
    }
    # If the type is a selection that includes only
    # individual the options then default to the first
    # one.
    elsif ( $type eq 'single' ) {
      $default = 1;
    }
    # If the type of selection is a directory
    # then use the current directory.
    elsif ( $type eq 'directory' ) {
      $default = `pwd`;
      chomp $default;
    }
    # If the type of selection is a yes or no.
    elsif ( $type eq 'yesno' ) {
      $default = 'Y';
    }
  } elsif ( $type eq 'single' || $type eq 'multiple' ) {
    # Split the default into a list of defaults
    # and make sure it is unique.
    my @defaults = split( "$;", $default );
    if ( scalar( @defaults ) > 1 ) {
      my %defaults;
      @defaults{@defaults} = ();
      @defaults = sort keys %defaults;
    }

    # Initialize the default.
    $default = '';

    # If the prompt will be a selection them make sure the default
    # value is converted to a set of options (one or more).
    my $i;
    foreach $i (0..$#choices) {
      my $selection;
      foreach $selection ( @defaults ) {
	if ( $selection eq $choices[$i] ) {
	  $default .= "," if ( $default );
	  $default .= $i+1;
	  # If only one option is allowed then quit
	  # once it has been found.
	  last if ( $type eq 'single' && $default );
	}
      }
    }
  }

  # Display the pre-message.
  print STDERR "\n";
  print STDERR sprintf( "%s\n", $self->preMessage ) if ( $self->preMessage );

  # If the type is a yes/no and there are choices then display the options
  if ( $type eq 'yesno' && scalar(@choices) > 0) {
    foreach $i (0, 1) {
        print STDERR ($i ? 'N' : 'Y') . ") $choices[$i]\n";
    } 
  }
  # If the type is a selection then display the options.
  elsif ( $type eq 'single' || $type eq 'multiple' ) {
    # Get the number of columns and lines currently on the screen.
    my $dimensions = `resize`;
    my ( $screenWidth ) = ( $dimensions =~ /COLUMNS\D+(\d+)/i );
    my ( $lines ) = ( $dimensions =~ /LINES\D+(\d+)/i );

    if ( $screenWidth == 0 && $lines == 0 ) {
       if ( `which resize` =~ /not found/i ) {
          warn "The utility (resize) for sizing the window could not be found\n";
          $screenWidth = 20;
          $lines = 10;
       } else {
          die "The window is too small to display a menu\n";
       }
    }

    # Adjust the lines by removing the ones necessary for the messages.
    $lines -= scalar( split( /\n/, $self->preMessage ) );
    $lines -= scalar( split( /\n/, $self->postMessage ) );
    # Adjust the lines by removing the one needed for the prompt.
    $lines -= 1;

    # Determine the total number of choices.
    my @menuChoices = @choices;
    if ( $type eq 'multiple' ) {
      push( @menuChoices, 'ALL' );
    }
    my $total = $#menuChoices + 1;
    my $numLength = length( $total );

    # Initialize the indicies.
    my $i,$j;

    # Determine the width of the longest choice.
    my $choiceLength = length( $menuChoices[0] );
    foreach $i ( 1..$#menuChoices ) {
      my $length = length( $menuChoices[$i] );
      $choiceLength = $length if ( $choiceLength < $length );
    }

    # Determine the width of each choice in the menu (with selection number).
    # Length of Number + Bracket + Space + Length of Choice
    my $entryWidth = $numLength + 2 + $choiceLength;

    # Determine the maximum number of columns available AND
    # the number of necesary columns.
    my $maxColumns = int( ( $screenWidth + 1 ) / ( $entryWidth + 1 ) );
    $maxColumns = 1 if ($maxColumns == 0);

    my $columns = 1;
    if ( $total > $lines ) {
      $columns = int($total/$lines);
      $columns++ if ( $columns*$lines < $total );
    }
    if ( $columns > $maxColumns ) {
      $columns = $maxColumns;
    }

    # Determine the number of rows.
    my $rows = $total;
    $rows = $lines if ( $lines < $total );

    # Display as many choices as possible before the columns and rows
    # are all used up. Then ask the user to scroll to the next set of options.
    $i = 0;
    while( $i < $total ) {
      # Display the choices.
      foreach $row ( 1..$rows ) {
	my $offset = 0;
	foreach $column ( 1..$columns ) {
	  my $index = $i + $row + $offset - 1;
	  print STDERR sprintf( "%${numLength}d) %-${choiceLength}s", ($index+1), $menuChoices[$index] ) if ( $index < $total );
	  print STDERR " " if ( $j != 1 );
	  $offset += $lines;
	}
	print STDERR "\n";
      }
      # Update the index.
      $i += $rows*$columns;

      # Display the prompt and collect the input.
      if ( $i < $total ) {
	print STDERR "<Press any key to continue...>";
        system($any_cmd);
      }
    }
  }

  # Display the post-message.
  print STDERR sprintf( "%s\n", $self->postMessage ) if ( $self->postMessage );

  # Display the prompt and collect the input.
  print STDERR "Select[$default]: ";
  ( $choice ) = `$prompt_cmd`;
  chomp $choice;

  # Continue to collect input until a valid option is selected.
  while ( $choice =~ /\S/ ) {
    # Initialize the flag.
    my $prompt = !$self->_validate( $choice, 1 );

    # If the prompt is still disabled then break.
    last unless ( $prompt );

    print STDERR "Select[$default]: ";
    chomp( $choice = <STDIN> );
  }

  # If nothing was returned then use the default answer.
  $choice = $default if ( $choice !~ /\S/ );

  # If the type is a selection then return the selected options.
  if ( $type eq 'single' || $type eq 'multiple' ) {
    # Clean up the choice.
    $choice =~ s/^\s+//;
    $choice =~ s/\s+$//;

    # Initialize the list of selected choices..
    my @selectedChoices = ();

    # Process each choice.
    my $selectedChoice;
    foreach $selectedChoice ( split( ',', $choice ) ) {
      if ( $selectedChoice == ( $#choices + 2 ) ) {
	return @choices;
      } elsif ( $selectedChoice =~ /(\d+)-(\d+)/ ) {
	my $i;
	foreach $i ($1..$2) {
	  push( @selectedChoices, $choices[$i-1] );
	}
      } elsif ( $selectedChoice =~ /^\d+$/ ) {
	push( @selectedChoices, $choices[$selectedChoice-1] );
      }
    }

    # Return the list of selected choices.
    return @selectedChoices;
  } elsif ( $type eq 'yesno' ) {
    ( $choice ) = ( $choice =~ /([YN])/i );
    $choice = uc $choice;
  }

  # Otherwise simply return what was entered.
  return $choice;
};

1; # Return true.
