#!/usr/bin/bash
#SBATCH -o slurm-%%j.out
#SBATCH -e slurm-%%j.err
#SBATCH --nodes=%(nodes)d
#SBATCH --ntasks-per-node=%(tasks_per_node)d
#SBATCH --mem-per-cpu=%(mem)dM
#SBATCH --time=%(wt_hours)02d:%(wt_minutes)02d:%(wt_seconds)02d
#SBATCH --job-name=%(job_name)s
#SBATCH --tmp=5GB
#SBATCH --account=oz022
#SBATCH --gres=gpu:1

module load perl/5.26.1
module load lalsuite-lalapps/6.21.0

set -o errexit
set -o nounset
set -o pipefail

echo Start at: $(date)
echo "Job temporary directory: $JOBFS"

# Make sure the output directory exists
mkdir -p "%(job_output_directory)s"

echo "Job output directory: %(job_output_directory)s"

export PATH=".:$PATH"

# First set up our directories
mkdir -p $JOBFS/{data,atoms,output}

# Change to the bin directory so that paths to the perl script and bilby executable are valid
cd /fred/oz022/bilby_cw/bin/bin/

# Actually run the script
perl sch_mgr.pl --config "%(job_parameter_file)s" --task prepare

perl sch_mgr.pl --config "%(job_parameter_file)s" --task search --stage 1 --step 0-1
perl sch_mgr.pl --config "%(job_parameter_file)s" --task search --stage 2 --step 0
perl sch_mgr.pl --config "%(job_parameter_file)s" --task search --stage 3 --step 0

export COPY_OUTPUT_TO="%(job_output_directory)s"

if [ -z "${COPY_OUTPUT_TO:-}" ] ; then
	echo "You didn't ask me to put the output anywhere special so I've left it in $JOBFS/output"
else
	cp -r $JOBFS/output/ $COPY_OUTPUT_TO/
fi

cd 

# Change to the job output directory
cd "%(job_output_directory)s"

# Finally tar up all output in to one file
tar cf bilby_job_%(ui_job_id)d.tar.gz *

# Done!

echo End at: $(date)

