# provision.py
import boto3
import yaml
import sys
import time

def load_config(config_path='config.yaml'):
    """Loads configuration from a YAML file."""
    try:
        with open(config_path, 'r') as file:
            config = yaml.safe_load(file)
        return config
    except FileNotFoundError:
        print(f"Error: Config file '{config_path}' not found.")
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"Error parsing config file '{config_path}': {e}")
        sys.exit(1)

def create_security_group(ec2_client, vpc_id, sg_name, sg_description):
    """
    Creates a security group and adds rules for SSH (22) and HTTP (80).
    Returns the Security Group ID.
    """
    print(f"Checking for existing security group: {sg_name}...")
    try:
        response = ec2_client.describe_security_groups(GroupNames=[sg_name])
        sg_id = response['SecurityGroups'][0]['GroupId']
        print(f"Security Group '{sg_name}' already exists with ID: {sg_id}")
        return sg_id
    except ec2_client.exceptions.ClientError as e:
        if "DoesNotExist" in str(e):
            print(f"Security Group '{sg_name}' does not exist. Creating...")
            try:
                response = ec2_client.create_security_group(
                    GroupName=sg_name,
                    Description=sg_description,
                    VpcId=vpc_id
                )
                sg_id = response['GroupId']
                print(f"Security Group '{sg_name}' created with ID: {sg_id}")

                # Add SSH rule
                ec2_client.authorize_security_group_ingress(
                    GroupId=sg_id,
                    IpPermissions=[
                        {
                            'IpProtocol': 'tcp',
                            'FromPort': 22,
                            'ToPort': 22,
                            'IpRanges': [{'CidrIp': '0.0.0.0/0'}] # Be cautious with 0.0.0.0/0 in production
                        }
                    ]
                )
                print(f"Ingress rule for SSH (Port 22) added to {sg_name}.")

                # Add HTTP rule
                ec2_client.authorize_security_group_ingress(
                    GroupId=sg_id,
                    IpPermissions=[
                        {
                            'IpProtocol': 'tcp',
                            'FromPort': 80,
                            'ToPort': 80,
                            'IpRanges': [{'CidrIp': '0.0.0.0/0'}] # Be cautious with 0.0.0.0/0 in production
                        }
                    ]
                )
                print(f"Ingress rule for HTTP (Port 80) added to {sg_name}.")
                return sg_id
            except ec2_client.exceptions.ClientError as creation_error:
                print(f"Error creating security group or adding rules: {creation_error}")
                sys.exit(1)
        else:
            print(f"Error describing security group: {e}")
            sys.exit(1)

def provision_ec2_instance(ec2_client, config, sg_id):
    """Provisions an EC2 instance."""
    print(f"\nAttempting to launch {config['instance_count']} EC2 instance(s)...")
    try:
        response = ec2_client.run_instances(
            ImageId=config['ami_id'],
            MinCount=1,
            MaxCount=config['instance_count'],
            InstanceType=config['instance_type'],
            KeyName=config['key_pair_name'],
            SecurityGroupIds=[sg_id],
            TagSpecifications=[
                {
                    'ResourceType': 'instance',
                    'Tags': [
                        {
                            'Key': 'Name',
                            'Value': f"Automated-Instance-{int(time.time())}"
                        },
                        {
                            'Key': 'Project',
                            'Value': 'Python-DevOps-Provisioner'
                        }
                    ]
                },
            ]
        )
        instances = response['Instances']
        instance_ids = [i['InstanceId'] for i in instances]
        print(f"Launched instance(s) with IDs: {', '.join(instance_ids)}")

        # Wait for instances to be running
        print("Waiting for instance(s) to enter 'running' state...")
        waiter = ec2_client.get_waiter('instance_running')
        waiter.wait(InstanceIds=instance_ids)
        print("Instance(s) are now running.")

        # Fetch public IPs
        running_instances = ec2_client.describe_instances(InstanceIds=instance_ids)
        public_ips = []
        for reservation in running_instances['Reservations']:
            for instance in reservation['Instances']:
                if 'PublicIpAddress' in instance:
                    public_ips.append(instance['PublicIpAddress'])

        print("\n--- Provisioning Summary ---")
        for i, instance_id in enumerate(instance_ids):
            print(f"Instance ID: {instance_id}")
            if i < len(public_ips): # Ensure we have an IP for each if count > 1
                 print(f"Public IP: {public_ips[i]}")
            print(f"Instance Type: {config['instance_type']}")
            print(f"AMI ID: {config['ami_id']}")
            print(f"Key Pair: {config['key_pair_name']}")
            print(f"Security Group: {config['security_group_name']} ({sg_id})")
            print("-" * 25)

        return instance_ids, public_ips

    except ec2_client.exceptions.ClientError as e:
        print(f"Error launching EC2 instance(s): {e}")
        # Specific error handling for key pair not found
        if "InvalidKeyPair.NotFound" in str(e):
            print("Please ensure the key_pair_name in config.yaml exists in your AWS EC2 Key Pairs.")
        # Specific error handling for AMI not found
        if "InvalidAMIID.NotFound" in str(e) or "InvalidAMIID.Malformed" in str(e):
             print("Please verify the ami_id in config.yaml is correct for your region.")
        sys.exit(1)

def cleanup_resources(ec2_client, instance_ids, sg_id):
    """
    (Optional) Terminates EC2 instances and deletes the security group.
    Use with extreme caution!
    """
    if instance_ids:
        print(f"\nTerminating instance(s): {', '.join(instance_ids)}...")
        try:
            ec2_client.terminate_instances(InstanceIds=instance_ids)
            waiter = ec2_client.get_waiter('instance_terminated')
            waiter.wait(InstanceIds=instance_ids)
            print("Instance(s) terminated successfully.")
        except ec2_client.exceptions.ClientError as e:
            print(f"Error terminating instance(s): {e}")

    if sg_id:
        print(f"Deleting security group: {sg_id}...")
        try:
            # Give some time for instances to fully de-register from SG
            time.sleep(10)
            ec2_client.delete_security_group(GroupId=sg_id)
            print(f"Security group '{sg_id}' deleted successfully.")
        except ec2_client.exceptions.ClientError as e:
            print(f"Error deleting security group '{sg_id}': {e}")
            print("You might need to manually delete the security group if instances were still attached.")


if __name__ == "__main__":
    config = load_config()

    # Initialize boto3 EC2 client
    # boto3 automatically picks up credentials from AWS CLI config or env vars
    ec2_client = boto3.client(
        'ec2',
        region_name=config['aws_region']
    )

    # Get the default VPC ID (you could make this configurable too)
    try:
        response = ec2_client.describe_vpcs(Filters=[{'Name': 'isDefault', 'Values': ['true']}])
        if not response['Vpcs']:
            print("Error: No default VPC found. Please specify a VPC ID in config or create a default VPC.")
            sys.exit(1)
        default_vpc_id = response['Vpcs'][0]['VpcId']
        print(f"Using Default VPC ID: {default_vpc_id}")
    except ec2_client.exceptions.ClientError as e:
        print(f"Error getting default VPC: {e}")
        sys.exit(1)


    # Create or get security group
    security_group_id = create_security_group(
        ec2_client,
        default_vpc_id,
        config['security_group_name'],
        config['security_group_description']
    )

    # Provision EC2 instance(s)
    provisioned_instance_ids, provisioned_public_ips = provision_ec2_instance(
        ec2_client, config, security_group_id
    )

    # --- IMPORTANT: Manual Cleanup Required ---
    print("\n--- IMPORTANT: MANUAL CLEANUP REQUIRED ---")
    print("Please manually terminate the created EC2 instance(s) and delete the security group from the AWS console")
    print(f"Instance IDs: {', '.join(provisioned_instance_ids)}")
    print(f"Security Group ID: {security_group_id}")
    print("Alternatively, you can uncomment and call `cleanup_resources` function (USE WITH CAUTION).")
    # To enable automatic cleanup, uncomment the line below and understand its implications!
    # cleanup_resources(ec2_client, provisioned_instance_ids, security_group_id)