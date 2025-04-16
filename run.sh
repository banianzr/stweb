#! /bin/bash

CONENV="stweb"

CONCON=$(which conda)
CONBIN=${CONCON%/*}
CONPATH=${CONBIN%/*}

OUT=$(conda --version)
VER=${OUT#*\ }
PRI_SEC=${VER%\.*}
PRI=${PRI_SEC%%\.*}
SEC=${PRI_SEC##*\.}

if [ $PRI -lt 5 ] && [ $SEC -lt 4 ]
then
    source activate $CONENV
else
    source $CONPATH"/etc/profile.d/conda.sh"
    conda deactivate
    conda activate $CONENV
fi

export PYTHONPATH=$PYTHONPATH:`pwd`

if [ $# -eq 0 ]
then
    streamlit run main.py
else
    python $1
fi

