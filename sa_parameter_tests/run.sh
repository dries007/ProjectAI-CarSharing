#!/usr/bin/env bash

# Arg 1 = input file
# Arg 2 = runtime

export DEBUG=True
export NO_SHOW=True
export PYTHONPATH=..

IN_FILE="$1"
RUNTIME="$2"

#export SA_TMAX='1000'
#export SA_TMIN='10'
#export SA_ITERATIONS='1000'
#export SA_ALPHA='0.65'

# Test every set of parameters with a resulting total iterations per run between 1k and 100k
# 110 runs x 60 sec = approx 2h!

i=0
for SA_TMAX in '100' '1000' '10000' '100000'; do
    export SA_TMAX
    for SA_TMIN in '1' '10' '100'; do
        export SA_TMIN
        for SA_ITERATIONS in '10' '100' '500' '1000' '5000' '10000'; do
            export SA_ITERATIONS
            for SA_ALPHA in '0.55' '0.65' '0.75' '0.85' '0.95'; do
                export SA_ALPHA
                PARAMETERS="${SA_TMAX}-${SA_TMIN}-${SA_ALPHA}-${SA_ITERATIONS}"
                # Only do runs with between 1k and 100k total iterations per run
                N=$(python -c "import math; print(math.ceil(math.log(${SA_TMIN} / ${SA_TMAX}, ${SA_ALPHA})) * ${SA_ITERATIONS})")
                if (( N >= 1000 && N <= 100000 )); then
                    ((i++))
                    echo "Running parameters: $PARAMETERS N: $N"
                    BASE_NAME="${IN_FILE%.*}-${PARAMETERS}"
                    # Skip any runs that already happened.
                    if [[ ! -f "${BASE_NAME}.out.csv.png" ]]; then
                        python -m CarSharing "${IN_FILE}" "${BASE_NAME}.out.csv" "${RUNTIME}" 42 1 2>&1 | tee "${BASE_NAME}.log"
                    fi
                fi
            done
        done
    done
done

echo "Total $i runs of $RUNTIME seconds"

egrep 'Saving a solution with score' -r . | sed -rn 's#./([0-9_]+)-([0-9 -]+).*([0-9]{3,})#\1,\2,\3#p' | tr '-' ',' > results.csv
