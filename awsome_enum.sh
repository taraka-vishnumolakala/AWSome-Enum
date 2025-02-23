#!/usr/bin/env bash

##############################################################################
# AWS Enumeration Script
# 
# A tool to gather information about AWS resources in your account
# Version: 1.4
# Author: Taraka Vishnumolakala
##############################################################################

# Disable AWS CLI pager to prevent waiting for key presses on long output
export AWS_PAGER=""

AWS_PROFILE_OPT=""  # Global variable to store --profile option
OUTPUT_FILE=""      # Global variable to store output file option

BOLD_CYAN='\033[1;36m'

# Instead of using associative array, use simple array with key-value pairs
INTERESTING_PERMISSIONS=()

# Load permissions from JSON file
load_permissions() {
    local json_file="interesting_permissions.json"
    if [[ -f "$json_file" ]]; then
        # Load permissions into flat array in format "key|value"
        while IFS= read -r line; do
            INTERESTING_PERMISSIONS+=("$line")
        done < <(jq -r 'to_entries[] | "\(.key)|\(.value)"' "$json_file")
    else
        echo "Warning: interesting_permissions.json not found. Interesting permissions will not be checked."
    fi
}

# Function to check for interesting permissions
check_interesting_permissions() {
    local actions="$1"
    
    print_cyan "\n[*] Analyzing permissions for potential privilege escalation vectors:\n"
    
    # Loop through each action
    while IFS= read -r perm; do
        perm=$(echo "$perm" | tr -d '[]" ')  # Clean up formatting
        if [[ -z "$perm" ]]; then continue; fi

        # Check each interesting permission
        for interesting in "${INTERESTING_PERMISSIONS[@]}"; do
            KEY="${interesting%%|*}"
            VALUE="${interesting#*|}"
            
            if [[ "$perm" == "$KEY" ]]; then
                print_green "  [!] Interesting Permission Found: $perm"
                print_green "  ➡️  More info: $VALUE"
            fi
        done
    done <<< "$actions"
}

# Function to print messages in green
print_green() {
    echo -e "\e[32m$1\e[0m"
}

# Function to print messages in yellow
print_yellow() {
    echo -e "\e[33m$1\e[0m"
}

# Function to print messages in cyan
print_cyan() {
    echo -e "\033[0;36m$1\033[0m"
}

# Function to check AWS CLI and yq installation
check_aws_cli() {
    if ! command -v aws &> /dev/null; then
        echo "AWS CLI not installed. Please install it before running the script."
        exit 1
    fi
    if ! command -v yq &> /dev/null; then
        echo "yq not installed. Please install it for YAML parsing."
        exit 1
    fi
}

# Function to parse arguments
parse_arguments() {
    COMMAND=""
    
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --profile)
                if [[ -z "$2" ]]; then
                    echo "Error: --profile requires a value"
                    exit 1
                fi
                AWS_PROFILE_OPT="--profile $2"
                shift 2
                ;;
            --output)
                if [[ -z "$2" ]]; then
                    echo "Error: --output requires a filename"
                    exit 1
                fi
                OUTPUT_FILE="$2"
                shift 2
                ;;
            enumerate-user-permissions|help)
                COMMAND="$1"
                shift
                ;;
            *)
                echo "Invalid option: $1"
                usage
                ;;
        esac
    done

    if [[ -z "$COMMAND" ]]; then
        usage
    fi
}

# Function to display section headers
display_section_header() {
    local title="$1"
    local char="${2:--}"
    local length="${3:-60}"
    
    local divider=$(printf "%${length}s" | tr " " "$char")
    
    echo -e "\n${divider}"
    echo "  ${title}"
    echo -e "${divider}"
}

# Function to fetch policy details - modified to handle both managed and inline policies
fetch_policy_details() {
    local policy_arn="$1"
    local is_inline="$2"
    local username="$3"
    local policy_name="$4"

    if [[ "$is_inline" == "true" ]]; then
        # Handle inline policy
        statement_yaml=$(aws iam get-user-policy --user-name "$username" --policy-name "$policy_name" --query "PolicyDocument" --output yaml $AWS_PROFILE_OPT 2>/dev/null)
        print_cyan "\n[*] Inline Policy Details: $policy_name\n"
    else
        # Handle managed policy
        policy_version=$(aws iam get-policy --policy-arn "$policy_arn" --query "Policy.DefaultVersionId" --output text $AWS_PROFILE_OPT 2>/dev/null)
        if [[ -z "$policy_version" ]]; then
            echo "  [!] Failed to retrieve policy version for $policy_arn"
            return
        fi  # Fixed: Added missing closing brace

        statement_yaml=$(aws iam get-policy-version --policy-arn "$policy_arn" --version-id "$policy_version" --query "PolicyVersion.Document" --output yaml $AWS_PROFILE_OPT 2>/dev/null)
        print_cyan "\n[*] Policy Version Details: $policy_arn\n"
    fi

    echo "$statement_yaml"

    # Extract actions using the correct yq v4 syntax
    actions=$(echo "$statement_yaml" | yq '.Statement[].Action | select(. != null) | ... | select(. != null)' -)
    
    check_interesting_permissions "$actions"

    if [[ -n "$OUTPUT_FILE" ]]; then
        echo "$statement_yaml" >> "$OUTPUT_FILE"
    fi
}

# Function to enumerate user permissions
enumerate_user_permissions() {
    display_section_header "Enumerating User Permissions for $AWS_PROFILE_OPT" "=" 80
    
    # Get user identity information
    print_cyan "\n[*] Fetching user identity information:\n"
    user_info=$(aws sts get-caller-identity --output yaml $AWS_PROFILE_OPT 2>/dev/null)
    
    if [[ -z "$user_info" ]]; then
        echo "  [!] Failed to retrieve user identity. Check AWS credentials." 
        exit 1
    fi

    echo "$user_info"

    # Extract username from ARN
    user_arn=$(echo "$user_info" | yq eval '.Arn' -)
    username=$(echo "$user_arn" | cut -d'/' -f2-)

    # List attached user policies (managed policies)
    print_cyan "\n[*] Attached User Policies (Managed):\n"
    attached_policies=$(aws iam list-attached-user-policies --user-name "$username" --query "AttachedPolicies[*].PolicyArn" --output yaml $AWS_PROFILE_OPT 2>/dev/null)
    echo "$attached_policies"

    # List inline user policies
    print_cyan "\n[*] Inline User Policies:\n"
    inline_policies=$(aws iam list-user-policies --user-name "$username" --output yaml $AWS_PROFILE_OPT 2>/dev/null)
    echo "$inline_policies"

    # Process managed policies
    echo "$attached_policies" | yq eval '.[]' - | while read -r policy_arn; do
        print_yellow "\n[*] Processing Managed Policy: $policy_arn\n"
        fetch_policy_details "$policy_arn" "false"
    done

    # Process inline policies
    echo "$inline_policies" | yq eval '.PolicyNames[]' - | while read -r policy_name; do
        print_yellow "\n[*] Processing Inline Policy: $policy_name\n"
        fetch_policy_details "" "true" "$username" "$policy_name"
    done
}

# Function to display usage information
usage() {
    echo "Usage: $0 [--profile <profile_name>] [--output <file.yaml>] <option>"
    echo "Options:"
    echo "  enumerate-user-permissions  - Get permissions and attached policies for the current user"
    echo "  help                        - Display this help message"
    echo ""
    echo "Optional:"
    echo "  --profile <profile_name>    - Specify an AWS CLI profile (default: uses the default profile)"
    echo "  --output <file.yaml>        - Save the results to a YAML file"
    exit 1
}

# Main execution block
check_aws_cli
load_permissions
parse_arguments "$@"

case "$COMMAND" in
    enumerate-user-permissions) enumerate_user_permissions ;;
    help) usage ;;
esac