# AWSome-enum

```bash
   █████╗ ██╗    ██╗███████╗ ██████╗ ███╗   ███╗███████╗
  ██╔══██╗██║    ██║██╔════╝██╔═══██╗████╗ ████║██╔════╝
  ███████║██║ █╗ ██║███████╗██║   ██║██╔████╔██║█████╗  
  ██╔══██║██║███╗██║╚════██║██║   ██║██║╚██╔╝██║██╔══╝  
  ██║  ██║╚███╔███╔╝███████║╚██████╔╝██║ ╚═╝ ██║███████╗
  ╚═╝  ╚═╝ ╚══╝╚══╝ ╚══════╝ ╚═════╝ ╚═╝     ╚═╝╚══════╝
                                                        
  ███████╗███╗   ██╗██╗   ██╗███╗   ███╗
  ██╔════╝████╗  ██║██║   ██║████╗ ████║
  ███████╗██╔██╗ ██║██║   ██║██╔████╔██║
  ██╔════╝██║╚██╗██║██║   ██║██║╚██╔╝██║
  ███████╗██║ ╚████║╚██████╔╝██║ ╚═╝ ██║
  ╚══════╝╚═╝  ╚═══╝ ╚═════╝ ╚═╝     ╚═╝
```

## Overview
AWSome-enum is a comprehensive AWS security enumeration and privilege escalation detection tool designed for AWS penetration testing and security auditing. The tool recursively analyzes IAM permissions, resource policies, and identifies potential privilege escalation paths within AWS environments.

## Tool Capabilities
AWSome-enum is designed with a modular approach to AWS service enumeration. Current capabilities include:

- **Core Functionality**:
  - Identify and analyze IAM permissions and policies
  - Flag potentially dangerous permissions with detailed explanations
  - Provide links to relevant privilege escalation techniques
  - Perform targeted analysis of specific resources

The tool is built with an extensible architecture to support additional AWS services as they are implemented.

## Installation
```bash
# Install Poetry if not already installed
pip install poetry

# Clone the repository
git clone https://github.com/yourusername/AWSome-enum.git
cd AWSome-enum

# Install dependencies using Poetry
poetry install
```

## Usage
AWSome-enum uses Poetry for dependency management and execution:

```bash
# Basic enumeration of all services
Usage: poetry run awsome-enum [-h] [-p PROFILE] [-e [SERVICE]] [subcommand] [args...]

Options:
  -h, --help                 # Show help message and exit
  -p, --profile [PROFILE]    # Specify an AWS CLI profile
  -e, --enumerate [SERVICE]  # Service to enumerate (e.g., iam, s3, lambda, etc.)
                               Use without a value to enumerate all services

Usage Examples:
  poetry run awsome-enum -h                                    # Show this help message
  poetry run awsome-enum -p [PROFILE] -e [SERVICE] -h          # Show available service-specific commands
```

### Service-Specific Enumeration
```bash
Usage: poetry run awsome-enum -e [SERVICE] [subcommand] [args...]

Enumerate AWS services and resources

Available services:
  iam
  kms
  s3
  secretsmanager

Enumeration Examples:
  poetry run awsome-enum --p [PROFILE] -e                       # Enumerates all services with default profile
  poetry run awsome-enum -p [PROFILE] -e [SERVICE] -h           # Show available service-specific commands
  poetry run awsome-enum -p [PROFILE] -e [SERVICE] [subcommand] [args...]  # Execute a specific subcommand
```

### Advanced Usage
```bash
# Example usage for iam service
Available subcommands for IAM service:

Command                     Description
-------------------------  ------------------------------------------------
  find-roles                Finds all IAM roles with matching names

Usage examples:
  poetry run awsome-enum -e iam find-roles <pattern1> [<pattern2> ...]
```

## Privilege Escalation Detection
AWSome-enum automatically flags and highlights permissions that could lead to privilege escalation by providing links to relevant sections of the [Cloud Hacktricks Wiki](https://cloud.hacktricks.wiki/) for detailed exploitation techniques.

## Prerequisites
- Python 3.9+
- AWS CLI configured with appropriate credentials
- AWS credentials with at least read access to resources

## Security Considerations
- For ethical use in authorized environments only
- Obtain proper permissions before running against any AWS account
- Some commands may generate significant AWS API activity

## Author
Taraka Vishnumolakala

## License
BSD 3-Clause License

Copyright (c) 2024, Taraka Vishnumolakala
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this
   list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.

3. Neither the name of the copyright holder nor the names of its
   contributors may be used to endorse or promote products derived from
   this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.