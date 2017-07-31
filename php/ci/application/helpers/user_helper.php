<?php 

if ( ! function_exists('userTable') ) {
    function userTable($table) 
    {
        return "bhill_${table}";
    }
}