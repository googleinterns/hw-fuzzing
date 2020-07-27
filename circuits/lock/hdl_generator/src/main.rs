use kaze::*;
use rand::Rng;
use structopt::StructOpt;

/// This tool generates lock-style state machines that output an `unlocked` flag after receiving a
/// specific sequence of input symbols. It can configurably generate the length of the unlock
/// sequence, the width of the interface, and the probability of it inserting backtracking
/// transitions.
#[derive(StructOpt)]
struct Options {
    /// The number of states between the initial and unlocked state.
    #[structopt(long, default_value = "32")]
    states: u32,

    /// The width of the registers and ports making up the lock.
    #[structopt(long, default_value = "32")]
    width: u32,

    /// The probability of inserting a reverse transition with a random input symbol.
    #[structopt(long, default_value = "0")]
    backtrack: f32,
}

fn main() -> std::io::Result<()> {
    let options = Options::from_args();

    let generator = Generator {
        states: options.states,
        width: options.width,
        backtrack: options.backtrack,
    };

    let mut context = Context::new();
    let lock = generator.generate(&mut context);
    verilog::generate(&lock, std::io::stdout())
}

struct Generator {
    states: u32,
    width: u32,
    backtrack: f32,
}

impl Generator {
    fn generate<'a>(&'a self, c: &'a mut Context<'a>) -> &'a Module {
        let mut rng = rand::thread_rng();

        let lock = c.module("lock");
        let lit = |v: u32| lock.lit(v, self.width);
        let input = lock.input("in", self.width);
        let state = lock.reg("state", self.width);

        state.default_value(0x00000000u32);

        let mut transitions = Vec::new();
        for i in 0..self.states {
            transitions.push((i, i, i + 1));
        }

        let mut next = state.value;
        for (from, trigger, to) in transitions {
            let (from, trigger, to) = (lit(from), lit(trigger), lit(to));
            next = (state.value.eq(from) & input.eq(trigger)).mux(to, next);

            if rng.gen::<f32>() < self.backtrack {
                next = (state.value.eq(to) & input.eq(lit(rng.gen::<u32>()))).mux(from, next);
            }
        }
        state.drive_next(next);

        lock.output("unlocked", state.value.eq(lit(self.states)));
        lock.output("state", state.value);

        lock
    }
}
