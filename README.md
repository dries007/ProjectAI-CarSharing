# "The Cambio Problem"

Project for course on AI 2018-2019 at KULeuven.

Copyright © 2019 Dries Kennes & Olivier Van den Eede

See [CourseMaterial](./CourseMaterial) for more info.

Created with Python 3.7 (Insertion order dict is required, so CPython 3.6 might work too.)

Run with `python -m CarSharing <input_file> <solution_file> [time_limit] [random_seed] [num_threads]`

## Algorithm descriptions

A list of algorithms.

### greedy_assign

_Used for the initial solution._

Assign as much requests as possible to existing cars (zone first, then neighbours), 
then assigns free cars if possible.

This is not deterministic due to the random picking of a match in 1.i.a and 1.ii.a.

1. For each request:
    1. Check every car already assigned to this zone:
        1. If their is no overlap, assign this car to this request. (random)
        2. Continue from 1.
    2. Check every car already assigned to a neighbouring zone:
        1. If their is no overlap, assign this car to this request. (random)
        2. Continue from 1.
    3. If this request has a car that is not assigned yet:
        1. Assign it to this zone & this request
        2. Continue from 1.
    4. Leave this request unassigned.

