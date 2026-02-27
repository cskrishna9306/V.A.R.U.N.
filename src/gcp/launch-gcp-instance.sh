# Cookie cutter template for launching GCP VMs of the provided instance types and storage size
# This script will also configure the VM w/ user-data scripts @ ./boot-up-scripts.sh 
# We will primarily employ the gcloud CLI for VM instantiation 
# Finally, the script will return an external IP address which will then be plugged into the app's respective AWS Route 53 Hosted Zone

#! /bin/bash

# Step 1: Parse the arguments to the script

# Step 2: Instantiate the GCP VM w/ the provided instance name, type, zone, and storage size
gcloud compute instances create my-vm \
    --image-family=debian-11 \
    --image-project=debian-cloud \
    --metadata-from-file=startup-script=./boot-up-scripts.sh \
    --zone=us-central1-a

# Step 3: Return the external IP address of the newly instantiated VM 

