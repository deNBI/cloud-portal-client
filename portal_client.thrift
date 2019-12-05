namespace	py VirtualMachineService



typedef i32 int
/** The Version of the Portal-Client*/
const string VERSION= '1.0.0'


struct Backend {
    1: i64 id,
    2: string owner,
    3: string location_url,
    4: string template,
    5: string template_version
}

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

	/** List of tags from flavor */
	7: required list<string> tags
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

    /** List of tags from image */
	9: required list<string> tag

	/** If the Image is a snapshot*/
	10:optional bool is_snapshot
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

    /** Diskspace in GB from additional volume*/
	12:optional int diskspace

    /** Id of additional volume */
	13:optional string volume_id
}

/**
 * This Struct defines the result of a playbook run.
 */
struct PlaybookResult {
    /**The exit status code of the run*/
    1: required int status
    /**The standard logs of the run*/
    2: required string stdout
    /**The error logs of the run*/
    3: required string stderr
}

exception otherException {
    /** Every other exception. */
    1: string Reason
}
exception ressourceException {
    /** Name already used. */
    1: string Reason
}

exception nameException {
    /**@ Name already used. */
    1: string Reason
}

exception serverNotFoundException {
    /** Server not found. */
    1: string Reason
}

exception networkNotFoundException{
    /** Network not found. */
    1: string Reason
}

exception imageNotFoundException {
    /** Image not found. */
    1: string Reason
}

exception flavorNotFoundException {
    /* Flavor not found*/
    1: string Reason
}


/** Authentication Failed Exception*/
exception authenticationException {
    /** Reason why the Authentication failed*/
    1: string Reason
}

/**
 * This VirtualMachiine service deploys methods for creating,deleting,stopping etc. VirtualMachines in Openstack.
 */
service VirtualMachineService {


    bool check_Version(1:double version)

    /**
     * Get Client version.
     * Returns Version of the client
     */
    string get_client_version()

    /**
     * Import Key to openstack.
     * Returns : keypair
     */
    string import_keypair(

    /** Name for the keypair */
    1:string keyname,

    /** The public key */
    2:string public_key)

    /**
     * Get Ip and Port of server
     * Returns:  {'IP': ip, 'PORT': port,'UDP':udp}
     */
    map<string,string> get_ip_ports(

    /** Id of server */
    1: string openstack_id)


	 /**
	 * Get Flavors.
	 * Returns: List of flavor instances.
	 */
	list<Flavor> get_Flavors()


	/**
	 * Get Images.
	 * Returns: List of Image instances.
	 */
	list<Image> get_Images()

	/**
	 * Get an image with tag.
	 * Returns: Image with tag.
	 */
	Image get_Image_with_Tag(1:string openstack_id)


	 /**
	  * Delete server.
	  * Returns: True if deleted, False if not
	  */
	bool delete_server(

	/** Id of the server. */
	1:string openstack_id)

	throws (1:serverNotFoundException e)


	map<string,string> add_metadata_to_server(1:string servername,2:map<string,string> metadata) throws (1:serverNotFoundException e)


	set<string> delete_metadata_from_server(1:string servername,2:set<string> keys) throws (1:serverNotFoundException e)

	/**
	 * Add floating ip to server.
	 * Returns: the floating ip
	 */
	string add_floating_ip_to_server(

	/** Id of the server */
	1:string openstack_id,

	/** Network name of the network which provides the floating Ip.*/
	2:string network) throws (1:serverNotFoundException e, 2:networkNotFoundException f)


	/**
	 * Create connection to OpenStack.
	 * Connection instance
	 */
	bool create_connection(

	/** Name of the OpenStack user. */
	1:string username,

	/** Password of the OpenStack user */
	2:string password ,

	/** Auth Url from OpenStack*/
	3:string auth_url,

	/** Name of the project from the OpenStack user.
	4:string project_name,

	/** Domain name of OpenStack*/
	5:string user_domain_name,

	/** Project domain name of OpenStack*/
	6:string project_domain_name )

	throws (1:authenticationException e),


	/**
	 * Start a new server.
	 */
    map<string,string> start_server(

    /** Name of the  Flavor to use.*/
    1:string flavor,

    /** Name of the image to use. */
    2:string image,

    /** Public Key to use*/
    3:string public_key,

    /** Name for the new server */
    4:string servername,

    /** Metadata for the new instance*/
    5:map<string,string> metadata,

    /** Diskspace in GB for additional volume.*/
    6:string diskspace,

    /** Name of additional Volume*/
    7:string volumename, 8:bool https,9:bool http)

    throws (1:nameException e,2:ressourceException r,3:serverNotFoundException s,4: networkNotFoundException n,5:imageNotFoundException i,6:flavorNotFoundException f,7:otherException o)


    /**
	 * Start a new server with custom key for ansible.
	 */
    map<string,string> start_server_with_custom_key(

    /** Name of the  Flavor to use.*/
    1:string flavor,

    /** Name of the image to use. */
    2:string image,

    /** Name for the new server */
    3:string servername,

    /** Metadata for the new instance*/
    4:map<string,string> metadata,

    /** Diskspace in GB for additional volume.*/
    5:string diskspace,

    /** Name of additional Volume*/
    6:string volumename,

    /** Boolean for http security rule*/
    7:bool http,

    /** Boolean for https security rule*/
    8:bool https)

    throws (1:nameException e,2:ressourceException r,3:serverNotFoundException s,4: networkNotFoundException n,5:imageNotFoundException i,6:flavorNotFoundException f,7:otherException o)

    /** Check if there is an instance with name */
    bool exist_server(
    1:string name
    )

    /** Create and deploy an anaconda ansible playbook*/
    int create_and_deploy_playbook(
    1:string public_key,
    2:map<string, map<string,string>> playbooks_information
    3:string openstack_id
    )

    /** Get the logs from a playbook run*/
    PlaybookResult get_playbook_logs(
    1:string openstack_id
    )


    /** Get boolean if client has backend url configured*/
    bool has_forc()

    /** Create a backend*/
    Backend create_backend(
    1:string elixir_id,
    2:string user_key_url,
    3:string template,
    4:string template_version,
    5:string upstream_url
    )

    /** Get all backends*/
    list<Backend> get_backends()

    /** Get all backends by owner*/
    list<Backend> get_backends_by_owner(
    1:string elixir_id
    )

    /** Get all backends by template*/
    list<Backend> get_backends_by_template(
    1:string template
    )

    /** Get a backend by id*/
    Backend get_backend_by_id(
    1:i64 id
    )

    /** Delete a backend*/
    string delete_backend(
    1:i64 id
    )

    list<map<string, string>> get_templates()

    list<map<string, string>> get_templates_by_template(
    1:string template_name
    )

    map<string, string> check_template(
    1:string template_name
    2:string template_version
    )


    /**
    * Adds a security group to a server
    */
    bool add_security_group_to_server(
    /** If http ports are open*/
    1:bool http,

    /** If https ports are open*/
    2:bool https,

    /** If udp ports are open*/
    3:bool udp,

    /** OpenStack id of the server*/
    4:string server_id)

    throws (1:ressourceException r,2:serverNotFoundException s

    )


    /**
	 * Get all servers.
	 * Returns: List of server instances.
	 */
	list<VM> get_servers(),

	/**
	* Get list of servers by ids
**/
	list<VM> get_servers_by_ids(1:list<string> server_ids)


	/**
	 * Get a Server.
	 * Returns: A server instance.
	 */
	VM get_server(

	/** Id of the server.*/
	1:string openstack_id)

	 throws (1:serverNotFoundException e),


	/**
	 * Stop a Server.
	 * Returns: True if stopped, False if not.
	 */
    bool stop_server(

    /** Id of the server.*/
    1:string openstack_id)

    throws (1:serverNotFoundException e)


    /**
     * Create Snapshot.
     * Returns: Id of new Snapshot
     *
     */
    string create_snapshot(
    /** Id of the server */
    1:string openstack_id,

     /** Name of new Snapshot */
     2:string name,

     /** Elixir-Id of the user who requested creation of Snapshot */
     3: string elixir_id,

     /** Tag with which the servers image is also tagged ( for connection information at the webapp) */
     4:string base_tag,
     /** Description of the new snapshot*/
     5:string description)

     throws (1:serverNotFoundException e),


    /**
     * Get Limits of OpenStack Projekt from client.
     * Returns: {'maxTotalVolumes': maxTotalVolumes, 'maxTotalVolumeGigabytes': maxTotalVolumeGigabytes,
     *           'maxTotalInstances': maxTotalInstances, 'totalRamUsed': totalRamUsed,
     *          'totalInstancesUsed': totalInstancesUsed}
     */
    map<string,string> get_limits()

    /**
     * Delete Image.
     * Return: True if deleted, False if not
     */
    bool delete_image(
    /** Id of image */
    1:string image_id) throws (

    1:imageNotFoundException e)


    /**
     * Delete volume attachment
     * Return: True if deleted, False if not
     */
    bool delete_volume_attachment(
    /** Id of the attached volume */
    1:string volume_id,

    /** Id of the server where the volume is attached */
    2:string server_id)

    throws (1:serverNotFoundException e),


    /**
     * Delete volume.
     * Returns:  True if deleted, False if not
     */
    bool delete_volume(1:string volume_id)

    /**
     * Attach volume to server.
     * Returns:  True if attached, False if not
     */
    bool attach_volume_to_server(
    /** Id of server*/
    1:string openstack_id,

    /** Id of volume*/
    2:string volume_id)

    throws (1:serverNotFoundException e),


    /**
     * Check status of server.
     * Returns: server instance
     */
    VM check_server_status(
    /** Id of the server */
    1:string openstack_id,

    /** diskspace of server(volume will be attached if server is active and diskpace >0) */
    2:int diskspace,

    /** Id of the volume */
    3:string volume_id)

    throws (1:serverNotFoundException e,2:ressourceException r),


    /**
     * Set Password of a User
     * Returns: the new password
     */
    string setUserPassword(
    /** Elixir-Id of the user which wants to set a password */
    1:string user,

    /** New password */
    2:string password)

    throws (1:otherException e),


    /**
     * Resume Server.
     * Returns: True if resumed False if not
     */
    bool resume_server(
    /** Id of the server */
    1:string openstack_id)

    throws (1:serverNotFoundException e)


    /**
     * Create volume.
     * Returns: Id of new volume
     */
    string create_volume(

    /**  Name of volume*/
    1:string volume_name,

    /** Diskspace in GB for new volume */
    2:int diskspace,

     /** Metadata for the new volume*/
    3:map<string,string> metadata)

    throws (1:ressourceException r)


    /**
     * Reboot server.
     * Returns: True if rebooted False if not
     */
    bool reboot_server(

    /** Id of the server*/
    1:string server_id,

    /** HARD or SOFT*/
    2:string reboot_type)

    throws (1:serverNotFoundException e)

}
