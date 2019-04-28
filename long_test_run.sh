#!/usr/bin/env bash

# Arg 1 = input file
# Arg 2 = runtime

# Move/link to ./run and chmod +x OR edit PYTHONPATH to actual project root.

export DEBUG=True
export NO_SHOW=True
export PYTHONPATH=..

IN_FILE="$1"
RUNTIME="$2"

#export SA_TMAX='1000'
#export SA_TMIN='10'
#export SA_ITERATIONS='1000'
#export SA_ALPHA='0.65'

for SA_TMAX in '100' '1000' '10000' '100000'; do
    export SA_TMAX
    for SA_TMIN in '1' '10' '100'; do
        export SA_TMIN
        for SA_ITERATIONS in '10' '100' '1000' '10000'; do
            export SA_ITERATIONS
            for SA_ALPHA in '0.55' '0.65' '0.75' '0.85' '0.95'; do
                export SA_ALPHA
                PARAMETERS="${SA_TMAX}-${SA_TMIN}-${SA_ALPHA}-${SA_ITERATIONS}"
                N=$(python -c "import math; print(math.ceil(math.log(${SA_TMIN} / ${SA_TMAX}, ${SA_ALPHA})) * ${SA_ITERATIONS})")
                echo "Parameters: $PARAMETERS N: $N"
                if (( N > 500 )); then
                    BASE_NAME="${IN_FILE%.*}-${PARAMETERS}"
                    python -m CarSharing "${IN_FILE}" "${BASE_NAME}.out.csv" "${RUNTIME}" 42 1 2>&1 | tee "${BASE_NAME}.log"
                fi
            done
        done
    done
done
