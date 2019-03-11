import argparse
import signal
from .input_parser import parse_input
from .Solution import Solution


parser = argparse.ArgumentParser()
parser.add_argument('--runtime', '-r', type=int, default=0, help='Max runtime in seconds.')
parser.add_argument('--threads', '-j', type=int, default=0, help='Max number of threads.')

args = parser.parse_args()


# noinspection PyUnusedLocal
def timeout_handler(signum, frame):
    raise TimeoutError("Out of time!")


if args.runtime:
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(args.runtime)


if __name__ == "__main__":
    solution = Solution(*parse_input('toy1.csv'))

    print(solution)
