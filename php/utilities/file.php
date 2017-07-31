<?php

/****************************************************
 * File utilities
 * 
 * Utilities used to query information about file
 * information.
 */

class File
{
    /****************************************************
     *%FUNCTION: getRelativePath
     *%DESCRIPTION: Used to find the relative path 
     * from the reference. The search can be both 'up'
     * and/or 'down'. 
     * If the seach is 'down' the number of levels should
     * be provided.
     * Note: If the file to be search for is neither above 
     * or below the reference it will not be found.
     *%ARGUMENTS:
     * file -- The file path to search for.
     * [reference] -- The reference point for the search, 
     * which defaults to the current directory.
     * [direction] -- The direction for the search which could be
     * 'up', 'down' or 'both.
     * [depth] -- If the direction includes 'down' then this 
     * the is maximum number of directories to decend.
     *%RETURNS:
     * The relative path or -1 if one could not be found.
     */
    function getRelativePath( $file, 
                              $reference = '', 
                              $direction = 'up', 
                              $depth = 3 ) {
        $location = ( $reference == '' ) ? getcwd() : $reference;
        $relative_path = '';

        // Check 'up' first.
        if ( $direction == 'up' ||
             $direction == 'both' ) {
            while( $location != '' && 
                   $location != '/' &&
                   $location != '.' ) {
                if ( file_exists( "$location/$file" ) ) {
                    return $relative_path;
                }
                $location = dirname( $location );
                $relative_path .= "../";
            }
        }
        
        // Check 'down' next.
        if ( $direction == 'down' ||
             $direction == 'both' ) {
            $filename = basename( $file );
            $dir = dirname( $file );
            if ( $dir != '.' &&  $dir != '' ) {
                $depth += sizeof( explode( '/', $dir ) );
            }            
            $command =  "pushd ${reference} >/dev/null;";
            $command .= "find -maxdepth ${depth} -name ${filename} 2>/dev/null | grep ${file};";
            $command .= 'popd >/dev/null';
            exec( $command, $result );
            if ( sizeof( $result ) ) {
                preg_match( "|^(.*)${file}\$|", $result[0], $matches );
                return $matches[1];
            }
        }
        
        return -1;
    }
}

?>
