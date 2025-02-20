#!/bin/bash

##############################################################################
# AWS Enumeration Script
# 
# A tool to gather information about AWS resources in your account
# Version: 1.1
# Author: Taraka Vishnumolakala
##############################################################################

# Disable AWS CLI pager to prevent waiting for key presses on long output
export AWS_PAGER=""

# Function to check AWS CLI installation
check_aws_cli() {
    if ! command -v aws &> /dev/null; then
        echo "AWS CLI not installed. Please install it before running the script."
        exit 1
    fi
}

# Function to display section headers with consistent formatting
display_section_header() {
    local title="$1"
    local char="${2:--}"
    local length="${3:-60}"
    
    local divider=$(printf "%${length}s" | tr " " "$char")
    
    echo -e "\n${divider}"
    echo "  ${title}"
    echo -e "${divider}"
}

# Function to display command output with a subtitle
display_command_output() {
    local subtitle="$1"
    local command="$2"
    
    echo -e "\n$subtitle"
    eval "$command"
}

# Function to get policy details (default version)
fetch_policy_details() {
    local policy_arn="$1"
    
    # Get the default policy version
    policy_version=$(aws iam get-policy --policy-arn "$policy_arn" --query "Policy.DefaultVersionId" --output text 2>/dev/null)
    if [[ -z "$policy_version" ]]; then
        echo "  [!] Failed to retrieve policy version for $policy_arn"
        return
    fi
    
    # Get policy details
    display_command_output "Policy Version Details: $policy_arn" \
        "aws iam get-policy-version --policy-arn \"$policy_arn\" --version-id \"$policy_version\" --query \"PolicyVersion.Document.Statement[*].{Effect: Effect, Action: to_string(Action), Resource: to_string(Resource)}\" --output table"
}

# Function to enumerate current user permissions
enumerate_user_permissions() {
    display_section_header "Enumerating Current User Permissions" "=" 80
    
    # Get and store user identity information
    echo -e "\nFetching user identity information..."
    user_info=$(aws sts get-caller-identity 2>/dev/null)
    
    if [[ -z "$user_info" ]]; then
        echo "  [!] Failed to retrieve user identity. Check AWS credentials."
        exit 1
    fi
    
    # Extract username from ARN
    user_arn=$(echo "$user_info" | jq -r .Arn)
    username=$(echo "$user_arn" | cut -d'/' -f2-)

    # Display user identity information
    display_command_output "User Identity" \
        "aws sts get-caller-identity --query '[{\"UserId\": UserId, \"Account\": Account, \"Arn\": Arn}]' --output table"

    # Check if user is an IAM user
    if [[ -n "$username" && "$user_arn" == *":user/"* ]]; then
        # List inline user policies
        inline_policies=$(aws iam list-user-policies --user-name "$username" --query "PolicyNames" --output json 2>/dev/null | jq -r '.[]')
        
        display_section_header "Inline User Policies" "-" 60
        if [[ -n "$inline_policies" ]]; then
            for policy in $inline_policies; do
                display_command_output "Policy: $policy" \
                    "aws iam get-user-policy --user-name \"$username\" --policy-name \"$policy\" --query 'PolicyDocument' --output table"
            done
        else
            echo "  [!] No inline policies found for user $username."
        fi
        
        # List attached user policies
        attached_policies=$(aws iam list-attached-user-policies --user-name "$username" --query "AttachedPolicies[*].PolicyArn" --output json 2>/dev/null | jq -r '.[]')
        
        display_section_header "Attached User Policies" "-" 60
        if [[ -n "$attached_policies" ]]; then
            for policy_arn in $attached_policies; do
                display_command_output "Policy ARN: $policy_arn" \
                    "aws iam get-policy --policy-arn \"$policy_arn\" --query '[{\"PolicyName\": Policy.PolicyName, \"PolicyARN\": Policy.Arn}]' --output table"
                
                # Fetch and display policy version details
                fetch_policy_details "$policy_arn"
            done
        else
            echo "  [!] No attached policies found for user $username."
        fi
    else
        echo -e "\n  [!] Not an IAM user or username could not be determined."
        echo "  ARN: $user_arn"
    fi
}

# Function to display usage information
usage() {
    echo "Usage: $0 <option>"
    echo "Options:"
    echo "  enumerate-user-permissions  - Gets permissions and attached policies for the current user profile"
    echo "  help                        - Display this help message"
    exit 1
}

# Main execution block
check_aws_cli  # Ensure AWS CLI is installed

if [ $# -eq 0 ]; then
    usage
fi

case "$1" in
    enumerate-user-permissions) enumerate_user_permissions ;;
    help) usage ;;
    *) echo "Invalid option! Use 'help' for available options." ;;
esac
