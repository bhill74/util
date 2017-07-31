source $::env(HOME)/tcl/lib/line.tcl

namespace eval line_segment {

    proc is_line_segment {test} {
	if { [line::is_line $test] } {
	    return 1
	}
	return 0
    }

    proc is_upper {A B} {
	set Ax [lindex $A 0]
	set Ay [lindex $A 1]
	set Bx [lindex $B 0]
	set By [lindex $B 1]
	if { $Ax == $Bx } {
	    if { $Ay > $By } {
		return 1
	    }
	    return 0
	} elseif { $Ay == $By } {
	    if { $Ax > $Bx } {
		return 1
	    }
	    return 0
	}

	return 0
    }

    proc length {line} {
	if { ![is_line_segment $line] } {
	    return
	}

	set A [lindex $line 0]
	set B [lindex $line 1]
	set Ax [lindex $A 0]
	set Ay [lindex $A 1]
	set Bx [lindex $B 0]
	set By [lindex $B 1]
	set dx [expr $Bx - $Ax]
	set dy [expr $By - $Ay]
	return [expr sqrt( pow($dx,2) + pow($dy,2) )]
    }

    proc contains {line point} {
	set A [lindex $line 0]
	set B [lindex $line 1]
	if { $B == {} } {
	    return 0
	}

	if { ![line::contains $line $point] } {
	    return 0
	}

	set Ax [lindex $A 0]
	set Ay [lindex $A 1]
	set Bx [lindex $B 0]
	set By [lindex $B 1]

	set minX [value::min $Ax $Bx]
	set maxX [value::max $Ax $Bx]
	set minY [value::min $Ay $By]
	set maxY [value::max $Ay $By]

	set x [lindex $point 0]
	set y [lindex $point 1]
	if { $minX > $x || $maxX < $x } {
	    return 0
	} elseif { $minY > $y || $maxY < $y } {
	    return 0
	}

	return 1
    }

    proc intersect {lineA lineB} {
	set C [line::intersect $lineA $lineB]
	if { $C == {} } {
	    return {}
	} elseif { [point::is_point $C] } {
	    if { ![line_segment::contains $lineA $C] || \
		     ![line_segment::contains $lineB $C] } {
		return
	    }
	} elseif { [line_segment::is_line_segment $C] } {
	    foreach point $C {
		if { ![line_segment::contains $lineA $point] || \
			 ![line_segment::contains $lineB $point] } {
		    return
		}
	    }
	} else {
	    return
	}

	return $C
    }
}
