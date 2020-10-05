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

# Write CSV headers
echo -e "IP CORE\c" >$2
for CSV_HEADER in \
  ASSERT_I \
  ASSERT_INIT \
  ASSERT_FINAL \
  ASSERT \
  ASSERT_NEVER \
  ASSERT_KNOWN \
  ASSERT_PULSE \
  ASSERT_IF \
  ASSERT_KNOWN_IF; do
  echo -e ",\c" >>$2
  echo -e "$CSV_HEADER\c" >>$2
done
echo "" >>$2

# Write Assertion data
for IP_CORE in \
  aes \
  alert_handler \
  csrng \
  edn \
  entropy_src \
  flash_ctrl \
  gpio \
  hmac \
  i2c \
  keymgr \
  kmac \
  nmi_gen \
  otbn \
  otp_ctrl \
  padctrl \
  pinmux \
  pwrmgr \
  rstmgr \
  rv_core_ibex \
  rv_dm \
  rv_plic \
  rv_timer \
  spi_device \
  uart \
  usbdev \
  usbuart; do

  echo -e "$IP_CORE\c" >>$2

  for SVA_MACRO in \
    ASSERT_I \
    ASSERT_INIT \
    ASSERT_FINAL \
    ASSERT \
    ASSERT_NEVER \
    ASSERT_KNOWN \
    ASSERT_PULSE \
    ASSERT_IF \
    ASSERT_KNOWN_IF; do

    RTL_DIR=$1/hw/ip/$IP_CORE/rtl
    echo -e ",\c" >>$2

    if [ -d $RTL_DIR ]; then
      NUM_SVAS=$(grep -R "\`$SVA_MACRO(" $RTL_DIR | wc -l | awk '{$1=$1};1')
    else
      NUM_SVAS="0*"
    fi
    echo "$IP_CORE -- num. $SVA_MACRO: $NUM_SVAS"
    echo -e "$NUM_SVAS\c" >>$2
  done
  echo "" >>$2
  echo "---------------------------------------------"
done
