# DevOps-EC2-Automator

Project Overview <br>
This project presents an automated Python-based solution for provisioning Amazon EC2 instances and their associated network configurations (Security Groups). Developed with a strong focus on DevOps principles, this tool streamlines the process of deploying cloud infrastructure, reducing manual effort, enhancing consistency, and accelerating development and testing workflows.

Leveraging the boto3 AWS SDK, the script reads desired infrastructure configurations from a simple YAML file and programmatically interacts with the AWS API to create resources. This demonstrates key skills in Infrastructure as Code (IaC), cloud automation, and API integration.

Features <br>
YAML-driven Configuration: Define EC2 instance parameters (AMI ID, instance type, key pair, region, instance count) and security group rules in an easy-to-read config.yaml file.
Automated Security Group Creation: Automatically creates a new Security Group with inbound rules for SSH (Port 22) and HTTP (Port 80), ensuring network access for common web server setups.
Idempotent Security Group Handling: Prevents recreation of existing security groups, ensuring smooth re-runs.
EC2 Instance Launch: Provisions one or more EC2 instances based on the specified configuration.
Resource Tagging: Automatically applies meaningful tags (Name, Project) to provisioned instances for better resource management and identification.
Real-time Feedback: Provides console output on the provisioning progress, including instance IDs and public IP addresses.
Error Handling: Includes robust error handling for common issues like missing credentials, invalid AMIs, or non-existent key pairs.
Technologies Used
Python 3.x: The core programming language.
boto3: AWS SDK for Python, used to interact with AWS services.
PyYAML: For parsing the YAML configuration file.
AWS EC2: Cloud computing service for virtual servers.
AWS Identity and Access Management (IAM): For managing programmatic access.
AWS Command Line Interface (CLI): For credential management.
DevOps Relevance & Impact
This project directly addresses several critical DevOps practices:

Infrastructure as Code (IaC): Defines infrastructure in a version-controlled YAML file, promoting consistency, repeatability, and reducing "configuration drift."
Automation: Eliminates manual clicks and potential human errors in the AWS console, accelerating provisioning time for development, testing, and even production environments.
Repeatability: Ensures that environments can be spun up and torn down identically multiple times, crucial for consistent testing and disaster recovery simulations.
API Integration: Demonstrates proficiency in interacting with cloud provider APIs, a fundamental skill for building sophisticated automation tools and integrating with CI/CD pipelines.
Efficiency: Streamlines resource deployment, allowing teams to focus more on application development and less on infrastructure setup.
Getting Started
Prerequisites
Python 3.x installed.
pip (Python package installer).
An active AWS Account.
AWS CLI configured with programmatic access credentials (Access Key ID and Secret Access Key) for a user/role with sufficient permissions to manage EC2 instances and Security Groups.
An existing EC2 Key Pair in your chosen AWS region.
Installation
Clone the repository (or create the files manually):
<br>
Bash <br>
<br>
<br>
Install dependencies:<br>
<br>
Bash

pip install boto3 PyYAML
Configuration
Create or Update config.yaml:

Create a file named config.yaml in the project root directory.
Populate it with your desired AWS resource details. Ensure key_pair_name matches an existing EC2 Key Pair in your AWS account, and ami_id is valid for your aws_region.
YAML

# config.yaml
aws_region: ap-south-1 # Example: Mumbai
key_pair_name: your-key-pair-name # IMPORTANT: Must exist in AWS EC2 Key Pairs
instance_type: t2.micro
ami_id: ami-0f5ee92e2d634125b # IMPORTANT: Verify latest AMI ID for your region/OS
security_group_name: provisioner-sg
security_group_description: Security group for automated EC2 provisioning
instance_count: 1
Running the Script
Ensure AWS Credentials are set up:

Run aws configure in your terminal and provide your AWS Access Key ID, Secret Access Key, and default region. This is the recommended method.
Execute the provisioning script:

Bash

python provision.py
The script will output the details of the provisioned EC2 instance(s), including their public IP addresses.

Cleanup (Important!)
AWS charges for running resources. To avoid unexpected costs, remember to terminate the provisioned instances and delete the security group after you are done.

Manual Cleanup (Recommended for learning):

Navigate to the AWS EC2 Console.
Go to "Instances", select the instance(s) created by the script, and choose "Instance state" -> "Terminate instance".
Go to "Security Groups", select the security group (provisioner-sg), and choose "Actions" -> "Delete security group". (You may need to wait a few minutes after instance termination before deleting the SG).
Automated Cleanup (Use with extreme caution!):

The provision.py script contains a cleanup_resources function. If you uncomment the call to this function at the end of the if __name__ == "__main__": block, the script will attempt to terminate instances and delete the security group immediately after provisioning. Use this feature only after thoroughly understanding its implications, as it can lead to unintended resource deletion.
