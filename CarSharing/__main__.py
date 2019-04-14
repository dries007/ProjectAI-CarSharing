import argparse
import logging
import multiprocessing
import os
import random
import signal
import time

from .Problem import Problem
from .input_parser import parse_input

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s [%(process)d %(levelname)s] %(message)s', datefmt='%H:%M:%S')


parser = argparse.ArgumentParser()

parser.add_argument('input', help='The input file to parse')
parser.add_argument('output', help='The output file')
parser.add_argument('runtime', type=int, default=0, help='Max runtime in seconds.', nargs='?')
parser.add_argument('seed', type=int, default=0, help='A seed for the RNG', nargs='?')
parser.add_argument('threads', type=int, default=1, help='Max number of threads.', nargs='?')
parser.add_argument('runs', type=int, default=0, help='Number of runs. Defaults to nr of threads', nargs='?')

args = parser.parse_args()


def timeout_handler(signum, frame):
    raise TimeoutError("Out of time!")


def validate(input_filename: str, output_filename: str):
    logging.info('Verified output')
    logging.info('---------------')
    os.system('java -jar validator.jar "{}" "{}"'.format(input_filename, output_filename))
    logging.info('---------------')


def main(inp, runtime, rng):
    if runtime != 0:
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(runtime)
    start = time.perf_counter()

    logging.info('Start')
    problem = Problem(rng, *parse_input(inp))
    i, stats = problem.run()
    logging.info('end')

    runtime = time.perf_counter() - start
    logging.info('Total time: %r for %d iterations -> %d Hz', runtime, i, i / runtime)
    return problem, stats, runtime


if __name__ == '__main__':
    N = args.threads if args.runs == 0 else args.runs

    with multiprocessing.Pool(args.threads) as p:
        rng = random.Random(args.seed) if args.seed != 0 else random.Random()
        main_args = [
            (args.input, args.runtime, random.Random(rng.random()))
            for _ in range(N)
        ]
        results = p.starmap(main, main_args)

    results.sort(key=lambda x: x[1][-1])
    best: Problem = results[0][0]

    best.save(args.output)
    validate(args.input, args.output)

    with open(args.output + '.stats.csv', 'a') as f:
        for _, stats, runtime in results:
            print(*stats, sep=',', file=f)
