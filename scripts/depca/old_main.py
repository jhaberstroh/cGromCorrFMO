from depca import sidechain_corr as sc
import h5py
import sys
import argparse
import ConfigParser


def main_trackmodes():
    parser = argparse.ArgumentParser(description="Compute the eigenvalues of the correlation matrix produced by SidechainCorr, then plot the timeseries for the modes selected. Leaves the database unmodified.")
    parser.add_argument("-site", type=int, default=1,                                                   help="Site that the data is requested for, use 1-based indexing. No error checking.")
    parser.add_argument("-dEtmodes", type=int, nargs='+', action='append',                              help="(requires plot dEt) A collection of all modes to include in the timeseries, using zero-based indexing.")
    parser.add_argument("-Nframes", type=int,                                                           help="Number of frames to include in calculations")
    parser.add_argument("-offset", type=int, default=0,                                                 help="Number of frames to skip before beginning computation")
    parser.add_argument("-plotspectrum", action='store_true',                                           help="Set to plot PCA spectrum")
    parser.add_argument("-hist2d", type=int, nargs=2, action='append',                                  help="A list of mode-pairs for 2d histogram. Repeat option for multiple plots.")
    parser.add_argument("-hist2d_opt", type=int, nargs=2, action='append',                              help="Options for 2D hist. None available.")
    parser.add_argument("-hist1d", type=int, nargs='*', action='append',                                help="A list of modes to histogram together. Modes will be plotted with residual energy distribution. Repeat option for multiple plots.")
    parser.add_argument("-hist1d_opt", type=str, nargs='*', default=[], choices=['parabola'],           help="Options for 1D hist. Parabola plots a parabola with the residual dE.")
    parser.add_argument("-modesCt", type=int, nargs='*', action='append',                               help="A list of modes to compute time-correlations for. Modes will be plotted with residual correlation. Repeat option for multiple plots.")
    parser.add_argument("-outfnamebase", default="plot",                                                help="Filename base for output from plotspectrum and other outputs")
    parser.add_argument("-savemode", default=['display'], nargs='+', choices=['pdf','png','display'],   help="Set format for file output")
    parser.add_argument("-evmtx", action='store_true',                                                  help="Analyze the eigenvalue matrix")


    args = parser.parse_args()
    print args
    args.site -= 1
    print args.savemode


    config = ConfigParser.RawConfigParser()
    config.read('./f0postProcess.cfg')
    h5file = config.get('sidechain','h5file')
    h5stats= config.get('sidechain','h5stats')
    timetag = config.get('sidechain','time_h5tag')
    corrtag = config.get('sidechain','corr_h5tag')
    h5eavtag = config.get('sidechain','h5eavtag')
    h5crtag = config.get('sidechain','h5crtag')

    
   
    with h5py.File(h5file,'r') as f_time:
        if (h5file != h5stats):
            f_corr =  h5py.File(h5stats,'r')
        else:
            f_corr = f_time
        print "Loading timeseries '{}' from hdf5 file {}...".format(timetag,h5file)
        E_t_ij = f_time[timetag]
        print "Loading covariance and averages '{},{}' from hdf5 file {}...".format(corrtag+h5crtag,corrtag+h5eavtag,h5stats)
        corr   = f_corr[corrtag+h5crtag]
        Eav_ij = f_corr[corrtag+h5eavtag]
    
        print "Computing Modes..."
        vi, wi, impact_i = ComputeModes(corr)
        print "\tModes Computed!"
    
        if args.plotspectrum:
            print "Plotting spectrum..."
            fname = "{}_spect{}".format(args.outfnamebase,args.site+1)
            PlotLogSpectrum(args.site, vi, impact_i, plottype=args.savemode, fname=fname)

        if args.evmtx:
            raise NotImplementedError("No analysis tools for the eigenvector matrix is available yet")
        
        print "1D HIST MODES: ", args.hist1d
        if args.hist1d:
            for modeset in args.hist1d:
                legend = ["Mode {}".format(mode) for mode in modeset]
                legend.append("Residual")
                print "LEGEND: ", legend
                fname = "{}_s{}_1d{}".format(args.outfnamebase, args.site+1, '-'.join([str(j) for j in modeset]))
                dDE_nt, residual_t = DeltaModeTracker(E_t_ij, Eav_ij, wi, args.site, modeset, Nframes=args.Nframes, offset=args.offset)
                Plot1DHist(dDE_nt, residual_t, legend=legend, plottype=args.savemode, fname=fname, parabola='parabola' in args.hist1d_opt)

        if args.hist2d:
            for modepair in args.hist2d:
                print "Plotting 2D histogram for site {}...".format(args.site+1)
                xylabels = ["Mode {}".format(modepair[0]), "Mode {}".format(modepair[1])]
                fname = "{}2D_s{}_{}v{}".format(args.outfnamebase, args.site+1, modepair[0], modepair[1])
                dDE_nt,_ = DeltaModeTracker(E_t_ij, Eav_ij, wi, args.site, modepair, Nframes=args.Nframes, offset=args.offset)
                Plot2DHist(dDE_nt[0], dDE_nt[1], xylabels = xylabels, plottype = args.savemode, fname=fname)
        
        if args.dEtmodes:
            for modeset in args.dEtmodes:
                legend = ["Mode {}".format(mode) for mode in modeset]
                legend.append("Residual")
                print "LEGEND: ", legend
                fname = "{}dEt_s{}".format(args.outfnamebase, args.site+1)
                dDE_nt, residual_t = DeltaModeTracker(E_t_ij, Eav_ij, wi, args.site, modeset, Nframes=args.Nframes, offset=args.offset)
                PlotTimeseries(dDE_nt, residual_t, plottype = args.savemode, legend=legend, fname=fname)


        if args.modesCt:
            for modeset in args.modesCt:
                legend = ["Mode {}".format(mode) for mode in modeset]
                legend.append("Residual")
                legend.append("Total")
                print "LEGEND: ", legend
                fname = "{}_s{}_Ct{}".format(args.outfnamebase, args.site+1, '-'.join([str(j) for j in modeset]))
                dDE_nt, residual_t = DeltaModeTracker(E_t_ij, Eav_ij, wi, args.site, modeset, Nframes=args.Nframes, offset=args.offset)
                print "Modes retrieved, computing Ct..."
                PlotCt(dDE_nt, residual_t, legend=legend, totalCt = True, plottype=args.savemode, fname=fname, dt = E_t_ij.attrs["dt"])

        f_corr.close()


if __name__ == "__main__":
	main()


def main_csv2hdf5():
    print "---------------------------------csv2hdf5, hurrah!---------------------------------------"
    parser = argparse.ArgumentParser(description='Take (input1-N) [csv format] and append into (input2) [hdf5 format] under database name (input3). Requires that .csv file fits in memory. Also, requires that csv row width is 357 (value from FMO).')
    parser.add_argument('hdf_file', type=str, help=".hdf5 destination file.")
    parser.add_argument('hdf_dsname', type=str, help="database entry name within hdf_file")
    parser.add_argument('csv_file', type=str, nargs='*', help=".csv file(s) to merge into hdf5.")
    parser.add_argument('--open_with_write', action='store_true', help="when set, delete or create database at hdf_file ('w' flag); without flag, append or create database at hdf_file ('a' flag).")
    parser.add_argument('--frames_per_file', type=int, default=50000, help="number of frames in each file; must be correct for script to function. (Default = 50,000)")
    parser.add_argument('--dt', type=float, default=None, help="timestep, in picoseconds")

    args = parser.parse_args()
    open_flag = "a"
    if args.open_with_write:
        open_flag = "w"

    NFRAMES=args.frames_per_file

    dEcsv2hdf5_init(args.hdf_file, args.hdf_dsname, open_flag, dt=args.dt)
    for csv in csv_file:
        dEcsv2hdf_append(csv, args.hdf_file, args.hdf_dsname, NFRAMES)



def main_timecorrelate():
    config = ConfigParser.RawConfigParser()
    config.read('./f0postProcess.cfg')
    h5_filename = config.get('sidechain','h5file')
    h5time = config.get('sidechain','time_h5tag')
    h5corr = config.get('sidechain','corr_h5tag')
    h5ct = config.get('sidechain','ct_h5tag')

    parser = argparse.ArgumentParser(description = "Module to store temporal correlations")
    parser.add_argument('-newCt', action="store_true", help="Create new Ct matrix?")
    parser.add_argument('-overwrite', action="store_true", help="Delete old Ct matrix? Must be paired with newCt for confirmation.")
    parser.add_argument('-lenCt', type=float, default=200., help="Length of Ct to store, ps")
    parser.add_argument('-chromo', type=int, default=1, help="Chromophore to compute correlations for")
    args = parser.parse_args()

    num_t = 0
    size_Ct_ab = (0,0,0) # Set value with data from E_tij

    h5ct = "".join([h5ct, "{}".format(args.chromo)])

    with h5py.File(h5_filename, 'r+') as f:
        E_tij = f[h5time]
        num_t = int(np.round(args.lenCt / E_tij.attrs['dt']))
        size_Ct_ab = (num_t, E_tij.shape[2], E_tij.shape[2])

        disk_size = np.product(size_Ct_ab) * 8 / float(10**9)
        print "Note: Estimated maximum size on disk: {0:.1f} GB".format(disk_size)

        if args.newCt and h5ct in f:
            if args.overwrite:
                raise NotImplementedError("No implementation found for overwrite yet!")
            else:
                raise RuntimeError("Warning: Dataset found when newCt was requested, but overwrite flag was not passed. Use -overwrite to delete previous data or remove -newCt flag.")
        elif args.newCt and not h5ct in f:
            f.create_dataset(h5ct, size_Ct_ab)

    print size_Ct_ab
    for a in xrange(size_Ct_ab[1]):
        Ct_b = np.zeros((size_Ct_ab[0],size_Ct_ab[2]))
        for b in xrange(size_Ct_ab[2]):
            print "{},{}".format(a,b),
            Ct_b[:,b] = HDFStoreCt_v3(h5_filename,h5time, h5ct, a, b, chromo=args.chromo)
        with h5py.File(h5_filename, 'r+') as f:
            Ct_ab = f[h5ct]
            print "Data Chunks:",Ct_ab.chunks
            print Ct_ab[:, a, :].shape, Ct_b.shape
            Ct_ab[:,a,:] = Ct_b[:]



def main_correlate():
    parser = argparse.ArgumentParser(description = 'Program to compute same-time correlation PCA for csv or hdf5 data, and save the correlation matrix out to file for use in other pyPCA modules')
    parser.add_argument('-num_frames', default=0, type=int,help='Number of frames to use for the corrlelation (Note: default and 0 mean all frames after offset)')
    parser.add_argument('-frame_offset', default=0, type=int,help='Number of frames to skip before beginning corrlelation')
    parser.add_argument('-frame_stride', default=1, type=int,help='Number of frames to stride between while computing average. Stride preferred over frame subset to reduce slow heterogenaety')
    args = parser.parse_args()
    
    config = ConfigParser.RawConfigParser()
    config.read('./f0postProcess.cfg')
    
    
    h5file = config.get('sidechain','h5file')
    h5stats= config.get('sidechain','h5stats')
    corr_h5tag = config.get('sidechain','corr_h5tag')
    time_h5tag = config.get('sidechain','time_h5tag')
    h5crtag = config.get('sidechain','h5crtag')
    h5eavtag = config.get('sidechain','h5eavtag')
    
    t_start = args.frame_offset
    t_end   = args.num_frames + t_start
    
    with h5py.File(h5file,'r') as f:
        E_t_ia = f[time_h5tag]
        print E_t_ia.shape
        if args.num_frames == 0:
            t_end = E_t_ia.shape[0]
        print "Computing same-time spatial correlations across {} time samples...".format(t_end-t_start)
        args.dt = E_t_ia.attrs['dt']
        corr_iab,Avg_Eia = sc.AvgAndCorrelateSidechains(E_t_ia, t_end, t_start, args.frame_stride)
    print "Database read closed..."
    print "Database append beginning..."
    with h5py.File(h5stats,'w') as f:
        try:
            print "\tSaving to "+corr_h5tag+h5crtag+" correlation matrix of shape",corr_iab.shape,"..."
    	crdset = f.require_dataset(corr_h5tag+h5crtag, corr_iab.shape, dtype='f');
    	crdset[...] = corr_iab
            crdset.attrs['dt'] = args.dt
            crdset.attrs['tstart'] = t_start
            crdset.attrs['tend']   = t_end
    	# Store the time-average at each site
    	print "\tSaving to "+corr_h5tag+h5eavtag+" averages of shape",Avg_Eia.shape,"..."
    	eavdset = f.require_dataset(corr_h5tag+h5eavtag, Avg_Eia.shape, dtype='f');
    	eavdset[...] = Avg_Eia
            eavdset.attrs['dt'] = args.dt
            eavdset.attrs['tstart'] = t_start
            eavdset.attrs['tend']   = t_end
    
        except TypeError:
    	print "\n\nERROR: Error in write encountered, you should consider changing the h5_tag to a value that has not been used."
    	raise
    
    print "Database closed"


if __name__ == "__main__":
	main_correlate()
