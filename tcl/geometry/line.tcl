source $::env(HOME)/tcl/lib/point.tcl

namespace eval line {

    proc is_line {test} {
	if { [point::is_point $test] } {
	    return 0
	}

	if { [llength $test] != 2 } {
	    return 0
	}

	foreach sub_test $test {
	    if { ![point::is_point $sub_test] } {
		return 0
	    }
	}

	return 1
    }

    proc contains {line point} {
	set pA [lindex $line 0]
	set pB [lindex $line 1]
	if { $pB == {} } {
	    return 0
	}

	set Ax [lindex $pA 0]
	set Ay [lindex $pA 1]
	set Bx [lindex $pB 0]
	set By [lindex $pB 1]

	set dx [expr $Ax - $Bx]
	set dy [expr $Ay - $By]

	set x [lindex $point 0]
	set y [lindex $point 1]
	# Manhattan
	if { $dy == 0 } {
	    if { $Ay == $y } {
		return 1
	    }
	    return 0
	} elseif { $dx == 0 } {
	    if { $Ax == $x } {
		return 1
	    }
	    return 0
	}
	# Non Manhattan
	set s [expr $dy / $dx]
	set b [expr $Ay - ( $s * $Ax ) ]

	set ny [expr ( $s * $x ) + $b]
	if { [value::equal $y $ny ] } {
	    return 1
	}

	return 0
    }

    proc intersect {lineA lineB} {
	set A1 [lindex $lineA 0]
	set A2 [lindex $lineA 1]
	set B1 [lindex $lineB 0]
	set B2 [lindex $lineB 1]

	set A1x [lindex $A1 0]
	set A1y [lindex $A1 1]
	set A2x [lindex $A2 0]
	set A2y [lindex $A2 1]

	set B1x [lindex $B1 0]
	set B1y [lindex $B1 1]
	set B2x [lindex $B2 0]
	set B2y [lindex $B2 1]

	set dxA [expr $A2x - $A1x]
	set dyA [expr $A2y - $A1y]
	set dxB [expr $B2x - $B1x]
	set dyB [expr $B2y - $B1y]

	set sA INF
	set sB INF
	catch {set sA [expr $dyA/$dxA]}
	catch {set sB [expr $dyB/$dxB]}

	if { $sA == INF && $sB == INF} {
	    if { $A1x != $B1x } {
		return
	    }

	    set minY [value::min $B1y $B2y]
	    set maxY [value::max $B1y $B2y]

	    if { $A2y > $A1y } {
		if { $maxY < $A1y } {
		    return [list [list $A1x $maxY] $A1]
		}

		set R2 [list $A1x [value::min $A2y $maxY]]
		if { $minY < $A1y } {
		    return [list $A1 $R2]
		} elseif { $minY < $A2y } {
		    return [list [list $A1x $minY] $R2]
		}
		return [list [list $A1x $A2y] [list $A1x $minY]]
	    }

	    if { $minY > $A1y } {
		return [list [list $A1x $minY] $A1]
	    }

	    set R2 [list $A1x [value::max $A2y $minY]]
	    if { $maxY > $A1y } {
		return [list $A1 $R2]
	    } elseif { $maxY > $A2y } {
		return [list [list $A1x $maxY] $R2]
	    }
	    return [list [list $A1x $A2y] [list $A1x $maxY]]
	}

	if { $sA == 0 && $sB == 0 } {
	    if { $A1y != $B1y } {
		return
	    }

	    set minX [value::min $B1x $B2x]
	    set maxX [value::max $B1x $B2x]

	    if { $A2x > $A1x } {
		if { $maxX < $A1x } {
		    return [list [list $maxX $A1y] $A1]
		}

		set R2 [list [value::min $A2x $maxX] $A1y]
		if { $minX < $A1x } {
		    return [list $A1 $R2]
		} elseif { $minX < $A2x } {
		    return [list [list $minX $A1y] $R2]
		}
		return [list [list $A2x $A1y] [list $minX $A1y]]
	    }

	    if { $minX > $A1x } {
		return [list [list $minX $A1y] $A1]
	    }

	    set R2 [list [value::max $A2x $minX] $A1y]
	    if { $maxX > $A1x } {
		return [list $A1 $R2]
	    } elseif { $maxX > $A2x } {
		return [list [list $maxX $A1y] $R2]
	    }
	    return [list [list $A2x $A1y] [list $maxX $A1y]]
	}

	if { $sA == INF && $sB != INF } {
	    set bB [expr $B1y - ( $sB * $B1x )]
	    set Cy [expr ( $sB * $A1x ) + $bB]
	    return [list $A1x $Cy]
	}

	if { $sB == INF && $sA != INF } {
	    set bA [expr $A1y - ( $sA * $A1x )]
	    set Cy [expr ( $sA * $B1x ) + $bA]
	    return [list $B1x $Cy]
	}

	set bA [expr $A1y - ( $sA * $A1x )]
	set bB [expr $B1y - ( $sB * $B1x )]
	set Cx [expr ( $bB - $bA ) / ( $sA - $sB )]
	set Cy [expr ( $sA * $Cx ) + $bA]
	return [list $Cx $Cy]
    }
}
