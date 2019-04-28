import argparse
import logging
import multiprocessing as mp
import os
import random
import signal
import subprocess as sp
import tempfile
import time

# Yey circular imports
DEBUG = 'DEBUG' in os.environ
NO_SHOW = 'NO_SHOW' in os.environ
logging.basicConfig(level=logging.DEBUG if DEBUG else logging.INFO, format='%(asctime)s [%(name)s %(levelname)s] %(message)s', datefmt='%H:%M:%S')


from CarSharing.Problem import Problem
from CarSharing.input_parser import parse_input


parser = argparse.ArgumentParser()

parser.add_argument('input', help='The input file to parse')
parser.add_argument('output', help='The output file')
parser.add_argument('runtime', type=int, default=0, help='Max runtime in seconds.', nargs='?')
parser.add_argument('seed', type=int, default=0, help='A seed for the RNG', nargs='?')
parser.add_argument('threads', type=int, default=1, help='Max number of threads.', nargs='?')


def validate(input_filename: str, output_filename: str):
    logging.info('Verified output')
    logging.info('---------------')
    args = ('java', '-jar', 'validator.jar', input_filename, output_filename)
    p = sp.Popen(args, stdout=sp.PIPE, stderr=sp.STDOUT, universal_newlines=True)
    while True:
        line = p.stdout.readline()
        if line == '':
            break
        logging.info(line.rstrip())
    logging.info('---------------')


def create_stats_graph(filename, best_cost, results):
    if NO_SHOW:
        import matplotlib as mpl
        mpl.use('Agg')
    import matplotlib.pyplot as plt
    plt.figure(figsize=(16, 9), dpi=100, frameon=False)
    plt.title('%s Best: %d' % (filename, best_cost))
    plt.xlabel('Iterations')
    plt.ylabel('Cost')

    with open(filename + '.stats.csv', 'a') as f:
        for score, name, stats in results:
            print(name, *stats, sep=',', file=f)
            plt.plot(stats)

    plt.tight_layout()
    plt.autoscale()

    plt.savefig('%s.png' % filename)
    if not NO_SHOW:
        plt.show()


def single_thead_debug_run(args, rng, inp):
    def interrupt(_, __):
        raise KeyboardInterrupt("Time's up!")

    signal.signal(signal.SIGALRM, interrupt)
    signal.alarm(args.runtime)

    start = time.perf_counter()
    total_iterations = 0
    results = []
    try:
        aborted = False
        while not aborted:
            start_i = time.perf_counter()
            problem = Problem(0, random.Random(rng.random()), *inp)
            iterations, stats, aborted = problem.run(DEBUG)
            runtime = time.perf_counter() - start_i
            problem.log.debug('Time: %r for %d iterations -> %d Hz Cost: %d', runtime, iterations, iterations / runtime, problem.solution.cost)
            total_iterations += iterations
            results.append((problem.solution.cost, stats, problem))
    except (KeyboardInterrupt, TimeoutError):
        pass

    runtime = time.perf_counter() - start
    logging.debug('Global runtime: %r for %d iterations -> %d Hz', runtime, total_iterations, total_iterations / runtime)
    results.sort(key=lambda x: x[0])

    with open(args.output, 'w') as f:
        results[0][2].save(f)

    results = [(cost, args.output, stats) for cost, stats, problem in results]
    create_stats_graph(args.output, results[0][0], results)


def proc_main(queue: mp.Queue, i, root, rng, inp):
    """
    Main function for subprocess
    :param queue: Pass values back to master
    :param i: thread/job number
    :param root: Root folder
    :param rng: RNG number to be used as seed
    :param inp: The input arguments for Problem as tuple
    """
    proc_best_score = None
    proc_best_instance = None
    proc_best_stats = None
    try:
        aborted = False
        while not aborted:
            problem = Problem(i, random.Random(rng), *inp)
            rng += 1
            start = time.perf_counter()
            iterations, stats, aborted = problem.run(DEBUG)
            runtime = time.perf_counter() - start
            problem.log.debug('Time: %r for %d iterations -> %d Hz Cost: %d', runtime, iterations, iterations / runtime, problem.solution.cost)

            if proc_best_score is None or problem.solution.cost < proc_best_score:
                problem.log.debug('New best run with cost: %d', problem.solution.cost)
                proc_best_score = problem.solution.cost
                proc_best_instance = problem
                proc_best_stats = stats
    except (KeyboardInterrupt, TimeoutError):
        pass

    # Store the result to a tmp file. If it's the best, it will get moved/renamed by the main thread.
    # This is such a filthy hack, but it works. Passing back the whole problem/solution obj does not.
    with tempfile.NamedTemporaryFile(mode='w', delete=False, dir=root, prefix='tmp-', suffix='.csv') as f:
        proc_best_instance.save(f)
    queue.put((proc_best_score, f.name, proc_best_stats))


def main():
    # Start times
    start = time.perf_counter()
    global_start = start

    # Parsing input is a done once, because it's common anyway.
    logging.info('Parsing input...')

    args = parser.parse_args()
    logging.debug('Args: %r', args)
    root = os.path.dirname(os.path.abspath(args.output))
    logging.info('Working & output dir: %r', root)
    rng = random.Random(args.seed) if args.seed != 0 else random.Random()
    inp = parse_input(args.input, False)

    # For performance profiling ONLY, it can't use multiple processes.
    # This could be used if the threads parameter was 1 EXCEPT it doesn't write the file in time.
    if args.threads == 1 and DEBUG:
        single_thead_debug_run(args, rng, inp)
        return

    # The queue is used to pass back values to the mail thread.
    queue = mp.Queue()
    # Setup workers
    procs = [mp.Process(target=proc_main, args=(queue, i, root, rng.random(), inp)) for i in range(args.threads)]

    # post-Start, pre-Compute times
    end = time.perf_counter()
    startup_time = end - start
    logging.info('Startup time: %r', startup_time)
    start = end

    # Start workers
    for p in procs:
        p.start()

    # Keep some time to save the best result. Saving should be comparable to the starting up.
    sleep_time = args.runtime - 3 * startup_time
    logging.info('Target compute time: %r', sleep_time)
    # Sleep until workers need to die.
    if sleep_time < 0:
        sleep_time = 60*60*24*356.25*10  # See you in 10 years...
    try:
        time.sleep(sleep_time)
    except (KeyboardInterrupt, TimeoutError):
        pass

    # Tell workers to die (sigint = ctrl+c = KeyboardInterrupt = good because of try-except)
    for p in procs:
        os.kill(p.pid, signal.SIGINT)

    # post-Compute, pre-Save times
    end = time.perf_counter()
    compute_time = end - start
    logging.info('Effective compute time: %r', compute_time)
    start = end

    # Wait for threads to clean up after themselves and pass back the results
    results = [queue.get() for _ in procs]

    # Get the best result
    best_cost, best_filename, best_stats = min(results, key=lambda x: x[0])
    # Rename the file to the proper output name
    os.replace(best_filename, args.output)

    # post-Save & total times
    end = time.perf_counter()
    save_time = end - start
    global_time = end - global_start
    logging.info('Save time: %r', save_time)
    logging.info('Global time: %r', global_time)

    # No longer counts for time, just some stats/plots, and cleanup :)
    # ================================================================

    # Cleanup, technically not required, so not counted towards the timers.
    for result, filename, stats in results:
        # Already moved.
        if filename != best_filename:
            os.unlink(filename)

    validate(args.input, args.output)

    if DEBUG:
        create_stats_graph(args.input, best_cost, results)


if __name__ == '__main__':
    main()
