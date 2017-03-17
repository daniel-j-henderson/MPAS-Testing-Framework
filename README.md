# MPAS-Testing-Framework
This is a regression testing suite being implemented in python for MPAS, the Model for Prediction Across Scales, which is a part of the MMM division at NCAR.


### Organization
The testing suite is organized thusly: there is a main driver script called test_driver.py which sets up the testing environment and launches all tests. Each test is provided in the form of a python module inside a directory which contains the .py module implementation file (of the same name as the directory) and any files that are specific to that test that the test may require (namelists or stream definitions or things of that nature). See the restartability test (restartability directory) or the examples in the example directory. To run the 'example' test, see the <b>Run</b> section. If you'd like to run the 'toytest' example, simply compile the toy.f90 file using an mpi compiler, move it to some other directory (equivalent to MPAS directory) which also contains your XML config file (described later), and run the test from there. Also, the toytest directory must be copied/moved (not linked) one level up.

You must specify which groups of tests or individual tests you want to run on the command line (groups are specified in the Tests.xml file, which can be found in this directory). An additional XML file is required to configure each run environment (it may also specify the test code directory). This XML file (see yellowstone.xml) tells the driver where to find the standard library as well as some other useful information about the environment in which we are running the tests. This file may be placed in the run directory (usually the top-level MPAS directory) and called 'Environment.xml' (you can link Environment.xml -> /foo/[...]/bar.xml), or it may be explicitly given with the '-env' option.

The directory of the MPAS source code to be tested (referred to as the source directory or src_dir) may be provided using the optional '-src' argument. If it is not provided, it defaults to the run directory (the directory from which you launched the test_driver script, where the Environment.xml file might also be located).

Both the driver and the individual tests may make use of the utils module, whose implementation can be found in the utils subdirectory. Note: each test module will not import the utils module directly, but rather it is passed along by the driver as a member of the env object when the test is invoked.

### Standard Library
The Standard Library is simply an archive of many files that are most likely going to be required by many tests; rather than have multiple tests provide the same file (which would be cumbersome and costly), these files are stored in the Standard Library. Each environment for testing MPAS has its own SL, and the SL may not be the same across computing environments (for instance, the SL on Yellowstone may contain very large meshes like the 3km mesh, while the SL on mmmtmp or one's local hard drive may not contain such large, obscure files). The test writer requests any files that he or she desires from the SL by specifying them in the test setup function, then the driver will locate the files (if they can be found) in the SL and link them to the desired location. 

The SL is set up as a file hierarchy so that it can easily be perused by a human. In order to search through it, the utility makes use of the Library.xml file included in the top level of the SL, which describes the file hierarchy in xml form (it must exactly mirror the SL directory structure). If a tester wishes to add a useful file to the SL on a given system, he or she must simply add the file into the appropriate subdirectory and add the corresponding xml tag in the Library.xml file. 

### Run

1. Clone this repository, into the top-level MPAS directory if desired (should already be compiled)
2. Make sure an environment xml file (named 'Environment.xml') and the Tests.xml file are in the top-level MPAS directory. You may have to link and/or rename those files from this repository.
3. From the top-level MPAS directory, run the command <br>
python SMARTS/test_driver.py \<group_name\> ... \<test_name\>... -n \<max_num_tasks\> -env [...]/foo.xml -src [...]/MPAS-Release <br>
  to run all of the desired tests (try 'python SMARTS/test_driver.py example -n 4')

When the tests have completed, a results folder will be made with a pdf report of the results of all tests. 
