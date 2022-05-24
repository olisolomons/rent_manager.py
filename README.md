# rent_manager.py

Created to replace a vastly overcomplicated spreadsheet, this piece of software records and manages rent for landlords. It is intended to be used by an agent who manages the property for a landlord.

It records incoming rent payments, costs, paying the profit to the landlord, agent's fees and even witholding money back in a "float", ready for expected costs.
There are automatic calculations for arrears, balance, remaining float and more.

Monthly PDF reports can be generated to explain to the landlord the payments that they should expect.

# Technologies used

The project is written in Python, with tkinter for the GUI, and pyinstaller to build it to an executable. Reports are generated using FPDF2.

# What I learned

This is the first time I had made a GUI project of any real complexity, and I learned the value of GUI frameworks. If I were doing this again I would use Electron with a javascript framework, or perhaps try the Python library Edifice, or learn ReasonML and Revery. In this project I essentially create a custom UI framework (in the `src/traits` folder), which is inferior to the more mature and carefully designed frameworks.

In order to gain access to MacOS and more easily access Windows in order to build executables for those platforms, I used continuous deployment with Github Actions for the first time. I found this very useful, although Github Actions used a newer version of MacOS than the person who wanted to use the software, which caused some problems, since MacOS executables and dynamic libraries only run on the same or newer OS versions. The workarounds for this were not well documented, and even then, not all libraries worked, because the Python package manager wouldn't download versions of the dynamic libraries compiled for older OS versions. My workaound for this was to make an installer script that would install miniconda python and all required packages on the user's machine.



# Running from source

After cloning the repository, create a Python 3.10 virtual environment, and activate it. Install the packages from the `requirements.txt` file. Navigate to the the `src` directory and run the `python main.py`.
