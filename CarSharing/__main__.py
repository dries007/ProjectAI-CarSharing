import argparse
import signal
import os.path
from .input_parser import parse_input
from .Solution import Solution


parser = argparse.ArgumentParser()
parser.add_argument('--runtime', '-r', type=int, default=0, help='Max runtime in seconds.')
parser.add_argument('--threads', '-j', type=int, default=0, help='Max number of threads.')
parser.add_argument('input', help='The input file to parse')

args = parser.parse_args()


# noinspection PyUnusedLocal
def timeout_handler(signum, frame):
    raise TimeoutError("Out of time!")


def main(filename):
    solution = Solution(*parse_input(filename))
    out_filename = os.path.splitext(filename)[0] + '_sol.csv'
    solution.save(out_filename)
    solution.validate(filename, out_filename)
    print(solution)


if __name__ == "__main__":
    if args.runtime:
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(args.runtime)
    main(args.input)
