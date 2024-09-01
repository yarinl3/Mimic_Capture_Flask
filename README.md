This project can run in web mode with flask with nice user interface and also can run through [terminal / IDE with low user interface](#modes).










To run the script from IDE select mode and screenshot_path.  
For example:
```
mode = MODES['PLAY']
screenshot_path = '1.png'
```
To run the script from terminal load the environment if it exists, run the script with two parameters: screenshot path and mode.  
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

For any other questions: yarinl330@gmail.com
