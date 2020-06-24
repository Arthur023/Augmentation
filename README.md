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


<img src="images/stap_0.JPG" width="300" >


