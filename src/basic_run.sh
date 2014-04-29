cd ..

make -j 8

if [ $? -eq 0 ]; then
    JOB=$HOME/mass-storage/Jobs/2014B_Ct
    PROJECT=$HOME/Code/photosynth/cGromCorrFMO
    
    fmo_traj_path=$JOB/BCX0/md/splittraj/md1.gro

    fmo_top_path=$JOB/FMO_conf/4BCL_pp.top
    bcx_itp_path=$JOB/FMO_conf/amber_mod.ff/bcx.itp
    output_path=$PROJECT/data/CsvOut/test/test

    num_frames=$(grep 'Generated by trjconv' $fmo_traj_path | wc -l)

    echo "Computing with $num_frames frames"
    
    $PROJECT/src/traj2dEcsv $fmo_traj_path $fmo_top_path $bcx_itp_path $output_path $num_frames
else
    echo "FAILED TO BUILD: Check stderr for information from gnu make"
fi
