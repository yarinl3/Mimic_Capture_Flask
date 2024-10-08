This branch is under construction.
Please download the tool from ["combined tool" branch.](https://github.com/yarinl3/Mimic_Capture_Flask/tree/combined-tool)









This project can run in [web mode with flask](#web-mode) with nice user interface and also can run through [terminal / IDE with low user interface](#ide--terminal).

# Installation instructions:
1. Download zip from and extract it.<br>
<img width="412" alt="image" src="https://github.com/user-attachments/assets/237bb8d8-3435-4f57-af10-ca4216c223b3">
<br><br>
2. Check if python exist with the command python in terminal / cmd. (ctrl+z to exit)<br>
<code>python</code><br>
<img width="572" alt="image" src="https://github.com/user-attachments/assets/5002b6f9-51e7-40c6-833e-b4738b1a5c60">
<br><br>
3. If python does not exist [download python](https://www.python.org/downloads/).<br>
<img width="663" alt="image" src="https://github.com/user-attachments/assets/7f180546-e93c-43f3-ba83-d3a4291abaa4">
<br><br>
4. Install virtualenv package with the command:
<code>
python -m pip install virtualenv
</code>
<br>
<img width="568" alt="image" src="https://github.com/user-attachments/assets/6b90d767-cff9-4190-93cb-76fa76057e8f">
<br><br>
5. Nevigate to the extract folder with
<code>
cd
</code>
<br>
<img width="343" alt="image" src="https://github.com/user-attachments/assets/4aba4cf9-7166-456b-b156-f59fd698ab9c">
<br><br>
6. Create a new environment with the command: <code>python -m venv myenv</code><br>
<img width="366" alt="image" src="https://github.com/user-attachments/assets/f2ad7e21-26f6-491d-8ae1-2189d7420945">
<br><br>
7. Activate the environment with the command:<br>
Mac / Ubuntu:<br>
&nbsp;&nbsp;&nbsp;&nbsp;<code>source myenv/bin/activate</code><br>
Windows:<br>
&nbsp;&nbsp;&nbsp;&nbsp;<code>myenv\Scripts\activate</code><br>
<img width="378" alt="image" src="https://github.com/user-attachments/assets/dfa54877-b436-4302-8b4b-f5c5f5adc569">
<br><br>
8. Install Mimic dependencies with the command: <code>python -m pip install -r requirements.txt</code><br>
<img width="637" alt="image" src="https://github.com/user-attachments/assets/87876faa-8c09-453f-8cef-7a3ff40bbfaa">
<br><br>
Web mode:<br>
9. Run the server with the command: <code>flask run --host=0.0.0.0 --port=1234</code><br>
<img width="815" alt="image" src="https://github.com/user-attachments/assets/610292e8-afc5-4999-8beb-7544fda6d690">
<br><br>

# Web Mode  
* The first url can opened only from the same computer.<br>
  The other url can opened from any device that connected to the same local network.
* To close the server use ctrl+c otherwise you will have to use other port next run.
* <b>From this moment on, to run the program again, you need to open the terminal and perform steps 5 -> 7 -> 9. </b>

## How to use
### Home Page
Upload screenshot of the board (initial game state and only png / jpg / jpeg / webp)<br>
<img width="550" alt="image" src="https://github.com/user-attachments/assets/8cc7b4fa-31f8-4fed-9c12-9e63d67c8862">


### Fix Points Page
Different phones have different resolutions so you need to correct the position of the dots.<br>
First of all place the central point in the center of the mimic treasure block with X / Y offsets.<br>
Then widen the distance between the points so that they are roughly in the center of the blocks using vertical / horizontal offsets.<br>
Click the change button to apply.<br>
The "Solve" button will display all results with maximum benefit.<br>
If you want to skip it and get the order of the first result use the checkbox before click "Solve".<br>
In case all the solutions have no winning order, you can look for solutions with smaller benefit using "Specific benefit" textbox before click "Solve".<br>
<img width="519" alt="image" src="https://github.com/user-attachments/assets/34a67750-2cf2-4204-aa0a-fe58718e36ad">
<img width="464" alt="image" src="https://github.com/user-attachments/assets/5087d377-21eb-4a4f-a20c-d61bc0a618f3">


### Solutions Page
<img width="554" alt="image" src="https://github.com/user-attachments/assets/87a66da8-4828-4619-b490-d49f36b4e1c4">


### Get Order Page
<img width="595" alt="image" src="https://github.com/user-attachments/assets/c98aa966-ec35-436d-9271-929258af4e50">


### Play Page
<img width="481" alt="image" src="https://github.com/user-attachments/assets/9e3dfaa7-a6e0-4ca7-86ef-5bcdf23af9ab">


# IDE / Terminal
Install as in web mode up to step 8 (inclusive).
To run the script from IDE select mode and screenshot_path.  
For example:
```
mode = MODES['PLAY']
screenshot_path = '1.png'
```
To run the script from terminal load the environment if it exists (step 7), run the script with two parameters: screenshot path and mode.  
For example:
```
py ~/pythonProject/Mimic_Capture.py test.png get_order
```

If no mode is selected, the default is play.  
<b>The script will convert the image to png (from jpeg / jpg / webp), so in the next run you must change the extension to png.</b>

## Modes
### SOLVE
Solves a given board and prints blocks to remove with the highest benefit.

### GET_ORDER
Gets a list of blocks to remove and finds the order in which they must be removed to win.  
After using the solver, copy the printed block list as input to this mode.

### PLAY
Runs a game with the given board. It is recommended to play through the terminal.  
A block index consists of letter a-g for column index and numbers 1-7 for row index.  
For example: A1, A5, G4, C5  
At the end of the game a record of the moves is shown.

### DEBUG
Different phones have different resolution.  
The program is aimed at the resolution of most phones.  
If the parameters not match the resolution the dots will not be in the center of the blocks and it will cause wrong results.  
To fix it do this steps:
1. Run the script in debug mode and look at the result image.
2. Change height_fix parameter to place the center dot vertically in the center of the Mimic block.
3. Change width_fix parameter to place the center dot horizontally in the center of the Mimic block.
4. Change horizontal_fix, vertical_fix parameters to place other dots in the middle of their blocks.
5. Change the global parameters that in the head of the script to the correct values.

For questions and bug reporting: yarinl330@gmail.com
