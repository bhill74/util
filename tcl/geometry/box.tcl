source $::env(HOME)/tcl/lib/line_segment.tcl

namespace eval box {
    proc is_box {test} {
	if { ![line_segment::is_line_segment $test] } {
	    return 0
	}

	set A [lindex $test 0]
	set B [lindex $test 1]

	if { [lindex $A 0] > [lindex $B 0] } {
	    return 0
	}

	if { [lindex $A 1] > [lindex $B 1] } {
	    return 0
	}

	return 1
    }

    proc line_intersection {box line} {
	set BL [lindex $box 0]
	set TR [lindex $box 1]
	set I {}

	set R [line_segment::intersect $box [list $BL $TL]]
	if { $R != {} } {
	    lappend I $R
	}
    }

    proc intersects_line {box line} {
	set R [line_segment::intersect $box $line]
	if { $R != {} } {
	    return 1
	}

	return 0
    }
}
