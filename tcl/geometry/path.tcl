source $::env(HOME)/tcl/lib/line_segment.tcl

namespace eval path {

    proc is_path {test} {
	if { [point::is_point $test ] } {
	    return 0
	}

	if { [llength $test] == 1 } {
	    return 0
	}

	for { set i 0 } { $i < [expr [llength $test] - 1] } {incr i} {
	    set A [lindex $test $i]
	    set B [lindex $test [expr $i + 1]]
	    if { ![line_segment::is_line_segment [list $A $B]] } {
		return 0
	    }
	}

	return 1
    }

    proc get_edge {path index} {
	if { $index == end } {
	    return [list [lindex $path [expr [llength $path] - 2]] [lindex $path end]]
	}
	return [list [lindex $path $index] [lindex $path [expr $index + 1]]]
    }

    proc is_loop {path} {
	if { ![is_path $path] } {
	    return 0
	}

	if { [lindex $path 0] != [lindex $path end] } {
	    return 0
	}

	return 1
    }

    proc is_valid {path} {
	set path_length [llength $path]
	for { set i 1 } { $i < [expr $path_length - 1] } { incr i } {
	    set A [lindex $path $i]
	    for { set j [expr $i + 1] } { $j < $path_length } { incr j } {
		set B [lindex $path $j]
		if { $A != $B } {
		    continue
		}

		if { $i != 0 || $j != [expr $path_length - 1] } {
		    return 0
		}
	    }
	}

	return 1
    }

    proc display {paths} {
	foreach path $paths {
	    puts "   $path"
	}
    }

    proc simplify {path} {
	if { [llength $path] < 2 } {
	    return $path
	} elseif { [llength $path] == 2 } {
	    set A [lindex $path 0]
	    set B [lindex $path 1]
	    if { [point::equal $A $B] } {
		return [list $A]
	    }
	    return $path
	}

	set new_path {}
	for { set i 0 } { $i < [expr [llength $path] - 2] } { incr i } {
	    set A [lindex $path $i]
	    set B [lindex $path [expr $i + 1]]
	    set C [lindex $path [expr $i + 2]]

	    if { $i == 0 } {
		lappend new_path $A
	    }

	    if ![line_segment::contains [list $A $C] $B] {
		lappend new_path $B
	    }
	}

	if { [lindex $new_path end] != $C } {
	    lappend new_path $C
	}

	return $new_path
    }

    proc divide {path point {position 0}} {
	# If the point is actually a path.
	if { [is_path $point] } {
	    set resultA [divide $path [lindex $point 0] 0]
	    set resultB [divide $path [lindex $point end] end]
	    if { [llength $resultA] > 1 && [llength $resultB] > 1 } {
		return [list [lindex $resultA 0] [lindex $resultB 1]]
	    }
	    return [list $path]
	}

	set result [lsearch -exact -all $path $point]
	set i [lindex $result $position]

	if { $i == {} } {
	    for { set j 0 } { $j < [expr [llength $path] - 1] } { incr j } {
		set A [lindex $path $j]
		set B [lindex $path [expr $j + 1]]
		if { [line_segment::contains [list $A $B] $point ] } {
		    set pathA [lreplace $path 0 $j $point]
		    set pathB [lreplace $path $j end $A $point]
		    return [list $pathB $pathA]
		}
	    }
	    return [list $path]
	}

	if { $i == 0 } {
	    return [list {} $path]
	} elseif { $i == [expr [llength $path] - 1]} {
	    return [list $path {}]
	}

	set pathA [lreplace $path 0 $i $point]
	set pathB [lreplace $path $i end $point]
	return [list $pathB $pathA]
    }

    proc difference {path other_paths} {
	set difference {}
	set remainder 0
	foreach other_path $other_paths {
	    set result [divide $path $other_path]
	    set pathA [lindex $result 0]
	    set pathB [lindex $result 1]
	    if { $pathA != {} } {
		lappend difference $pathA
	    }
	    if { $pathB != {} } {
		set path $pathB
		set remainder 1
	    } else {
		set remainder 0
	    }
	}

	if { $remainder && [lsearch $difference $path] == -1 } {
	    lappend difference $path
	}

	return $difference
    }

    proc overlaps {pathA pathB} {
	set overlaps {}

	for { set i 0 } { $i < [expr [llength $pathA] - 1] } { incr i } {
	    set A1 [lindex $pathA $i]
	    set A2 [lindex $pathA [expr $i + 1]]
	    set edgeA [list $A1 $A2]

	    for { set j 0 } { $j < [expr [llength $pathB] - 1] } { incr j } {
		set B1 [lindex $pathB $j]
		set B2 [lindex $pathB [expr $j + 1]]
		set edgeB [list $B1 $B2]

		set C [line_segment::intersect $edgeA $edgeB]
		if { ![line_segment::is_line_segment $C] } {
		    continue
		}

		if { [lsearch $overlaps $C] == -1 } {
		    lappend overlaps $C
		}
	    }
	}

	return [paths::merge $overlaps]
    }

    proc merge {pathA pathB {avoid {}}} {
	set A2 [lindex $pathA end]
	set B1 [lindex $pathB 0]
	if { $A2 != $B1 || [lsearch $avoid $A2] != -1 } {
	    return
	}

	for { set i 1 } { $i < [llength $pathB] } { incr i } {
	    lappend pathA [lindex $pathB $i]
	}

	return $pathA
    }
}
