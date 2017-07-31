<?php

class Category extends CI_Controller {  
    function __construct() {
        parent::__construct();
    }

    function index() 
    {
        $this->load->model( "category_model" );
        $data = array( 'tree' => $this->category_model->tree(),
                       'all_info' => $this->category_model->all(),
                       'url' => base_url(),
                       'edit' => true );
        echo "A";
        $this->load->view( "category_table", $data);
        echo "B";
    }   
}
