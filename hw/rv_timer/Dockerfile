# Docker image for fuzzing various lock circuits with AFL
ARG FUZZER=sim
FROM gcr.io/hardware-fuzzing/base-${FUZZER}
MAINTAINER ttrippel@opentitan.org

# create DUT directory
ENV DUT=$HW/lock
RUN mkdir $DUT

# Copy in HDL and testbench
RUN git clone  --depth=1 https://github.com/lowRISC/opentitan.git
COPY hdl $DUT/hdl
COPY tb $DUT/tb
COPY seeds $DUT/seeds

# Copy in build scripts
COPY Makefile $DUT/

WORKDIR $DUT
CMD ["run"]

