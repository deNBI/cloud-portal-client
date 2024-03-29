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

struct ClusterInfo {
1:optional string launch_date,
2:optional string group_id,
3:optional string network_id,
4:optional string public_ip,
5:optional string subnet_id,
6:optional string user,
7:optional int inst_counter,
8:optional string cluster_id,
9:optional string key_name,
10:optional string pub_key,
}

struct Volume{
1:optional string id,
2:optional string name,
3:optional string description,
4:optional string status,
5:optional string created_at,
6:optional string device,
7:optional int size,
8:optional string server_id
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

	/** The ephemeral disk space of the flavor*/
	8:optional i32 ephemeral_disk
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

	11:optional string os_version
		12:optional string os_distro
		13:optional string slurm_version

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

struct ClusterInstance{

1: required string type
2: required string image
3: optional int count
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

/** Conflict with request (e.g. while vm is in create image task)*/
exception conflictException {
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
	 * Gets the gateway ip.
	 */
    map<string,string> get_gateway_ip()



    map<string,string>  get_calculation_formulars()

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
    map<string,string> get_vm_ports(

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
	 * Get Images.
	 * Returns: List of public Image instances.
	 */
	list<Image> get_public_Images()

    /**
	 * Get Images.
	 * Returns: List of private Image instances.
	 */
	list<Image> get_private_Images()

	/**
	 * Get an image with tag.
	 * Returns: Image with tag.
	 */
	Image get_Image_with_Tag(1:string openstack_id)

	/**
    * Get Images and filter by list of strings.
    * Returns: List of Image instances.
    */
	list<Image> get_Images_by_filter(1: map<string, string> filter_json)


	Volume get_volume(
	1:string volume_id
	)

	list<Volume> get_volumes_by_ids(
	1:list<string> volume_ids
	)

	int resize_volume(1:string volume_id,2:int size)



	 /**
	  * Delete server.
	  * Returns: True if deleted, False if not
	  */
	bool delete_server(

	/** Id of the server. */
	1:string openstack_id)

	throws (1:serverNotFoundException e, 2: conflictException c)


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

	map<string,string> start_server_without_playbook(
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


    6:bool https,
    7:bool http,
    8:list<string> resenv,
     9:list<map<string,string>> volume_ids_path_new,
     10:list<map<string,string>> volume_ids_path_attach,
     11:list <string> additional_keys
)

    throws (1:nameException e,2:ressourceException r,3:serverNotFoundException s,4: networkNotFoundException n,5:imageNotFoundException i,6:flavorNotFoundException f,7:otherException o)

    bool bibigrid_available()
    bool detach_ip_from_server(1:string server_id,2:string floating_ip)

	map<string,string> start_server_with_mounted_volume(
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


    6:bool https,
    7:bool http,
    8:list<string> resenv,
     9:list<map<string,string>> volume_ids_path_new,
     10:list<map<string,string>> volume_ids_path_attach
)


    throws (1:nameException e,2:ressourceException r,3:serverNotFoundException s,4: networkNotFoundException n,5:imageNotFoundException i,6:flavorNotFoundException f,7:otherException o)





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
    7:string volumename,
    8:bool https,
    9:bool http,
    10:list<string> resenv)


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

    /** Boolean for http security rule*/
    5:bool http,

    /** Boolean for https security rule*/
    6:bool https,

    7:list<string> resenv,
    9:list<map<string,string>> volume_ids_path_new,
     10:list<map<string,string>> volume_ids_path_attach)


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

    string get_forc_url()

    /** Create a backend*/
    Backend create_backend(
    1:string elixir_id,
    2:string user_key_url,
    3:string template,
    4:string upstream_url
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

    /** Add a user to a backend*/
    map<string,string> add_user_to_backend(
    1:i64 backend_id,
    2:string user_id
    )

    /** Get users from a backend*/
    list<string> get_users_from_backend(
    1:i64 backend_id
    )

    /** Delete user from a backend*/
    map<string,string> delete_user_from_backend(
    1:i64 backend_id,
    2:string user_id
    )

    list<map<string, string>> get_templates()

    list<string> get_allowed_templates()

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
    bool add_udp_security_group(
    /** OpenStack id of the server*/
    1:string server_id)

    throws (1:ressourceException r,2:serverNotFoundException s

    )


    /**
	 * Get all servers.
	 * Returns: List of server instances.
	 */
	list<VM> get_servers(),

	/**
	* Get all server ids.
	* Returns: List of server ids.
    */
	list<string> get_server_openstack_ids(
	    1: string filter_tag
	),

	/**
	* Get list of servers by ids
    **/
	list<VM> get_servers_by_ids(1:list<string> server_ids)

	string check_server_task_state(1: string openstack_id)

	/**
	* Get servers by bibigrid cluster id.
    **/
	list<VM> get_servers_by_bibigrid_id(1:string bibigrid_id)




    void add_server_metadata(1:string server_id,2: map<string,string> metadata) 	 throws (1:serverNotFoundException e),
    void create_resenv_security_group_and_attach_to_server(1:string server_id,2:string resenv_template) throws (1:serverNotFoundException e),

    string add_cluster_machine(
        1:string cluster_id,
        2:string cluster_user,
        3:string cluster_group_id,
        4:string image,
        5:string flavor,
        6:string name,
        7:string key_name,
        8:int batch_idx,
        9:int worker_idx,
        10:string pub_key
        11: string project_name,
        12: string project_id,
        13:string slurm_version
    )

	ClusterInfo get_cluster_info(1:string cluster_id)

	map<string,string>get_cluster_status(1:string cluster_id)




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

    throws (1:serverNotFoundException e , 2: conflictException c)


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

     /** Tags with which the servers image is also tagged ( for connection information at the webapp) */
     4: list<string> base_tags,
     /** Description of the new snapshot*/
     5:string description)

     throws (1:serverNotFoundException e, 2: conflictException c),


    /**
     * Get Limits of OpenStack Projekt from client.
     * Returns: {'maxTotalVolumes': maxTotalVolumes, 'maxTotalVolumeGigabytes': maxTotalVolumeGigabytes,
     *           'maxTotalInstances': maxTotalInstances, 'totalRamUsed': totalRamUsed,
     *          'totalInstancesUsed': totalInstancesUsed}
     */
    map<string,string> get_limits()

     map<string,string> start_cluster(1:list<string> public_keys,2: ClusterInstance master_instance,3:list<ClusterInstance> worker_instance,4:string user)

     map<string,string> terminate_cluster(1:string cluster_id)

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

    throws (1:serverNotFoundException e, 2: conflictException c),


    /**
     * Delete volume.
     * Returns:  True if deleted, False if not
     */
    bool delete_volume(1:string volume_id) throws (1: conflictException c)

    /**
     * Attach volume to server.
     * Returns:  True if attached, False if not
     */
    map<string,string> attach_volume_to_server(
    /** Id of server*/
    1:string openstack_id,

    /** Id of volume*/
    2:string volume_id,
    )

    throws (1:serverNotFoundException e, 2: conflictException c),


    /**
     * Check status of server.
     * Returns: server instance
     */
    VM check_server_status(
    /** Id of the server */
    1:string openstack_id)

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

    throws (1:serverNotFoundException e, 2: conflictException c)


    /**
     * Create volume.
     * Returns: Id of new volume
     */
    map<string,string> create_volume(

    /**  Name of volume*/
    1:string volume_name,

    /** Diskspace in GB for new volume */
    2:int volume_storage,

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

    throws (1:serverNotFoundException e, 2: conflictException c)

}
