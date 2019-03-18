import argparse
import logging
import os
import random
import signal
import time
import multiprocessing
import itertools

from .Problem import Problem
from .input_parser import parse_input

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s [%(levelname)s] %(message)s', datefmt='%H:%M:%S')


parser = argparse.ArgumentParser()

parser.add_argument('input', help='The input file to parse')
parser.add_argument('output', help='The output file')
parser.add_argument('runtime', type=int, default=0, help='Max runtime in seconds.', nargs='?')
parser.add_argument('seed', type=int, default=0, help='A seed for the RNG', nargs='?')
parser.add_argument('threads', type=int, default=1, help='Max number of threads.', nargs='?')

args = parser.parse_args()


def timeout_handler(signum, frame):
    logging.warning("Out of time! Signal: %r Frame: %r", signum, frame)
    raise TimeoutError("Out of time!")


def validate(input_filename: str, output_filename: str):
    logging.info('Verified output')
    logging.info('---------------')
    os.system('java -jar validator.jar "{}" "{}"'.format(input_filename, output_filename))
    logging.info('---------------')


def main(inp, rng):
    start = time.perf_counter()
    problem = Problem(rng, *parse_input(inp))
    stats = []
    # noinspection PyBroadException
    try:
        problem.run(stats)
    except Exception:
        logging.exception('Exception during run, saving anyway...')
    # problem.save(outp)
    # validate(inp, outp)
    logging.info('Total time: %r', time.perf_counter() - start)
    return problem, stats


if __name__ == '__main__':
    if args.runtime != 0:
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(args.runtime)

    with multiprocessing.Pool(args.threads) as p:
        rng = random.Random(args.seed) if args.seed != 0 else random.Random()
        main_args = [
            (args.input, random.Random(rng.random()))
            for _ in range(args.threads)
        ]
        results = p.starmap(main, main_args)

    results.sort(key=lambda x: x[1][-1])
    best: Problem = results[0][0]

    best.save(args.output)
    validate(args.input, args.output)

    with open('stats.csv', 'a') as f:
        for _, stats in results:
            print(args.input, *stats, sep=',', file=f)
