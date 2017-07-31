source $::env(HOME)/tcl/lib/value.tcl

#**************************************************************************#
#%NAMESPACE: point
#%DESCRIPTION: Includes functions that are capable of processing geometric
# coordinate information.
#**************************************************************************#
namespace eval point {
   #***********************************************************************#
   #%FUCNTION: is_point
   #%DESCRIPTION: Used to validate if a given variable value representes a
   # coordinate/point
   #%ARGUMENTS:
   # test -- The value to test
   #%RETURNS:
   # TRUE if the given value is a point, FALSE otherwise.
   #***********************************************************************#
    proc is_point {test} {
	if { [llength $test] != 2 } {
	    return 0
	}

	if { [llength [lindex $test 0]] != 1 || \
		 [llength [lindex $test 1]] != 1 } {
	    return 0
	}

	return 1
    }

   #***********************************************************************#
   #%FUCNTION: equal 
   #%DESCRIPTION: Used to validate if two given point values are considered
   # equal. 
   #%ARGUMENTS:
   # A, B -- The two points to compare
   #%RETURNS:
   # TRUE if the given points are equal, FALSE otherwise.
   #***********************************************************************#
    proc equal {A B} {
	if { ![is_point $A] || ![is_point $B] } {
	    return 0
	}

	set Ax [lindex $A 0]
	set Ay [lindex $A 1]
	set Bx [lindex $B 0]
	set By [lindex $B 1]

	if { ![value::equal $Ax $Bx] || ![value::equal $Ay $By] } {
	    return 0
	}

	return 1
    }
}
