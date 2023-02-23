# salary_breakdown
 A project that takes input with GUI and creates a PDF report based on the information

This is a small pet project I started to help my mum with her job. She said there's a monthly report
on club expenses in different schools she has to make. It is simple to compute, but rather tedious to do by 
hand in Excel for every organisation they work with.
So I came up with this program.

## How does it work?
Fairly simple:
1) The program starts with an input window. The user picks an organisation from the drop-off list
(the list of orgs is read from a JSON file in the same folder), or creates a new one. Once an organisation is chosen,
the program automatically fills the input field from the information stored in the JSON file.
2) Has an organisation been chosen, the field for choosing a club becomes active (also a drop-off list). The user
chooses a club to work with from the list or creates a new one. Once a club is chosen, all the relevant input fields
are automatically filled with the information from the JSON file.
3) Now the user has an opportunity to change the information (e.g. if the headmaster for the school has changed, 
new expense data has been calculated, etc.). If everything's correct, the user presses the 'Save' button.
4) Once the 'Save' button is pressed, all the information is taken to generate a PDF of the report. At the same time,
all the saved data is saved/updated in the JSON file.
5) In a separate window, the user chooses where to save the PDF file. Once it is saved, the save window closes.
6) The main window is still open in case the user wants to generate another report/change the information entered.
The user exits the program either by pressing the 'Quit' button or the X in the top-right corner.