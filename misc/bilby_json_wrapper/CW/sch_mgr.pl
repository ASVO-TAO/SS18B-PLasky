#!/usr/bin/env perl

# The V2 search manager.
# See also my notebook for more information.
# Author: Patrick Clearwater <p.clearwater@student.unimelb.edu.au>

use strict;
use warnings;

use Getopt::Long;
use JSON;
use LWP::UserAgent;
use POSIX;
use File::Basename;
use File::Temp;
use File::Path;
use Hash::Merge::Simple;
use Fcntl;
use Text::Wrap;
use Data::Dumper;
use File::Slurp;

sub usage {
	"$0 -- search manager for V2O2. Options are:
 --config=   Search configuration file
 --task=     What to do:
        prepare    -- perform preparatory work (e.g. download data)
        describe   -- describe the work to be done, as a series of stages:
          For example: stage 1 - 45 steps - prepare atoms
                       stage 2 - 12896 steps - run search
        helpconfig -- show help about how the configuration file should be written
        help       -- this help
        search     -- run the search
 --stage=    (for task = search) which stage to run
 --step=     (for task = search) which job step to run (can specify multiple as 4-7 for steps 4 to seven, or use a simple expression like 5*4 to mean 'steps 20 - 24')
 --help      Show this help
"
}

sub main {
	my ($config_file, $task, $stage, $step, $help);
	GetOptions(
		'config=s' => \$config_file,
		'task=s' => \$task,
		'stage=i' => \$stage,
		'step=s' => \$step,
		'help' => \$help,
	);
	if($help || !defined $task || $task eq 'help') {
		die usage;
	}
	if($task eq 'helpconfig') {
		helpconfig();
		exit(0);
	}

	if($task ne 'prepare' && $task ne 'describe' && $task ne 'search') {
		die "Didn't understand the value to --task";
	}

	# Right, now read in the configuration file
	my $config = load_config($config_file);

	# What are we doing? help and helpconfig are dealt with already. If we want
	# to prepare, then we need to check what's there, and download it if it
	# isn't. Conversely, if we want to search, we still need to check whether
	# what we need is there. Thus, we can handle that together, and bail out if
	# we're just preparing (and if we're not preparing, then we'll be bailed
	# out automatically when checking that the source data are there).
	my $scoreboards = check_search_for_find_h0($config, $task eq 'prepare');
	my $first_stage = check_datasource($config, $task eq 'prepare');
	if($task eq 'prepare') {
		return; # Done!
	}

	# If we've made it here, then all the source data are present and accounted
	# for. If $first_stage is defined, the first stage is whatever that is
	# (usually generating SFTs, for data sources that don't provide them);
	# in any event, the next stage will be atom-caching and then the third
	# stage will be actually running the search.
	#
	# The way this is structured, we gather up all the tasks that need to be
	# done (in stages which are dependent on the previous one). We can then
	# do them (if the user has asked for that). We are careful to ensure that
	# we always generate the stages in the same order, so that they easily fit
	# into a SLURM-style "do N things in an array" model.
	#
	# Elements on the @stages array are hashrefs that look like this:
	# {
	#   name => "human readable name",
	#   tasks => [],
	# }
	# Then elements of the task arrayref are hashrefs that look like this:
	# {
	#   done => 0, # has this been done yet?
	#   task => coderef, # thing to call to actually run the coderef
	#   data => {}, # opaque hashref that gets passed to the task coderef
	#   description =>, # human readable description
	# }
	my @stages;
	push @stages, $first_stage if defined $first_stage;

	# Injections
	if(defined $config->{injection}) {
		push @stages, prepare_injection_stage($config);
	}

	my $engine_cache_stage = prepare_engine($config);
	push @stages, $engine_cache_stage if defined $engine_cache_stage;

	my $search_stage = prepare_search($config, $scoreboards);
	push @stages, $search_stage;

	# Now we've drawn up a plan for what we're going to do. We either do that,
	# or describe it to the user (depending on what they've asked for)
	if($task eq 'describe') {
		describe($config, $stage, $step, \@stages);
	} elsif($task eq 'search') {
		run_search($config, $stage, $step, \@stages);
	}
}

sub prepare_injection_stage {
	my ($config) = @_;

	# We want to inject a signal on top of the data we've been provided from
	# the previous stage (which could of course be anything). We're going to do
	# that, and then re-write the _realisation sftglobs to point in the right
	# place.
	# Makefakedata has an option, --noiseSFTs, that will do exactly what we
	# want, as long as we're careful to match up the times &c carefully.
	my $stage = {
		name => "Inject the signal",
		tasks => [],
	};

	# We want to create a new SFT for each existing SFT. In our case, this is
	# made slightly more difficult by the fact the SFTs could be anything, but
	# we can be completely self-consistent by calling lalapps_dumpSFT on them.
	# However, lalapps_dumpSFT is relatively slow, and so we don't actually
	# look inside the files, yet.

	mkdir $config->{injection}->{datadir}.'/sft';
	for my $realisation (@{$config->{datasource}->{_realisations}}) {
		my ($realisation_name, $sftglob) = @$realisation;
		# TODO: allow generation of a binary signal
		my %args = (
			outSingleSFT => 1,
			h0           => $config->{injection}->{h0},
			cosi         => $config->{injection}->{cosi},
			psi          => $config->{injection}->{psi},
			Alpha        => $config->{injection}->{alpha},
			Delta        => $config->{injection}->{delta},
			window       => 'None',
			_sftglob     => $sftglob,
			_datadir     => $config->{injection}->{datadir},
		);

		# We can never reliably tell we're done, but the injection wrapper
		# handles that for us.
		my $task = {
			done => 0,
			task => \&call_Makefakedata_injection_wrapper,
			data => \%args,
			description => (defined $realisation_name ? "Signal injection for realisation $realisation_name" : 'Signal injection'),
		};
		push @{$stage->{tasks}}, $task;
	}
	return ($stage);
}

sub prepare_search {
	my ($config, $scoreboards) = @_;
	if($config->{engine}->{implementation} eq 'CJS') {
		return prepare_search_CJS($config, 0, $scoreboards);
	} elsif($config->{engine}->{implementation} eq 'CJS_GPU') {
		return prepare_search_CJS($config, 1, $scoreboards);
	} elsif($config->{engine}->{implementation} eq 'CFS') {
		return prepare_search_CFS($config);
	} # has to be valid, because it was checked in prepare_engine
}

my %special_cache;
sub prepare_search_CJS {
	my ($config, $is_GPU, $scoreboards) = @_;
	# We're searching over different choices of a0, phi_a.
	my @a0_choices = expand_range($config->{search}->{a0});
	my ($phi_name, @phi_choices);
	if(defined $config->{search}->{phi}) {
		$phi_name = 'phi';
		@phi_choices = expand_range($config->{search}->{phi});
	} else {
		$phi_name = 'orbitTp';
		@phi_choices = expand_range($config->{search}->{orbitTp});
	}

	my $stage = {
		name => "Search over a0, phi",
		tasks => [],
	};

	# Work out what options to pass to CJS so that we get the output that's
	# been asked for.
	-d $config->{output}->{dir} or die "Output directory doesn't exist: $config->{output}->{dir}";
	my %extra_args; # What extra args do we need to add to CJS?
	foreach my $type (@{$config->{output}->{capture}}) {
		if($type eq 'bestpath') {
			# At the moment, we don't need to do anything special for this,
			# because as soon as the --viterbiOutputDirectory is set, CJS
			# automatically gives us the best path
			$extra_args{viterbiOutputDirectory} = $config->{output}->{dir};
		} elsif($type =~ m/^path>([\d.]+)$/) {
			$extra_args{viterbiOutputDirectory} = $config->{output}->{dir};
			$extra_args{viterbiThreshold} = $1;
		} else {
			die "Unrecognised capture type in output section";
		}
	}

	for my $a0 (@a0_choices) {
	for my $phi (@phi_choices) {
	my $realisation_index = 0;
	for my $realisation (@{$config->{datasource}->{_realisations}}) {
		my ($realisation_name, $sftglob) = @{$realisation};
		my %args = (
			alpha => $config->{search}->{alpha},
			delta => $config->{search}->{delta},
			minStartTime => $config->{datasource}->{starttime},
			maxStartTime => $config->{datasource}->{starttime} + $config->{datasource}->{duration},
			freqStart => $config->{search}->{freq},
			freqBand => $config->{search}->{band},
			dataFiles => $sftglob,
			'orbital-P' => $config->{search}->{orbitP},
			$phi_name => $phi,
			driftTime => $config->{viterbi}->{driftTime},
			rngMedWindow => 90,
			loadFstatAtoms => $config->{engine}->{_acdir}->[$realisation_index] . '/atoms-%03d.dat',
			dFreq => (1 / (2 * $config->{viterbi}->{driftTime})),
			%extra_args, # Output control options
		);
		if(defined $config->{engine}->{bandWingSize}) {
			$args{bandWingSize} = $config->{engine}->{bandWingSize};
		}

		# Handle a0. Since we allow searching over a0 ranges, and also need to
		# support differing syntax for GPU vs CJS, we need to be a bit careful
		# with this.
		if(ref($a0) eq 'ARRAY') {
			if($is_GPU) {
				$args{a0_band} = ($a0->[2] - $a0->[0]);
				$args{central_a0} = $a0->[0] + ($a0->[2] - $a0->[0]) / 2;
				$args{a0_bins} = int(($a0->[2] - $a0->[0])/$a0->[1]);
			} else {
				$args{asini} = $a0->[0];
				$args{'asini-step'} = $a0->[1];
				$args{'asini-end'} = $a0->[2];
			}
		} else {
			if($is_GPU) {
				$args{central_a0} = $a0;
				$args{a0_band} = 0;
				$args{a0_bins} = 1;
			} else {
				$args{asini} = $a0;
			}
		}

		# TODO: This is a bit ugly, think of a better way of handling it...
		if($args{viterbiOutputDirectory}) {
			$args{viterbiOutputDirectory} .= '/' . (defined $realisation_name ?  "i=$realisation_name," : '') . "a0=$a0,$phi_name=$phi";
			if($config->{output}->{use_process_specific_results_file}) {
				$args{_output_file} = $config->{output}->{dir} . '/' . (defined $realisation_name ?  "i=$realisation_name" : 'bestpaths').".$$.summary";
			} else {
				$args{_output_file} = $config->{output}->{dir} . '/' . (defined $realisation_name ?  "i=$realisation_name" : 'bestpaths').'.summary';
			}
			$args{_output_mode} = $config->{output}->{summarise};
		}
		# How to tell if we're done? TODO: in the future, come up with a
		# more elegant way of determining this (one that loops over all of
		# the 'capture' elements) -- but for now, we'll just check for the
		# presence of best.path in the vOD.
		my $done = 0;
		if(($config->{output}->{summarise} // '') ne 'all') {
			$done = (defined $args{viterbiOutputDirectory} ? -e $args{viterbiOutputDirectory}.'/best.path' : 0);
			#print "check $args{viterbiOutputDirectory}.'/best.path'";
		} # else we'll deal with it later, when we open the file

		if($is_GPU) {
			# If we're using the GPU code, then we need to replace a few of the
			# arguments with new ones
			delete $args{alpha};
			delete $args{delta};
			$args{start_time} = delete $args{minStartTime};
			delete $args{maxStartTime};
			delete $args{freqStart};
			delete $args{freqBand};
			delete $args{dataFiles};
			$args{P} = delete $args{'orbital-P'};
			# Thankfully 'phi' and 'orbitTp' are spelt the same way in both
			# codes...
			$args{"central_$phi_name"} = delete $args{$phi_name};
			$args{"${phi_name}_band"} = 0;
			$args{"${phi_name}_bins"} = 1;
			$args{tblock} = delete $args{driftTime};
			$args{block_size} = 1048576;
			delete $args{rngMedWindow};
			$args{cjs_atoms} = delete $args{loadFstatAtoms};

			if($args{bandWingSize}) {
				# In this case we need to be a bit careful. Originally, we
				# based --bandWingSize to CJS, which would have caused it to
				# create jstat atoms for the range [search band start - wing
				# size, search band end + wing size]. To loop the GPU code in
				# on this tomfoolery, we need to tell it we have a larger block
				# size (matching the actual, generated block size), and then
				# pass in an appropriate --ignore_wing parameter.
				# Remember both block_size and are in bins, not frequency, so
				# we convert them using 1/tdrift
				my $fdrift = (1 / (2 * $config->{viterbi}->{driftTime}));
				my $wing_size = delete $args{bandWingSize};
				$args{block_size} = $args{block_size} + sprintf("%.0f", 2*$wing_size/$fdrift);
				$args{ignore_wings} = sprintf("%.0f", 1*$wing_size/$fdrift)
			}

			if($args{viterbiOutputDirectory}) {
				$args{out_prefix} = delete($args{viterbiOutputDirectory}) . '/';
			}
			if($args{viterbiThreshold}) {
				die "CJS_GPU doesn't support thresholds.";
			}
		}

		my $this_task = {
			done => $done,
			task => ($is_GPU ? \&CJS_GPU_output_handler : \&CJS_output_handler),
			data => \%args,
			description => sprintf("Search for a0 = %f, %s = %f, i = %s (%d)", $a0, $phi_name, $phi, $realisation_name // 'undef', $realisation_index),
			_realisation => $realisation_name,
			_asini => $a0,
			_orbitTp => $phi, # TODO: replace with $phi and $phi_name
		};
		# Now we have a bit of ugliness to do. If $scoreboards is undefined,
		# simply add $this_task to the set of tasks.
		# However, if $scoreboards is defined, then this is a 'find_h0' style
		# search, and we need to do the full search as a single step, i.e.,
		# each element of @$stage->tasks corresponds to a particular
		# realisation index.
		unless(defined $scoreboards) {
			push @{$stage->{tasks}}, $this_task;
		} else {

			# A *further* ugliness in this case is that in the special case of
			# doing an upper limit search, we need to "reach in" to each task
			# and update its a0, orbitTp range to match what was injected
			if($config->{search}->{special_case_for_upper_limits}) {
				$is_GPU and die "special_case_for_upper_limits not implemented for GPU search";

				# We want to match the actual search grid used for the V2O2
				# search (which means a bit of hard-coding). That search is
				# between
				#   a0: 1.45 to 3.25
				# orTp: 897753894 to 897754094
				# and the number of bins is given in the text CSV template file
				# that is the argument to this key.
				if(!%special_cache) {
					%special_cache = map { chomp; my @q = split /,/, $_; ($q[0] => [$q[1], $q[2]]) } File::Slurp::read_file($config->{search}->{special_case_for_upper_limits});
				}
				defined $special_cache{$config->{search}->{freq}} or die "no number of templates entry";
				my $num_tpl = $special_cache{$config->{search}->{freq}};

				# OK, for this realisation, we need to overwrite the a0 and
				# orbitTp specified in the args. For now we support the CPU
				# code only which hopefully makes it a bit easier
				# asini, asini-step, asini-end
				# orbitTp, orbitTp-step, orbitTp-end

				my $target_a0 = $realisation->[2]->{orbitasini};
				my ($a0_start, $a0_end) = (1.45, 3.25);
				my $a0_step_size = ($a0_end - $a0_start) / $num_tpl->[0];
				# What is the nearest bin?
				my $nearest_a0_bin = $a0_start + $a0_step_size * sprintf("%0.0f", ($target_a0 - $a0_start) / $a0_step_size);
				# THUS
				$this_task->{data}->{asini} = $nearest_a0_bin - $a0_step_size;

				my $target_oTp = $realisation->[2]->{orbitTp};
				my ($oTp_start, $oTp_end) = (897753894, 897754094);
				my $oTp_step_size = ($oTp_end - $oTp_start) / $num_tpl->[1];
				# What is the nearest bin?
				my $nearest_oTp_bin = $oTp_start + $oTp_step_size * sprintf("%0.0f", ($target_oTp - $oTp_start) / $oTp_step_size);
				# THUS
				$this_task->{data}->{orbitTp} = $nearest_oTp_bin - $oTp_step_size;
				if(defined($config->{search}->{special_case_oTP_subtract})) {
					$this_task->{data}->{orbitTp} -= $config->{search}->{special_case_oTP_subtract};
				}
				#$this_task->{data}->{orbitTp} = $nearest_oTp_bin - $oTp_step_size;

				if(!($config->{search}->{special_case_for_upper_limits_closest_bin})) {
					$this_task->{data}->{'asini-step'} = $a0_step_size;
					$this_task->{data}->{'asini-end'} = $nearest_a0_bin + 1.1*$a0_step_size;
					$this_task->{data}->{'orbitTp-step'} = $oTp_step_size;
					$this_task->{data}->{'orbitTp-end'} = $nearest_oTp_bin + 1.1*$oTp_step_size;
				}

			}

			$stage->{tasks}->[$realisation_index] //= {
				done => 0,
				task => \&run_find_h0_subtasks,
				# realisation->[2] here is the realisation_info struct, put in
				# here for MfD-type multi-realisation tasks only in
				# check_datasource_mfd
				data => { scoreboard => $scoreboards->[$realisation_index], r => $realisation->[2], r_idx => $realisation_index, r_name => $realisation_name, subtasks => [] },
				description => sprintf("Do the search for realisation %s (%d)", $realisation_name // 'undef', $realisation_index)
			};
			push @{$stage->{tasks}->[$realisation_index]->{data}->{subtasks}}, $this_task;
		}
		++$realisation_index;
	} # for each realisation
	} # for each phi
	} # for each a0

	# Now, fix up the $done in that $stage. As above, how we do this depends on
	# whether or not we're doing a find_h0 style search.
	if(defined $scoreboards) {
		foreach my $i (0..scalar(@$scoreboards)-1) {
			$stage->{tasks}->[$i]->{done} = ($scoreboards->[$i]->{final_h0} ne 'incomplete');
		}
	} else {
		# Since the user can ask us to write to a summary file (per
		# realisation), we open it up and mark as done all tasks that appear in
		# the file.
		for my $realisation (@{$config->{datasource}->{_realisations}}) {
			my ($realisation_name, undef) = @{$realisation};
			my $summary_file = $config->{output}->{dir} . '/' . (defined $realisation_name ?  "i=$realisation_name" : 'bestpaths').'.summary';
			-e $summary_file or next; # No summary file? Nothing to do...
			my $summary_data = read_summary_file($summary_file);

			# Now go through all of the tasks and fix them up
			foreach my $t (@{$stage->{tasks}}) {
				if(defined $realisation_name) {
					next unless $t->{_realisation} eq $realisation_name;
				} # realisation name not defined? only one, then
				if(ref($t->{_asini}) eq 'ARRAY') {
					# In this case, the hashref won't contain the correct a0 value
					# (we search over it in the GPU code but don't correctly write
					# it to the output file).
					# Instead, we check to see if the number of entries
					# corresponding to a particular orbitTp is correct
					my ($key) = grep { /^[^,]+,$t->{_orbitTp}$/ } keys %$summary_data;
					if(defined $key) {
						# TODO: this > test is not fantastic
						if($summary_data->{$key} >= int(($t->{_asini}->[2] - $t->{_asini}->[0])/$t->{_asini}->[1])) {
							$t->{done} = 1;
						}
					}
				} else {
					# Check to see whether that particular task has a result
					my $key = $t->{_asini} . ',' . $t->{_orbitTp};
					if($summary_data->{$key}) {
						$summary_data->{$key} = 'DONE'; # for debugging
						$t->{done} = 1;
					}
				}
			}
		}
	}

	return $stage;
}

sub prepare_search_CFS {
	my ($config) = @_;
	not defined $config->{viterbi} or die "At the moment, we don't support Viterbi searches using ComputeFstatistic";

	# At the moment, this is just an isolated search, so there's nothing to
	# search over.
	# However, we *do* allow the user to specify the "segmentation" parameter
	# to generate Fstats cleverly segmented by N durations.
	$config->{engine}->{segmentation} //= $config->{datasource}->{duration};
	my $n_segs = POSIX::ceil($config->{datasource}->{duration} / $config->{engine}->{segmentation});

	my %args = (
		Alpha     => $config->{search}->{alpha},
		Delta     => $config->{search}->{delta},
		Freq      => $config->{search}->{freq},
		FreqBand  => $config->{search}->{band},
	);
	$args{ephemEarth} = $config->{search}->{ephem_earth} if defined $config->{search}->{ephem_earth};
	$args{ephemSun} = $config->{search}->{ephem_sun} if defined $config->{search}->{ephem_sun};

	my @tasks;
	foreach my $realisation (@{$config->{datasource}->{_realisations}}) {
		my ($rname, $sftglob) = @{$realisation};
		$rname //= 'the'; # For single-realisation runs

		my %extraargs = (
			%args,
			DataFiles => $sftglob,
		);

		# And now, per segment...
		for my $seg_num (0 .. ($n_segs - 1)) {
			# Work out extra arguments we'll need for the various forms of output we
			# can capture. At the same time, we work out if we've got that output
			# (which would imply the task is done)
			my %extraargs2 = (
				%extraargs,
				minStartTime => $config->{datasource}->{starttime} + ($seg_num * $config->{engine}->{segmentation}),
				maxStartTime => $config->{datasource}->{starttime} + (($seg_num + 1) * $config->{engine}->{segmentation}),
			);

			my $done = 1;
			foreach (@{$config->{output}->{capture}}) {
				if($_ eq 'fstat') {
					my $fstat_path = "$config->{output}->{dir}/i=${rname}_${seg_num}.fstat";
					-e $fstat_path or $done = 0;
					$extraargs2{outputFstat} = $fstat_path;
				}
			}
			push @tasks, {
				done => $done,
				task => \&call_ComputeFStatistic,
				data => \%extraargs2,
				description => "Run ComputeFstatistic_v2 for realisation $rname, segment $seg_num",
			}
		}
	}

	return {
		name => "Compute F-statistic",
		tasks => \@tasks,
	}
}

sub prepare_engine {
	my ($config) = @_;
	# Check that the engine {} section is right, and if so, prepare tasks for
	# (e.g.) preparing the atomcache.
	if($config->{engine}->{implementation} eq 'CJS') {
		return prepare_engine_CJS($config);
	} elsif($config->{engine}->{implementation} eq 'CFS') {
		# Nothing to do here
	} elsif($config->{engine}->{implementation} eq 'CJS_GPU') {
		# Note that we need regular CJS to prepare the atoms (in exactly the
		# same way it does for a CJS-based search) so we can just call p_e_CJS
		# without doing anything special
		return prepare_engine_CJS($config);
	} else {
		die "Sorry, for now, only these engines are supported:
 - CJS (ComputeJStatistic)
 - CJS_GPU (ComputeJStatistic for atoms, GPU code for search)
 - CFS (ComputeFstatistic_2)";
	}
}

sub prepare_engine_CJS {
	my ($config) = @_;
	# ComputeJStatistic performance is greatly enhanced if we record the
	# F-statistic atoms first, and then do the main search (over a0 and phi0).
	# At some point in the future, it might be nice to support not doing this
	# (e.g. if you just want to quickly do a single a0/phi).
	defined $config->{engine}->{atomcache} or die "Need to specify atomcache for CJS";
	my $atomcache = $config->{engine}->{atomcache};
	my ($alpha, $delta) = ($config->{search}->{alpha}, $config->{search}->{delta});


	# For this to work, we will need to have a driftTime specified
	defined $config->{viterbi}->{driftTime} or die "No driftime specified (specify in the 'viterbi' section)";

	my $stage = {
		name => "Prepare atom cache",
		tasks => [],
	};

	# One per realisation
	$config->{engine}->{_acdir} = [];

	foreach my $realisation (@{$config->{datasource}->{_realisations}}) {
		my ($rname, $sftglob) = @{$realisation};
		# CJS can actually handle preparing the whole atomcache in one go, as
		# long as the F-statistic parameters (principally sky position) are
		# fixed.
		# TODO: Work out how to support multiple sky positions cleanly.
		mkdir "$atomcache/atoms";
		my $acdir = "$atomcache/atoms/" . (defined $rname ? "i=$rname," : '') . "alpha=$alpha,delta=$delta/";
		mkdir $acdir;
		push @{$config->{engine}->{_acdir}}, $acdir;

		# We just need one single task here. To work out if we've already done
		# this, we check for the presence of *every* atom.
		my $decades = int($config->{datasource}->{duration} / $config->{viterbi}->{driftTime})-1;
		my $done = 1;
		for my $i (0..$decades) {
			if(! -e sprintf("%s/atoms-%03d.dat", $acdir, $i)) {
				print "no check on " . sprintf("%s/atoms-%03d.dat", $acdir, $i) . "\n";
				$done = 0;
				last;
			}
		}

		# Normally we use the same bandwidth for generating the atoms as we do
		# for the search (and that is set by what the user asked for). However,
		# this leads to sensitivity loss at the edge of the band, because some
		# of the sidebands "fall out" of the side of the search band.
		# To avoid this, the user can ask us to generate atoms that are larger,
		# and then later only process a subset of them.
		# This is handled different between the GPU and CPU code (CPU - pass
		# search band and --bandWingSize; GPU - run atoms through CJS first,
		# and then pass appropriate blocksize)
		my $args = {
			alpha => $alpha,
			delta => $delta,
			minStartTime => $config->{datasource}->{starttime},
			maxStartTime => $config->{datasource}->{starttime} + $config->{datasource}->{duration},
			# Now, we don't need a wider band
			freqStart => $config->{search}->{freq},
			freqBand => $config->{search}->{band},
			dataFiles => $sftglob,
			asini => 1, # dummy for atoms
			'orbital-P' => 1,
			phi => 1,
			driftTime => $config->{viterbi}->{driftTime},
			rngMedWindow => 90,
			saveFstatAtoms => "$acdir/atoms-%03d.dat",
			dFreq => (1 / (2 * $config->{viterbi}->{driftTime})),
		};
		if(defined $config->{engine}->{bandWingSize}) {
			$args->{bandWingSize} = $config->{engine}->{bandWingSize};
		}

		my $task = {
			done => $done,
			task => \&call_ComputeJStatistic,
			data => $args,
			description => "Generate the F-statistic atoms",
		};
		push @{$stage->{tasks}}, $task;
	}

	return $stage;
}

sub describe {
	my ($config, $stageno, $task, $stages) = @_;
	# If --stage wasn't specified, then just print a summary
	if(not defined $stageno) {
		print "Plan is as follows:\n";
		printf "%4s %-45s %11s\n", 'Stg#', 'Description', 'Compl/Total';
		printf "%4s %-45s %11s\n", '----', '-' x 45, '-' x 11;
		my $i = 1;
		foreach(@$stages) {
			my $total = scalar @{$_->{tasks}};
			my $completed = scalar grep { $_->{done} } @{$_->{tasks}};
			printf "%4d %-45s %5d/%5d\n", $i, $_->{name}, $completed, $total;
			++$i;
		}
	} else {
		print "Steps for stage $stageno:\n";
		printf "%1s %-6s %-75s\n", ' ', 'Step', 'Description';
		printf "%1s %6s %75s\n", '-', '-' x 6, '-' x 75;
		my $stage = $stages->[$stageno-1];
		my $i = 0;
		foreach my $step (@{$stage->{tasks}}) {
			printf "%1s % 6d %-75s\n", ($step->{done} ? '*' : ' '), $i, $step->{description};
			++$i;
		}
	}
}

sub run_search {
	my ($config, $stageno, $task, $stages) = @_;
	defined $stageno or die "Specify the stage to run.\n";
	defined $task or die "Specify the task(s) to run.\n";
	my $stage = $stages->[$stageno-1];
	# We support multiple tasks but not multiple stages
	# In the user interface, stages are one-indexed but tasks are zero-indexed.
	# (For better or worse.)

	# Work out what tasks we need to do.
	my @tasks;
	if($task =~ /^\d+$/) {
		@tasks = ($task);
	} elsif($task =~ /^(\d+)-(\d+)$/) {
		@tasks = ($1..$2);
	} elsif($task =~ /^(\d+)\*(\d+)$/) {
		# i.e. something that looks like 8*4
		# This is interpreted to mean "suppose we're doing this in tasks of 8
		# at a time -- I want you to do the fifth such tranche" (because the
		# first is of course numbered 0)
		my $start = $1 * $2;
		my $end = $start + $1 - 1;
		@tasks = ($start..$end);
	} else {
		die "Unrecognised task specification: $task\n";
	}

	foreach my $t (@tasks) {
		my $task = $stage->{tasks}->[$t];
		if(not defined $task) {
			print "Stage $stageno, step $t: no such task, moving on.\n";
		} elsif($task->{done}) {
			print "Stage $stageno, step $t: completed already, moving on.\n";
		} else {
			print "Stage $stageno, step $t: executing.\n";
			$task->{task}->($config, $task->{data});
		}
	}
}

sub run_find_h0_subtasks {
	my ($config, $data) = @_;
	# First, run the search
	my $i = 1;
	foreach my $subtask (@{$data->{subtasks}}) {
		print "Running substep $i.\n";
		$subtask->{task}->($config, $subtask->{data});
		++$i;
	}

	my $scoreboard = $data->{scoreboard};

	# Did we detect the signal?
	my ($detect, $false_alarms) = check_if_detected($config, $data->{r_name}, $data->{r}->{Freq} // $config->{datasource}->{signalfreq}, $data->{r}->{orbitasini} // $config->{datasource}->{a0}, $data->{r}->{orbitTp} // $config->{datasource}->{orbitTp});
	print "got $detect detections, $false_alarms false alarms\n";

	my $history_h0;
	if($scoreboard->{current_h0} eq 'low') {
		$history_h0 = '(low) ' . $scoreboard->{h0_low};
	} elsif($scoreboard->{current_h0} eq 'high') {
		$history_h0 = '(high) ' . $scoreboard->{h0_high};
	} else {
		$history_h0 = '(mid) ' . $scoreboard->{h0_mid};
	}
	push @{$scoreboard->{history}}, "Search at h0 = $history_h0. Found $false_alarms false alarms, $detect detection(s).";

	if($scoreboard->{current_h0} eq 'low') {
		# This is the first time through, and we *expect* not to detect it
		# (indeed, if we do detect it, we error out)
		if($detect) {
			die "Error - *detected* the signal at the lowest h0!";
		} else {
			# Now check that the high *is* detectable
			$scoreboard->{current_h0} = 'high';
		}
	} elsif($scoreboard->{current_h0} eq 'high') {
		# The *second* time through, now we *do* expect to detect it, and apply
		# the inverse of the rules above
		if($detect) {
			$scoreboard->{current_h0} = 'mid';
		} else {
			die "Error - could *not* detect the signal at the highest h0!";
		}
	} else {
		# This is the most common case, we've just checked the midpoint
		# In this case, we are doing a binary search.
		if($detect) {
			# Move the high down to the mid
			$scoreboard->{h0_high} = $scoreboard->{h0_mid};
		} else {
			# Inverse - move the low point up to the mid
			$scoreboard->{h0_low} = $scoreboard->{h0_mid};
		}
		$scoreboard->{h0_mid} = $scoreboard->{h0_low} + ( ($scoreboard->{h0_high} - $scoreboard->{h0_low}) / 2);
		# Have we closed the gap enough?
		if(($scoreboard->{h0_high} - $scoreboard->{h0_low}) < $config->{search}->{h0_tolerance}) {
			# Perfect, we're done
			$scoreboard->{final_h0} = $scoreboard->{h0_mid};
		} else {
			# Nothing to do here?
		}
	}

	# Now delete everything, if we haven't found the final h0
	if($scoreboard->{final_h0} eq 'incomplete') {
		# Remove SFTs
		my $seed = $data->{r_name};
		foreach my $ifo (@{$config->{datasource}->{ifo}}) {
			my $sftfile = $config->{datasource}->{datadir} . "/sft/${seed}_$ifo.sft";
			unlink($sftfile);
		}
		# Remove atoms
		# TODO: need to put some of this in a separate function or it'll
		# kill me
		my $acdir = $config->{engine}->{atomcache} . '/atoms/i=' . $data->{r_name} . ',alpha=' . $config->{search}->{alpha} . ',delta=' . $config->{search}->{delta} . '/';
		File::Path::remove_tree($acdir);
		# Remove results
		for my $q (qw(summary detections)) {
			my $filename = $config->{output}->{dir} . '/i=' . $data->{r_name} .  '.' . $q;
			unlink($filename);
		}
	}

	# And write out the scoreboard
	flock_write($config->{search}->{find_h0_scoreboard_dir} . '/scoreboard_' .  $data->{r_idx} . '.json', JSON::encode_json($scoreboard));
}

sub check_if_detected {
	my ($config, $realisation_name, $freq, $a0, $orbitTp) = @_;
	# Looking at paths over the threshold (which of course is set by the user),
	# and then comparing them to the injected frequency.

	# We're looking for output_dir/i=${realisation_name}.detections
	my $filename = $config->{output}->{dir} . '/i=' . $realisation_name .  '.detections';
	# If that file doesn't exist, then there were no detections and no false
	# alarms
	if(! -f $filename) {
		return (0, 0);
	}
	# The fields are:
	# a0 orbitTp a0 phi score last_freq
	open my $fh, '<', $filename or die "Couldn't open detections file $filename";
	my $any_true_detection = 0;
	my $false_alarms = 0;
	while(<$fh>) {
		my $true_detection = 1;
		my ($cand_a0, $cand_orbitTp, undef, undef, $score, $cand_freq) = split /\s+/;

		# a0 right -- is it close by? (We allow the neighbouring bins.)
		my $search_a0 = $config->{search}->{a0_tolerance};
		#if(ref($search_a0) eq 'ARRAY') {
		#$search_a0 = $search_a0->[1]
		#}
		my $search_orbitTp = $config->{search}->{orbitTp_tolerance};
		#if(ref($search_orbitTp) eq 'ARRAY') {
		#$search_orbitTp = $search_orbitTp->[1]
		#}

		if(abs($a0 - $cand_a0) > $search_a0) {
			print "reject as wrong a0 $a0 - $cand_a0\n";
			$true_detection = 0;
		}
		# are we within one orbitTp bin?
		# TODO: do we need to handle phi here?
		elsif(abs($orbitTp - $cand_orbitTp) > $search_orbitTp) {
			print "reject as wrong otp |$orbitTp - $cand_orbitTp| > $search_orbitTp\n";
			$true_detection = 0;
		}
		# what about frequency -- are we within 37 bins?
		# TODO: make this more configurable
		#elsif(abs($cand_freq - $freq) > 37 * (1/(2*864000))) {
		elsif(abs($cand_freq - $freq) > 0.05) {
			print "reject as wrong freq $cand_freq - $freq\n";
			$true_detection = 0;
		}

		if($true_detection) {
			$any_true_detection = 1;
		} else {
			++$false_alarms;
		}
	}
	close $fh;

	return ($any_true_detection, $false_alarms);
}

# This sub handles setting up, in the case we're doing a find_h0-type search.
# If search.mode == find_best_path, then there are no scoreboard shenanigans,
# and this sub will return undef.
# If search.mode == find_h0, then this sub will load the scoreboards (which are
# per-realisation), and return them as an (appropriately-sorted) array.
# In the latter case, if the scoreboards don't exist, then is_prepare controls
# what the sub does. If is_prepare is true, then it creates fresh scoreboards;
# if is_prepare is false, it dies.
sub check_search_for_find_h0 {
	my ($config, $is_prepare) = @_;
	if($config->{search}->{mode} ne 'find_h0') {
		return undef;
	}

	# Check we have the keys we need
	defined $config->{search}->{$_} or die "Missing key from 'search': $_"
	  foreach qw/h0_low h0_high h0_tolerance find_h0_scoreboard_dir/;

	# And some more checks...
	my $r_num = $config->{datasource}->{realisations};
	if(!defined($r_num)) {
		die "Need to specify datasource.realisations (number of realisations) when doing a find_h0-type search.";
	}
	my $dir = $config->{search}->{find_h0_scoreboard_dir};
	if(!-d $dir) {
		die "find_h0_scoreboard_dir doesn't exist (or not a directory)";
	}

	# Load/create all realisations.
	my @realisations;
	for my $i (0..$r_num-1) {
		if(-e "$dir/scoreboard_$i.json") {
			push @realisations, load_json("$dir/scoreboard_$i.json");
		} elsif($is_prepare) {
			my $mid = (($config->{search}->{h0_high} - $config->{search}->{h0_low}) / 2) + $config->{search}->{h0_low};
			my $scoreboard = {
				final_h0 => 'incomplete',
				h0_low => $config->{search}->{h0_low},
				h0_high => $config->{search}->{h0_high},
				h0_mid => $mid,
				current_h0 => 'low',
				history => []
			};
			push @realisations, $scoreboard;
			flock_append("$dir/scoreboard_$i.json", JSON::encode_json($scoreboard));
		} else {
			die "Scoreboard doesn't exist for realisation $i.";
		}
	}

	# Now put the right 'h0' value into the datasource. Since all the
	# realisations can be at different places, it goes in as an array (which,
	# of course, is also a syntax allowed in the JSON datafile)
	$config->{datasource}->{h0} = [map { get_numeric_h0_from_scoreboard($_) } @realisations];

	return \@realisations;
}

sub get_numeric_h0_from_scoreboard {
	my $s = shift;
	if($s->{current_h0} eq 'low') {
		return $s->{h0_low};
	} elsif($s->{current_h0} eq 'high') {
		return $s->{h0_high};
	} elsif($s->{current_h0} eq 'mid') {
		return $s->{h0_mid};
	} else {
		die 'Unrecognised current_h0 value in scoreboard';
	}
}

sub check_datasource {
	my ($config, $download_missing) = @_;
	if(not defined $config->{datasource}->{source}) {
		die "Incomplete configuration: please specify datasource->source.";
	}
	if($config->{datasource}->{source} eq 'LOSC') {
		return check_datasource_losc($config, $download_missing);
	} elsif($config->{datasource}->{source} eq 'fakedata') {
		# fakedata generated with lalapps_Makefakedata_v4
		return check_datasource_mfd($config, $download_missing);
	} elsif($config->{datasource}->{source} eq 'sfts') {
		return check_datasource_rawsft($config, $download_missing);
	} else {
		die "Unrecognised datasource source: " . $config->{datasource}->{source};
	}
}

sub check_datasource_rawsft {
	# This is for SFTs that are sitting there on disk -- relatively easy to
	# handle, we just need to massage a few things
	# TODO: should we check the glob is 'right' i.e. actually matches
	# something?
	my ($config, $is_prepare) = @_;

	defined $config->{datasource}->{$_} or die "Missing key from 'datasource' section: $_"
	  foreach qw/glob starttime duration/;
	# We don't directly need starttime or duration, but they're needed for a
	# Viterbi search

	# The SFT glob is really easy to handle here... :)
	$config->{datasource}->{_realisations} = [ [undef, $config->{datasource}->{glob}] ];

	# Don't need to return a stage
	return undef;
}

sub check_datasource_mfd {
	my ($config, $is_prepare) = @_;
	# Check whether we have everything we need

	defined $config->{datasource}->{$_} or die "Missing key from 'datasource' section: $_"
	  foreach qw/datadir h0 ifo starttime duration cosi psi signalfreq alpha delta/;

	# Need either noiselevel or noisesfts
	if(!defined($config->{datasource}->{noiselevel}) && !defined($config->{datasource}->{noisesfts})) {
		die "Must specify either noiselevel or noisesfts in 'datasource' section";
	}

	# Some stuff we can infer
	# We first check that there's some frequency somewhere
	if(! defined $config->{datasource}->{freq} && ! defined $config->{search}->{freq}) {
		die "Need to specify 'freq' in at least the 'search' section";
	}
	if(! defined $config->{datasource}->{band} && ! defined $config->{search}->{band}) {
		die "Need to specify 'band' in at least the 'search' section";
	}

	# TODO: figure out how wide the comb should be -- for now we just add 0.5Hz
	# on either side
	$config->{datasource}->{freq} //= $config->{search}->{freq} - 0.5;
	$config->{datasource}->{band} //= $config->{search}->{band} + 1;

	my $realisation_data;
	if(defined $config->{datasource}->{randseed}) {
		$realisation_data = [to_array($config->{datasource}->{randseed})];
	} elsif(defined $config->{datasource}->{realisations}) {
		defined $config->{datasource}->{seedfile} or die "Need to specify the location of the seedfile in the 'datasource' block";
		$realisation_data = seedfile($config->{datasource}->{seedfile}, $config->{datasource}->{realisations}, $is_prepare);
	} else {
		die "Need to specify at least one of randseed or realisations in the 'datasource' block";
	}

	my $stage = {
		name => "Generate the fake dataset",
		tasks => [],
	};

	my %args = (
		outSingleSFT => 1,
		startTime    => $config->{datasource}->{starttime},
		duration     => $config->{datasource}->{duration},
		fmin         => $config->{datasource}->{freq},
		Band         => $config->{datasource}->{band},
		Tsft         => 1800,
		h0           => $config->{datasource}->{h0},
		cosi         => $config->{datasource}->{cosi},
		psi          => $config->{datasource}->{psi},
		Freq         => $config->{datasource}->{signalfreq},
		Alpha        => $config->{datasource}->{alpha},
		Delta        => $config->{datasource}->{delta},
	);
	$args{noiseSqrtSh} = $config->{datasource}->{noiselevel} if defined $config->{datasource}->{noiselevel};
	# Orbital parameters, if specified
	# (We tell using the presence of the orbitP key)
	if($config->{datasource}->{orbitP}) {
		$args{orbitPeriod} = $config->{datasource}->{orbitP};
		$args{orbitEcc}    = $config->{datasource}->{orbitEcc} // 0;
		$args{orbitTp}     = $config->{datasource}->{orbitTp}  // 0;
		$args{orbitasini}  = $config->{datasource}->{a0}       // 0;
		$args{orbitArgp}   = $config->{datasource}->{orbitargp} // 0;
	}
	my $datadir_sft = $config->{datasource}->{datadir}."/sft";
	if(! -d $datadir_sft) {
		mkdir $datadir_sft or die "Couldn't create SFT output directory $datadir_sft: $!";
	}
	$config->{datasource}->{_realisations} = [];

	my @ifos = to_array($config->{datasource}->{ifo});
	my $noiselevels = undef;
	if(ref($config->{datasource}->{noiselevel}) eq 'ARRAY' &&
	  scalar(@{$config->{datasource}->{noiselevel}}) == scalar(@ifos)) {
		$noiselevels = $config->{datasource}->{noiselevel};
	}

	# If noiselevels wasn't specified, then noisesfts will be
	my $noisesfts = undef;
	if(defined $config->{datasource}->{noisesfts}) {
		# TODO: should we verify ref eq ARRAY, etc?
		$noisesfts = [to_array($config->{datasource}->{noisesfts})];
	}

	# For now, we just support making one big SFT (per IFO). In the future,
	# we'll support:
	#  * breaking the SFTs into decades for a more convenient handling

	# To handle generating injection parameters on a per-realisation basis
	# (that is, to handle things like randomly selected injection frequencies),
	# we copy the arguments hash, and then loop over it. Anything that is a
	# hashref we replace with a number (where the hashref tells us how to do
	# that).
	# Since we need to remember the parameters we generated, we store them in
	# the same file the realistions are stored in, namely, the seedfile.
	my $seedfile_needs_updating = 0;
	my $i = 0;
	foreach my $realisation_info (@$realisation_data) {
		# $realisation_info can either be a hash of data from the realisations
		# seedfile (in which case it has the random seed inside it, as well as
		# potentially other per-realisation information); OR it can just be a
		# number (from a list of -- or single -- number specified directly in
		# the 'datasource' block). In the former case, we unwrap it to get the
		# actual seed here, and in a moment we'll handle other information that
		# may be in it. In the latter case, we don't support other
		# realisation-specified info (i.e., everything must be specified in the
		# 'datasource' block).
		my $seed = (ref($realisation_info) eq 'HASH' ?  $realisation_info->{randseed} : $realisation_info);
		my %per_realisation_args = ( %args );

		# If we have per-realisation info, go through the arguments and find
		# the ones that are hashes. (Arrays will be stuff like interferometers
		# and other per-ifo data.)
		foreach my $k (keys %per_realisation_args) {
			if(ref($per_realisation_args{$k}) eq 'HASH') {
				if($realisation_info->{$k}) {
					# Just replace the hash with the pre-calculated data
					$per_realisation_args{$k} = $realisation_info->{$k};
				} else {
					if(!$is_prepare) {
						die "Realisation file seems incomplete (missing $k for '$seed'). Run with --task=prepare first.\n";
					}
					my $rv = process_plan_hash($per_realisation_args{$k});
					$per_realisation_args{$k} = $rv;
					$realisation_info->{$k} = $rv;
					$seedfile_needs_updating = 1;
				}
			}
		}

		# Allow per-realisation h0s. At the moment this is done only for h0
		# (for the benefit of the find_h0 search mode)... but there may well be
		# some value in extending this to more options. Could easily be done by
		# adding another limb to the if() above (for ref(...) eq 'ARRAY'), but
		# then need to think carefully about anything else that might be an
		# array type.
		if(ref($per_realisation_args{h0}) eq 'ARRAY') {
			$per_realisation_args{h0} = $per_realisation_args{h0}->[$i];
		}

		my $per_ifo = 0;
		foreach my $ifo (@ifos) {
			my $new_args = { %per_realisation_args,
				outSFTbname  => "$config->{datasource}->{datadir}/sft/${seed}_${ifo}.sft",
				IFO          => $ifo,
				randSeed     => $seed,
			};
			if(defined $noiselevels) {
				$new_args->{noiseSqrtSh} = $noiselevels->[$per_ifo];
			}
			if(defined $noisesfts) {
				$new_args->{noiseSFTs} = $noisesfts->[$per_ifo];
				$new_args->{window} = 'None';
			}
			my $task = {
				done => -e $new_args->{outSFTbname},
				task => \&call_Makefakedata,
				data => $new_args,
				description => "Generate data for realisation $seed, ifo $ifo",
			};
			push @{$stage->{tasks}}, $task;
			++$per_ifo;
		}
		# Only one entry per realisation (i.e., not per IFO per realisation)
		push @{$config->{datasource}->{_realisations}}, [$seed, $config->{datasource}->{datadir}."/sft/${seed}_*.sft", $realisation_info];
		++$i;
	}

	if($seedfile_needs_updating) {
		# We must be in "prepare" mode if we get here
		write_seedfile($config->{datasource}->{seedfile}, $realisation_data);
	}

	return $stage;
}

sub seedfile {
	my ($filename, $number, $is_prepare) = @_;
	# A 'seedfile', for Makefakedata, stores the random seeds associated with
	# each realisation. This function looks for the seedfile. If it's there, it
	# checks that it's valid (i.e., has the right number of random seeds, and
	# they all look like numbers); if it's not there, then it generates it (if
	# $is_prepare is true, otherwise it complains).
	# Formerly, a seedfile was a file with one seed per line. However, since
	# we want to support the ability to generate (e.g.) random injections, it's
	# now a JSON file. This function returns the whole JSON file, but concerns
	# itself only with the random seeds part of things. Generating the other
	# random parameters is handled in check_datasource_mfd.
	if(open my $fh, '<', $filename) {
		local $/;
		my $json_text = <$fh>;
		my $json_data = JSON::decode_json($json_text);
		my @random_numbers;
		foreach(@$json_data) { chomp;
			$_->{randseed} =~ m/^-?\d+$/ or die "Bad data on line $. of random seed file: $_";
			push @random_numbers, $_->{randseed};
		}
		scalar(@random_numbers) == $number or die "Wrong number of random seeds in random seed file";
		close $fh;
		return $json_data;
	} else {
		$is_prepare or die "Random seed file is missing (or can't be read) -- run with --task=prepare to generate it";

		my @random_numbers;
		foreach (1..$number) {
			my $rand = int(rand(2**32)-2**31);
			# Pedantically avoid generating '0' as a random number, because
			# Makefakedata_v4 will interpret this as "no random seed supplied,
			# go get your own randomness" and, in the frighteningly unlikely
			# event that happens, it will be the world's most annoying
			# reproducibility problem to debug
			while(!$rand) { $rand = int(rand(2**32)-2**31); }
			push @random_numbers, { randseed => $rand };
		}
		open my $fh, '>', $filename or die "Couldn't open random seed file $filename for writing: $!";
		print $fh JSON::encode_json(\@random_numbers);
		close $fh;
		return \@random_numbers;
	}
}

sub write_seedfile {
	my ($filename, $data) = @_;

	open my $fh, '>', $filename or die "Couldn't open seedfile: $filename";
	print $fh JSON::encode_json($data);
	close $fh;
}

my %LOSC_RUN_URLS = (
	'O1' => 'https://losc.ligo.org/archive/links/O1/%{ifo}/1126051217/1137254417/json/',
);
sub check_datasource_losc {
	# Check whether we have all the data we need from the LIGO open science
	# centre.
	my ($config, $download_missing) = @_;
	if(not defined $LOSC_RUN_URLS{$config->{datasource}->{run}}) {
		die "I don't currently have support for LOSC data for run " . $config->{datasource}->{run};
	}
	my $cachedir = $config->{datasource}->{localcache};
	if(not -d $cachedir) {
		die "Local cache directory doesn't seem to exist; I refuse to go any further.";
	}
	if(not defined $config->{datasource}->{ifo}) {
		die "Please specify the interferometer(s) you want to use.";
	}
	# Get a useragent ready
	my $ua = LWP::UserAgent->new;
	$ua->env_proxy;
	# Great! LOSC gives us a file list. We download the whole thing to the
	# cache (i.e., not just for the time range requested -- to save effort) and
	# then use that to check if we have the frame files.
	my @ifos = to_array($config->{datasource}->{ifo});
	# Start and end time for the overall search
	my ($starttime, $endtime) = ($config->{datasource}->{starttime}, $config->{datasource}->{starttime} + $config->{datasource}->{duration});
	(defined $starttime && defined $endtime) or die "Search configuration missing start and end.";
	my @gwf_files;
	for my $ifo (@ifos) {
		if(! -e "$cachedir/index/$ifo") {
			if($download_missing) {
				mkdir "$cachedir/index";
				download_to($ua, substitutestr($LOSC_RUN_URLS{$config->{datasource}->{run}}, { ifo => $ifo }), "$cachedir/index/$ifo");
			} else {
				die "Dataset incomplete, please re-run with --prepare. (Missing $ifo index file.)";
			}
		}

		# Now that we have the index file, we can load it in, find the files
		# that we're interested in (based on the requested starttime and
		# duration), and check that they're present/download them
		my $indexfile = load_json("$cachedir/index/$ifo");
		foreach my $entry (@{$indexfile->{strain}}) {
			# This is the start and end of *this entry*
			next unless $entry->{format} eq 'gwf';
			my ($start, $end) = ($entry->{GPSstart}, $entry->{GPSstart} + $entry->{duration});
			if($start >= $starttime && $end <= $endtime) {
				# We want this one!
				# Check to see if it's available
				my $filename = (split(m@/@, $entry->{url}))[-1];
				if(! -e "$cachedir/data/$filename") {
					if($download_missing) {
						mkdir "$cachedir/data";
						download_to($ua, $entry->{url}, "$cachedir/data/$filename");
					} else {
						die "Dataset incomplete, please re-run with --prepare. (Missing datafile $filename.)";
					}
				}
				push @gwf_files, $entry;
			}
		}

	}
	# Create the frame cache file
	# We just do this unconditionally, because it's quick, and it's relatively
	# combersome to work out if the frame cache file needs updating
	call_lalapps_cache("$cachedir/data/*.gwf", "$cachedir/frames.lcf");

	# We want to end up with SFTs. However, LOSC only gives us GWF files.
	# Since the process of generating SFTs is quite a laborious one, we
	# treat it as "stage 1" for LOSC-derived datasets.
	# The way we communicate this is necessary is by going through all the
	# GWF files, working out what needs to be done, and creating tasks for
	# them. In order to ensure that calls are idempotent, if we see the
	# SFTs are already there, we'll still return the task, but mark it
	# done.
	#
	# For LOSC, we handle SFTs by making SFTs that are 5 Hz wide (and
	# trusting CJS will patch them back up, if a search crosses a 5 Hz
	# boundary).
	#
	# TODO: properly figure out how wide the comb is
	# (for now we just add a 0.5 Hz buffer on each side and hope that's
	# enough)
	if(! defined $config->{search}->{freq} && ! defined $config->{search}->{band}) {
		die "Frequency band not defined, so I can't generate LOSC SFTs.";
	}
	my $comb = 0.5;
	my $low_freq = $config->{search}->{freq} - $comb;
	my $high_freq = $config->{search}->{freq} + $config->{search}->{band} + $comb;
	$low_freq = POSIX::floor($low_freq);
	$low_freq -= $low_freq % 5;
	my $start_freq = $low_freq;
	my @bands;
	while($start_freq < $high_freq) {
		push @bands, $start_freq;
		$start_freq += 5;
	}
	my $stage = {
		name => "Generate SFTs from LOSC GW data",
		tasks => [],
	};
	# We create the SFTs using the standard lalapps_MakeSFTs tool. However, we
	# can only create SFTs where there are segments that are at least 1800 sec
	# long. For this, we use the segment file specified in the database.
	defined $config->{datasource}->{segments} or die "Malformed input: I need to know the valid segments.";
	my @segments = (ref $config->{datasource}->{segments} ? @{$config->{datasource}->{segments}} : $config->{datasource}->{segments});
	if(scalar @segments != scalar @ifos) { die "Malformed input: need one (and only one) segment file per interferometer."; }

	mkdir "$cachedir/sft";
	# Tell other parts of the program where to find the SFTs.
	# (We can use 'undef' as the realisation name, because there's only going
	# to be one realisation of LOSC data.)
	$config->{datasource}->{_realisations} = [ [undef, "$cachedir/sft/*.sft"] ];

	foreach my $ifo_idx (0..$#ifos) {
		my $ifo = $ifos[$ifo_idx];
		my $segfile = $segments[$ifo_idx];
		my $segments = read_segment_file($segfile, $config->{datasource}->{starttime}, $config->{datasource}->{starttime} + $config->{datasource}->{duration});

		foreach my $seg (@$segments) {
			foreach my $band (@bands) {
				my %args = (
					'high-pass-freq' => 7,
					'sft-write-path' => "$cachedir/sft/",
					'sft-duration' => 1800,
					'frame-cache' => "$cachedir/frames.lcf",
					'gps-start-time' => $seg->[0],
					'gps-end-time' => $seg->[1],
					'channel-name' => "$ifo:LOSC-STRAIN",
					'start-freq' => $band,
					'band' => (5 - (2/3600)),
					'misc-desc' => "${band}Hz",
				);
				my $name = get_makeSFTs_name($ifo, 1800, $seg->[0], $band);
				push @{$stage->{tasks}}, {
					done => (-e "$cachedir/sft/$name"),
					task => \&call_makeSFTs,
					data => \%args,
					description => "Make SFT for " . $ifo . " starting " .  $seg->[0] . " at ${band}Hz",
				};
			}
		}
	}
	return $stage;
}

sub load_config {
	my ($config_file) = @_;
	# Check if the configuration file is there, valid, etc
	# And if so, return it; otherwise, die
	# We check the major bits are there, but it's the responsibility of each
	# handler to check that the bits it needs are there
	# (e.g., we check there is a "datasource" key, but we don't check that the
	# right bits are there/directories that should exist do/etc)
	if(not defined $config_file) {
		die "Please specify configuration file with --config";
	}
	if(! -e $config_file) {
		die "Configuration file $config_file doesn't exist.";
	}
	my $config = load_json($config_file);

	# If there are any template files to include, do that now, before any other
	# processing.
	if(defined $config->{template}) {
		my $tpl_config = {};
		foreach (to_array($config->{template}->{file})) {
			# Simple rule: we load the file "in order", so start at the first
			# file, go through to the last file, and then go through the rest
			# of *this* file, with at all times, new bits replace old bits.
			# Remember for H::M::S::merge, the right-hand hash takes
			# precedence.
			$tpl_config = Hash::Merge::Simple::merge($tpl_config, load_config($_));
		}
		$config = Hash::Merge::Simple::merge($tpl_config, $config);
	}

	# Now do some basic checks on the decoded file
	if(ref($config) ne 'HASH') {
		die "Config file malformed: should be a hash at the outermost level.";
	}
	if(not defined $config->{name}) {
		$config->{name} = "(unnamed search)";
	}
	for my $sec (qw/datasource engine search output/) {
		if(not defined $config->{$sec}) {
			die "Config file malformed: required section $sec missing";
		}
	}
	# Now, pre-process the config file to handle convenience features.
	# That is, for *every* leaf, we substitute in variables
	# For all "duration-like" leaves, we convert "Xd" -> X * 86400
	my $substitutions = {
		o1start     => 1126051217,
		o2start     => 1164562334,
		aligo_noise => '4e-24',
		pi          => 3.14159265359,
		'2pi'       => 6.28318530718,
	};
	# Allow environment variables to be substituted in
	foreach (keys %ENV) {
		$substitutions->{"ENV_$_"} = $ENV{$_};
	}

	$config = substitute_recursive($config, $substitutions);
	defined $config->{datasource}->{duration} and $config->{datasource}->{duration} = process_duration($config->{datasource}->{duration});
	defined $config->{engine}->{segmentation} and $config->{engine}->{segmentation} = process_duration($config->{engine}->{segmentation});
	if(defined $config->{viterbi}) {
		defined $config->{viterbi}->{driftTime} and $config->{viterbi}->{driftTime} = process_duration($config->{viterbi}->{driftTime});
	}
	# We also cleverly allow the use of defaults in the "search" and the
	# "datasource" blocks
	load_search_defaults($config, 'datasource');
	load_search_defaults($config, 'search');
	load_search_defaults($config, 'injection') if defined $config->{injection};

	# A few default values
	$config->{search}->{mode} //= 'find_best_path';

	my %valid_search_modes = qw(find_best_path 1 find_h0 1);
	exists $valid_search_modes{$config->{search}->{mode}} or die "Unrecognised search mode.";

	print "Loaded configuration file $config_file for search '" . $config->{name} . "'\n";
	return $config;
}

sub load_search_defaults {
	my ($config, $section) = @_;
	defined $config->{$section}->{base} or return; # If they're not using the feature, do nothing
	my %DEFAULTS = (
		ScoX1 => {
			# Scorpius X1
			alpha => 4.27569923849971,
			delta => -0.250624917263256,
			psi => 4.08407044966673,
			cosi => 0.7193398003,
			a0 => 1.44,
			orbitTp => 897_753_994,
			orbitP => 68023.7,
		},
		ScoX1_isolated => {
			# Scorpius X1 as if it was an isolated neutron star (not LMXB)
			alpha => 4.27569923849971,
			delta => -0.250624917263256,
			psi => 4.08407044966673,
			cosi => 0.7193398003,
		}
	);
	if(defined $DEFAULTS{$config->{$section}->{base}}) {
		my $defs = $DEFAULTS{$config->{$section}->{base}};
		$config->{$section}->{$_} //= $defs->{$_} foreach keys %$defs;
	} else {
		die "Using target " . $config->{$section}->{base} . " as a base for $section parameters, but I don't know that target!";
	}
}

sub call_Makefakedata {
	my ($config, $args) = @_;
	call_generic('lalapps_Makefakedata_v4', $args);
}

sub call_Makefakedata_injection_wrapper {
	my ($config, $args) = @_;
	# This sub is designed to help out prepare_injection_stage. As well as the
	# Makefakedata arguments, we get a special '_sftglob' argument. We then
	# expand that glob, and for each SFT add its specific parameters:
	#   startTime, endTime
	#   fmin, fband
	# on to args, and then call Makefakedata.
	my $sftglob = $args->{_sftglob};
	my $datadir = $args->{_datadir};
	delete $args->{_sftglob};
	delete $args->{_datadir};
	foreach my $file (glob $sftglob) {
		# Reprocess the name
		# TODO: do we run a risk of name collisions here?
		my $filename = File::Basename::basename($file);
		if(-e $filename) { print "Skipping $file, injection prepared already...\n"; }

		my %new_args = %$args;
		# Call and parse lalapps_dumpSFT to get 
		my $sftinfo = `lalapps_dumpSFT -H -i $file`;
		defined $sftinfo or die "Error with the lalapps_dumpSFT call";
		# We need to get this information: lowest starting time, highest
		# starting time, frequency start & band, Tsft, IFO
		my ($fmin, $fband, $tsft, $ifo, $deltaf, $numbins);
		my @times;
		foreach (split /\n/, $sftinfo) {
			if(m/Name:\s+'(..)'/) {
				$ifo = $1;
			} elsif(m/epoch:\s+\[(\d+), (\d+)\]/) {
				# TODO: handle fractional seconds (?)
				push @times, $1;
			} elsif(m/f0:\s+([\d.]+)/) {
				$fmin = $1;
			} elsif(m/deltaF:\s+([\d.]+)/) {
				$deltaf = $1;
			} elsif(m/numBins:\s+(\d+)/) {
				$numbins = $1;
			}
		}
		defined $ifo or die "Couldn't read IFO from $file";
		defined $fmin or die "Couldn't read fmin from $file";
		defined $deltaf or die "Couldn't read deltaf from $file";
		defined $numbins or die "Couldn't read bin count from $file";
		scalar(@times) or die "Couldn't find any times in $file";
		$fband = $deltaf * $numbins;
		# Verify the SFT is full of contiguous times
		my $tstart = $times[0];
		my $tlast;
		foreach (@times) {
			if(not defined $tlast) {
				$tlast = $tstart;
				next;
			}
			$tsft //= $tlast - $_;
			if($_ != $tlast + $tsft) {
				die "Bad SFTs: times don't fit nicely.";
			}
			$tlast = $_;
		}
		$tsft //= 1800; # TODO: come up with some other plan here?
		# OK, now stuff that into the arguments
		$new_args{outSFTbname} = $datadir.'/'.$filename;
		$new_args{startTime} = $tstart;
		$new_args{duration}  = scalar(@times) * $tsft;
		$new_args{Tsft}      = $tsft;
		$new_args{fmin}      = $fmin;
		$new_args{Band}      = $fband;
		$new_args{noiseSFTs} = $file;
		$new_args{IFO}       = $ifo;
		call_Makefakedata(\%new_args);
	}
}

sub call_generic {
	my ($prg, $args) = @_;
	print "DEBUG command will be: " . join(' ', $prg, map { ('--'.$_ => $args->{$_}) } keys %$args) . "\n";
	my $rv = system($prg, map { ('--'.$_ => $args->{$_} ) } keys %$args);
	print "DEBUG command was: " . join(' ', $prg, map { ('--'.$_ => $args->{$_}) } keys %$args) . "\n";
	if($rv != 0) {
		die "Call to $prg failed: rv == $rv, \$? == $?";
	}
}

sub call_ComputeJStatistic {
	my ($config, $args) = @_;
	if($args->{viterbiOutputDirectory} && !(-d $args->{viterbiOutputDirectory})) {
		mkdir $args->{viterbiOutputDirectory} or die "Error making directory $args->{viterbiOutputDirectory}: $!";
	}
	if($args->{saveFstatAtoms} && $config->{datasource}->{special_case_O2_break}) {
		# In this case, we're doing this for O2 real data. That means that we
		# need to account for the break at block 16. We do this by:
		#  (a) rewrite args to run for first 160 days
		#  (b) symlink in special "null" block for bock 16
		#  (c) rewrite args (again) to run for last 60 days
		#  (d) cleverly rename the files so we have one contiguous sequence
		my $end_time = $args->{maxStartTime};
		$args->{maxStartTime} = $args->{minStartTime} + (16*864000);
		call_generic('lalapps_ComputeJStatistic', $args);
		# (b) symlink
		my $band = $config->{search}->{freq};
		my $target = sprintf($args->{saveFstatAtoms}, 16);
		`ln -s /home/patrick.clearwater/V2O2/kappa/nullatoms/atoms-016.dat.$band $target`;
		# (c) next 60 days
		$args->{minStartTime} = $args->{minStartTime} + (17*864000);
		$args->{maxStartTime} = $end_time;
		my $atomname = $args->{saveFstatAtoms};
		$args->{saveFstatAtoms} .= "tmp";
		call_generic('lalapps_ComputeJStatistic', $args);
		# We now have a bunch of files like
		#  atoms-000.dat
		#  ...
		#  atoms-015.dat # real atoms for start
		#  atoms-016.dat # symlink
		#  atoms-000.dattmp
		#  ...
		#  atoms-005.dattmp # real atoms for end
		# we need to move the 'tmp' atoms to the right place
		for my $i (0..5) {
			my $src = sprintf($args->{saveFstatAtoms}, $i);
			my $dst = sprintf($atomname, $i + 17);
			`mv $src $dst`;
			print "Move $src -> $dst";
		}
	} else {
		call_generic('lalapps_ComputeJStatistic', $args);
	}
}

sub call_ViterbiJstatGpu {
	my $args = shift;
	if($args->{out_prefix} && !(-d $args->{out_prefix})) {
		mkdir $args->{out_prefix} or die "Error making directory $args->{out_prefix}: $!";
	}
	call_generic('viterbi_jstat_gpu', $args);
}

# This sub calls ComputeJStatistic, and then cleverly handles the output so
# that we don't end up with excessive directories floating around
sub CJS_output_handler {
	my ($config, $args) = @_;
	my $output_file = $args->{_output_file};
	my $output_mode = $args->{_output_mode} // 'best';
	delete $args->{_output_file};
	delete $args->{_output_mode};

	# The output will be in $args->{viterbiOutputDirectory}, which we will
	# process and delete. However, we won't delete it if there were detections
	# other than the best path (because at this stage, that's too complicated
	# to manage) - although we *will* delete the best path itself.
	# Basically, we roll up all of the best paths, and record the a0 and phi in
	# the file
	# HOWEVER, if the user specified tempdir in config, things get special. We
	# create a new temporary directory of that name, write the output there,
	# process it as describe above (but putting it in viterbiOutputDirectory).
	# (i.e. you almost certainly want a outputdir, if using tempdir)
	my $final_output_dir = $args->{viterbiOutputDirectory};
	if(defined $config->{output}->{tempdir}) {
		$args->{viterbiOutputDirectory} = File::Temp::tempdir($config->{output}->{tempdir}, CLEANUP => 1);
		# Don't need to remember viterbiOutputDirectory, because the final
		# output will be in _output_file; and we'll never created vOD.
	}
	call_ComputeJStatistic($config, $args);

	if(defined $output_file) {
		my ($a0, $phi0, $score, $last_f) = parse_CJS_output($args->{viterbiOutputDirectory}.'/best.path');

		# We write out:
		# search_a0 search_phi0 best_search_a0 best_search_phi0 viterbi_score
		# TODO: this is a total hack -- what about when we search phi directly
		# rather than using orbitTp?
		flock_append($output_file, sprintf "%s\t%s\t%0.17g\t%0.17g\t%0.10g\t%0.10f\n", $args->{asini}, $args->{orbitTp}, $a0, $phi0, $score, $last_f);

		# If output->summarise is set to 'all', then we also roll up the paths
		if($output_mode eq 'all') {
			my $i = 0;
			my @detections;
			while(-e sprintf('%s/%d.path', $args->{viterbiOutputDirectory}, $i)) {
				my $filename = sprintf('%s/%d.path', $args->{viterbiOutputDirectory}, $i);
				push @detections, [parse_CJS_output($filename)];
				unlink $filename or die "Couldn't remove $filename...\n";
				++$i;
			}
			if(scalar @detections) {
				# TODO: super-hack!!
				substr($output_file, -7, 7) = 'detections';
				print " ******* printing detections to $output_file\n";
				open my $fh, '>>', $output_file or die "Can't open output file $output_file for CJS summary";
				flock $fh, Fcntl::LOCK_EX or die "Can't lock output file $output_file for CJS summary";
				seek($fh, 0, SEEK_END);
				foreach (@detections) {
					printf $fh "%s\t%s\t%0.17g\t%0.17g\t%0.10g\t%0.10f\n", $args->{asini}, $args->{orbitTp}, @$_;
				}
				flock $fh, Fcntl::LOCK_UN;
				close $fh;
			} else {
				#die " (****** no detections\n";
			}
		}

		unlink $args->{viterbiOutputDirectory}.'/best.path';
		rmdir $args->{viterbiOutputDirectory}; # Take advantage of rmdir's
		# non-recursive behaviour to *not* delete the directory if there are
		# detection paths in it
	} # if $output_file isn't defined, the user didn't ask for best path output;
	  # don't do anything special
}

sub CJS_GPU_output_handler {
	my ($config, $args) = @_;
	my $output_file = delete($args->{_output_file});
	my $output_mode = delete($args->{_output_mode});

	# If we're asked to put the results in a temporary directory, then create
	# it
	if(defined $config->{output}->{tempdir}) {
		$args->{out_prefix} = File::Temp::tempdir($config->{output}->{tempdir}, CLEANUP => 1).'/';
		# Don't need to remember the original prefix, because the final
		# output will be in _output_file; and we'll never create it
	}

	call_ViterbiJstatGpu($args);

	if(defined $output_file) {
		my $outdir = $args->{out_prefix};
		# The GPU code creates these files:
		# ..._path.dat # best path
		# ..._scores.dat # all scores
		# ..._a0_phase_loglikes_scores.dat # map a0, phase, etc together
		# We throw away _path and _scores, parse _a0..., and then remove the
		# containing directory
		unlink "$outdir/_path.dat";
		unlink "$outdir/_scores.dat";
		my $results_aryref = parse_GPU_output("$outdir/_a0_phase_loglikes_scores.dat");
		unlink "$outdir/_a0_phase_loglikes_scores.dat";
		rmdir $outdir;

		# TODO: fix orbitTp here
		my $outstr = '';
		foreach my $res (@$results_aryref) {
			my ($a0, $phi, $score, $f) = @$res;
			$outstr .= sprintf "%s\t%s\t%0.17g\t%0.17g\t%0.10g\t%0.10f\n", $args->{central_a0}, $args->{central_orbitTp}, $a0, $phi, $score, $f // 0.0
		}
		flock_append($output_file, $outstr);
	}
}

# Read in a CJS summary file (as produced by CJS_output_handler) and return a
# hash that maps "asini,orbitTp" to number of entries for all entries present
# TODO: handle phi vs orbitTp
sub read_summary_file {
	my ($infile) = @_;
	my %rv;
	open my $fh, '<', $infile or die "Couldn't open summary file $infile: $!";
	while(<$fh>) {chomp;
		my ($asini, $orbitTp) = split /\s+/;
		if(!defined($orbitTp)) {
			print STDERR "Malformed data in summary file $infile\n";
			next;
		}
		$rv{"$asini,$orbitTp"} //= 0;
		++$rv{"$asini,$orbitTp"};
	}
	close $fh;
	return \%rv;
}

sub call_ComputeFStatistic {
	my ($config, $args) = @_;
	call_generic('lalapps_ComputeFstatistic_v2', $args);
}

sub call_makeSFTs {
	my ($config, $args) = @_;
	my $rv = system('lalapps_MakeSFTs', '--ht-data', map { ('--'.$_ => $args->{$_} ) } keys %$args);
	if($rv != 0) {
		die "Call to lalapps_MakeSFTs failed: rv == $rv; \$? == $?";
	}
	#print 'lalapps_MakeSFTs --ht-data ' . join(' ', map { ('--'.$_ => $args->{$_} ) } keys %$args) . "\n";
}

sub create_SFT_name {
	my ($gps, $step, $tsft, $ifo) = @_;
	return sprintf("%10d_%02d_%4d_%2s.sft", $gps, $step, $tsft, $ifo);
}

# Calls the lalapps cache program with the given argument, and then puts the
# resulting file in the place requested. This function is careful to die if
# something goes wrong with the call to lalapps_cache.
sub call_lalapps_cache {
	my ($source_glob, $cachefile) = @_;
	# Note that lalapps_cache internally understands how to expand glob
	# patterns, so we don't need to pass it through a command interpreter
	open my $fh_out, '>', $cachefile or die "Couldn't open cache file: $cachefile for writing, bailing out.";

	# We don't just use shell redirection in a (possibly misguided) view that
	# this makes it easier to handle errors.
	open my $cache_process, '-|', "lalapps_cache $cachefile" or die "Problem forking for lalapps_cache: $!";
	while(<$cache_process>) {
		print $fh_out $cache_process;
	}
	close $cache_process or die "Problem closing cache process: $!";

	close $fh_out;
}

# Given a hashref taken from a planfile, create an appropriate data element and
# return it. (For example, given a hash asking for a random number, make that
# random number.)
sub process_plan_hash {
	my ($h) = @_;
	if(defined $h->{random}) {
		if($h->{random} eq 'uniform') {
			my $range = $h->{to} - $h->{from};
			return $h->{from} + rand($range);
		} else {
			die "While producing a random number in process_plan_hash, got an unrecognised distribution: $h->{random}.";
		}
	} else {
		die "Unrecognised plan hash structure.";
	}
}

## Helper functions

# Given a filename, flock the file, then append to it the given string
sub flock_append {
	my ($filename, $str) = @_;

	open my $fh, '>>', $filename or die "Can't open output file $filename for locked write: $!";
	flock $fh, Fcntl::LOCK_EX or die "Can't lock output file $filename for locked write: $!";
	seek($fh, 0, SEEK_END);

	print $fh $str;

	flock $fh, Fcntl::LOCK_UN;
	close $fh;
}

# Given a filename, flock the file, then write to it the given string
sub flock_write {
	my ($filename, $str) = @_;

	open my $fh, '>', $filename or die "Can't open output file $filename for locked write: $!";
	flock $fh, Fcntl::LOCK_EX or die "Can't lock output file $filename for locked write: $!";
	seek($fh, 0, SEEK_END);

	print $fh $str;

	flock $fh, Fcntl::LOCK_UN;
	close $fh;
}

# Given a filename, load it as JSON and return the hashref/arrayref (or die if
# there's an error).
sub load_json {
	my ($infile) = @_;
	open my $fh, '<', $infile or die "Couldn't load JSON from file file $infile: $!";
	flock $fh, Fcntl::LOCK_SH or die "Can't lock JSON input $infile for locked read: $!";
	local $/;
	my $json_text = <$fh>;
	flock $fh, Fcntl::LOCK_UN;
	close $fh;
	my $rv;
	eval {
		$rv = JSON::decode_json($json_text);
	};
	if($@) {
		print STDERR "Uh-oh, problem decoding JSON - $@\n";
		print STDERR " when reading JSON file: $infile\n";
		print STDERR " which contains: <<<$json_text>>>\n";
		die "Bad load JSON";
	}
	return $rv;
}

# Given a LWP::UserAgent object, a URL and a destination path, download the
# file and place it in the destionation. Dies if any problems occur.
sub download_to {
	my ($ua, $url, $dest) = @_;
	print "Downloading '$url'...\n";
	my $resp = $ua->get($url);
	if($resp->is_success) {
		open my $fh, '>', $dest or die "Couldn't open file $dest: $!";
		print $fh $resp->decoded_content;
		close $fh;
	} else {
		die "Error downloading $url: " . $resp->status_line;
	}
}

# Given an input string and a hashref of substitution variables, returns a new
# string where everything like:
#   %{xyz}
# is replaced with whatever 'xyz' pointed to in the hashref.
sub substitutestr {
	my ($str, $repl) = @_; # {
	$str =~ s/%\{([^}]+)\}/$repl->{$1}/g;
	return $str;
}

# Like substitutestr, except works on a potentially-nested series of hashrefs
# and arrayrefs
sub substitute_recursive {
	my ($branch, $repl) = @_;
	if(! ref($branch)) {
		return substitutestr($branch, $repl);
	} elsif(ref($branch) eq 'ARRAY') {
		return [map { substitute_recursive($_, $repl) } @$branch];
	} elsif(ref($branch) eq 'HASH') {
		# A little bit harder, because we have to keep the keys and things
		# there but we don't substitute on them
		return {
			map { ($_ => substitute_recursive($branch->{$_}, $repl) ) } keys %$branch
		};
	} else {
		die "Something went wrong in substitute_recursive: ref == " . ref($branch);
	}
}

# Take a string like "20d" and convert it into seconds
# TODO: handle other times?
sub process_duration {
	my $s = shift;
	if($s =~ /^(\d+)d$/) {
		$s = $1 * 86400;
	}
	return $s;
}

# Read in a segment file $segfile, check that it meets the required format, and
# then provide it an arrayref as a series of arrays like:
#  [ start time, end time ]
# where it is guaranteed that end time >= start time + $Tsft (which defaults to
# 1800), start time >= $tstart, end time <= $tend.
sub read_segment_file {
	my ($segfile, $tstart, $tend, $Tsft) = @_;
	$Tsft //= 1800;
	my @rv;
	open my $fh, '<', $segfile;
	while(<$fh>) {chomp;
		m/^(\d+)\s+(\d+)$/ or die "Bad segment file $segfile: didn't understand $_.";
		my ($start, $end) = ($1, $2);
		next if($end - $start < $Tsft);
		next if($start < $tstart);
		next if($end > $tend);
		push @rv, [$start, $end];
	}
	return \@rv;
}

# This function makes filenames in the same way that lalapps_MakeSFTs does (so
# that we can check if the file is already created). Note that for now, we
# assume one SFT per file.
# TODO: If we have a segment > 1800 seconds, will it put multiple SFTs in a
# file? Check...
sub get_makeSFTs_name {
	my ($ifo, $Tsft, $tstart, $band) = @_;
	my $site = substr $ifo, 0, 1;
	return sprintf("%s-%d_%s_%dSFT_%s-%d-%d.sft", $site, 1, $ifo, $Tsft, "${band}Hz", $tstart, $Tsft);
}

# This function takes a "range" from the config file and returns every value in
# that range (as an array, not an arrayref).
# We allow ranges to be specified in a few ways:
#  1.44 -- just a single value, so the range is that wide only
#  [0.361, 0.01805, 0.3249] -- from 0.361 to 0.3249 in steps of 0.01805
# At some point, we'll support x to y in z bins
sub expand_range {
	my ($r) = @_;
	if(!defined $r) {
		die "Range not defined.";
	} elsif(!ref($r)) {
		return ($r);
	} elsif(ref($r) eq 'ARRAY') {
		if(scalar @$r == 3) {
			my @rv;
			my ($start, $step, $end) = @$r;
			while($start <= $end) {
				push @rv, $start;
				$start += $step;
			}
			return @rv;
		} elsif(scalar @$r == 4) {
			# In this case the user wants the program to handle the search
			# across this parameters itself. We support an array of arrayrefs
			# with the relevant values in them. In the future, we'll split the
			# search grid into as many buckets as are asked for. However, for
			# now, we just put everything into one bucket.
			$r->[3] == 1 or die "At the moment we don't support splitting arrays";
			return ([$r->[0], $r->[1], $r->[2]]);
		} else {
			die "Range specifications should be arrays of three or four values.";
		}
	} else {
		die "Invalid specification for a range.";
	}
}

# Take an argument that's either a scalar or arrayref. If it's an arrayref,
# return it as an array. If it's a scalar, return it as a single item array.
sub to_array {
	my $a = shift;
	if(!wantarray) {
		die "Remember that to_array should only ever be called in list context";
	}
	if(ref($a) eq 'ARRAY') {
		return @$a;
	} elsif(!ref($a)) {
		return ($a);
	} else {
		die "Internal error in to_array: $a is a ". ref($a);
	}
}

# Parse the output of a GPU code file (which contains lines with a0, phi0,
# loglikelihood and score).
sub parse_GPU_output {
	my ($filename) = @_;
	my @rv;
	open my $fh, '<', $filename or die "Couldn't open GPU Jstat output file $filename: $!";
	while(my $line = <$fh>) {
		chomp $line;
		my ($a0, $phi, undef, $score, $f) = split /\s+/, $line;
		push @rv, [$a0, $phi, $score, $f];
	}
	close $fh;

	return \@rv;
}

# Parse the output of a ComputeJStatistic path file and return the a0, phi0 and
# score (throwing away everything else)
sub parse_CJS_output {
	my ($filename) = @_;
	open my $fh, '<', $filename or die "Couldn't open CJS output file $filename";

	# Here we want to remember the score, a0 value and phi value
	# At some point in the future we'll probably want to remember the path, too
	my ($score, $a0, $phi, $last_freq);
	while(<$fh>) { chomp;
		/score = ([-.0-9]+)/ and $score = $1;
		/phi = ([-.0-9]+)/   and $phi = $1;
		/a0 = ([-.0-9]+)/    and $a0 = $1;
		/\t([-.0-9]+) .delta bin/ and $last_freq = $1;
	}
	defined $score or die "No score in (CJS output file) $filename\n";
	defined $phi   or die "No phi in (CJS output file) $filename\n";
	defined $a0    or die "No a0 in (CJS output file) $filename\n";
	defined $last_freq or die "No last freq in (CJS output file) $filename\n";
	close $fh;

	return ($a0, $phi, $score, $last_freq);
}

sub helpconfig {
	# This hash contains documentation for (not) all of the keys contained in
	# the configuration file. Each key can map either to a string, in which
	# case that string is the help text; or can map to another hashref. That
	# hashref should have an element '_', which is the help for that level, and
	# then all of the keys of that hash correspond to possible sub-keys at that
	# level.
	# print Text::Wrap::wrap('', '', ...)
	my %help = (
		'_' => "sch_mgr expects to be controlled by JSON configuration files (specified on the command line by --config). In general, you want to run --task=prepare first, and then you can run --task=search specifying the stage and step number(s) to execute. The JSON file should have a top level object, which can contain the keys documented below",
		name => "The name of the string experiment.",
		description => "A human readable description of what the experiment is, its purpose, et cetera.",
		search => {
			_ => "These parameters control how the search itself is run.",
			mode => "What kind of search to do. This parameter accepts these options:

 - find_best_path: [the default] a normal search, for the best path
 - find_h0: use a binary search to find the lowest h0 for which the signal can be detected",
 			h0_low => "(for mode = find_h0) the lowest h0 to use when running the search",
			h0_high => "(for mode = find_h0) the highest h0 to use when running the search",
			h0_tolerance => "(for mode = find_h0) the tolerance to which to find the magic h0, that is, |h0_hi - h0_lo| h0_tolerance",
			find_h0_scoreboard_dir => "(for mode = find_h0) where the scoreboards (i.e., progress files) are stored"
		},
		datasource => {
			_ => "The 'datasource' section specified how the data should be made or acquired.",
			datadir => "(for source = fakedata) Where to store the generated data",
			source => "How to generate/acquire the data. This can be one of:

 - fakedata: generate the data using lalapps_Makefakedata_v4
 - LOSC: generate the data from the LIGO Open Science centre, by downloading it and converting it to SFTs. This datasource caches downloaded files (with --prepare) so that you don't need to continually redownload data
 - sfts: use some SFTs that are generated outside of sch_mgr",
		}
	);
	showhelp(\%help);
}

sub showhelp {
	my ($help, $k) = @_;

	print "\n\n" . Text::Wrap::wrap('', '', $help->{_});
	print "\n\nMore information on:\n";
	foreach my $k (sort keys %$help) {
		next if $k =~ /^_/;
		if(ref($help->{$k}) eq 'HASH') {
			print "$k->...\n";
		} else {
			print "$k\n";
		}
	}
	print "\n(Or leave blank to go up a level, Ctrl+C to exit.)\n\n";

	while(1) {
		printf "\n%s> ", ($k // '');
		my $what = <STDIN>;
		chomp $what;
		if(length($what)) {
			if(not exists $help->{$what}) {
				print "Unrecognised subkey: '$what'\n";
			} elsif(ref($help->{$what}) eq '') {
				print "Help for $what:\n";
				print Text::Wrap::wrap('', '', $help->{$what});
				print "\n";
			} else {
				showhelp($help->{$what}, (defined $k ? "$k " : '') . $what);
			}
		} else {
			return;
		}
	}
}


main @ARGV;
