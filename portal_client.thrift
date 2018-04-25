namespace	py VirtualMachineService



typedef i32 int
/** The Version of the Portal-Client*/
const double VERSION=1.0




/**
 * This Struct defines a Flavor.
 */
 struct Flavor{
	/** The vcpus of the flavor*/
	1:required i32 vcpus,

	/** The ram of the flavor*/
	2:required i32 ram,

	/** The disk of the flavor*/
	3:required i32 disk,

	/** The name of the flavor*/
	4:required string name

	/** The openstack_id of the flavor*/
	5:required string openstack_id

	/** The description of the flavor*/
	6:optional string description
	
	
}
/**
 * This Struct defines an Image.
 */
struct Image{	
	
	/** The name of the image*/
	1:required string name

	/** The min_diks of the image*/
	2:required i32 min_disk

	/** The min_ram of the image*/
	3:required i32 min_ram

	/** The status of the image*/
	4:required string status

	/** The creation time of the image*/
	5:optional string created_at

	/** The updated time of the image*/
	6:optional string updated_at

	/** The openstack_id the image*/
	7:required string openstack_id

	/** The description of the image*/
	8:optional string description

	/** The defaut_user of the image*/
	9:optional string default_user
}
/**
 * This Struct defines a VirtualMachine.
 */
struct VM {
   
    	/** The flavor of the VM*/
    1: required Flavor flav,

	/** The image of the VM*/
	2: required Image img,

	/** The status of the VM*/
	3: required string status

	/** The metadata of the VM*/
	4: optional map<string,string> metadata

	/** The project_id of the VM*/
	5: optional string project_id

	/** The keyname from the public key of the VM*/
	6: required string keyname

	/** The openstack_id of the VM*/
	7: required string openstack_id

	/** The name of the VM*/
	8: required string name

	/** The the creation time of the VM*/
	9: required string created_at

	/** The floating ip of the VM*/
	10: optional string floating_ip

	/** The fixed ips of the VM*/
	11: required string fixed_ip

	
}


/**
 * Exceptions inherit from language-specific base exceptions.
 */
exception otherException {
    /**@ Name already used. */
    1: string Reason
}
exception ressourceException {
    /**@ Name already used. */
    1: string Reason
}

exception nameException {
    /**@ Name already used. */
    1: string Reason
}

exception serverNotFoundException {
    /**@ Server not found. */
    1: string Reason
}

exception networkNotFoundException{
    /**@ Network not found. */
    1: string Reason
}

exception imageNotFoundException {
    /**@ Image not found. */
    1: string Reason
}

exception flavorNotFoundException {
    /**@ flavor not found. */
    1: string Reason
}



exception authenticationException {
    /**@ Authentication failed */
    1: string Reason
}

/**
 *
 * This VirtualMachiine service deploys methods for creating,deleting,stopping etc. VirtualMachines in Openstack.
 */
service VirtualMachineService {
     /**
     * This Method  compares the version of the Portal-Client with the Version of the Client from the Cloud-Portal-Client-Connector. 
     *
     * param: version The Version of the Client from the Connector
     **/
    bool check_Version(1:double version)
    /**
     * This Method  imports a new keypair.
     * @param version 
     */
    string import_keypair(1:string keyname,2:string public_key)

    string checkServerStatus(1: string servername)
    /**@
     * This Method generates a String the user can use to login in in the instance
     */
    string generate_SSH_Login_String(1: string servername)
	 /**@
     * This Method returns a list with all Flavors.
     */
	list<Flavor> get_Flavors()
	 /**@
     * This Method returns a list with all Images.
     */
	list<Image> get_Images()
	 /**@
     * This Method deletes a server.
     */
	bool delete_server(1:string openstack_id) throws (1:serverNotFoundException e)
	 /**@
     * This Method adds Metadata to a Server
     */
	map<string,string> add_metadata_to_server(1:string servername,2:map<string,string> metadata) throws (1:serverNotFoundException e)
	 /**@
     * This Method deletey Metadata from a server.
     */
	set<string> delete_metadata_from_server(1:string servername,2:set<string> keys) throws (1:serverNotFoundException e)
	 /**@
     * This Method adds a floating IP to a Server.
     */
	string add_floating_ip_to_server(1:string servername,2:string network) throws (1:serverNotFoundException e, 2:networkNotFoundException f)
	 /**@
     * This Method creates a connection to the openstack API.
     */
	bool create_connection(1:string username,2:string password ,3:string auth_url,4:string project_name,5:string user_domain_name,6:string project_domain_name ) throws (1:authenticationException e),
	 /**
     * This Method starts a VirtualMachine .
     */
    string start_server(1:string flavor, 2:string image,3:string public_key,4:string servername,5:string elixir_id) throws (1:nameException e,2:ressourceException r,3:serverNotFoundException s,4: networkNotFoundException n,5:imageNotFoundException i,6:flavorNotFoundException f,7:otherException oe),
	/**
	*This Method returns a VirtualMachine with a specific Name.
	*/
	VM get_server(1:string servername) throws (1:serverNotFoundException e),
	/**
     * This Method stops a VirtualMachine with a specific Openstack-ID.
     */
    bool stop_server(1:string openstack_id) throws (1:serverNotFoundException e),
						  /**@
     * This Method unpause a VirtualMachine with a specific Openstack-ID.
     */
    bool resume_server(1:string openstack_id) throws (1:serverNotFoundException e),
}
