# Salary Breakdown
This is a program that takes user's input with GUI and creates a PDF report based on the information entered.

It's a pet project I started to help my mum with her job. She said there's a monthly report
on club expenses in different schools she has to make. It is simple to compute, but rather tedious to do by 
hand in Excel for every organisation they work with.
So I came up with this program.

## How does it work?
Fairly simple:
1) The program starts with an input window. The user picks an organisation from the drop-off list
(the list of orgs is read from a JSON file in the same folder), or creates a new one.

   <img height="300" src="C:\Users\multi\Documents\маме\choosingSchool.png" width="350"/>
2) Once an organisation is chosen, the program automatically fills the input fields from the information 
stored in the JSON file. The field for choosing a club also becomes active (a drop-off list). The user chooses
a club to work with from the list or creates a new one. Once a club is chosen, all the relevant input fields
are automatically filled with the information from the JSON file.

   <img height="300" src="C:\Users\multi\Documents\маме\choosingClub.png" width="350"/>
3) Now the user has an opportunity to change the information (e.g. if the headmaster for the school has changed, 
new expense data has been calculated, etc.). If everything's correct, the user presses the 'Save' button.

   <img height="300" src="C:\Users\multi\Documents\маме\allFilled.png" width="350"/>
4) Once the 'Save' button is pressed, all the information is taken to generate a PDF of the report. At the same time,
all the saved data is saved/updated in the JSON file.
5) In a separate window, the user chooses where to save the PDF file (below is the sample report). Once it is saved, the save window closes.

   <img title="Sample Report PDF" height="596" width="420" src="C:\Users\multi\Documents\маме\sample_report-1.png"/>
6) The main window is still open in case the user wants to generate another report/change the information entered.
The user exits the program either by pressing the 'Quit' button or the X in the top-right corner.

There's also a menu that only runs the numbers (without any input on club/school names, etc.) and outputs
the correct report figures on screen. This was added by request (users needed just to check the reports that they
already had at hand and didn't need to create any reports themselves). It works just the same.

## How to install the program
This repository only contains the Python code I wrote myself. Should you wish to install and run the program,
first install the necessary Python libraries (listed in ```requirements.txt```). Then either simply launch 
```main.py``` script, or use pyinstaller to 'compile' a program into an executable file.

## License
This project is distributed with the MIT license. You may use my work however you like, however, I cannot
give any guarantees about its work.