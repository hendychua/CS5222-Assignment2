CS5222-Assignment2
==================

Calculate number of cycles needed by 3 different superscalar processors for a set of assembly code. The 3 superscalar processors are: (A) Infinite instruction window and execution units (B) Limited instruction window and infinite execution units (C) Limited instruction window and execution units

Instructions
==================
- Executables are in bin/
- Make sure you are in the same directory as MakeAll file and run ./MakeAll. The script will run chmod 700 bin/SSS_*.exe files to give them permissions to execute.
- To execute a script, cd into bin/ and enter one of the following commands:
	- ./SSS_Infinite.exe <test_file.in>
	- ./SSS_LWindow.exe <test_file.in> <window_size>
	- ./SSS_LWinExe.exe <test_file.in> <window_size> <execution_units>
