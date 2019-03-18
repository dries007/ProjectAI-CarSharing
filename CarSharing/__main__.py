import argparse
import logging
import os
import random
import signal
import time

from .Problem import Problem
from .input_parser import parse_input

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s [%(levelname)s] %(message)s', datefmt='%H:%M:%S')


parser = argparse.ArgumentParser()

parser.add_argument('input', help='The input file to parse')
parser.add_argument('output', help='The output file')
parser.add_argument('runtime', type=int, default=0, help='Max runtime in seconds.', nargs='?')
parser.add_argument('seed', type=int, default=0, help='A seed for the RNG', nargs='?')
parser.add_argument('threads', type=int, default=0, help='Max number of threads.', nargs='?')

args = parser.parse_args()


def timeout_handler(signum, frame):
    logging.warning("Out of time! Signal: %r Frame: %r", signum, frame)
    raise TimeoutError("Out of time!")


def validate(input_filename: str, output_filename: str):
    logging.info("Verified output")
    logging.info("---------------")
    os.system('java -jar validator.jar "{}" "{}"'.format(input_filename, output_filename))
    logging.info("---------------")


def main(inp, outp, threads, rng):
    start = time.perf_counter()
    problem = Problem(rng, *parse_input(inp))
    # noinspection PyBroadException
    try:
        problem.run(threads)
    except Exception:
        logging.exception("Exception during run, saving anyway...")
    problem.save(outp)
    validate(inp, outp)
    logging.info("Total time: %r", time.perf_counter() - start)


if __name__ == "__main__":
    if args.runtime != 0:
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(args.runtime)
    rng = random.Random(args.seed) if args.seed != 0 else random.Random()
    main(args.input, args.output, args.threads, rng)
