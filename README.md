# MPAS-Testing-Framework
This is a regression testing suite being implemented in python for MPAS, the Model for Prediction Across Scales, which is a part of the MMM division at NCAR.


###Organization
The testing suite is organized thusly: there is a main driver script called test_driver.py which sets up the testing environment and launches all tests. Each test is provided in the form of a python module inside a directory which contains the .py module implementation file (of the same name as the directory), an __init__.py file, and any files that are specific to that test that the test may require (namelists or stream definitions or things of that nature). See the restartability test (restartability directory). At present, the test driver will run all tests found. An XML file is required to configure each run environment (it may also specify the test code directory). This XML file (see cocobolo.xml) tells the driver where to find the standard library as well as some other useful information about the environment in which we are running the tests. The test code directory may be specified on the command line. 

Both the driver and the individual tests may make use of the utils module, whose implementation can be found in the utils subdirectory. Note: each test module will not import the utils module directly, but rather it is passed along by the driver as a member of the env object when the test is invoked.

###Standard Library
The Standard Library is simply an archive of many files that are most likely going to be required by many tests; rather than have multiple tests provide the same file (which would be cumbersome and costly), these files are stored in the Standard Library. Each environment for testing MPAS has its own SL, and the SL may not be the same across computing environments (for instance, the SL on Yellowstone may contain very large meshes like the 3km mesh, while the SL on mmmtmp or one's local hard drive may not contain such large, obscure files). The test writer requests any files that he or she desires from the SL by specifying them in the test setup function, then the driver will locate the files (if they can be found) in the SL and link them to the desired location. 

The SL is set up as a file hierarchy so that it can easily be perused by a human. In order to search through it, the utility makes use of the Library.xml file included in the top level of the SL, which describes the file hierarchy in xml form (it must exactly mirror the SL directory structure). If a tester wishes to add a useful file to the SL on a given system, he or she must simply add the file into the appropriate subdirectory and add the corresponding xml tag in the Library.xml file. 

###Run

To run all tests, run 'python test_driver.py' on the command line.

When the tests have completed, a results folder will be made with a pdf report of the results of all tests. 
