# TODO(ttrippel): include license header

# Docker image for fuzzing various lock circuits with AFL
ARG FUZZER=sim
FROM gcr.io/hardware-fuzzing/base-${FUZZER}
MAINTAINER ttrippel@opentitan.org

# create DUT directory
ENV DUT=$HW/rv_timer
RUN mkdir $DUT

# Copy in HDL and testbench
RUN apt-get install -y git
RUN git clone --depth=1 https://github.com/lowRISC/opentitan.git
RUN apt-get remove --purge -y git && apt-get autoremove -y
COPY hdl $DUT/hdl
COPY tb $DUT/tb
COPY seeds $DUT/seeds

# Copy in build scripts
COPY Makefile $DUT/

WORKDIR $DUT
CMD ["run"]
