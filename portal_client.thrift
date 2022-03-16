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


struct ResearchEnvironmentTemplate{
1:optional string template_name,
2:optional string title,
3:optional string description,
4:optional string logo_url,
5:optional string info_url,
6:optional i32 port,
7: optional list<string> incompatible_versions,
8: optional bool is_maintained,
9: optional map<string,string> information_for_display
}
struct CondaPackage{
1:optional string build,
2:optional string build_number,
3:optional string name,
4:optional string version,
5:optional string home
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
}

struct Volume{
1:optional string id,
2:optional string name,
3:optional string description,
4:optional string status,
5:optional string created_at,
6:optional string device,
7:optional int size,
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

	/** The description of the flavor*/
	5:optional string description

	/** The ephemeral disk space of the flavor*/
	6:optional i32 ephemeral_disk
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
	9: required list<string> tags

	/** If the Image is a snapshot*/
	10:optional bool is_snapshot
}
/**
 * This Struct defines a VirtualMachine.
 */
struct VM {

    	/** The flavor of the VM*/
    1: required Flavor flavor,

	/** The image of the VM*/
	2: required Image image,

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
	12:optional string task_state
	13:optional i32 power_state
	14:optional string vm_state
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

exception ResourceNotFoundException {
    /** Name already used. */
    1: string message
    2: string resource_type
    3: string name_or_id
}

exception ResourceNotAvailableException {
    /** Name already used. */
    1: string message

}

exception TemplateNotFoundException {
    /** Name already used. */
    1: string message
    2: string template

}

exception NameAlreadyUsedException {
    /**@ Name already used. */
    1: string message
    2: string name
}

exception ServerNotFoundException {
    /** Server not found. */
    1: string message
    2: string name_or_id
}


exception FlavorNotFoundException {
    1: string message
    2: string name_or_id
}

exception VolumeNotFoundException {
    1: string message
    2: string name_or_id
}
exception ImageNotFoundException {
    1: string message
    2: string name_or_id
}
exception ClusterNotFoundException {
    1: string message
    2: string name_or_id
}

exception BackendNotFoundException {
    1: string message
    2: string name_or_id
}

exception PlaybookNotFoundException {
    1: string message
    2: string name_or_id
}

exception DefaultException {
    1: string message
}


/** Conflict with request (e.g. while vm is in create image task)*/
exception OpenStackConflictException {
       1: string message

}

/**
 * This VirtualMachiine service deploys methods for creating,deleting,stopping etc. VirtualMachines in Openstack.
 */
service VirtualMachineService {


    bool is_version(1:double version)

    /**
     * Get Client version.
     * Returns Version of the client
     */
    string get_client_version()

    	/**
	 * Gets the gateway ip.
	 */
    map<string,string> get_gateway_ip()



    map<string,i32>  get_calculation_values()

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
    1: string openstack_id) throws(1:ServerNotFoundException s)


	 /**
	 * Get Flavors.
	 * Returns: List of flavor instances.
	 */
	list<Flavor> get_flavors()


	/**
	 * Get Images.
	 * Returns: List of Image instances.
	 */
	list<Image> get_images()

    /**
	 * Get Images.
	 * Returns: List of public Image instances.
	 */
	list<Image> get_public_images()

    /**
	 * Get Images.
	 * Returns: List of private Image instances.
	 */
	list<Image> get_private_images()

	/**
	 * Get an image with tag.
	 * Returns: image.
	 */
	Image get_image(1:string openstack_id) throws (1:ImageNotFoundException i)


	Volume get_volume(
	1:string volume_id
	) throws (1:VolumeNotFoundException v)

	list<Volume> get_volumes_by_ids(
	1:list<string> volume_ids
	)

	void resize_volume(1:string volume_id,2:int size) throws(1:VolumeNotFoundException v)



	 /**
	  * Delete server.
	  * Returns: True if deleted, False if not
	  */
	void delete_server(

	/** Id of the server. */
	1:string openstack_id)

	throws (1:ServerNotFoundException e, 2: OpenStackConflictException c)


	string start_server(
	/** Name of the  Flavor to use.*/
    1:string flavor_name,

    /** Name of the image to use. */
    2:string image_name,

    /** Public Key to use*/
    3:string public_key,

    /** Name for the new server */
    4:string servername,

    /** Metadata for the new instance*/
    5:map<string,string> metadata,

    7:string research_environment,
     8:list<map<string,string>> volume_ids_path_new,
     9:list<map<string,string>> volume_ids_path_attach,
     10:list <string> additional_keys
)

    throws (1:NameAlreadyUsedException e,2:ResourceNotAvailableException r,5:ImageNotFoundException i,6:FlavorNotFoundException f,7:DefaultException o)

    bool is_bibigrid_available()
    void detach_ip_from_server(1:string server_id,2:string floating_ip) throws(1:ServerNotFoundException s)




    /**
	 * Start a new server with custom key for ansible.
	 */
    string start_server_with_custom_key(

    /** Name of the  Flavor to use.*/
    1:string flavor_name,

    /** Name of the image to use. */
    2:string image_name,

    /** Name for the new server */
    3:string servername,

    /** Metadata for the new instance*/
    4:map<string,string> metadata,


    5:optional string research_environment,
    6:list<map<string,string>> volume_ids_path_new,
     7:list<map<string,string>> volume_ids_path_attach)


    throws (1:NameAlreadyUsedException e,2:ResourceNotAvailableException r,3: ImageNotFoundException i,4: FlavorNotFoundException f,5:DefaultException d)

    /** Check if there is an instance with name */
    bool exist_server(
    1:string name
    )

    /** Create and deploy an anaconda ansible playbook*/
    int create_and_deploy_playbook(
    1:string public_key,
     2:string openstack_id
    3:list<CondaPackage> conda_packages,
    4:string  research_environment_template,
    5:bool        create_only_backend,

    ) throws (1:ServerNotFoundException s)

    /** Get the logs from a playbook run*/
    PlaybookResult get_playbook_logs(
    1:string openstack_id
    ) throws(1:PlaybookNotFoundException p)


    /** Get boolean if client has backend url configured*/
    bool has_forc()

    string get_forc_url()

    /** Create a backend*/
    Backend create_backend(
    1:string username,
    2:string user_path,
    3:string template,
    4:string upstream_url
    ) throws(1: TemplateNotFoundException e,2:DefaultException d)

    /** Get all backends*/
    list<Backend> get_backends() throws(1:DefaultException d)

    /** Get all backends by owner*/
    list<Backend> get_backends_by_owner(
    1:string username
    )  throws(1:DefaultException d)

    /** Get all backends by template*/
    list<Backend> get_backends_by_template(
    1:string template
    )  throws(1:DefaultException d)

    /** Get a backend by id*/
    Backend get_backend_by_id(
    1:i64 id
    ) throws (1:BackendNotFoundException b,2:DefaultException d)



    /** Delete a backend*/
    void delete_backend(
    1:i64 id
    ) throws (1:BackendNotFoundException b)

    /** Add a user to a backend*/
    map<string,string> add_user_to_backend(
    1:i64 backend_id,
    2:string owner_id,
    3:string user_id
    ) throws (1:BackendNotFoundException b)

    /** Get users from a backend*/
    list<string> get_users_from_backend(
    1:i64 backend_id
    ) throws (1:BackendNotFoundException b)

    /** Delete user from a backend*/
    map<string,string> delete_user_from_backend(
    1:i64 backend_id,
    2:string owner_id,
    3:string user_id
    ) throws (1:BackendNotFoundException b)


    list<ResearchEnvironmentTemplate> get_allowed_templates()


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
	* Get servers by bibigrid cluster id.
    **/
	list<VM> get_servers_by_bibigrid_id(1:string bibigrid_id)

	map<string,list<string>> scale_up_cluster(1: string cluster_id,2: string image_name,3:string flavor_name,4:int count,
                          5:list<string>names,6:int start_idx,7:int batch_idx)


    string add_cluster_machine(1:string cluster_id,2:string cluster_user,3:string cluster_group_id,4:string image_name,5: string flavor_name,6: string name,7: string key_name,8: int batch_idx,
                            9:int worker_idx)

	ClusterInfo get_cluster_info(1:string cluster_id) throws(1:ClusterNotFoundException c)

	map<string,string>get_cluster_status(1:string cluster_id) throws(1:ClusterNotFoundException c)




	/**
	 * Get a Server.
	 * Returns: A server instance.
	 */
	VM get_server(

	/** Id of the server.*/
	1:string openstack_id)

	 throws (1:ServerNotFoundException e),


	/**
	 * Stop a Server.
	 * Returns: True if stopped, False if not.
	 */
    void stop_server(

    /** Id of the server.*/
    1:string openstack_id)

    throws (1:ServerNotFoundException e , 2: OpenStackConflictException c)


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

     /** unique username of the user who requested creation of Snapshot */
     3: string username,

     /** Tags with which the servers image is also tagged ( for connection information at the webapp) */
     4: list<string> base_tags,
     /** Description of the new snapshot*/
     5:string description)

     throws (1:ServerNotFoundException e, 2: OpenStackConflictException c),


    /**
     * Get Limits of OpenStack Projekt from client.
     * Returns: {'maxTotalVolumes': maxTotalVolumes, 'maxTotalVolumeGigabytes': maxTotalVolumeGigabytes,
     *           'maxTotalInstances': maxTotalInstances, 'totalRamUsed': totalRamUsed,
     *          'totalInstancesUsed': totalInstancesUsed}
     */
    map<string,string> get_limits()

     map<string,string> start_cluster(1:string public_key,2: ClusterInstance master_instance,3:list<ClusterInstance> worker_instances,4:string user)

     map<string,string> terminate_cluster(1:string cluster_id) throws(1:ClusterNotFoundException c)

    /**
     * Delete Image.
     * Return: True if deleted, False if not
     */
    void delete_image(
    /** Id of image */
    1:string image_id) throws (

    1:ImageNotFoundException e)


    /**
     * Delete volume attachment
     * Return: True if deleted, False if not
     */
    void detach_volume(
    /** Id of the attached volume */
    1:string volume_id,

    /** Id of the server where the volume is attached */
    2:string server_id)

    throws (1:ServerNotFoundException e, 2: OpenStackConflictException c,3: VolumeNotFoundException v),


    /**
     * Delete volume.
     * Returns:  True if deleted, False if not
     */
    void delete_volume(1:string volume_id) throws (1: OpenStackConflictException c,2:VolumeNotFoundException v)

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

    throws (1:VolumeNotFoundException e, 2: OpenStackConflictException c),




    /**
     * Resume Server.
     * Returns: True if resumed False if not
     */
    void resume_server(
    /** Id of the server */
    1:string openstack_id)

    throws (1:ServerNotFoundException e, 2: OpenStackConflictException c)


    /**
     * Create volume.
     */
    Volume create_volume(

    /**  Name of volume*/
    1:string volume_name,

    /** Diskspace in GB for new volume */
    2:int volume_storage,

     /** Metadata for the new volume*/
    3:map<string,string> metadata)

    throws (1:DefaultException r,2:ResourceNotAvailableException n)


      /**
     * Reboot server.
     * Returns: True if rebooted False if not
     */
    void reboot_hard_server(

    /** Id of the server*/
    1:string openstack_id,
)

    throws (1:ServerNotFoundException e, 2: OpenStackConflictException c)

       /**
     * Reboot server.
     * Returns: True if rebooted False if not
     */
    void reboot_soft_server(

    /** Id of the server*/
    1:string openstack_id,
)

    throws (1:ServerNotFoundException e, 2: OpenStackConflictException c)

}
