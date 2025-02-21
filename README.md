# AWSome-Enum

## Overview
AWSome-Enum is a comprehensive AWS security enumeration and permission analysis tool developed as part of preparation for the Hacktricks AWS Red Team Expert Exam. The project focuses on providing in-depth insights into AWS account configurations and user permissions.

## Key Features
- 🔍 AWS User Permission Enumeration
- 🚨 Interesting Permissions Detection
- 📋 Detailed Policy Analysis
- 🔐 Security Reconnaissance

## Script Capabilities
The core AWS enumeration script offers:
- Retrieve user identity information
- List and analyze attached user policies
- Detect potential privilege escalation vectors
- Support for multiple AWS CLI profiles
- Optional output to YAML file

## Usage
```bash
# Basic usage
./aws-enum.sh enumerate-user-permissions

# With specific profile
./aws-enum.sh --profile my-profile enumerate-user-permissions

# Save output to file
./aws-enum.sh --output results.yaml enumerate-user-permissions
```

## Prerequisites
- AWS CLI
- jq
- yq (v4+)

## Exam Preparation
This tool is specifically crafted to support learning and preparation for the Hacktricks AWS Red Team Expert Exam, focusing on:
- AWS IAM permission analysis
- Security misconfiguration detection
- Advanced cloud infrastructure reconnaissance

## Interesting Permissions
The script leverages a `interesting_permissions.json` file to flag potentially risky or escalation-prone permissions, providing insights into potential security weaknesses.

## Disclaimer
- For educational and authorized testing purposes only
- Always obtain proper authorization before security testing
- Use responsibly and ethically

## Contributing
Contributions that enhance AWS security enumeration techniques or support exam preparation are welcome.

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

## Author
Taraka Vishnumolakala