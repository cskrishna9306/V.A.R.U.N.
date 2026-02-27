# Cookie-cutter template for installing and running basic dependencies
# The basic dependencies will include HTTPS configuration via certbot and nginx, python, ollama, and GitHub repository fetching capabilities
# This script DOES NOT take any arguments

#! /bin/bash

# Step 1: Error handling for any invalid arguments
sudo apt update

# Step 2: Setup Certbot and nginx to allow HTTPS connections to the server from https://varun.saichaparala.com
cd ~
sudo apt install nginx certbot python3-certbot-nginx -y
sudo certbot --nginx -d varun.saichaparala.com

# Step 3: Setup python and pyenv
cd ~
sudo apt install python3
sudo apt install python3.11-venv

# Step 4: Setup ollama to run directly on the server (optional)

# Step 5: Setup GitHub credentials to access private repositories (optional)
cd ~
sudo apt install git
git clone https://github.com/cskrishna9306/V.A.R.U.N..git
