# Augmentation

This project is used for data preprocessing in object detection algoritmes. It is devided in two parts. 
The two parts work on different kinds of data and are used for different tasks.
Both parts are used on pictures combined with .txt files.
The .txt file will contain information on the bounding boxes of the pictures.


## Count_click.py

Is used to: 
* add bounding boxes
* move bounding boxes
* add size of bounding boxes

The code will need a .txt file ordered like the image below. So it needs a x-coordinate, y-coordinate and name of the image.

<img src="images/lijst.JPG" width="500" >

The code will work in a few steps and generate a new text file with the updated bounding boxes and the size of the boxes.

### Step 1
Choose the right .txt file and the path to the pictures.
This happens at the bottom of the code.


<img src="images/stap_0.JPG" width="500" >


### Step 2

Run the code. The code will first show the user a picture with bounding boxes of differend sizes. This makes it possible for the user to estimate how large the correct boxes should be. The boxes are of size: 60, 120 and 240.

<img src="images/stap_1JPG.JPG" width="500" >

### Step 3
Here some input of the user is needed.

First the user is asked to give the size he wants to use for the picture.

<img src="images/stap_2.JPG" width="300" >

After this the full image is shown again and the user is asked if he wants to change the location of some of the boxes.
If that is the case the user kan type: sommige

Otherwise the user can type: ok

If the user wants to change some locations an image will apear of all the boxes. To change the location you can click on the center of the box and then to the new location. This can be done for multiple boxes at the same time. 

After this you have to close the window and type the numbers of the locations you want to change.

For example: If the first click was on the center of a box and the second click was on the new location then you type 0,1

If you change two boxes it is possible to type 0,1,2,3. Or you can also type "goed" and the program will change everything automatically.

### Step 4
Now it is possible to add some boxes if it's needed to add more boxes. This will be done 




