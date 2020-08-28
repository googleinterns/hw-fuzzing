# Fuzzing Hardware Like Software

**Author**: Timothy Trippel <br>
**Email**: ttrippel@opentitan.org <br>
**Personal Website**: https://timothytrippel.com <br>

## Motivation

Hardware flaws are both *permanent* and *potent*. Unlike software, hardware
cannot be patched once it is fabricated. Making matters worse, hardware is
foundational: hardware flaws can completely undermine even formally verified
software that sits above. Due to the economic and reputational incentives to
design and fabricate flawless hardware, design verification research has been an
active arena. Unfortunately the fruits of this labor mainly consist of
strategies concentrated at two extremes: 1) broad coverage through constrained
random verification, or 2) (bounded) formal verification. Moreover, both of
these techniques require extensive implementation knowledge of the Design Under
Test (DUT) to be effective.

## Approach

To close this gap, we propose *fuzzing hardware like software* to
automate test vector generation in an intelligent manner---that boosts
coverage---*without* requiring expensive Design Verification (DV) engineers and
tools. Specifically, we demonstrate how to translate RTL hardware to a software
model, and leverage coverage-guided software fuzzers---like
[AFL](https://github.com/google/AFL)---to automate
test vector generation for hardware verification (Figure. 1). While we do not
suggest this as a replacement to traditional DV methods for sign-off, we argue
this technique serves a low-cost preventative mechanism to identify complex
hardware vulnerabilities *before* they are exploited for malice.

![Fuzzing HW Like SW](docs/figures/fuzzing_hardware_like_software.png
"Figure 1: Fuzzing Hardware Like Software.")

## HW Fuzzing Pipeline

Thus far, we have designed and built a *Hardware Fuzzing Pipeline*
leveraging an open-source *RTL* simulator
[Verilator](https://www.veripool.org/wiki/verilator), coverage-guided
greybox fuzzer [AFL](https://github.com/google/AFL), and
[GCP](https://cloud.google.com/). Our pipeline is modeled after Google's
[OSS-Fuzz](https://github.com/google/oss-fuzz) open-source software fuzzing
architecture and is illustrated in Figure 2.

![HW Fuzzing Pipeline](docs/figures/hw_fuzzing_pipeline.png
"Figure 2: Hardware Fuzzing Pipeline.")

## Results

Using our pipeline, we demonstrate the
power of coverage-guided test vector generation by comparing the verification
runtimes observed to achieve full FSM coverage of several sequential state
machines of various complexities. With
AFL we observe over two orders of
magnitude reduction in verification runtime to achieve full FSM coverage across
the various RTL designs we study, when compared to traditional
constrained-random verification.

## Ongoing Work

Currently, we are using this pipeline to apply these techniques to the
[OpenTitan](https://opentitan.org/) root of trust ecosystem.
