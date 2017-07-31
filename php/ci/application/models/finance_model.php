<?php

/****************************************************
 * Includes:
 */
set_include_path( get_include_path() . PATH_SEPARATOR . "$_ENV[HOME]/php/lib" );
include_once( "db.php" );
include_once( "db_access.php" );
include_once( "arguments.php" );
include_once( "filter.php" );

/************************************************************
 * Class Finance_model
 * 
 * This is the base class for all data that will be stored
 * in the Financial database.
 * 
 * It assists is keeping the mapping to teh unique ID
 * as well as defining the data consistenty.
 */
class Finance_model extends CI_Model {
  public function __construct() {
    $this->load->database();
  }

  public function userCountry () {
    return 'CAD';
  }

  public function userName() {
    return 'bhill';
  }

  public function userFullName() {
    return 'Brian Hill';
  }

  private static function isAssoc( $array ) {
    return array_keys( $array ) !== range(0, count($array) - 1);
  }

  private static $mapping = array();
  public function addObject( $name, $object ) {
    Finance_model::$mapping[$name] = $object;
  }

  public function object( $name ) {
    if ( isset( Finance_model::$mapping[$name] ) ) {
      return Finance_model::$mapping[$name];
    }
    return false;
  }

  /**********************************************************
   *%FUNCTION: name()
   *%DESCRIPTION: 
   * Used to retrieve the name of the current child class.
   *%ARGUMENTS: 
   * None
   *%RETURNS:
   * The name of the current class, in lowercase.
   */
  public function name() {
    return strtolower( get_class($this) );
  }

  /**********************************************************
   *%FUNCTION: debug()
   *%DESCRIPTION: 
   * Used to retrieve the value of the DEBUG flag.
   * Note: Can be controlled by each class using a defined
   * 'debug' local static variable.
   *%ARGUMENTS: 
   * None
   *%RETURNS: 
   * The value of the DEBUG flag.
   */
   public static $debug = 0;
   public function debug() {
      $vars = get_class_vars( get_class( $this ) );
      return $vars['debug'];
   }

  /**********************************************************
   *%FUNCTION: unknownName()
   *%DESCRIPTION: 
   * Used to retrieve the name of 'Unknown'
   * entry used by the current class.
   * Note: Can be controlled by each class using a defined
   * 'unknown' local static variable.
   *%ARGUMENTS: 
   * None
   *%RETURNS: 
   * The name of the unknown entry corresponding 
   * to the current class.
   */
  public static $unknown = 'Unknown';
  public function unknownName() {
    $vars = get_class_vars( get_class( $this ) );
    return $vars['unknown'];
  }

  /**********************************************************
   *%FUNCTION: unknownId()
   *%DESCRIPTION: 
   * Used to retrieve the ID of 'Unknown'
   * entry used by the current class. This will correspond
   * to the ID used in the corresonding MySQL table.
   * Note: Can be controlled by each class using a defined
   * 'unknownId' local static variable.
   *%ARGUMENTS: 
   * None
   *%RETURNS: 
   * The ID of the unknown entry corresponding 
   * to the current class.
   */
  public static $unknownId = 1;
  public function unknownId() {
    $vars = get_class_vars( get_class( $this ) );
    return $vars['unknownId'];
  }

  /********************************************************** 
   * MySQL Table and Fields
   **********************************************************/

  /**********************************************************
   *%FUNCTION: table()
   *%DESCRIPTION: 
   * Used to retrieve the name of the MySQL
   * table that corresponds to the current child class.
   * Note: Can be controlled by each class using a defined
   * 'table' local static variable.
   *%ARGUMENTS: 
   * None
   *%RETURNS: 
   * The name of the table corresponding to the current class.
   */
  public static $table = '_invalid_';
  public function table( &$join = array() ) {
    $vars = get_class_vars( get_class( $this ) );
    $table = Finance_model::userName() . "_" . $vars['table'];
    if ( is_array( $join ) && sizeof( $join ) > 0 ) {
      $table = $this->joinedTable( $join, $table, $this->name() );
    }
    return $table;
  }
  
  public function joinedTable( $join, $table = false, $name = false ) {
    $table = ( $table !== false ) ? $table : $this->table();
    $name = ( $name !== false ) ? $name : $this->name();    

    $columns = $this->columns();
    $this->prefixColumns( $columns, $name );

    $others = array();
    foreach( array_keys( $join ) as $key ) {
      $other = Finance_model::object( $key );
      if ( $other === false ) {
	debug_print_backtrace();	
	print "Invalid object for $key";
	exit;
      }      
      $otherName = $other->name();
      if ( is_array( $join[$key] ) ) {
	foreach( $join[$key] as $field ) {
	  $columns[$key+'_'+$field] = $this->prefixName( $field, $otherName );
	}
      } else if ( is_string( $join[$key] ) ) {
	$field = $join[$key];
	$columns[$key+'_'+$field] = $this->prefixName( $field, $otherName );
      }
      $others[$otherName] = $other;
    }
       
    return $this->join( $others, $columns, $table, $name );
  }   
  
  public function join( $others, &$columns = false, $table = false, $name = false ) {
    $table = ( $table !== false ) ? $table : $this->table();
    $name = ( $name !== false ) ? $name : $this->name();
    
    $sql = '';
    if ( $columns !== false ) {
      $sql = "SELECT ";
      $sql .= $this->selectColumns( $columns );
      $sql .= " FROM ";
    }    
    $sql .= "${table} ${name} ";   
    foreach ( array_keys( $others ) as $otherName ) {
      $other = $others[$otherName];      
      $sql .= sprintf( ' LEFT JOIN %1$s %2$s ON %2$s.`%3$s` = %4$s.`%5$s` ',
		       $other->table(),
		       $otherName,
		       $other->idField(),
		       $name,
		       $other->name() );
    }

    return $sql;
  }

  /**********************************************************
   *%FUNCTION: idLength()
   *%DESCRIPTION: 
   * Used to retrieve the number of digits used
   * to represent the ID for entries in the current class which
   * can be used to define the MySQL table.
   * Note: Can be controlled by each class using a defined
   * 'idLength' local static variable.
   *%ARGUMENTS: 
   * None
   *%RETURNS: 
   * The number of digits used to represent the unique
   * ID for entries corresponding to the current class.
   */
  public static $idLength = '5';
  public function idLength() {
    $vars = get_class_vars( get_class( $this ) );
    return $vars['idLength'];
  }										    
  
  /**********************************************************
   *%FUNCTION: nameLength()
   *%DESCRIPTION: 
   * Used to retrieve the number of characters used
   * to represent the name for entries in the current class which
   * can be used to define the MySQL table.
   * Note: Can be controlled by each class using a defined
   * 'nameLength' local static variable.
   *%ARGUMENTS: 
   * None
   *%RETURNS: 
   * The number of characters used to represent the unique
   * name for entries corresponding to the current class.
   */
  public static $nameLength = '100';
  public function nameLength() {
    $vars = get_class_vars( get_class( $this ) );
    return $vars['nameLength'];
  }  
  
  /**********************************************************
   *%FUNCTION: idField()
   *%DESCRIPTION: 
   * Used to define the field name that should
   * be used for the unique ID for entries corresponding to the
   * current class.
   *%ARGUMENTS:
   * [name] -- The name to be used when generating the field name.
   * If not provided the name of the current class is used.
   *%RETURNS: 
   * The generated field name.
   */ 
  public function idField( $name = '' ) {
    $name = ( $name == '' ) ? $this->name() : $name;
    return $this->name() . "_id";
  }
  
  /**********************************************************
   *%FUNCTION: idType()
   *%DESCRIPTION: 
   * Used to define the TYPE of field that should
   * be used in MySQL when storing ID values for entries
   * corresponding to the current class.
   *%ARGUMENTS: 
   * None
   *%RETURNS: 
   * The MySQL Data type to use for the ID values.
   */ 
  public function idType() {
    return 'INT(' . $this->idLength() . ')';
  }    
  
  /**********************************************************
   *%FUNCTION: field()
   *%DESCRIPTION:
   * Used to define the fields that should be used
   * corresponding specifically to the current class.
   * This function determines the TYPE, DEFAULT and COMMENT (if
   * not provided) based on the given field name.
   *%ARGUMENTS: 
   * name -- The name of the field to use, 'id' is used by default.
   * comment -- The comment to be used in the field definition.
   *%RETURNS: 
   * The MySQL code for defining a table field of the
   * given name.
   */ 
  public function field ( $name = 'id', $comment = '' ) {
    $type = 'TEXT';
    $default = '';
    $class_name = $this->name();
    $options = '';
    
    switch ($name) {
    case 'id':
      $name = $this->idField();
      $type = $this->idType();
      $comment = ( $comment == '' ) ? "The unique ID for the ${class_name}" : $comment;
      $options = "AUTO_INCREMENT";
      break;
    case 'name':
      $type = 'VARCHAR('. $this->nameLength() . ')';
      $comment = ( $comment == '' ) ? "The identifying name for the ${class_name}" : $comment;
      break;
    case 'description':
      $type = 'TEXT';
      $comment = ( $comment == '' ) ? "The description for the ${class_name} entry" : $comment;
      break;
    case 'keywords':
      $type = 'TEXT';
      $comment = ( $comment == '' ) ? "The collection of keywords to associate with this ${class_name}" : $comment;
      break;
    case $class_name:
      $type = $this->idType();
      $comment = ( $comment == '' ) ? "The ID for the ${class_name}" : $comment;
      break;
    default:	   
      break;
    }
    
    return Finance_model::define_field( $name, $type, $comment, $default, $options );
  }
  
  /**********************************************************
   *%FUNCTION: define_field()
   *%DESCRIPTION:
   * Used to combine the name, type, comment, default and 
   * other options into the MySQL syntax for defining a field
   * in a table.
   *%ARGUMENTS: 
   * name -- The name of the field to use.
   * type -- The type of data this field should store.
   * [comment = ''] -- The comment to be used in the field 
   * definition. If not provided it will not be used.
   * [default = ''] -- The default value of the field.
   * If not provided it will not be used.
   * [options = ''] -- The extra options for the field
   * definition. If not provided it will not be used.
   *%RETURNS: 
   * The MySQL code for defining a table field of the
   * given name and settings.
   */ 
  public static function define_field( $name, $type, $comment = '', $default = '', $options = '' ) {
    $sql = "`${name}` ${type} NOT NULL ";
    $sql .= ( $default != '' ) ? " DEFAULT ${default}" : '';
    $sql .= ( $options != '' ) ? "  ${options}" : '';
    $sql .= ( $comment != '' ) ? " COMMENT '${comment}'" : '';       
    return $sql;   
  }

  /**********************************************************
   *%FUNCTION: create()
   *%DESCRIPTION:
   * Used to create the MySQL table with the desired fields.
   * The existing table is DROPed and the new one is created
   * with the ID field given the attributes of PRIMARY and 
   * UNIQUE.
   *%ARGUMENTS: 
   * fields -- The list of fields to add to the table in 
   * MySQL syntax.
   *%RETURNS: 
   * TRUE if the table was created and FALSE otherwise.
   */
  public function create( $fields ) {
    $name = $this->name();
    $table = $this->table();
    array_unshift( $fields, $this->field( 'name' ) );
    array_unshift( $fields, $this->field( 'id' ) );
    array_push( $fields, $this->field( 'description' ) );
    $idField = $this->idField();
    
    $queries = array( "DROP TABLE `${table}`" );
    
    $query = "CREATE TABLE `${table}` ( ";
    $query .= implode( ', ', $fields );
    $query .= ", PRIMARY KEY ( `${idField}` ) , UNIQUE ( `${idField}`) ) ENGINE = MYISAM";
    array_push( $queries, $query );
    
    if ( $this->query( $queries ) ) {
      return $this->reset();
    }
    
    return false;
  }

  /**********************************************************
   *%FUNCTION: unique()
   *%DESCRIPTION:
   * Used to adjust the MySQL table to consider the 
   * combination of certain columns to be unique.
   *%ARGUMENTS: 
   * name -- The name of the new unique field.
   * fields -- The list of fields to add to the table in 
   * MySQL syntax.
   *%RETURNS: 
   * TRUE if the table was altered and FALSE otherwise.
   */
  public function unique( $name, $fields ) {
    $table = $this->table();
    $query = "ALTER TABLE ${table} ADD UNIQUE `${name}` (";
    $query .= $this->toNames( $fields );
    $query .= " )";
    return $this->query( $query );
  }
    
  /*****************************************
   *%FUNCTION: reset()
   *%DESCRIPTION:
   * Used to reset the table.
   *%ARGUMENTS:
   * None
   *%RETURNS:
   * The MySQL result of truncating the table.
   */
  public function reset() {
    $table = $this->table(); 
    
    $queries = array();
    array_push( $queries, "TRUNCATE ${table}" );
    return $this->query( $queries );
  }

  /********************************************************** 
   * MySQL Open/Close
   * 
   * The link to the MySQL database is stored in a static
   * variable and only needs to be done once in a script.
   * 
   * Note: The login in formation is accessed from a global 
   * variable called 'db_access' which is assumed to come 
   * from a file 'db_access.php' available locally.
   **********************************************************/
  
  /* The internal database link */
  private static $link;

  /**********************************************************
   *%FUNCTION: connect()
   *%DESCRIPTION: Used to override the 'connect()' function of
   * the parent Database class with the specific database 
   * login information.
   *%ARGUMENTS: 
   * None
   *%RETURNS:
   * The MySQL handle (also stored internally) in $link.
   */ 
  public function connect() {
    if ( Finance_model::$link != 0 ) {
      return Finance_model::$link;
    }
    
    global $db_access;
    Finance_model::$link = mysql_connect( $db_access['host'], 
				    $db_access['username'], 
				    $db_access['passwd'] );
    if ( Finance_model::$link ) {
      mysql_selectdb( $db_access['db'] );
      return true;
    }
    return false;
  }
  
  /**********************************************************
   *%FUNCTION: close()
   *%DESCRIPTION: Used to close the connection to the
   * MySQL database.
   *%ARGUMENTS: 
   * None
   *%RETURNS:
   * Nothing.
   */ 
  public function close() {
    mysql_close( Finance_model::$link );
  }
  
  /********************************************************** 
   * MySQL Data Management
   * 
   * The following commands are used to manage and
   * maniuplate entries in the MySQL table(s).
   **********************************************************/

  /*****************************************
   *%FUNCTION: isId()
   *%DESCRIPTION:
   * Used to determine whether a given value is
   * numeric ID or a text NAME.
   *%ARGUMENTS:
   * value -- The value to test.
   *%RETURNS:
   * TRUE if the value is numeric and FALSE otherwise.
   */
  public static function isId( $value ) {
    return ( is_numeric( $value ) && intval( $value ) == $value );
  }
  
  /*****************************************
   *%FUNCTION: match()
   *%DESCRIPTION:
   * Used to construct the matching MySQL code
   * for a WHERE statement that will match
   * to a given name or ID. 
   *%ARGUMENTS:
   * value -- The name OR ID of the item to 
   * search for.
   *%RETURNS:
   * Criteria that should be used for MySQL
   * queries. 
   */
  public function match( $value ) {
    $name = $this->name();
    $idField = $this->idField( $name );
    $sql = '';
    if ( is_array( $value ) ) {
      if ( isset( $value['id'] ) ) {
	$sql .= "`${idField}` = $value[id]";
      } else if ( isset( $value['name'] ) ) { 
	$sql .= "`name` = '$value[name]'";
      }
    } else if ( is_numeric( $value ) && intval( $value ) == $value ) {
      $sql .= "`${idField}` = $value";
    } else if ( is_string( $value ) ) {
      $sql .= "`name` = '${value}'";
    }
    
    return $sql;
  }

  /*****************************************
   *%FUNCTION: toIdArray()
   *%DESCRIPTION:
   * Used to convert a given value to an 
   * information array, if it is not already.
   * If the value is a number ID, it will be 
   * used for the 'id' value, otherwise it
   * is assumed to be the 'name' value.
   *%ARGUMENTS:
   * value -- The value to test and convert
   * by reference.
   *%RETURNS:
   * Nothing, but the given value may be modified.
   */
  public static function toIdArray( &$value ) {
    if ( !is_array( $value ) ) {
      if ( Finance_model::isId( $value ) ) {
	$value = array( 'id' => $value );
      } else { 
	$value = array( 'name' => $value );
      }
    }
  }
  
  /*****************************************
   *%FUNCTION: id()
   *%DESCRIPTION:
   * Used to retrieve the ID for a given item. 
   *%ARGUMENTS:
   * info -- The information for the item to 
   * search for and add if necessary by 
   * reference.
   * [insert] -- Whether to insert values
   * that do not already exist in the table.
   *%RETURNS:
   * TRUE if the item is found (or inserted),
   * FALSE otherwise.
   */
  public function id( &$info, $insert = false ) {
    $name = $this->name();
    $table = $this->table();
    $idField = $this->idField( $name );
    
    Finance_model::toIdArray( $info );
    
    if ( !isset( $info['name'] ) || $info['name'] == '' ) {
      $info['name'] = $this->unknownName();
    }
    
    $select_query = "SELECT `${idField}` AS id FROM ${table} WHERE " . $this->match( $info );
    $result = $this->query( $select_query );
    if ( $result === false ) {
      return false;
    }
    
    if ( $row = mysql_fetch_assoc( $result ) ) {
      $info['id'] = intval( $row['id'] );
      return true;
    } else if ( $insert === true ) {
      $fields = array_keys( $info );
      $values = array();
      foreach ( $fields as $field ) {
	array_push( $values, $info[$field] );
      }
      
      $queries = array();
      array_push( $queries, $this->insert( $table, $fields, $values ) );
      array_push( $queries, $select_query );     

      $result = $this->query( $queries );
      if ( $result === false ) {
	return false;
      }

      if ( $row = mysql_fetch_assoc( $result ) ) {
	$info['id'] = intval( $row['id'] );
	return true;
      } 
    } 
    
    $error = "Unknown ${name} '$info'";
    return false;
  }
  
  /*****************************************
   *%FUNCTION: matchQuery()
   *%DESCRIPTION:
   * Used to construct the query used to match
   * and retrieven information for a specific
   * item. 
   *%ARGUMENTS:
   * value -- The name OR ID of the item to 
   * search for.
   * [fields] -- The fields to retrieve, '*' is
   * used by default.
   *%RETURNS:
   * The generated MySQL query for collecting
   * matching information.
   */
  private function matchQuery( $value, $fields = '*' ) {
    $table = $this->variants( $fields );

    $query = "SELECT ";
    $query .= $this->toNames( $fields );
    $query .= " FROM ";
    $query .= $this->quoteTable( $table, 'names' );
    $query .= " WHERE ";
    $query .= $this->match( $value );
    return $query;
  }
  
  /*****************************************
   *%FUNCTION: info()
   *%DESCRIPTION:
   * Used to retrieve the information for a
   * given item. 
   *%ARGUMENTS:
   * value -- The name OR ID of the item to 
   * search for.
   * [fields] -- The fields to retrieve, '*' is
   * used by default.
   *%RETURNS:
   * The information about the given item
   * OR false if none could be found. 
   */
  public function info( $value, $fields = '*' ) {
    $result = $this->query( $this->matchQuery( $value, $fields ) );
    if ( $result === false ) {
      return false;
    }
    
    return mysql_fetch_assoc( $result );
  }
  
  /*****************************************
   *%FUNCTION: resolve()
   *%DESCRIPTION:
   * Takes a given piece of information and
   * expands it to all the relevant fields
   * from the corresponding table. The given
   * information is assumed to be an existing
   * record, name or ID value and the existing
   * ID value is returned. 

   * If the given information could not be 
   * found in the table it is inserted and 
   * the new ID number is returned.
   *%ARGUMENTS:
   * info -- The name, ID or record of the 
   * item to search for or insert.
   *%RETURNS:
   * The ID of the existing/new record in the
   * table.
   */
  public function resolve( $info ) {
    if ( !$this->id( $info, true ) ) {
      return $this->unknownId();
    }
    return $info['id'];
  } 

  public function parse( &$values ) {
    return;
  } 
  
  public function add( $args, $arg2 = '', $arg3 = '' ) {
    $fields = $this->fields( false );
    $num_fields = sizeof( $fields );
    $values = array();

    /* If all the info is in the first argument then use
     * only that.
     */
    $args = func_get_args();
    if ( sizeof( $args ) == 1 &&
	 is_array( $args[0] ) ) {
      $args = $args[0];
    }

    /* Arrange the information 
     */
    $info = array();
    if ( Finance_model::isAssoc( $args ) === false ) {      
      for( $i = 0; $i < $num_fields; $i++ ) {
	$field = $fields[$i];
	$info[$field] = ( isset( $args[$i] ) ) ? $args[$i] : '';
      }
    } else {
      for( $i = 0; $i < $num_fields; $i++ ) {
	$field = $fields[$i];     
	$info[$field] = ( isset( $args[$field] ) )  ? $args[$field] : '';
      }
    }

    /* Extract any necessary information from the other
     * fields 
     */
    $this->parse( $info );

    /* Resolve any information that may be necessary
     */
    for( $i = 0; $i < $num_fields; $i++ ) {
      $field = $fields[$i];
      $table = Finance_model::object( $field );
      if ( $table !== false ) {		
	//print_r( $info );
	$info[$field] = $table->resolve( $info[$field] );
	//print_r( $info );
	//print "TABLE " . $table->name() . "\n";
      }
    }

    /* Put the values in the proper order 
     */
    $values = array();
    for( $i = 0; $i < $num_fields; $i++ ) {
      $field = $fields[$i];
      array_push( $values, $info[$field] );
    }

    return $this->addFields( $fields, $values );
  }
  
  /*****************************************
   *%FUNCTION: addFields()
   *%DESCRIPTION:
   * Used to process an array of field names
   * and an array of corresponding values 
   * and create and process a MySQL INSERT 
   * statement including every field with 
   * valid value (not '').
   *%ARGUMENTS:
   * fields -- The field names to consider
   * (in order).
   * values -- The corresponding values to
   * consider.
   *%RETURNS:
   * The ID of the existing/new record in the
   * table.
   */
  public function addFields( $fields, $values ) {
    $insert_fields = array();
    $insert_values = array();
    $num_arguments = sizeof( $values );
    $num_fields = sizeof( $fields );
    for( $i = 0; $i < $num_fields; $i++ ) {
      if ( $num_arguments == $i ) {
	break;
      } else if ( $values[$i] != '' ) {
	array_push( $insert_fields, $fields[$i] );
	array_push( $insert_values, $values[$i] );
      }
    }
    $query = Database::insert( $this->table(), 
			       $insert_fields, 
			       $insert_values );
    return $this->query( $query );
  }
  
  public function update( $args, $arg2 = '', $arg3 = '' ) {
    $fields = $this->fields( true );
    $num_fields = sizeof( $fields );
    $values = array();

    /* If all the info is in the first argument then use
     * only that.
     */
    $args = func_get_args();
    if ( sizeof( $args ) == 1 &&
	 is_array( $args[0] ) ) {
      $args = $args[0];
    }
   
    /* Arrange the information 
     */
    $info = array();
    if ( Finance_model::isAssoc( $args ) === false ) {      
      for( $i = 0; $i < $num_fields; $i++ ) {
	$field = $fields[$i];
	$info[$field] = ( isset( $args[$i] ) ) ? $args[$i] : '';       
      }
    } else {
      for( $i = 0; $i < $num_fields; $i++ ) {
	$field = $fields[$i];
	$info[$field] = ( isset( $args[$field] ) )  ? $args[$field] : '';
      }
    }

    /* Extract any necessary information from the other
     * fields 
     */
    $this->parse( $info ); 

    /* Put the values in the proper order 
     */
    $values = array();
    for( $i = 0; $i < $num_fields; $i++ ) {
      $field = $fields[$i];
      array_push( $values, $info[$field] );
    }
    
    return $this->updateFields( $fields, $values );
  }

  /*****************************************
   *%FUNCTION: updateFields()
   *%DESCRIPTION:
   * Used to process an array of field names
   * and an array of corresponding values 
   * and create and process a MySQL UPDATE
   * statement including every field with 
   * valid value (not '').
   *%ARGUMENTS:
   * fields -- The field names to consider
   * (in order).
   * values -- The corresponding values to
   * consider.
   *%RETURNS:
   * The ID of the existing in the
   * table.
   */
  public function updateFields( $fields, $values ) {
    $update_fields = array();
    $update_values = array();
    $update_criteria = array();
    $num_arguments = sizeof( $values );
    $num_fields = sizeof( $fields );
    for( $i = 0; $i < $num_fields; $i++ ) {
      if ( $num_arguments == $i ) {
	break;
      } else if ( $values[$i] != '' ) {       
	if ( preg_match( '/_id$/', $fields[$i] ) ) {
	  array_push( $update_criteria, 
		      $this->toName( $fields[$i] ) . ' = ' . $values[$i] );
	} else {
	  array_push( $update_fields, $fields[$i] );
	  array_push( $update_values, $values[$i] );
	}
      }
    }

    if ( sizeof( $update_values ) == 0 ) {
      return false;
    }

    $query = Database::update( $this->table(), 
			       $update_fields, 
			       $update_values,
			       $update_criteria );   
    return $this->query( $query );
  }

  /*****************************************
   *%FUNCTION: process()
   *%DESCRIPTION:
   * Used to process a data based on the
   * arguments provided to the script.
   *%ARGUMENTS:
   * settings - The collection of arguments 
   * provided to the page.
   *%RETURNS:
   * Nothing.
   */
  public function process( &$settings ) {   
    $settings[$this->name()] = '';

    $modes = array( 'add', 'delete', 'update' );
    foreach ( $modes as $mode ) {
      $settings[$mode] = false;
    }

    $fields = $this->fields( false );
    foreach ( $fields as $field ) {
      $settings[$field] = '';
    }
    $settings[$this->name()] = '';   
    $settings = Arguments::process( $settings );

    foreach ( $modes as $mode ) {
      if ( $settings[$mode] === false &&
	   isset( $settings[$mode.'_x'] ) &&
	   isset( $settings[$mode.'_y'] ) ) {
	$settings[$mode] = true;
      }
    }    

    $result = true;

    /* Convert the Product string to an ID if possible */
    $name = $this->name();
    if ( $settings[$name] != '' &&
	 Finance_model::isId( $settings[$name] ) ) {
      $settings[$name] = intval( $settings[$name] );
    }
    
    /* Delete the value if specified */
    if ( $settings[$name] > 0 &&
	 $settings['delete'] !== false ) {
      $result = $this->delete( $settings[$name] );
    }
    
    /* If the data should be added then delete the ID
     * so it will force an addition
     */
    if ( $settings['add'] === true ) {
      $settings[$name] = 0;
    }
    
    /* If the data ID is set, then update the existing one */
    if ( $settings[$name] > 0 ) {
      $settings[$this->idField()] = $settings[$name];
      $result = $this->update( $settings );
    }
    /* Otherwise add any product information provided */
    else {
      $result = $this->add( $settings );
    }

    return $result;
  }

  /*****************************************
   *%FUNCTION: removeFromTable()
   *%DESCRIPTION:
   * Used to remove a particular entry from
   * the table of another class. All corresponding
   * entries in the other table will be set
   * to the 'unknown' name and ID.
   *%ARGUMENTS:
   * table -- The MySQL table corresponding to
   * the other class.
   * id -- The ID value to be removed.
   * [field] -- The field name in the other table.
   * If not provided the current child class 
   * name is used.
   *%RETURNS:
   * The result of the UPDATE query.
   */
  public function removeFromTable( $table, $id, $field = '' ) {
    if ( $field == '' ) {
      $field = $this->name();
    }
    
    $unknownId = $this->unknownId();
    $query = "UPDATE ${table} ";
    $query .= "SET `${field}` = ${unknownId} ";
    $query .= "WHERE `${field}` = ${id}";
    return $this->query( $query );
  }
  
  /*****************************************
   *%FUNCTION: delete()
   *%DESCRIPTION:
   * Used to remove a particular entry from
   * the table corresponding to the current child
   * class.
   *%ARGUMENTS:
   * id -- The ID or name value to be removed.
   *%RETURNS:
   * Always returns TRUE.
   */
  public function delete( $id ) {
    if ( $id == '' && !$this->id( $id ) ) {
      return false;
    }
    
    $table = $this->table();
    $query = "DELETE FROM ${table} WHERE " . $this->match( $id );
    $this->query( $query );
    
    return true;
  } 

  /********************************************************** 
   * MySQL Data Queries
   * 
   * The following commands are used to extract information
   * from the table.
   **********************************************************/

  public function processKeys( &$settings ) {
    $settings[$this->name()] = '';
    $settings['name'] = '';
    $settings['delete'] = false;
  }

  public function variantMerge( $tables ) {
    $table = '';
    foreach ( array_keys( $tables ) as $name ) {
      if ( $table != "" ) {
	$table .= " UNION ";
      }
      $table .= sprintf( "( %s ) ", $tables[$name] );
    }
    $query = "SELECT * FROM ";
    $query .= $this->quoteTable( $table, 'names' );
    $query .= " ORDER BY `id`";
    return $query;
  }

  /**********************************************************
   *%FUNCTION: variants()
   *%DESCRIPTION: 
   * Used to produce the query that will return a full set of
   * 'id' and 'name' values including all variants.
   *%ARGUMENTS: 
   * None.
   *%RETURNS: 
   * The resulting SQL code for a query.
   */
  public function variants() {
    return $this->table();
  }

  /**********************************************************
   *%FUNCTION: listing()
   *%DESCRIPTION: 
   * Used to produce the query that will return a listing of
   * all 'id' and 'name' values based on the settings provided.
   *%ARGUMENTS: 
   * settings -- The settings to alter the way the table is
   * constructed.
   *%RETURNS: 
   * The resulting SQL code for a query.
   */
  public function listing( &$settings = array(), $name = 'listing' ) {   
    return "SELECT * FROM " . $this->quoteTable( $this->nameAndId( '*', $settings ), $name );
  }
  
  /**********************************************************
   *%FUNCTION: nameAndId()
   *%DESCRIPTION: 
   * Used to produce the query that will return a listing
   * of 'id' and 'name' values.
   *%ARGUMENTS: 
   * [settings] -- The settings to alter the way the table is
   * constructed.
   * [name] -- The field or custom function for generating
   * the corresonding name.
   *%RETURNS: 
   * The resulting SQL code for a query.
   */
  public function nameAndId( $fields = '*', 
			     &$settings = array(),
			     $name = false ) {
    $nickname = ( isset( $settings['nickname'] ) ) ? $settings['nickname'] : false;
    unset( $settings['nickname'] );

    $table = $this->table( $settings );

    $columns = ( $fields == '*' ) ? $this->columns( false ) : $this->columns( false, $fields );
    $columns['id'] = $this->idField();   
    $columns['name'] = true;
      
    if ( is_string( $name ) ) {
      $columns['name'] = $name;
    } else if ( is_array( $name ) ) {
      $columns['name'] = call_user_func_apply( $name );
    }
    $query = "SELECT ";
    $query .= $this->selectColumns( $columns );    
    $query .= " FROM " . $this->quoteTable( $table, 'names' );
    return $query;
  } 

  /*****************************************
   *%FUNCTION: namesById()
   *%DESCRIPTION:
   * Used to retrieve all the names from the
   * table and index them by the ID value.
   *%ARGUMENTS:
   * None.
   *%RETURNS:
   * The array of names indexed by ID.
   */
  public function namesById( &$settings = array() ) {  
    $fields = array( 'name', 'id' );
    $query = $this->nameAndId( $fields, $settings );       
    $result = $this->query( $query );
    $results = array();
    while( $row = mysql_fetch_assoc( $result ) ) {
      $results[$row['id']] = $row['name'];      
    }
    return $results;
  }

  /**********************************************************
   *%FUNCTION: derive()
   *%DESCRIPTION: 
   * Used to produce the SQL code that will result in the
   * desired field value.
   *%ARGUMENTS: 
   * field
   * settings -- The settings to alter the way the table is
   * constructed.
   *%RETURNS: 
   * The resulting SQL code for a query.
   */
  public function derive( $field, &$settings = array() ) {
    switch ($field) {    
    case 'display_name':
      $sql = sprintf( 'IF( %1$s != \'\', %1$s, %2$s )',
		      $this->derive( 'nickname', $settings ),
		      $this->derive( 'name', $settings ) );
      break;
    default:
      $sql = ( isset( $settings[$field] ) ) ? $settings[$field] : $field;
	if ( !$this->isComplex( $sql ) ) {    
	  $sql = preg_replace( '/(\w+)$/', '`\\1`', $sql ); 
	}
    }
    return $sql;
  }
  
  public static function isComplex( $table ) {
    return ( preg_match( '/ /', $table ) > 0 );
  }
  
  public function quoteTable( $table, $name = false ) {
    if ( Finance_model::isComplex( $table ) ) {
      $name = ( $name !== false ) ? $name : $this->name();
      return "( $table ) $name";
    } 
    return $table;
  }
  
  /**********************************************************
   *%FUNCTION: columns()
   *%DESCRIPTION: 
   * Used to collect the names of each field in the current
   * object.
   *%ARGUMENTS: 
   * id -- Whether (1) or not (0) to include the ID field.
   *%RETURNS: 
   * The resulting array of field names.
   */  
  public function columns( $id = true, $fields = false ) {    
    $fields = ( $fields !== false && $fields != '*' ) ? $fields : $this->fields( $id );
    $mapping = array();
    foreach ( $fields as $field ) {
      $mapping[$field] = $field;
    }    
    return $mapping;
  }

  /**********************************************************
   *%FUNCTION: fields()
   *%DESCRIPTION: 
   * Used to collect the names of each field in the current object
   * and to optionally exclude the _id field.
   *%ARGUMENTS: 
   * id -- Whether (1) or not (0) to include the ID field.
   *%RETURNS: 
   * The resulting array of column names.
   */
  public function fields( $id = false ) {
    $table = $this->table();
    $query = "SELECT `COLUMN_NAME` AS 'field' FROM INFORMATION_SCHEMA.COLUMNS WHERE `TABLE_NAME` = '${table}'";
    
    $result = $this->query( $query );
    $fields = array();
    $idField = $this->idField();
    while( $row = mysql_fetch_assoc( $result ) ) {
      if ( $id !== true && $row['field'] == $idField ) {
	continue;
      }
      array_push( $fields, $row['field'] );
    }
    
    return $fields;
  }

  /**********************************************************
   *%FUNCTION: isWord()
   *%DESCRIPTION: 
   * Used to test whether a given name is a word or not.
   *%ARGUMENTS: 
   * name -- The string to test.
   *%RETURNS: 
   * TRUE if the given value is a word, FALSE otherwise.
   */
  private static function isWord( $name ) {
    if (is_numeric( $name ) ) {
      return false;
    }
    return preg_match( '/^\w+$/', $name );
  }
  


  public function selectColumns( $columns ) {
    if ( sizeof( $columns ) == 0 ) {
      return '*';
    }

    $statements = array();
    foreach ( array_keys( $columns ) as $column ) {
      if ( $columns[$column] == $column ||
	   $columns[$column] === true ) {
	array_push( $statements, 
		    $this->toName( $column ) );
      } else {
	$source = $columns[$column];
	if ( Finance_model::isWord( $source ) ) {
	  $source = $this->toName( $source );
	}
	array_push( $statements,
		    sprintf( "%s AS %s",
			     $source,
			     $this->toName( $column ) ) );
      }
    }
    return implode( ', ', $statements );
  }

  public static function prefixName( $field, $name = '' ) {
    if ( $name == '' ) {
      return $field;
    }
    return "$name." . Database::toName( $field );
  }

  public static function prefixColumns( &$columns, $name = '' ) {
    if ( $name == '' ) {
      return;
    }
    
    foreach ( array_keys( $columns ) as $column ) {
      $source = $columns[$column];
      if ( Finance_model::isWord( $source ) ) {
	$columns[$column] = Finance_model::prefixName( $source, $name );
      }
    }
  }

  public static function simplifyColumns( &$columns ) {
    foreach ( array_keys( $columns ) as $column ) {
      $columns[$column] = $column;
    }
  } 
  
  public function mergeWith( $other, &$columns = array(), $table = '' ) {    
    $name = $this->name();
    if ( $table == '' ) {
      $table = $this->table();
    }

    if ( $other == $this ) {
      $name = 'ZZ';
    }

    $table = $this->quoteTable( $table );

    $otherTable = $other->table();    
    $otherIdField = $other->idField();
    $otherName = $other->name();
    $otherName = $other->name();

    Finance_model::prefixColumns( $columns, $name );

    $sql = "SELECT ";
    $sql .= $this->selectColumns( $columns );    
    $sql .= " FROM ${table} AS $name ";
    $sql .= "LEFT JOIN ${otherTable} AS $otherName ON ( ${otherName}.${otherIdField} = ${name}.${otherName} ) ";
    $sql .= "WHERE 1";
    
    Finance_model::simplifyColumns( $columns );

    return $sql;
  }

  /********************************************************** 
   * Utility Functions
   * 
   * The following commands are used to help
   * the child classes manipulate information.
   **********************************************************/

  public static function isBlackberry() {
    if ( isset( $_SERVER['HTTP_USER_AGENT'] ) &&
	 preg_match( '/Blackberry/i', $_SERVER['HTTP_USER_AGENT'] ) ) {
      return true;
    }
    return false;
  }
  
  public static function style( $name = 'font_size' ) {
    $blackberry = Finance_model::isBlackberry();
    switch ($name) {
    case 'font_size':
      return ( $blackberry === false ) ? 12 : 11;
      break;
    case 'product/width':
      return ( $blackberry === false ) ? 150 : 60;
      break;
    case 'product/option/width':
      return ( $blackberry === false ) ? 400 : 250;
      break;
    case 'tax/width':
      return ( $blackberry === false ) ? 50 : 20;
      break;
    default:
      break;
    } 

    return '';
  }

  public static function js_array( $values, $name ) {
    $code = '';
    $keys = array_keys( $values );
    sort( $keys );
    foreach( $keys as $key ) {
      $code .= "${name}['${key}'] = '$values[$key]';\n";
    }
    return $code;
  }   

  /*****************************************
   *%FUNCTION: expand()
   *%DESCRIPTION:
   * Used to pad an array of values based on the 
   * desired size. The extra values are all set to ''.
   *%ARGUMENTS:
   * values -- The array of values to modify by reference.
   * size -- The desired size of the values array.
   *%RETURNS:
   * Nothing.
   */
  public static function expand( &$values, $size ) {
    $length = sizeof($values);
    $diff = $size - $length;
    if ( $diff > 0 ) {
      $values = array_merge( $values, array_fill( 0, $diff, '' ) );
    }
  } 
  
  public function toFieldName( $name, $extra = '' ) {
    $name = preg_replace( '/ /', '_', $name );
    if ( is_array( $extra ) ) {
      $extra = implode( ',', $extra );
    }
    if ( $extra != '' ) {
      $name .= '/'. $extra;
    }
    return $name;
  }

  public function fromFieldName( &$name, &$extra = array() ) {
    $info = explode( '/', $name );
    if( sizeof( $info ) > 1 ) {
      $name = $info[0];
      $extra = explode( ',', $info[1] );
    }
    
    $name = preg_replace( '/_/', ' ', $name );
  }

  public function randomString( $length ) {
    $string = md5( uniqid( mt_rand(), true ) );
    return strtoupper( substr( $string, 0, $length ) );
  }

  /**********************************************************
   *%FUNCTION: createCode()
   *%DESCRIPTION: 
   * Used to create a new code (name) to be used
   * for the current class. The new code should be the maximum 
   * number of characters and should not already exist in the
   * table corresponding to the current class.
   *%ARGUMENTS: 
   * None
   *%RETURNS: 
   * The generated unique code to be used as a name
   * for the current class.
   */
  public function createCode( $length = 0 ) {
    $table = $this->table();
    
    while( 1 ) {
      $code = $this->randomString( $this->nameLength() );
      
      /* Check if the code/name is already part of the table
       * (not likely) */
      $query = "SELECT * FROM ${table} WHERE `name` = '${code}'";
      $result = $this->query( $query );
      if ( !mysql_fetch_assoc( $result ) ) {
	return $code;
      }
    }
  }
  
  /**********************************************************
   *%FUNCTION: filter()
   *%DESCRIPTION: 
   * Used to filter the results that correspond to the 
   * given input using string matching.
   *%ARGUMENTS: 
   * input -- The input string to compare with.
   * values -- The set of values to compare against.
   * settings -- Additional settings to be passed in.
   *%RETURNS: 
   * The set of values that correspond to the given input.
   */
  public function filter( $input, &$values = false, &$settings = array() ) {
    $values = ( is_array( $values ) ) ? $values : $this->namesById();
    return Finance_model::filterMatchValues( $input, $values, true );
  }
  
  /**********************************************************
   *%FUNCTION: highlight()
   *%DESCRIPTION: 
   * Used to format strings for highlighting in the GUI
   *%ARGUMENTS: 
   * string -- The string to filter.
   *%RETURNS: 
   * The formatted string using HTML tags.
   */
  protected function highlight( $string ) {
    return trim( HTML::wrap( 'b', $string ) );
    return trim( HTML::font( $string, array( 'color' => "#AABBAA" ) ) );
    return trim( HTML::span( $string, array( 'style' => 'background: #AABBAA' ) ) );
  }
  
  /**********************************************************
   *%FUNCTION: filterOrder()
   *%DESCRIPTION: 
   * Used to determine the order of a given set of values  
   *%ARGUMENTS: 
   * values -- The set of values to analyze.
   * useId -- Whether (1) to not (0) to consider the numeric
   * indexes of the values.
   * useKeys -- Whether (1) or not (0) the keys of an associated
   * array are being retured (modified by reference).
   *%RETURNS: 
   * The values to be considered in order.
   */
  protected function filterOrder( $values, $useId = true, &$useKey = false ) {
    if ( isset( $values['_order'] ) ) {
      $useKey = true;
      return $values['_order'];
    } else if ( $useId ) {
      $useKey = true;
      return array_keys( $values );
    }   
    return $values;
  }
  
  /**********************************************************
   *%FUNCTION: filterMatch()
   *%DESCRIPTION: 
   * Used to compare a given input to a value and if a match
   * is successful to create the formated string that should
   * be displayed.
   *%ARGUMENTS: 
   * input -- The input string.
   * value -- The value to compare to.
   * formatted -- The resulting formatted string if a match
   * is successful.
   *%RETURNS: 
   * TRUE if a match is successful, FALSE otherwise.
   */
  protected function filterMatch( $input, $value, &$option ) {
    if ( $input == '' ) {
      $option = $value;
      return true;
    } else if ( preg_match( "/(.*)(${input})(.*)/i", $value, $match ) ) {
      $option = $match[1] . Finance_model::highlight( $match[2] ) . $match[3];       
      return true;
    }
    return false;
  }  
  
  /**********************************************************
   *%FUNCTION: filterMatchValues()
   *%DESCRIPTION: 
   * Used to compara a given input to a set of values and 
   * to collect all those where a match is successful.
   *%ARGUMENTS: 
   * input -- The input string.
   * values -- The values to compare to.
   * useId -- Whether (1) or not (0) the numeric IDs of the
   * value should be recorded.
   * extra -- An associative array of additional keyword and
   * functions for generating values.   
   *%RETURNS: 
   * An array of all matching values.
   */
  protected function filterMatchValues( $input, &$values, $useId = true,
					&$extra = array() ) {
    $results = array();
    $pattern = "/(.*)(${input})(.*)/i";    
    $useKey = false;
    foreach ( $this->filterOrder( $values, $useId, $useKey ) as $key ) {
      $name = ( $useKey === true ) ? $values[$key] : $key;
      if ( $this->filterMatch( $input, $name, $option ) ) {
	$item = array( 'label' => $name,
		       'option' => $option,
		       'type' => 'match' );
	if ( $useId ) {
	  $item['id'] = $key;
	}
	
	foreach ( array_keys( $extra ) as $extraKey ) {
	  $item[$extraKey] = call_user_func( $extra[$extraKey], $item );
	}
	
	array_push( $results, $item );
      }
    }
    
    return $results;
  }

  /**********************************************************
   *%FUNCTION: today()
   *%DESCRIPTION: 
   * Returns the date of today in MySQL DATE format.
   *%ARGUMENTS: 
   * None
   *%RETURNS: 
   * The MySQL DATE value for today.
   */
  public static function today() {
    $info = getdate();
    return sprintf( "%04d/%02d/%02d", $info['year'], $info['mon'], $info['mday'] );
  }

  /**********************************************************
   *%FUNCTION: now()
   *%DESCRIPTION: 
   * Returns the date and time of now in MySQL DATE format.
   *%ARGUMENTS: 
   * None
   *%RETURNS: 
   * The MySQL DATE value for now.
   */ 
  public static function now() {
    $info = getdate();    
    return sprintf( "%04d/%02d/%02d %02d:%02d:%02d", $info['year'], $info['mon'], $info['mday'], $info['hours'], $info['minutes'], $info['seconds'] );
  }



}

?>
