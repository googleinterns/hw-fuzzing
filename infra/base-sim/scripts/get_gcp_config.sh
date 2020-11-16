#!/bin/bash -eu
# Copyright 2020 Timothy Trippel
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Metadata Server URLS
METADATA_URL="http://metadata.google.internal/computeMetadata/v1"
PROJECT_ID_URL="$METADATA_URL/project/project-id"
ZONE_URL="$METADATA_URL/instance/zone"
INSTANCE_NAME_URL="$METADATA_URL/instance/name"
AUTH_TOKEN_URL="$METADATA_URL/instance/service-accounts/default/token"

# Get GCE VM instance info
PROJECT_ID=$(curl -H "Metadata-Flavor: Google" $PROJECT_ID_URL)
ZONE=$(curl -H "Metadata-Flavor: Google" $ZONE_URL)
IFS_BACKUP=$IFS
IFS=$'/'
ZONE_SPLIT=($ZONE)
ZONE="${ZONE_SPLIT[3]}"
IFS=$IFS_BACKUP
INSTANCE_NAME=$(curl -H "Metadata-Flavor: Google" $INSTANCE_NAME_URL)

# Get GCE metadata authorization token
TOKEN=$(curl -H "Metadata-Flavor: Google" $AUTH_TOKEN_URL | python3 -c \
  "import sys, json; print(json.load(sys.stdin)['access_token'])")
