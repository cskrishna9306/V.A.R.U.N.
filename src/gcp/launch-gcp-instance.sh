# Cookie cutter template for launching GCP VMs of the provided instance types and storage size
# This script will also configure the VM w/ user-data scripts @ ./boot-up-scripts.sh 
# We will primarily employ the gcloud CLI for VM instantiation 
# Finally, the script will update the corresponding AWS Route 53 DNS record to point to the newly configured GCP VM's external IP address

#! /bin/bash

# Instantiate default values for VM creation
INSTANCE_NAME="vllm-for-varun-llm"
ZONE="us-west2-c"
INSTANCE_TYPE="e2-highmem-2"
STORAGE_SIZE="10GB"

# Step 1: Parse the arguments provided to the script
while [[ $# -gt 0 ]]; do
  case $1 in
    -n|--instance-name)
      INSTANCE_NAME="$2"
      shift 2
      ;;
    -z|--zone)
      ZONE="$2"
      shift 2
      ;;
    -t|--instance-type)
      INSTANCE_TYPE="$2"
      shift 2
      ;;
    -s|--storage-size)
      STORAGE_SIZE="$2"
      shift 2
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

# Step 2: Set the right GCP project workspace

# Define the GCP project ID
GCP_PROJECT_ID="v-a-r-u-n"

# Set the right gcloud project via gcloud CLI
echo "Setting the GCP project to $GCP_PROJECT_ID ..."
gcloud config set project $GCP_PROJECT_ID

# Step 3: Instantiate the GCP VM w/ the provided instance name, type, zone, and storage size

# Define VM image parameters
IMAGE_PROJECT="ubuntu-os-cloud"
IMAGE_FAMILY="ubuntu-2204-lts"
USER_METADATA="./boot-up-script.sh"
SCRIPT_DIR=$(dirname "$(readlink -f "$0")")

# Create the VM instance via gcloud CLI
echo "Creating VM ..."
gcloud compute instances create "$INSTANCE_NAME" \
    --zone="$ZONE" \
    --machine-type="$INSTANCE_TYPE" \
    --image-family="$IMAGE_FAMILY" \
    --image-project="$IMAGE_PROJECT" \
    --metadata-from-file=startup-script="$SCRIPT_DIR/$USER_METADATA" \
    --boot-disk-size="$STORAGE_SIZE" \
    --tags=http-server,https-server

# Step 4: Extract the external IP address for the newly created VM
echo "Retrieving external IP for $INSTANCE_NAME ..."
EXTERNAL_IP=$(gcloud compute instances describe "$INSTANCE_NAME" \
    --zone="$ZONE" \
    --format='get(networkInterfaces[0].accessConfigs[0].natIP)')

# Step 5: Update the AWS Route 53 DNS A-record to the newly configured VM's external IP

# Define AWS Route 53 variables
HOSTED_ZONE_ID="Z021972228GN0DOV7MH51"
ROUTE_53_RECORD_NAME="varun.saichaparala.com"

# Fill the template and pipe it directly to AWS
envsubst < route53-template.json > filled-record.json

# Update the Route 53 A-record using AWS CLI
echo "Updating Route 53 A-record for $ROUTE_53_RECORD_NAME to $EXTERNAL_IP..."
aws route53 change-resource-record-sets \
    --hosted-zone-id "$HOSTED_ZONE_ID" \
    --change-batch "file://filled-record.json"

# Clean up
rm filled-record.json

echo "Route 53 update sent. Propagation may take a few minutes."
