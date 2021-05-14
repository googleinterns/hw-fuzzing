// Copyright 2020 Google LLC
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//      http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

use kaze::*;
use rand::Rng;
use structopt::StructOpt;

/// This tool generates lock-style state machines that output an `unlocked` flag
/// after receiving a specific sequence of input symbols. It can configurably
/// generate the length of the unlock sequence, the width of the interface, and
/// the probability of it inserting backtracking transitions.
#[derive(StructOpt)]
struct Options {
    /// The number of states between the initial and unlocked state.
    #[structopt(long, default_value = "32")]
    states: u32,

    /// The width of the registers and ports making up the lock.
    #[structopt(long, default_value = "32")]
    width: u32,
}

fn main() -> std::io::Result<()> {
    let options = Options::from_args();

    let generator = Generator {
        states: options.states,
        width: options.width,
    };

    let mut context = Context::new();
    let lock = generator.generate(&mut context);
    verilog::generate(&lock, std::io::stdout())
}

struct Generator {
    states: u32,
    width: u32,
}

const fn num_bits<T>() -> usize { std::mem::size_of::<T>() * 8 }

fn log_2(x: u32) -> u32 {
    num_bits::<u32>() as u32 - x.leading_zeros()
}

impl Generator {
    fn generate<'a>(&'a self, c: &'a mut Context<'a>) -> &'a Module {
        let mut rng = rand::thread_rng();

        // compute width of state register
        let state_reg_width = log_2(self.states - 1u32);

        // create lock module with a single state register and trigger input
        let lock = c.module("lock");
        let input = lock.input("code", self.width);
        let state = lock.reg("state", state_reg_width);
        state.default_value(0u32);

        // define lock state transitions
        let mut next = state.value;
        for i in 0..(self.states - 1u32) {
            let trigger_value = rng.gen_range(1u64, 2u64.pow(self.width));
            let from = lock.lit(i, state_reg_width);
            let to = lock.lit(i + 1u32, state_reg_width);
            let trigger = lock.lit(trigger_value, self.width);
            next = (state.value.eq(from) & input.eq(trigger)).mux(to, next);
        }
        state.drive_next(next);

        // define lock outputs
        lock.output("unlocked", state.value.eq(lock.lit(self.states - 1u32, state_reg_width)));
        lock.output("state", state.value);

        // return HDL
        lock
    }
}
