<?php

/****************************************************
 * User lookup utilities
 * 
 * Utilities used to query information about
 * employee information.
 */

class Lookup
{
    /* Define a cache to prevent multiple lookups */
    private static $cache = array();
    
    /* Define the binary to use */
    private static $tdph = "/usr/local/bin/tdph";
    
    /****************************************************
     *%FUNCTION: getInfo
     *%DESCRIPTION: Used to find the desired information
     * for the given user.
     * Note: The result is cached to prevent multiple
     * lookup delays.
     *%ARGUMENTS:
     * [id] -- The user id to search for.
     * [fields] -- The fields to search for, by default 'all'
     * is used.
     *%RETURNS:
     * The query results for the user id.
     */
    static function getInfo( $id = '', $fields = array( 'all' ) ) {
        if ( $id == '' ) {
            $id = $_ENV['USER'];
        }
        
        $results = 0;
        $return = array();
        $bin = Lookup::$tdph . " empcode=Active -w -u";
        
        if ( array_search( 'all', $fields, true ) !== false ) {            
            $temp_id = $id;
            if ( $temp_id == '' ) {
                $id = $_ENV['USER'];
            }
            $command = "${bin} email_userid=${id} return all";
            exec( $command, $result );
            $fields = explode( "\t", $result[0] );
            $results = explode( "\t", $result[1] );
        }
        
        $index = 0;
        foreach ( $fields as $field ) {
            $key = "lookup_${id}_${field}";            
            if ( isset( Lookup::$cache[$key] ) ) {           
                $return[$field] = Lookup::$cache[$key];
            } else {            
                $id = strtolower( $id );
                if ( !is_array( $results ) ) {
                    $command = "${bin} email_userid=${id} -h return " . implode( ' ', $fields );
                    exec( $command, $result );
                    $results = explode( "\t", trim( $result[0] ) );
                }
                $value = $results[$index];
                Lookup::$cache[$key] = $value;
                $return[$field] = $value;
            }
            $index++;
        }
        
        return $return;
    }
    
    static function getUsers($query) {
        $bin = Lookup::$tdph . " empcode=Active -w -u";
        $command = "${bin} ${query} return email_userid";
        exec( $command, $result );
        array_shift($result);
        return array_filter($result);
    }

    /****************************************************
     *%FUNCTION: getName
     *%DESCRIPTION: Used to find the id of the 
     * given user from the name.
     * Note: The result is cached to prevent multiple
     * lookup delays.
     *%ARGUMENTS:
     * name -- The user name to search for.
     *%RETURNS:
     * The user id for the given name.
     */
    static function getName( $id = '' ) {
        $result = Lookup::getInfo( array( 'name' ), $id );
        return $result['name'];
    }
}

?>
