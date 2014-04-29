#!/bin/bash

for i in {11..500}; do
    JOB=$HOME/mass-storage/Jobs/2014B_Ct
    PROJECT=$HOME/Code/photosynth/cGromCorrFMO
    
    fmo_traj_path=$JOB/BCX0/md/splittraj/md$i.gro
    fmo_top_path=$JOB/FMO_conf/4BCL_pp.top
    bcx_itp_path=$JOB/FMO_conf/amber_mod.ff/bcx.itp
    #output_path=$PROJECT/data/CsvOut/2014B_MDPost/md$i
    output_path=md
    #output_path=$JOB/md
    
    num_frames=$(grep 'Generated by trjconv' $fmo_traj_path | wc -l)
    
    echo "Computing with $num_frames frames"
    
    $PROJECT/src/traj2dEcsv $fmo_traj_path $fmo_top_path $bcx_itp_path $output_path $num_frames
done
