# Cookie cutter template for launching GCP VMs of the provided instance types and storage size
# This script will also configure the VM w/ user-data scripts @ ./boot-up-scripts.sh 
# We will primarily employ the gcloud CLI for VM instantiation 
# Finally, the script will return an external IP address which will then be plugged into the app's respective AWS Route 53 Hosted Zone

#! /bin/bash

# Instantiate default values for VM creation
INSTANCE_NAME="vllm-for-varun-llm"
ZONE="us-west2-c"
INSTANCE_TYPE="e2-highmem-2"
STORAGE_SIZE="20GB"

# Immutable values
IMAGE_PROJECT="ubuntu-os-cloud"
IMAGE_FAMILY="ubuntu-2204-lts"
USER_METADATA="./boot-up-script.sh"
SCRIPT_DIR=$(dirname "$(readlink -f "$0")")
PROJECT_ID="v-a-r-u-n"

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
echo "Setting the GCP project to $PROJECT_ID ..."

gcloud config set project $PROJECT_ID

# Step 3: Instantiate the GCP VM w/ the provided instance name, type, zone, and storage size
echo "Creating VM ..."

gcloud compute instances create "$INSTANCE_NAME" \
    --zone="$ZONE" \
    --machine-type="$INSTANCE_TYPE" \
    --image-family="$IMAGE_FAMILY" \
    --image-project="$IMAGE_PROJECT" \
    --metadata-from-file=startup-script="$SCRIPT_DIR/$USER_METADATA" \
    --boot-disk-size="$STORAGE_SIZE" \
    --tags=http-server,https-server

# Step 4: The above CLI command outputs the relevant details by default 

