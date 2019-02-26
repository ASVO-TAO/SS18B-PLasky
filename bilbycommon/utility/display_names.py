"""
Distributed under the MIT License. See LICENSE.txt for more info.
"""

# VARIABLES of this file must be unique
from django_hpc_job_controller.client.scheduler.status import JobStatus


# Dictionary to map names and corresponding display names (for UI)
DISPLAY_NAME_MAP = dict()
DISPLAY_NAME_MAP_HPC_JOB = dict()


# Job Status
NONE = 'none'
NONE_DISPLAY = 'None'
DRAFT = 'draft'
DRAFT_DISPLAY = 'Draft'
PENDING = 'pending'
PENDING_DISPLAY = 'Pending'
SUBMITTING = 'submitting'
SUBMITTING_DISPLAY = 'Submitting'
SUBMITTED = 'submitted'
SUBMITTED_DISPLAY = 'Submitted'
QUEUED = 'queued'
QUEUED_DISPLAY = 'Queued'
IN_PROGRESS = 'in_progress'
IN_PROGRESS_DISPLAY = 'In Progress'
CANCELLING = 'cancelling'
CANCELLING_DISPLAY = 'Cancelling'
CANCELLED = 'cancelled'
CANCELLED_DISPLAY = 'Cancelled'
ERROR = 'error'
ERROR_DISPLAY = 'Error'
WALL_TIME_EXCEEDED = 'wall_time_exceeded'
WALL_TIME_EXCEEDED_DISPLAY = 'Wall Time Exceeded'
OUT_OF_MEMORY = 'out_of_memory'
OUT_OF_MEMORY_DISPLAY = 'Out of Memory'
COMPLETED = 'completed'
COMPLETED_DISPLAY = 'Completed'
SAVED = 'saved'
SAVED_DISPLAY = 'Saved'
DELETING = 'deleting'
DELETING_DISPLAY = 'Deleting'
DELETED = 'deleted'
DELETED_DISPLAY = 'Deleted'
PUBLIC = 'public'
PUBLIC_DISPLAY = 'Public'

# Job Types
PARAMETER_ESTIMATION = 'parameter_estimation'
PARAMETER_ESTIMATION_DISPLAY = 'Parameter Estimation'
CONTINUOUS_WAVE = 'continuous_wave'
CONTINUOUS_WAVE_DISPLAY = 'Continuous Wave'

DISPLAY_NAME_MAP.update({
    DRAFT: DRAFT_DISPLAY,
    PENDING: PENDING_DISPLAY,
    SUBMITTING: SUBMITTING_DISPLAY,
    SUBMITTED: SUBMITTED_DISPLAY,
    QUEUED: QUEUED_DISPLAY,
    IN_PROGRESS: IN_PROGRESS_DISPLAY,
    CANCELLING: CANCELLING_DISPLAY,
    CANCELLED: CANCELLED_DISPLAY,
    ERROR: ERROR_DISPLAY,
    WALL_TIME_EXCEEDED: WALL_TIME_EXCEEDED_DISPLAY,
    OUT_OF_MEMORY: OUT_OF_MEMORY_DISPLAY,
    COMPLETED: COMPLETED_DISPLAY,
    SAVED: SAVED_DISPLAY,
    DELETING: DELETING_DISPLAY,
    DELETED: DELETED_DISPLAY,
    PUBLIC: PUBLIC_DISPLAY,
})

DISPLAY_NAME_MAP_HPC_JOB.update({
    JobStatus.DRAFT: DRAFT,
    JobStatus.PENDING: PENDING,
    JobStatus.SUBMITTING: SUBMITTING,
    JobStatus.SUBMITTED: SUBMITTED,
    JobStatus.QUEUED: QUEUED,
    JobStatus.RUNNING: IN_PROGRESS,
    JobStatus.CANCELLING: CANCELLING,
    JobStatus.CANCELLED: CANCELLED,
    JobStatus.ERROR: ERROR,
    JobStatus.WALL_TIME_EXCEEDED: WALL_TIME_EXCEEDED,
    JobStatus.OUT_OF_MEMORY: OUT_OF_MEMORY,
    JobStatus.DELETING: DELETING,
    JobStatus.DELETED: DELETED,
    JobStatus.COMPLETED: COMPLETED,
})

# Data Choice
DATA_CHOICE = 'data_choice'
DATA_CHOICE_DISPLAY = 'Type of Data'
SIMULATED_DATA = 'simulated'
SIMULATED_DATA_DISPLAY = 'Simulated'
OPEN_DATA = 'open'
OPEN_DATA_DISPLAY = 'Open'

DISPLAY_NAME_MAP.update({
    DATA_CHOICE: DATA_CHOICE_DISPLAY,
    SIMULATED_DATA: SIMULATED_DATA_DISPLAY,
    OPEN_DATA: OPEN_DATA_DISPLAY,
})

# Data Parameter Choice
DETECTOR_CHOICE = 'detector_choice'
DETECTOR_CHOICE_DISPLAY = 'Detector Choice'
SIGNAL_DURATION = 'signal_duration'
SIGNAL_DURATION_DISPLAY = 'Signal Duration (s)'
SAMPLING_FREQUENCY = 'sampling_frequency'
SAMPLING_FREQUENCY_DISPLAY = 'Sampling Frequency (Hz)'
START_TIME = 'start_time'
START_TIME_DISPLAY = 'Start Time'

HANFORD = 'hanford'
HANFORD_DISPLAY = 'Hanford'
LIVINGSTON = 'livingston'
LIVINGSTON_DISPLAY = 'Livingston'
VIRGO = 'virgo'
VIRGO_DISPLAY = 'Virgo'

DISPLAY_NAME_MAP.update({
    DETECTOR_CHOICE: DETECTOR_CHOICE_DISPLAY,
    SIGNAL_DURATION: SIGNAL_DURATION_DISPLAY,
    SAMPLING_FREQUENCY: SAMPLING_FREQUENCY_DISPLAY,
    START_TIME: START_TIME_DISPLAY,
    HANFORD: HANFORD_DISPLAY,
    LIVINGSTON: LIVINGSTON_DISPLAY,
    VIRGO: VIRGO_DISPLAY,
})

# Signal Extra Fields
SAME_MODEL = 'same_model'
SAME_MODEL_DISPLAY = 'Same Signal for Model?'

# Signal Choice
SIGNAL_CHOICE = 'signal_choice'
SIGNAL_CHOICE_DISPLAY = 'Signal Inject'
SIGNAL_MODEL = 'signal_model'
SIGNAL_MODEL_DISPLAY = 'Signal Model'
SKIP = 'skip'
SKIP_DISPLAY = 'None'
BINARY_BLACK_HOLE = 'binary_black_hole'
BINARY_BLACK_HOLE_DISPLAY = 'Binary Black Hole'

DISPLAY_NAME_MAP.update({
    SIGNAL_CHOICE: SIGNAL_CHOICE_DISPLAY,
    SIGNAL_MODEL: SIGNAL_MODEL_DISPLAY,
    SKIP: SKIP_DISPLAY,
    BINARY_BLACK_HOLE: BINARY_BLACK_HOLE_DISPLAY,
})

# Signal Parameter Choice
MASS1 = 'mass_1'
MASS1_DISPLAY = 'Mass 1 (M☉)'
MASS2 = 'mass_2'
MASS2_DISPLAY = 'Mass 2 (M☉)'
LUMINOSITY_DISTANCE = 'luminosity_distance'
LUMINOSITY_DISTANCE_DISPLAY = 'Luminosity Distance (Mpc)'
IOTA = 'iota'
IOTA_DISPLAY = 'iota'
PSI = 'psi'
PSI_DISPLAY = 'psi'
PHASE = 'phase'
PHASE_DISPLAY = 'Phase'
GEOCENT_TIME = 'geocent_time'
GEOCENT_TIME_DISPLAY = 'Merger Time (GPS Time)'
RA = 'ra'
RA_DISPLAY = 'Right Ascension (Radians)'
DEC = 'dec'
DEC_DISPLAY = 'Declination (Degrees)'

DISPLAY_NAME_MAP.update({
    MASS1: MASS1_DISPLAY,
    MASS2: MASS2_DISPLAY,
    LUMINOSITY_DISTANCE: LUMINOSITY_DISTANCE_DISPLAY,
    IOTA: IOTA_DISPLAY,
    PSI: PSI_DISPLAY,
    PHASE: PHASE_DISPLAY,
    GEOCENT_TIME: GEOCENT_TIME_DISPLAY,
    RA: RA_DISPLAY,
    DEC: DEC_DISPLAY,
})

# Prior Choice
FIXED = 'fixed'
FIXED_DISPLAY = 'Fixed'
UNIFORM = 'uniform'
UNIFORM_DISPLAY = 'Uniform'

DISPLAY_NAME_MAP.update({
    FIXED: FIXED_DISPLAY,
    UNIFORM: UNIFORM_DISPLAY,
})

# Sampler Choice
DYNESTY = 'dynesty'
DYNESTY_DISPLAY = 'Dynesty'
NESTLE = 'nestle'
NESTLE_DISPLAY = 'Nestle'
EMCEE = 'emcee'
EMCEE_DISPLAY = 'Emcee'

DISPLAY_NAME_MAP.update({
    DYNESTY: DYNESTY_DISPLAY,
    NESTLE: NESTLE_DISPLAY,
    EMCEE: EMCEE_DISPLAY,
})

# Sampler Parameter Choice
NUMBER_OF_LIVE_POINTS = 'number_of_live_points'
NUMBER_OF_LIVE_POINTS_DISPLAY = 'Number of Live Points'
NUMBER_OF_STEPS = 'number_of_steps'
NUMBER_OF_STEPS_DISPLAY = 'Number of Steps'

DISPLAY_NAME_MAP.update({
    NUMBER_OF_LIVE_POINTS: NUMBER_OF_LIVE_POINTS_DISPLAY,
    NUMBER_OF_STEPS: NUMBER_OF_STEPS_DISPLAY,
})


# BILBY GW JOB DISPLAY NAMES #

# JOB_NAME = 'job_name'
# JOB_NAME_DISPLAY = 'Job Name'
# JOB_DESCRIPTION = 'job_description'
# JOB_DESCRIPTION_DISPLAY = 'Job Description'
#
# DISPLAY_NAME_MAP.update({
#     JOB_NAME: JOB_NAME_DISPLAY,
#     JOB_DESCRIPTION: JOB_DESCRIPTION_DISPLAY,
# })

DATA_SOURCE = 'data_source'
DATA_SOURCE_DISPLAY = 'Data Source'
FAKE_DATA = 'fakedata'
FAKE_DATA_DISPLAY = 'Simulated Data'
REAL_DATA = 'sfts'
REAL_DATA_DISPLAY = 'Real Data'

DISPLAY_NAME_MAP.update({
    DATA_SOURCE: DATA_SOURCE_DISPLAY,
    FAKE_DATA: FAKE_DATA_DISPLAY,
    REAL_DATA: REAL_DATA_DISPLAY,
})

# REAL Data Parameters

GLOB = 'glob'
GLOB_DISPLAY = 'glob'
START_TIME_CW = 'starttime'
START_TIME_CW_DISPLAY = 'Start Time'
DURATION = 'duration'
DURATION_DISPLAY = 'Duration'

# GLOB Choices

O1 = 'O1'
O1_DISPLAY = 'O1'
O2 = 'O2'
O2_DISPLAY = 'O2'

DISPLAY_NAME_MAP.update({
    GLOB: GLOB_DISPLAY,
    START_TIME_CW: START_TIME_CW_DISPLAY,
    DURATION: DURATION_DISPLAY,
})

# FAKE Data Parameters

H0 = 'h0'
H0_DISPLAY = 'h0'
A0 = 'a0'
A0_DISPLAY = 'a0'
ORBIT_TP = 'orbitTp'
ORBIT_TP_DISPLAY = 'orbitTp'
SIGNAL_FREQUENCY = 'signalfreq'
SIGNAL_FREQUENCY_DISPLAY = 'Signal Frequency'
# PSI , PSI_DISPAY are already there
COSI = 'cosi'
COSI_DISPLAY = 'cosi'
ALPHA = 'alpha'
ALPHA_DISPLAY = 'alpha'
DELTA = 'delta'
DELTA_DISPLAY = 'delta'
ORBIT_P = 'orbitP'
ORBIT_P_DISPLAY = 'orbitP'
RAND_SEED = 'randseed'
RAND_SEED_DISPLAY = 'randseed'
IFO = 'ifo'
IFO_DISPLAY = 'ifo'
NOISE_LEVEL = 'noiselevel'
NOISE_LEVEL_DISPLAY = 'Noise Level'

DISPLAY_NAME_MAP.update({
    H0: H0_DISPLAY,
    A0: A0_DISPLAY,
    ORBIT_TP: ORBIT_TP_DISPLAY,
    SIGNAL_FREQUENCY: SIGNAL_FREQUENCY_DISPLAY,
    COSI: COSI_DISPLAY,
    ALPHA: ALPHA_DISPLAY,
    DELTA: DELTA_DISPLAY,
    ORBIT_P: ORBIT_P_DISPLAY,
    RAND_SEED: RAND_SEED_DISPLAY,
    IFO: IFO_DISPLAY,
    NOISE_LEVEL: NOISE_LEVEL_DISPLAY,
})

