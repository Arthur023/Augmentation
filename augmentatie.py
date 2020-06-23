from cv2 import cv2
import os
import numpy as np
import re
from time import sleep
import gc
from matplotlib import pyplot as plt
import argparse
import math
import copy 
import random
from PIL import Image, ImageOps 
from scipy.ndimage import gaussian_filter, median_filter, minimum_filter,maximum_filter, percentile_filter,uniform_filter
# import imutils

# READ ME: PAS OP: Als we naar het text file schrijvan dan moet dit [x1,y1,x2,y2] zijn

"""
    De werking uitgelegd
    1) In de main is het mogelijk om mee te geven wat je wilt doen met de booleans die er staan. 
        Mogelijkheden:  - X aantal huidmondje van elke soort uitknippen in figuren van 600x800
                                stomata_200 = True
                                x_snijden {int} = Het aantal huidmondje je per soort wilt. Bv 200
                        - De image roteren
                                rotatie = True
                        - Het aantal huidmondjes per soort tellen en uitschrijven
                                tellen_mondjes = True
                        - De afbeelding in 2 knippen en de 2 helften opslaan
                                uitknippen_data = True
                        
            Als er voor stomata_200 wordt gekozen zijn er nog enkele opties:
                        - Willen we de foto opslaan in grijswaarde
                                zet_naar_grijswaarde = True 
                        - De foto normaliseren
                                img_norm = True
                        - De foto stretchen en het histogram nog wat aanpassen. (wordt gebruikt op trainingsdata)
                                training = True

        Hier zal ook worden meegegeven welke data er gebruikt wordt, waar deze staat opgeslaan op de computer en waar de uitgeknipte afbeeldingen moeten worden opgelsaan
        Als ook hoe het datapath wordt meegegeven om later in de jupyter hub te gebruiken

    We zullen nu doorgaan op de werking van het uitsnijden van X stomata per plaatsoort. Dit is namelijk het hoofddoel van de code
    2) def regel_x() wordt opgeroepen
        Belangrijke parameter: 
                        - input_user {boolean}: Met deze parameter kan je instellen of je handmatig de grote van de stomata per soort wilt bepalen
                                                Als je dat niet wilt doen wordt deze op 120x120 ingsteld

        De werking hiervan  staat al uitgelegd bij de functie zelf. Deze functie zal alles regelen

    
"""


### Hier het ophalen en inlezen van een lijst en zijn informatie

def inlezen_lijst(data_path):
    """
        Deze functie zal een lijst inlezen en een array terug geven
    
    Arguments:
        data_path {string} -- [zal de naam van de lijst meegeven die overlopen wordt]
    
    Returns:
        [array] -- Deze array zal bestaan uit 4 componenten:
                    - nummer
                    - x_coordinaten
                    - y_coordinaten
                    - naam afbeelding  
    """
    neem_deel_data = False   # Zal maar een klein deel van de data nemen. Goed voor het debuggen
    f = open(data_path, "r")
    count = 0
    start_array=[]
    opgesplitste_array = []
    f.readline()                        # hier lezen we de eerste lijn in. Deze hebben we namelijk niet nodig
    for x in f:
        start_array.append(x)
        
    for line in start_array:                # splits nu elke lijn op in een [nummer,x,y,naam_foto]        
        if neem_deel_data == True:
            if count<7:
                #print(count," ",line)
                opgesplitste_array.append(opsplitsen_lijn(line))
                count +=1
        else:
            opgesplitste_array.append(opsplitsen_lijn(line))
    return opgesplitste_array
           
def opsplitsen_lijn(lijn):
    """Zal een lijn txt opsplitsen in de 4 onderdelen 
        lijst_1 = [n, x, y, Foto]
        lijst_2 = [n, x, y, Foto, Item]
    
    Arguments:
        lijn {string} -- lijn text
    
    Returns:
        array[sting] -- een array met de 4 delen opgesplitst
    """
    lijst_1 = False # .txt ---- [nummer x y naam \n]
    lijst_2 = False # .txt ---- [nummer x y naam item \n]
    lijst_3 = True  # .txt ---- [x;y;naam;\n]

    if lijst_3 == True:
        
        test = []
        gesplitst = []
        test = re.split(";",lijn)
        test.insert(0,2)
        test = test[0:5]

    if lijst_1 == True or lijst_2 == True:
        test = []
        gesplitst = []
        test = re.split("\\s",lijn,3)
        test[3] = test[3][:-1]

        if lijst_1 == True:
            # Er moet niets worden gedaan. Bovenstaande code is voldoende
            # Dit is gewoon om het visueel beter te verstaan
            nutteloos_nummer = 0

        if lijst_2 == True:
            gesplitst = test[3].split()[:-1]    
            aan_elkaar_gezet = ""
            tel = 0
            for stuk in gesplitst:
                if tel == 0:
                    aan_elkaar_gezet = stuk
                else:
                    aan_elkaar_gezet = aan_elkaar_gezet+" "+stuk 
                tel += 1
            test[3] = aan_elkaar_gezet
    return test

def vind_bbox(volledige_lijst,data_path_foto):
    """zal een array teruggeven waar alle bboxen zijn samengezet per afbeelding
    
    Arguments:
        volledige_lijst {array[string]} -- een array met de 4 delen opgesplitst (deze zal komen uit opsplitsen_lijn)
                                        -- [int, x_co, y_co, naam_image]
    
    Returns:
        {array[string]} -- array waarbij de boxen telkens bij de juiste image worden gezet
                        -- array[naam_image, array[x_co,y_co]]
    """
    
    all_imgs = {}
    for lijn in volledige_lijst:
        filename = lijn[3]
        if os.path.isfile(data_path_foto+filename):
            if filename not in all_imgs:            
                all_imgs[filename] = {}
                all_imgs[filename]['filepath'] = lijn[3]
                all_imgs[filename]['grootte_bbox'] = lijn[4]
                all_imgs[filename]['bboxes'] = []
           
            index_y = lijn[2].find(',')
            index_x = lijn[1].find(',')
            if index_x != -1:
                tijdelijk = split_word(lijn[1])
                tijdelijk = lijn[1][0:index_x]
                lijn[1] = str(tijdelijk)
            if index_y != -1:
                tijdelijk = split_word(lijn[2])
                tijdelijk = lijn[2][0:index_y]
                lijn[2] = str(tijdelijk)
            all_imgs[filename]['bboxes'].append({'x': int(round(float(lijn[1]))), 'y': int(round(float(lijn[2])))})
        
    all_data = []
    for key in all_imgs:
        all_data.append(all_imgs[key])
    return all_data

def split_word(word): 
    return [char for char in word]  

### Ongebruikte functies voor het hoofddoel
def regel_alles_links_rechts(all_data,data_path_nieuwe_foto,data_path_foto,data_path_text,data_path_opslaag_plaats):
    """Hier zal alles worden geregeld om de afbeelding in 2 te knippen en als een links en rechts deel op te slaan
    Werkingsprinciepe:
        1) vraag image_info op
                Met: co_in_twee_snijden(images,data_path_foto)
                image_info {list} -- list{filename_oud,filename_nieuw,uitsnij_co[x1,x2,y1,y2],lijst{bboxes[x,y]}}
        2) Vraag image_uitgesneden op
                Met: uitsnijden_figuur(info_foto_rechts,data_path_foto)
                image_uitgesneden {image} -- een uitgesneden image
        3) Sla image op
                Met: opslaan_image(info_foto_links,uitgesneden_links, data_path_nieuwe_foto)
        4) Vraag co_bboxen op (image_info_x1_x2_y1_y2)
                Met: co_box(info_foto_links)
                image_info_x1_x2_y1_y2{lijst} -- list{filename_oud,filename_nieuw,lijst{bboxes[x1,x2,y1,y2]}}
        5) Schrijf naar een text file
                Met: schrijven_text_file_x1_x2_y1_y2(image_info_x1_x2_y1_y2,text_w,data_path_opslaag_plaats)
    Arguments:
        all_data {lijst[string,array[middelpunt]]} -- een array waarbij elke afbeelding is opgelsaan met de middelpunten van elke stomata
        data_path_nieuwe_foto {string} -- path waar de nieuwe foto wordt opgeslagen
        data_path_foto {string} -- path waar de foto zich nu bevind
        data_path_text {string} -- path waar het text file wordt opgeslagen
        data_path_opslaag_plaats {string} -- path waar de foto wordt opgeslagen op jupyter hub
    """
    # Hier zal alles worden samengesmeten
    count = 0
    text_path = data_path_nieuwe_foto + data_path_text
    text_w = open(text_path, "w+")
    for images in all_data:
        print('count',count)
        count += 1
        info_foto_links, info_foto_rechts = co_in_twee_snijden(images,data_path_foto)
        uitgesneden_links = uitsnijden_figuur(info_foto_links,data_path_foto)
        uitgesneden_rechts = uitsnijden_figuur(info_foto_rechts,data_path_foto)
        opslaan_image(info_foto_links,uitgesneden_links, data_path_nieuwe_foto)
        opslaan_image(info_foto_rechts,uitgesneden_rechts, data_path_nieuwe_foto)
        #print('info_foto_links',info_foto_links)
        image_info_x1_x2_y1_y2_links = co_box(info_foto_links)
        schrijven_text_file_x1_x2_y1_y2(image_info_x1_x2_y1_y2_links,text_w,data_path_opslaag_plaats)
        
        image_info_x1_x2_y1_y2_rechts = co_box(info_foto_rechts)
        schrijven_text_file_x1_x2_y1_y2(image_info_x1_x2_y1_y2_rechts,text_w,data_path_opslaag_plaats)
        #schrijven_text_file_centrum_huidmondje(info_foto_links,text_w)    
    text_w.close()

def rotate_image(image, angle):
    image_center = tuple(np.array(image.shape[1::-1]) / 2)
    rot_mat = cv2.getRotationMatrix2D(image_center, angle, 1.0)
    result = cv2.warpAffine(image, rot_mat, image.shape[1::-1], flags=cv2.INTER_LINEAR)
    return result

  
def co_in_twee_snijden(array_image,data_path):
    """ Zal de nieuwe co teruggeven van 1 image nadat deze is uitgesneden

    Arguments:
        array_image {'filepath','bboxes'} 
                                    bboxes = array[{'x','y'}]
                                    -- Dit zal 1 filepath bevatten en van deze afbeelding dan alle middelpunt_coordinaten
    Returns:
        image_info {list} -- list{filename_oud,filename_nieuw,uitsnij_co[x1,x2,y1,y2],lijst{bboxes[x,y]}}
                            filename_oud: naam van originele image
                            filename_nieuw: Naam van uitgesneden image. Bv met links_ voor
                            uitsnij_co: De coordinaten van de hoekpunten van het deel dat zal worden uitgesneden
                            lijst{bboxes}: Een lijst van de coordinaten van het middelpunt van de huidmondjes die tot het uitgesneeden deel behoren
    """
    info_foto_links = {}
    info_foto_rechts = {}
    # Maak naam naar foto
    data_path_foto = data_path + array_image['filepath']
    # Haal foto op
    img = cv2.imread(data_path_foto)
    # Shape image
    #cv2.imshow('img',img)
    y_shape,x_shape,z_shape = img.shape
    naam_links = 'links_'+ array_image['filepath']
    info_foto_links['filename_oud'] = array_image['filepath']
    info_foto_links['filename_nieuw'] = naam_links
    info_foto_links['uitsnij_co'] = {}
    info_foto_links['bboxes'] = []

    info_foto_rechts['filename_oud'] = array_image['filepath'] 
    info_foto_rechts['filename_nieuw'] = 'rechts_'+ array_image['filepath'] 
    info_foto_rechts['uitsnij_co'] = {}  
    info_foto_rechts['bboxes'] = []

    if y_shape>x_shape:
        y_half = int(y_shape/2)
        info_foto_links['uitsnij_co']['x1'] = 0
        info_foto_links['uitsnij_co']['y1'] = 0
        info_foto_links['uitsnij_co']['x2'] = x_shape
        info_foto_links['uitsnij_co']['y2'] = y_half
        info_foto_rechts['uitsnij_co']['x1'] = 0
        info_foto_rechts['uitsnij_co']['y1'] = y_half
        info_foto_rechts['uitsnij_co']['x2'] = x_shape
        info_foto_rechts['uitsnij_co']['y2'] = y_shape
        for boxes in array_image['bboxes']:
            if boxes['y'] < y_half:
                info_foto_links['bboxes'].append({'x':boxes['x'],'y':boxes['y']})
            else:
                info_foto_rechts['bboxes'].append({'x':boxes['x'],'y':int(boxes['y']-y_half)})
            #print('boxes: ',boxes)
    if x_shape>y_shape:
        x_half = int(x_shape/2)
        info_foto_links['uitsnij_co']['x1'] = 0
        info_foto_links['uitsnij_co']['y1'] = 0
        info_foto_links['uitsnij_co']['x2'] = x_half
        info_foto_links['uitsnij_co']['y2'] = y_shape
        info_foto_rechts['uitsnij_co']['x1'] = x_half
        info_foto_rechts['uitsnij_co']['y1'] = 0
        info_foto_rechts['uitsnij_co']['x2'] = x_shape
        info_foto_rechts['uitsnij_co']['y2'] = y_shape
        for boxes in array_image['bboxes']:
            if boxes['x'] < x_half:
                info_foto_links['bboxes'].append({'x':boxes['x'],'y':boxes['y']})
            else:
                info_foto_rechts['bboxes'].append({'x':int(boxes['x']-x_half),'y':boxes['y']})
            #print('boxes: ',boxes)

    # Lange zijde in twee (x is lange zijde)
    # Alle bboxes met x>... in 1 tabel alle andere in een andere tabel
    # Deze tabellen moeten nu ook een nieuwe naam bevatten voor de image. Zoals naam_image + _links
    # Deze tabellen moeten ook de [x1,y1,x2,y2] co bevatten van hoe de figuur is uitgesneden 

    # Alles hierna moet eigenlijk waar we deze functie oproepen
    # Roep uitsnijden figuur op om de 2 nieuwe figuren uit te snijden. Geef hier ook de nieuwe naam van de image mee
    
    return info_foto_links, info_foto_rechts

### Schrijven text file en opslaan image

def schrijven_text_file_x1_x2_y1_y2(image_info_x1_x2_y1_y2,text_w,data_path_opslaag_plaats):
    """zal naar een text file schrijven met de bboxes van de huidmondjes
    
    Arguments:
        image_info_x1_x2_y1_y2{lijst} -- list{filename_oud,filename_nieuw,lijst{bboxes[x1,x2,y1,y2]}}
                            filename_oud: naam van originele image
                            filename_nieuw: Naam van uitgesneden image. Bv met links_ voor
                            lijst{bboxes}: Een lijst met de hoekpunt coordinaten van de huidmondjes die tot het uitgesneeden deel behoren
        text_w {text file} -- De text file waar we naar aan het schrijven zijn 
        data_path_opslaag_plaats {string} -- naam van waar we de image willen opslaan in jupyter hub
    """
    # print('schrijven_text_file_x1_x2_y1_y2!!!!!!!!')
    for lijn in image_info_x1_x2_y1_y2['bboxes']:
        opslaag_plaats = data_path_opslaag_plaats + image_info_x1_x2_y1_y2['filename_nieuw']
        text_w.write(opslaag_plaats + ',' + str(lijn['x1']) + ',' + str(lijn['y1']) + ',' + str(lijn['x2']) + ',' + str(lijn['y2'])+ ','+'huidmond' +'\n')

def schrijven_text_file_centrum_huidmondje(image_info,text_w):
    """Zal de middelpunten van de huidmondjes naar een textfile schrijven 
    
    Arguments:
        image_info {list} -- list{filename_oud,filename_nieuw,uitsnij_co[x1,x2,y1,y2],lijst{bboxes[x,y]}}
                            filename_oud: naam van originele image
                            filename_nieuw: Naam van uitgesneden image. Bv met links_ voor
                            uitsnij_co: De coordinaten van de hoekpunten van het deel dat zal worden uitgesneden
                            lijst{bboxes}: Een lijst van de coordinaten van het middelpunt van de huidmondjes die tot het uitgesneeden deel behoren
        text_w {text file} -- de text file
    """
    #print('image_info[filename_nieuw]',image_info['filename_nieuw'])
    for lijn in image_info['bboxes']:
        text_w.write(image_info['filename_nieuw'] + ',' + str(lijn['x']) + ',' + str(lijn['y']) +'\n')
    
def opslaan_image(image_info,image, path_nieuwe_foto):
    plaats_naam_image = path_nieuwe_foto+image_info['filename_nieuw']
    cv2.imwrite(plaats_naam_image,image) #array_images[tel])
  
### Functies die het aantal huidmondjes tellen

def count_stomata_eenmalig(array_ingelezen_lijst):
    """Zal per plant tellen hoeveel huidmondjes deze heeft
    
    Arguments:
        array_ingelezen_lijst {[type]} -- [description]
    Return:
        counted_data {list} -- list{plantnaam,'count'=nummer, 'filepath'=[namen]}
                            -- Met de plantnaam de algemene naam van de plant
                            -- count = hoeveel stomata deze plant bezit
                            -- filepath = een array met alle namen van de originele images. Dus met blad1_vlak2.jpg erbij
    """
    array_naam = []
    lijst_naam = {}
    for lijn in array_ingelezen_lijst:
        # print('lijn',lijn)
        naam = lijn[3].split('_')
        # print('naam',naam)
        tot_naam = naam[0]  #+' '+naam[1]
        # print('tot_naam: ',tot_naam)
        array_naam.append({'tot_naam':tot_naam, 'path':lijn[3]})
    #print('array_naam ',array_naam)
    for naam in array_naam:
        plantnaam = naam['tot_naam']
        if plantnaam not in lijst_naam:            
            lijst_naam[plantnaam] = {}
            lijst_naam[plantnaam]['plantnaam'] = plantnaam
            lijst_naam[plantnaam]['count'] = 1
            lijst_naam[plantnaam]['filepath'] = []
            lijst_naam[plantnaam]['filepath'].append(naam['path'])
        else:
            lijst_naam[plantnaam]['count'] = lijst_naam[plantnaam]['count'] + 1
            if naam['path'] not in lijst_naam[plantnaam]['filepath']:
                lijst_naam[plantnaam]['filepath'].append(naam['path'])
    
    all_data = []
    for key in lijst_naam:
        all_data.append(lijst_naam[key])
    #for lijn in all_data:
    #    print(lijn)  
    #print('all_data: ',all_data)  
    return(all_data)

def count_blad(blad):
    return len(blad['bboxes'])

def count_image_info(image_info):
    # print('len(image_info):',len(image_info['bboxes']))
    return len(image_info['bboxes'])

def count_all_data(all_data):
    """Zelfde als count_stomata_once maar nu op all_data
    
    Arguments:
        all_data {[type]} -- [description]
    Return:
        all_data_counted{lijst[string,int,array[namen]]} -- Een lijst hiervan. Dus met alle planten in 
                                            string = plantnaam. Dus de basis naam van ene plant zonder blad_vlak.jpg
                                            int = count: Aantal stomata van deze plant
                                            array[namen]: Een array van alle specifieke namen met blad_vlak.jpg
    """
    array_naam = []
    lijst_naam = {}
    for lijn in all_data:
        naam = lijn['filepath'].split('_')
        tot_naam = naam[0]+' '+naam[1]
        #print('tot_naam: ',tot_naam)
        array_naam.append({'tot_naam':tot_naam, 'path':lijn['filepath'], 'bboxes':lijn['bboxes']})
    #print('array_naam ',array_naam)
    for naam in array_naam:
        plantnaam = naam['tot_naam']
        if plantnaam not in lijst_naam:            
            lijst_naam[plantnaam] = {}
            lijst_naam[plantnaam]['plantnaam'] = plantnaam
            lijst_naam[plantnaam]['count'] = len(naam['bboxes'])
            lijst_naam[plantnaam]['filepath'] = []
            lijst_naam[plantnaam]['filepath'].append(naam['path'])
        else:
            lijst_naam[plantnaam]['count'] = lijst_naam[plantnaam]['count'] +  len(naam['bboxes'])
            if naam['path'] not in lijst_naam[plantnaam]['filepath']:
                lijst_naam[plantnaam]['filepath'].append(naam['path'])
    
    all_data_counted = []
    for key in lijst_naam:
        all_data_counted.append(lijst_naam[key])
    #for lijn in all_data:
    #    print(lijn)  
    #print('all_data: ',all_data)  
    return(all_data_counted)

def count_all_data_nummer(all_data):
    all_data_counted = count_all_data(all_data)
    return all_data_counted[0]['count']

### Ophalen coordinaten 

def co_box(image_info,bbox=120, stretch = [1,1]):
    """ We geven een list mee met de coordinaten van het deel van de afbeelding dat we willen uitsnijden. Hiervan de 2 hoeken
        En ook alle boxes binnen deze afbeelding
        We krijgen een list terug met alle boxes die hierbinnen liggen
    Arguments:
        image_info {list} -- list{filename_oud,filename_nieuw,uitsnij_co[x1,x2,y1,y2],lijst{bboxes[x,y]}}
                            filename_oud: naam van originele image
                            filename_nieuw: Naam van uitgesneden image. Bv met links_ voor
                            uitsnij_co: De coordinaten van de hoekpunten van het deel dat zal worden uitgesneden
                            lijst{bboxes}: Een lijst van de coordinaten van het middelpunt van de huidmondjes die tot het uitgesneeden deel behoren
    Returns:
        image_info_x1_x2_y1_y2{lijst} -- list{filename_oud,filename_nieuw,lijst{bboxes[x1,x2,y1,y2]}}
                            filename_oud: naam van originele image
                            filename_nieuw: Naam van uitgesneden image. Bv met links_ voor
                            lijst{bboxes}: Een lijst met de hoekpunt coordinaten van de huidmondjes die tot het uitgesneeden deel behoren
    """
    # print('bbox',bbox)
    test = int(bbox)
    # print('test',test)
    bbox_grootte = bbox/2
    image_info_x1_x2_y1_y2 = {}
    image_info_x1_x2_y1_y2['filename_oud'] =  image_info['filename_oud']
    image_info_x1_x2_y1_y2['filename_nieuw'] =  image_info['filename_nieuw']
    image_info_x1_x2_y1_y2['bboxes'] = []
    for lijn in image_info['bboxes']:        
        x_co = lijn['x']
        y_co = lijn['y']
        x1= x_co-bbox_grootte*stretch[0]
        x2= x_co+bbox_grootte*stretch[0]
        y1= y_co-bbox_grootte*stretch[1]
        y2= y_co+bbox_grootte*stretch[1]

        if(y_co<bbox_grootte):
            y1=0
        if(y_co+bbox_grootte>image_info['uitsnij_co']['y2']-image_info['uitsnij_co']['y1']):
            y2=int(image_info['uitsnij_co']['y2']-image_info['uitsnij_co']['y1'])
        if(x_co<bbox_grootte):
            x1=0
        if(x_co+bbox_grootte>image_info['uitsnij_co']['x2']-image_info['uitsnij_co']['x1']):
            x2=int(image_info['uitsnij_co']['x2']-image_info['uitsnij_co']['x1'])
        
        x1 = int(x1)
        x2 = int(x2)
        y1 = int(y1)
        y2 = int(y2)

        image_info_x1_x2_y1_y2['bboxes'].append({'x1':x1,'x2':x2,'y1':y1,'y2':y2})
   
    return image_info_x1_x2_y1_y2

def co_stuk_vier(array_image,image,stuk,augment):
    """Geeft de coordinaten terug van 1 van de 4 stukken
        Ook de bboxes zijn al aangepast naar de juiste coordinaten
    
    Arguments:
        array_image {'filepath','bboxes'} 
                                    bboxes = array[{'x','y'}]
                                    -- Dit zal 1 filepath bevatten en van deze afbeelding dan alle middelpunt_coordinaten
        data_path_foto {string} -- Data path waar de foto zich bevind
        stuk {int} -- Welk stuk we willen. 
                        = 0 -> Links boven
                        = 1 -> Links onder
                        = 2 -> Rechts boven
                        = 3 -> Rechts onder
    Returns:
        image_info {list} -- list{filename_oud,filename_nieuw,uitsnij_co[x1,x2,y1,y2],lijst{bboxes[x,y]}}
                            filename_oud: naam van originele image
                            filename_nieuw: Naam van uitgesneden image. Bv met links_ voor
                            uitsnij_co: De coordinaten van de hoekpunten van het deel dat zal worden uitgesneden
                            lijst{bboxes}: Een lijst van de coordinaten van het middelpunt van de huidmondjes die tot het uitgesneeden deel behoren
    """
    debug = False

    info_foto = {}
    H_filp = augment[0]
    V_flip = augment[1]
    rotate = augment[2]
    augment_naam = ''
    if H_filp == True:
        augment_naam = augment_naam + 'H_'
    if V_flip == True:
        augment_naam = augment_naam + 'V_'
    if rotate != 0:
        augment_naam = augment_naam + str(rotate) + '_'
    # Maak naam naar foto
    #data_path_foto = data_path_foto + array_image['filepath']
    # Haal foto op
    img = image
    y_shape = img.shape[0]
    x_shape = img.shape[1]
    if stuk == 0:
        keuze = 'LB'
    if stuk == 1:
        keuze = 'LO'
    if stuk == 2:
        keuze = 'RB'
    if stuk == 3:
        keuze = 'RO'
    naam = keuze + '_'+ augment_naam + array_image['filepath']
    if debug == True:
        print('naam_nu: ',naam)
    info_foto['filename_oud'] = array_image['filepath']
    info_foto['filename_nieuw'] = naam
    info_foto['uitsnij_co'] = {}
    info_foto['bboxes'] = []

    y_half = int(y_shape/2)
    x_half =   int(x_shape/2)
    if stuk == 0:
        info_foto['uitsnij_co']['x1'] = 0
        info_foto['uitsnij_co']['y1'] = 0
        info_foto['uitsnij_co']['x2'] = x_half
        info_foto['uitsnij_co']['y2'] = y_half
    if stuk == 1:
        info_foto['uitsnij_co']['x1'] = 0
        info_foto['uitsnij_co']['y1'] = y_half
        info_foto['uitsnij_co']['x2'] = x_half
        info_foto['uitsnij_co']['y2'] = y_shape
    if stuk == 2:
        info_foto['uitsnij_co']['x1'] = x_half
        info_foto['uitsnij_co']['y1'] = 0
        info_foto['uitsnij_co']['x2'] = x_shape
        info_foto['uitsnij_co']['y2'] = y_half
    if stuk == 3:
        info_foto['uitsnij_co']['x1'] = x_half
        info_foto['uitsnij_co']['y1'] = y_half
        info_foto['uitsnij_co']['x2'] = x_shape
        info_foto['uitsnij_co']['y2'] = y_shape
    for boxes in array_image['bboxes']:
        if debug == True:
            print('boxes_test:',boxes)
        if boxes['y'] < info_foto['uitsnij_co']['y2'] and boxes['y']>info_foto['uitsnij_co']['y1']:
            if boxes['x']<info_foto['uitsnij_co']['x2'] and boxes['x']>info_foto['uitsnij_co']['x1']:                
                info_foto['bboxes'].append({'x':boxes['x']-info_foto['uitsnij_co']['x1'],'y':boxes['y']-info_foto['uitsnij_co']['y1']})
                if debug == True:
                    print('TOEGEVOEGD')
                
    #print('info_foto:',info_foto)
    return(info_foto)

def co_stuk_rotate(array_image,image,image_rot,augment,angle,co_beginpunt,x_gevonden_stuk):
    """Geeft de coordinaten terug van het eerste uitgesneden stuk
        Ook de bboxes zijn al aangepast naar de juiste coordinaten
    
    Arguments:
        array_image {'filepath','bboxes'} 
                                    bboxes = array[{'x','y'}]
                                    -- Dit zal 1 filepath bevatten en van deze afbeelding dan alle middelpunt_coordinaten
        image {image} -- De geaugmenteerde image (voor rotatie)
                         Wordt niet gebruikt alleen tijdens debugging
        image_rot {image} -- De geroteerde image (dit is de image waarop we alles zullen uitvoeren )
        augment {array} -- [H_flip,V_flip,rotate]: Hier zal worden weergegeven ofdat er aan augmentatie wordt gedaan [Boolean,Boolean,int]
        angle {int} -- de angle waarmee de image geroteerd is
        co_beginpunt {array[int,int]} -- Array met x,y coordinaten van waar we beginnen zoeken. Dit zal eerst (0,0) zijn 
                                        maar als we al een vierkant hebben gevonden in de geroteerde image kan dit ook anders zijn
        x_gevonden_stuk {int} -- Dit is eerst 0 maar als er al een vierkant in de image is gevonden wordt dit 1
                                Wordt gebruikt bij de nieuwe naam van de image
        
    Returns:
        image_info {list} -- list{filename_oud,filename_nieuw,uitsnij_co[x1,x2,y1,y2],lijst{bboxes[x,y]}}
                            filename_oud: naam van originele image
                            filename_nieuw: Naam van uitgesneden image. Bv met links_ voor
                            uitsnij_co: De coordinaten van de hoekpunten van het deel dat zal worden uitgesneden
                            lijst{bboxes}: Een lijst van de coordinaten van het middelpunt van de huidmondjes die tot het uitgesneeden deel behoren
    """
    debug = False

    image_info = {}
    H_filp = augment[0]
    V_flip = augment[1]
    augment_naam = ''
    if H_filp == True:
        augment_naam = augment_naam + 'H_'
    if V_flip == True:
        augment_naam = augment_naam + 'V_'        
    augment_naam = augment_naam + str(angle) + '_'

    naam = str(x_gevonden_stuk) + '_'+ augment_naam + array_image['filepath']
    print('naam_nu: ',naam)
    image_info['filename_oud'] = array_image['filepath']
    image_info['filename_nieuw'] = naam
    image_info['uitsnij_co'] = {}
    image_info['bboxes'] = []

    image_info['uitsnij_co']['x1'] = co_beginpunt[0]
    image_info['uitsnij_co']['y1'] = co_beginpunt[1]
    image_info['uitsnij_co']['x2'] = co_beginpunt[0]+800
    image_info['uitsnij_co']['y2'] = co_beginpunt[1]+600
    for boxes in array_image['bboxes']:
        if debug == True:
            print('boxes_test:',boxes)
        if boxes['y'] < image_info['uitsnij_co']['y2'] and boxes['y']>image_info['uitsnij_co']['y1']:
            if boxes['x']<image_info['uitsnij_co']['x2'] and boxes['x']>image_info['uitsnij_co']['x1']:                
                image_info['bboxes'].append({'x':boxes['x']-image_info['uitsnij_co']['x1'],'y':boxes['y']-image_info['uitsnij_co']['y1']})
                if debug == True:
                    print('TOEGEVOEGD')
    #print('info_foto:',info_foto)
    
    #show_fliped_img(image,image_rot)
    return(image_info)    

### Het uitsnijden van een image in een blok van 600x800

def uitsnijden_figuur(image_info,data_path):
    """De figuur zal worden uitgesneden
        Doet alleen iets op de image zelf
    
    Arguments:
        mage_info {list} -- list{filename_oud,filename_nieuw,uitsnij_co[x1,x2,y1,y2],lijst{bboxes[x,y]}}
                            filename_oud: naam van originele image
                            filename_nieuw: Naam van uitgesneden image. Bv met links_ voor
                            uitsnij_co: De coordinaten van de hoekpunten van het deel dat zal worden uitgesneden
                            lijst{bboxes}: Een lijst van de coordinaten van het middelpunt van de huidmondjes die tot het uitgesneeden deel behoren
        data_path {string} -- waar op de computer de foto's terug te vinden zijn
    
    Returns:
        image_uitgesneden -- [een uitgesneden image]
    """
    debug = False
    plaats_naam_image = data_path+image_info['filename_oud'] # Zorg hier voor de plaatsnaam
    image_totaal = cv2.imread(plaats_naam_image)   
    if(debug == True):
        print('uitsnijden')
        print('y1',int(image_info['uitsnij_co']['y1']))
        print('y2',int(image_info['uitsnij_co']['y2']))
        print('x1',int(image_info['uitsnij_co']['x1']))
        print('x2',int(image_info['uitsnij_co']['x2']))
    image_uitgesneden = image_totaal[int(image_info['uitsnij_co']['y1']):int(image_info['uitsnij_co']['y2']), int(image_info['uitsnij_co']['x1']):int(image_info['uitsnij_co']['x2'])]
    return image_uitgesneden

def uitsnijden_figuur_image(image_info,image):
    """De figuur zal worden uitgesneden
        Doet alleen iets op de image zelf
    
    Arguments:
        mage_info {list} -- list{filename_oud,filename_nieuw,uitsnij_co[x1,x2,y1,y2],lijst{bboxes[x,y]}}
                            filename_oud: naam van originele image
                            filename_nieuw: Naam van uitgesneden image. Bv met links_ voor
                            uitsnij_co: De coordinaten van de hoekpunten van het deel dat zal worden uitgesneden
                            lijst{bboxes}: Een lijst van de coordinaten van het middelpunt van de huidmondjes die tot het uitgesneeden deel behoren
        image {image} -- Hier zal de image worden meegegeven 
    
    Returns:
        image_uitgesneden -- [een uitgesneden image]
    """
    debug = False
    #plaats_naam_image = data_path+image_info['filename_oud'] # Zorg hier voor de plaatsnaam
    image_totaal = image
    if(debug == True):
        print('uitsnijden')
        print('y1',int(image_info['uitsnij_co']['y1']))
        print('y2',int(image_info['uitsnij_co']['y2']))
        print('x1',int(image_info['uitsnij_co']['x1']))
        print('x2',int(image_info['uitsnij_co']['x2']))
    image_uitgesneden = image_totaal[int(image_info['uitsnij_co']['y1']):int(image_info['uitsnij_co']['y2']), int(image_info['uitsnij_co']['x1']):int(image_info['uitsnij_co']['x2'])]
    return image_uitgesneden

def augmentatie(blad,data_path_foto,augment,debug):
    # We willen hier gedraaide image terug geven samen met de aangepaste data
    debug = False
    H_flip = augment[0]
    V_flip = augment[1]
    rotate = augment[2]
    blad_aug = copy.deepcopy(blad)
    # if debug == True:
    #     print('augmentatie: ',augment)
    data_path_foto_test = data_path_foto + blad['filepath']
    # print('data_path_foto_test',data_path_foto_test)
    image = cv2.imread(data_path_foto_test)
    # if debug == True:
    #     beeld_bboxen_met_h_b_af(image,blad_aug,image)
    #plt.imshow(image)
    # show_img_hist_x([image])
    try:
        y_shape = image.shape[0]
        x_shape = image.shape[1]
    
    except:
        print('data_path_foto_test',data_path_foto_test)
        show_img_hist_x([image])

    
    image_flip = image
    if V_flip == True:
        image_flip = cv2.flip(image_flip, 0)
        # print('V_FLIP')
        for bbox in blad_aug['bboxes']:
            y = bbox['y']
            bbox['y'] = y_shape - y
    if H_flip == True:
        image_flip = cv2.flip(image_flip, 1)
        # print('H_FLIP')
        for bbox in blad_aug['bboxes']:
            x = bbox['x']
            bbox['x'] = x_shape - x
    image_rot = copy.deepcopy(image_flip)
    # if debug == True:        
    #     print('blad_flip',blad_aug)
    #     print('augment',augment)
        # beeld_bboxen_met_h_b_af(image_rot,blad_aug,image_flip)
    if rotate != 0:
        # if rotate == 3:
        #     image_rot = np.transpose(image_rot, (1,0,2))
        #     image_rot = cv2.flip(image_rot, 0)
        # elif rotate == 2:
        #     image_rot = cv2.flip(image_rot, -1)
        if rotate == 1:
            image_rot = np.transpose(image_rot, (1,0,2))
            image_rot = cv2.flip(image_rot, 1)
        y_shape = image_rot.shape[0]
        x_shape = image_rot.shape[1]
        if debug == True:        
            print('blad_flip',blad_aug)
            print('x',x_shape)
            print('y',y_shape)
        for bbox in blad_aug['bboxes']:
            x = bbox['x']
            y = bbox['y']
            # if rotate == 3:                
            #     bbox['x'] = y
            #     bbox['y'] = x_shape-x
            # elif rotate == 2:
            #     bbox['x'] = x_shape-x
            #     bbox['y'] = y_shape-y
            if rotate == 1:
                bbox['x'] = x_shape-y
                bbox['y'] = x
    #plt.imshow(image_flip)
    if debug == True:        
        # print('blad_flip',blad_aug)
        # print('blad_flip_normaal',blad)
        beeld_bboxen_met_h_b_af(image_flip,blad_aug,image_rot)
        #show_fliped_img(image,image_flip)
    return image_rot, blad_aug

### Kijken of de bboxen wel binnen de image liggen /  Kijken ofdat de stomata wel voor 70% wordt afgebeeld
def bewerk_image_info(image_info,image,bbox_grootte,debug = False):
    """
        Wordt gebruikt om de image_info wat te filteren.
        Wanneer de bbox niet voor minstens 70% op de afbeelding staat zal deze uit de lijst image_info worden verwijderd
        Zo vermijden dat we halve mondjes gaan proberen detecteren
    """
    x = image.shape[1]
    y = image.shape[0]
    pix_rand = bbox_grootte/2
    pix_rand = pix_rand*0.2
    nieuw_image_info = {}
    nieuw_image_info['filename_oud'] = image_info['filename_oud']
    nieuw_image_info['filename_nieuw'] = image_info['filename_nieuw']
    nieuw_image_info['uitsnij_co'] = image_info['uitsnij_co']    
    nieuw_image_info['bboxes'] = []
        # img_info: {'filename_oud': 'Gilbertiodendron dewevrei_G5-11_blad3-vlak2.jpg', 'filename_nieuw': 'LB_H_V_1_Gilbertiodendron dewevrei_G5-11_blad3-vlak2.jpg', 
        #                 'uitsnij_co': {'x1': 0, 'y1': 0, 'x2': 600, 'y2': 800}, 'bboxes': [{'x': 348, 'y': 688}, {'x': 379, 'y': 163}, {'x': 200, 'y': 65}]}
    if debug == True:
        print('x',x)    
        print('x-pix_rand',x-pix_rand)
        print('y',y)
        print('img_info_start',image_info)
    for bbox in image_info['bboxes']:     
        if debug == True:   
            print('bbox[x]',bbox['x'])
        if bbox['x'] < pix_rand or bbox['x']> x-pix_rand or bbox['y'] < pix_rand or bbox['y'] > y-pix_rand:
            i = 0
            # if debug == True:
            #     print('remove bbox[x]',bbox['x'])
            # image_info['bboxes'].remove(bbox)
        else:
            nieuw_image_info['bboxes'].append({'x':bbox['x'],'y':bbox['y']})
    if debug == True:
        print('img_info_stop',nieuw_image_info)
    return nieuw_image_info
   
### Het ophalen van de planten binnen een plantensoort   
def ophalen_planten(all_data,lijn):
    """Hier halen we de juiste planten op van een bepaalde soort.
    
    Arguments:
        all_data {lijst[string,array[middelpunt]]} -- een array waarbij elke afbeelding is opgelsaan met de middelpunten van elke stomata
        lijn {string,int,array[namen]} -- Slechts 1 plant soort
                                            string = plantnaam. Dus de basis naam van ene plant zonder blad_vlak.jpg
                                            int = count: Aantal stomata van deze plant
                                            array[namen]: Een array van alle specifieke namen met blad_vlak.jpg
    Returns:
        planten_soort {lijst[string,array[middelpunt]]} -- lijst in de vorm van all_data. Maar alleen met de juist planten in 
    """
    planten_soort = []
    # print('lijn',lijn)
    for soort in lijn['filepath']:
        # print('soort',soort)
        for so in all_data:
            if soort == so['filepath']:
                planten_soort.append(so)

    # for p_naam in planten_soort:
    #     print('p_naam',p_naam)
    return planten_soort

### Hier alle functies dit te maken hebben met het roteren, stretchen of uitknippen van een image en de image_info

def rotate_bound(image,blad,angle):
    # grab the dimensions of the image and then determine the
    # center
    debug = False
    gedraaid_blad = {}
    gedraaid_blad['filepath'] = blad['filepath']
    gedraaid_blad['bboxes'] = []
    gedraaide_punten = []
    (h, w) = image.shape[:2]
    (cX, cY) = (w // 2, h // 2)
    # grab the rotation matrix (applying the negative of the
    # angle to rotate clockwise), then grab the sine and cosine
    # (i.e., the rotation components of the matrix)
    M = cv2.getRotationMatrix2D((cX, cY), -angle, 1.0)
    cos = np.abs(M[0, 0])
    sin = np.abs(M[0, 1])
    # compute the new bounding dimensions of the image
    nW = int((h * sin) + (w * cos))
    nH = int((h * cos) + (w * sin))
    # adjust the rotation matrix to take into account translation
    M_Transponeerd = copy.deepcopy(M)
    M_Transponeerd[0, 2] += (nW / 2) - cX
    M_Transponeerd[1, 2] += (nH / 2) - cY
    # perform the actual rotation and return the image
    gedraaid_img = cv2.warpAffine(image, M_Transponeerd, (nW, nH))
    # print('M:',M)
    # print('M_Transponeerd',M_Transponeerd)
    # print('angle',angle)
    point = []
    for punten in blad['bboxes']:
        px = float(punten['x'])
        py = float(punten['y'])
        co = [px,py]
        point.append(co)
        gedraaid_punt = rotate_punt(co,M_Transponeerd)
        if debug == True:
            print('gedraaid',gedraaid_punt)
        x_draai = int(gedraaid_punt[0])
        y_draai = int(gedraaid_punt[1])
        gedraaide_punten.append([x_draai,y_draai])
    i = 0
    for punt in gedraaide_punten:
        gedraaid_blad['bboxes'].append({'x':punt[0],'y':punt[1]})
    # for punten in blad['bboxes']:
    #     punten['x'] = gedraaide_punten[i][0]
    #     punten['y'] = gedraaide_punten[i][1]
    
    if debug == True:
        print('gedraaide punten:',gedraaide_punten)
        print('punten',point)
        print('blad',blad)
        print('gedraaid_blad:',gedraaid_blad)
    return gedraaid_img,gedraaid_blad
        
def rotate_punt(punt,M):
    M_copy = np.delete(M,2,1)
    #print('M_copy',M_copy)
    #print('punt',punt)
    gedraaid_punt = np.dot(M_copy, punt)
    gedraaid_punt[0] += M[0][2]
    gedraaid_punt[1] += M[1][2]
    return gedraaid_punt

def check_600_verticaal(image_rot,co_beginpunt):
    # loop over the image, pixel by pixel
    """    
        Als we ooit 400x300 foto's willen dan gaan we hier de 600 moeten veranderen in 300
    """
    count = 0
    
    h = image_rot.shape[0]
    if(h>co_beginpunt[1]+606):
        for y in range(co_beginpunt[1], co_beginpunt[1]+606): 
            if np.any(image_rot[y,co_beginpunt[0]] != 0):
                count += 1
                #print('img',image_rot[y,x])
            if count == 601:
                # print('!!!!!!!!!!!!!!!!!!',[co_beginpunt[0],y])
                # print('img',image_rot[y-600,co_beginpunt[0]])
                return True
    #print('x')
    return False

def vind_800_pix_horizontaal(image_rot,start_co):
    """ Zal de plaats weergeven van de eerste pixel van de geroteerde image waar er 800 pixels 
        later horizontaal ook nog een image bevind

        Als we ooit 400x300 foto's willen dan gaan we hier de 800 moeten veranderen in 400
    """
    h = image_rot.shape[0]
    w = image_rot.shape[1]
    # loop over the image, pixel by pixel
    # # print('start_co[1]',start_co[1])
    # show_img_hist_x([image_rot])
    for y in range(start_co[1], h):        
        count=0
        for x in range(0, w):            
            if np.any(image_rot[y,x] != 0):
                count += 1
                # print('x',x)
                # print('y',y)
                # print('img',image_rot[y,x])
            if count == 801:
                co_beginpunt=[x-800,y]                
                goed = check_600_verticaal(image_rot,co_beginpunt)
                if goed == True:
                    # print('!!!!!!!!!!!!!!!!!!',co_beginpunt)
                    # print('img',image_rot[y,x-800])
                    return True,co_beginpunt
    
    # print('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
    # print('Hier is iets foutgelopen: vind_800_pix_horizontaal')
    # print('In de geroteerde figuur kunnen we geen 800x600 figuur uitsnijden')
    return False,[0,0]

def stretch_image_en_co(image_info, image):
    """
        De foto zal worden binnengenomen samen met de array image_info
        Er zal dan gekeken worden of en hoeveel er gestretched wordt
        Dit zal random bepaald worden
        Vervolgens wordt de gestretchte image terug afgesneden op 600x800
        Dit zal worden terug gegeven
        In de array image_info zullen de bboxen ook mee verschoven worden
    """
    i = 0    
    stretchen = random.randint(0, 1)
    stretchen = 1
    # print('image_info_start',image_info)
    if stretchen == 1:
        originele_width = image.shape[1]
        originele_height = image.shape[0]
        num1 = random.randint(0, 12)
        de_nummers = [0.8,0.85,0.9,0.95,0.98,0.99,1,1.01,1.02,1.05,1.1,1.15,1.2]
        nummer = de_nummers[num1]
        if nummer<1:
            nummer = 2- nummer
            height = int(image.shape[0]*nummer) 
            width = image.shape[1]
            stretch = [1,nummer]
            for bbox in image_info['bboxes']:
                bbox['y'] = int(bbox['y']*nummer)
        else:
            width = int(image.shape[1]*nummer)
            height = image.shape[0]
            stretch = [nummer,1]
            for bbox in image_info['bboxes']:
                bbox['x'] = int(bbox['x']*nummer)
        dim = (width,height)
        stretch_img = cv2.resize(image,dim)
        
        # print('image_info_stop',image_info)
        crop_img = stretch_img[0:originele_height, 0:originele_width]
        # print('number',num1)
        # print('lengt',len(de_nummers))
        # print('nummer',nummer)
        # show_img_hist_x([image,stretch_img,crop_img])
    
    return crop_img, image_info, stretch


### Hier alle functies die de zorgen voor aanpassingen op het histogram

def find_gamma(image):
    """ 
        Geeft de correcte gamma terug zodat de intensiteit van de afbeelding naar het midden wordt verschoven
        125: Het midden van de intensiteit
        Arguments:
            image - een foto
        
        Returns:
            gamma {int} -- De gamma
    """
    avg_intensity = np.mean(image)
    tus_1 = np.log(125/255)
    tus_2= np.log(avg_intensity/255)
    inVgamma = tus_1/tus_2
    gamma = 1/inVgamma
    return gamma

def adjust_gamma(image, gamma=1.0):
    """ 
        Build a lookup table mapping the pixel values [0, 255] to their adjusted gamma values
        Arguments:
            image - een foto
            gamma {float} -- De gamma voor de augmentatie
        
        Returns:
            De lookup table
    """
    invGamma = 1.0 / gamma
    table = np.array([((i / 255.0) ** invGamma) * 255
        for i in np.arange(0, 256)]).astype("uint8")

    return cv2.LUT(image, table)

def normalize(image):
    # All deze booleans worden niet gebruikt. Als je handmatig naar de histograms wilt kijken kunnen ze handig zijn 
    
    clip_limit = False
    histogram_equal = False

    # histogram_equalization(image)

    clahe2 = cv2.createCLAHE(clipLimit=1.4, tileGridSize=(32,32))
    cl2 = clahe2.apply(image)
    if clip_limit == True:
        # Dit is alleen gebruikt voor in het verslag. Hier gaan we addaptive histogram equalisation vergelijken met het gewone histogram equalization
        clahe2 = cv2.createCLAHE(clipLimit=40, tileGridSize=(32,32))
        adjusted2 = clahe2.apply(image)
    elif histogram_equal == True:
        adjusted2 = cv2.equalizeHist(image)
    else:
        gamma = find_gamma(cl2) 
        adjusted2 = adjust_gamma(cl2, gamma=gamma)
    # show_img_hist_cum_titels_1(adjusted2)
    # show_img_hist_cum_titels_3(image,cl2,adjusted2)
    # show_img_hist_cum_titels(image,cl2,adjusted2)


    show_img_hist_cum_x([image,cl2,adjusted2])

    return adjusted2

def normaliseer_training(image,debug):
    # gaussiaan = random.randint(0,2)
    # median = random.randint(0,2)
    # uniform_b = random.randint(0,2)
    gaussiaan = False
    median = False
    uniform_b = False
    welke_augmentatie = [False,False,False,False,False]
    # augmentatie_rand = random.randint(0,4)
    # welke_augmentatie[augmentatie_rand] = True

    gaussiaan = welke_augmentatie[0]
    median = welke_augmentatie[1]
    uniform_b = welke_augmentatie[2]
    if gaussiaan == True:
        sigma = random.uniform(0.05, 2)
        # result = image
        image = gaussian_filter(image, sigma=sigma)
    if median == True:
        median_num = random.randint(1,4)
        image = median_filter(image,median_num)
    if uniform_b == True:
        uniform_num = random.randint(1,4)
        image = uniform_filter(image,uniform_num)


    alpha = random.uniform(0.85, 1.15)
    new_image = cv2.convertScaleAbs(image, alpha=alpha, beta= 0)
    gamma = find_gamma(new_image) 
    adjusted_image = adjust_gamma(new_image, gamma=gamma)
    clip = random.uniform(0.01, 1.1)
    maal = random.uniform(0.001, 1)
    x  = clip*maal
    gamma = random.uniform(0.75, 1.25)

    adjusted = adjust_gamma(adjusted_image, gamma=gamma)
    
    
    # show_img_hist_cum_x([image,adjusted_image,adjusted])
    return adjusted

def histogram_equalization(img):
    # cdf_m = np.ma.masked_equal(cdf,0)
    # cdf_m = (cdf_m - cdf_m.min())*255/(cdf_m.max()-cdf_m.min())
    # cdf = np.ma.filled(cdf_m,0).astype('uint8')
    # img2 = cdf[img]
    
    # hist,bins = np.histogram(img.flatten(),256,[0,256])

    # cdf = hist.cumsum()
    # cdf_normalized = cdf * hist.max()/ cdf.max()

    # plt.plot(cdf_normalized, color = 'b')
    # plt.hist(img.flatten(),256,[0,256], color = 'r')
    # plt.xlim([0,256])
    # plt.legend(('cdf','histogram'), loc = 'upper left')
    # plt.show()
    equ = cv2.equalizeHist(img)
    
    plt.imshow(equ,cmap='gray', vmin=0, vmax=255)
    plt.show()
    
### Hier alle functies die de afbeelding kunnen afbeelden
def beeld_bboxen_af(image_info_x1_x2_y1_y2,img,image_aug):
    debug = False
    if debug == True:
        print('naam afbeelding:',image_info_x1_x2_y1_y2['filename_nieuw'])
    for boxen in image_info_x1_x2_y1_y2['bboxes']:
        gt_x1, gt_x2 = boxen['x1'], boxen['x2']
        gt_y1, gt_y2 =  boxen['y1'], boxen['y2']
        gt_x1, gt_y1, gt_x2, gt_y2 = int(gt_x1), int(gt_y1), int(gt_x2), int(gt_y2)
        
        if debug == True:
            print('Coordinaten bbox',gt_x1, gt_y1, gt_x2, gt_y2)

        color = (0, 255, 0)
        cv2.putText(img, 'gt bbox', (gt_x1, gt_y1-5), cv2.FONT_HERSHEY_DUPLEX, 0.7, color, 1)
        cv2.rectangle(img, (gt_x1, gt_y1), (gt_x2, gt_y2), color, 2)
        cv2.circle(img, (int((gt_x1+gt_x2)/2), int((gt_y1+gt_y2)/2)), 3, color, -1)
    
    plt.figure(figsize=(15,5))
    plt.subplot(1,2,1)
    plt.imshow(image_aug,cmap='gray', vmin=0, vmax=255)
    plt.title('img_normaal')
    plt.subplot(1,2,2)
    plt.imshow(img,cmap='gray', vmin=0, vmax=255)
    plt.title(image_info_x1_x2_y1_y2['filename_nieuw'])    
    plt.grid()
    plt.show()

def beeld_groters_bboxen_met_h_b_af(image,blad,aantal):    
    i=0
    extra_image = copy.deepcopy(image)
    debug = False
    lijst_i = [1,2,4,8]
    while i<aantal:        
        nummer = lijst_i[i]
        print('i',i)
        for boxen in blad['bboxes']:
            gt_x1, gt_x2 = boxen['x']-30*nummer, boxen['x']+30*nummer
            gt_y1, gt_y2 =  boxen['y']-30*nummer, boxen['y']+30*nummer
            if gt_x1<0:
                gt_x1 = 0
            if gt_x2>image.shape[1]:
                gt_x2 = image.shape[1]
            if gt_y1<0:
                gt_y1 = 0
            if gt_y2> image.shape[0]:
                gt_y2 = image.shape[0]
            gt_x1, gt_y1, gt_x2, gt_y2 = int(gt_x1), int(gt_y1), int(gt_x2), int(gt_y2)
            
            if debug == True:
                print('Coordinaten bbox',gt_x1, gt_y1, gt_x2, gt_y2)
            if i == 0 or i == 1:
                color = (0, 255, 0)
            if i == 2 or i == 3:
                color = (0, 0, 255)
            

            if i% 2 == 0:
                #color = (0, 255, 0)
                print('even')
                cv2.putText(image, 'gt bbox', (gt_x1, gt_y1-5), cv2.FONT_HERSHEY_DUPLEX, 0.7, color, 1)
                cv2.rectangle(image, (gt_x1, gt_y1), (gt_x2, gt_y2), color, 2)
                cv2.circle(image, (int((gt_x1+gt_x2)/2), int((gt_y1+gt_y2)/2)), 3, color, -1)
            else:
                #color = (0, 255, 0)
                print('odd')
                cv2.putText(extra_image, 'gt bbox', (gt_x1, gt_y1-5), cv2.FONT_HERSHEY_DUPLEX, 0.7, color, 1)
                cv2.rectangle(extra_image, (gt_x1, gt_y1), (gt_x2, gt_y2), color, 2)
                cv2.circle(extra_image, (int((gt_x1+gt_x2)/2), int((gt_y1+gt_y2)/2)), 3, color, -1)
        i+=1


    plt.figure(figsize=(15,5))
    plt.subplot(1,2,1)
    plt.imshow(image)
    plt.title('img_normaal')
    plt.subplot(1,2,2)
    plt.imshow(extra_image)
    plt.title(blad['filepath'])    
    plt.grid()
    plt.show()

def beeld_bboxen_met_h_b_af(image,blad,image_flip):    
    i=0
    debug = False
    for boxen in blad['bboxes']:
        gt_x1, gt_x2 = boxen['x']-60, boxen['x']+60
        gt_y1, gt_y2 =  boxen['y']-60, boxen['y']+60
        if gt_x1<0:
            gt_x1 = 0
        if gt_x2>image_flip.shape[1]:
            gt_x2 = image_flip.shape[1]
        if gt_y1<0:
            gt_y1 = 0
        if gt_y2> image_flip.shape[0]:
            gt_y2 = image_flip.shape[0]
        gt_x1, gt_y1, gt_x2, gt_y2 = int(gt_x1), int(gt_y1), int(gt_x2), int(gt_y2)
        
        if debug == True:
            print('Coordinaten bbox',gt_x1, gt_y1, gt_x2, gt_y2)

        color = (0, 255, 0)
        cv2.putText(image_flip, 'gt bbox', (gt_x1, gt_y1-5), cv2.FONT_HERSHEY_DUPLEX, 0.7, color, 1)
        cv2.rectangle(image_flip, (gt_x1, gt_y1), (gt_x2, gt_y2), color, 2)
        cv2.circle(image_flip, (int((gt_x1+gt_x2)/2), int((gt_y1+gt_y2)/2)), 3, color, -1)

        # color = (0, 255, 0)
        # cv2.putText(image, 'gt bbox', (gt_x1, gt_y1-5), cv2.FONT_HERSHEY_DUPLEX, 0.7, color, 1)
        # cv2.rectangle(image, (gt_x1, gt_y1), (gt_x2, gt_y2), color, 2)
        # cv2.circle(image, (int((gt_x1+gt_x2)/2), int((gt_y1+gt_y2)/2)), 3, color, -1)

    plt.figure(figsize=(15,5))
    plt.subplot(1,2,1)
    plt.imshow(image)
    plt.title('img_normaal')
    plt.subplot(1,2,2)
    plt.imshow(image_flip)
    plt.title(blad['filepath'])    
    plt.grid()
    plt.show()

def show_img_hist_x(array_image):
    """
        Geef een array mee van images
        Deze zullen worden afgebeeld samen met hun histogram
    """
    x=int(len(array_image))
    plt.figure(figsize=(15,10))
    positie = 0
    array_namen = ['1','2','3','4','5','6','7','8','9','5','6','7','8','9']
    for img in array_image:        
        pos_hist = positie+x
        plt.subplot(2,x,positie+1)
        plt.title(array_namen[positie])        
        plt.imshow(img,cmap='gray', vmin=0, vmax=255)

        plt.subplot(2,x,pos_hist+1)
        plt.title(array_namen[positie])    
        plt.hist(img.ravel(),256,[0,256])
        
        avg_intensity = np.mean(img)
        print('avg_intensity',avg_intensity)
        positie +=1
    plt.show()

def show_img_hist_3_images(image,hist_img,gamma_img):
    """
        Geef een array mee van images
        Deze zullen worden afgebeeld samen met hun histogram
    """
    x=3
    plt.figure(figsize=(15,10))
    positie = 0
        
    pos_hist = positie+x
    plt.subplot(2,x,positie+1)
    plt.title('Input image')
    plt.imshow(image,cmap='gray', vmin=0, vmax=255)

    plt.subplot(2,x,pos_hist+1)
    plt.hist(image.ravel(),256,[0,256])
    
    avg_intensity = np.mean(image)
    print('avg_intensity',avg_intensity)
    positie +=1

    pos_hist = positie+x
    plt.subplot(2,x,positie+1)
    plt.title('Histogram equalisation')
    plt.imshow(hist_img,cmap='gray', vmin=0, vmax=255)

    plt.subplot(2,x,pos_hist+1)
    plt.hist(hist_img.ravel(),256,[0,256])
    
    avg_intensity = np.mean(hist_img)
    print('avg_intensity',avg_intensity)
    positie +=1

    pos_hist = positie+x
    plt.subplot(2,x,positie+1)
    plt.title('Gamma')
    plt.imshow(gamma_img,cmap='gray', vmin=0, vmax=255)

    plt.subplot(2,x,pos_hist+1)
    plt.hist(gamma_img.ravel(),256,[0,256])
    
    avg_intensity = np.mean(gamma_img)
    print('avg_intensity',avg_intensity)
    positie +=1
    plt.show()

def show_fliped_img(img_normaal,img_flipt):
    plt.figure(figsize=(10,10))
    plt.subplot(2,2,1)
    plt.imshow(img_normaal,cmap='gray', vmin=0, vmax=255)
    plt.title('img_normaal')
    plt.subplot(2,2,2)
    plt.imshow(img_flipt,cmap='gray', vmin=0, vmax=255)
    plt.title('img_flipt')
    plt.subplot(2,2,3)
    plt.hist(img_normaal.ravel(),256,[0,256])
    plt.title('histogram normaal')
    plt.subplot(2,2,4)
    plt.hist(img_flipt.ravel(),256,[0,256])
    plt.title('histogram aangepast')
    plt.show()

def show_img_hist_cum_x_2_rijen(array_image):
    """
        Geef een array mee van images
        Deze zullen worden afgebeeld samen met hun histogram
    """
    lengte_array=int(len(array_image))
    plt.figure(figsize=(15,10))
    positie = 0
    array_namen = ['1','2','3','4','5','6','7','8','9','5','6','7','8','9','10','11','12','13','14','15','16','17']
    
    print('leng',len(array_image))
    if len(array_image)>3:
        rijen = 4
        x = 3
    else:
        rijen = 2 
        x = int(lengte_array)
    for img in array_image:        
        pos_hist = positie+x
        
        plt.subplot(rijen,x,positie+1)
        plt.title(array_namen[positie])
        plt.imshow(img,cmap='gray', vmin=0, vmax=255)

        plt.subplot(rijen,x,pos_hist+1)
        # print('pos_hist',pos_hist)
        plt.title(array_namen[pos_hist])
        y,_,_ = plt.hist(img.ravel(),256,[0,256])
        max_waarde_hist = max(y)
        cum,base = cumulutief_histogram(img,max_waarde_hist)

        plt.plot(base[:-1], cum, c='green')

        avg_intensity = np.mean(img)
        print('avg_intensity',avg_intensity)
        positie +=1   
        if positie == 3:
            positie += 3     
    plt.show()

def show_img_hist_cum_x(array_image):
    """
        Geef een array mee van images
        Deze zullen worden afgebeeld samen met hun histogram
    """
    x=int(len(array_image))
    plt.figure(figsize=(15,10))
    positie = 0
    array_namen = ['Originele figuur','Figuur na AHE','Genormaliseerde figuur','Histogram','Histogram','Histogram']
    # print(len(array_namen)/2)
    if int(len(array_namen)/2) != len(array_image):
        array_namen = ['1','2','3','4','5','6','7','8','9','5','6','7','8','9','10','11','12','13','14','15','16','17']
    
    for img in array_image:        
        pos_hist = positie+x
        
        plt.subplot(2,x,positie+1)
        plt.title(array_namen[positie])
        plt.imshow(img,cmap='gray', vmin=0, vmax=255)

        plt.subplot(2,x,pos_hist+1)
        # print('pos_hist',pos_hist)
        plt.title(array_namen[pos_hist])
        y,_,_ = plt.hist(img.ravel(),256,[0,256])
        max_waarde_hist = max(y)
        cum,base = cumulutief_histogram(img,max_waarde_hist)

        plt.plot(base[:-1], cum, c='green')

        avg_intensity = np.mean(img)
        print('avg_intensity',avg_intensity)
        positie +=1        
    plt.show()

def show_img_hist_cum_titels(img,img_hist,img_gamma):
    """
        Geef een array mee van images
        Deze zullen worden afgebeeld samen met hun histogram
    """
    x=3
    plt.figure(figsize=(15,12))
    positie = 0
           
    pos_hist = positie+x
    pos_cum_his = positie+x+x
    plt.subplot(3,x,positie+1)
    plt.title('Input image')
    plt.imshow(img,cmap='gray', vmin=0, vmax=255)

    plt.subplot(3,x,pos_hist+1)
    plt.title('Histogram')
    y,_,_ = plt.hist(img.ravel(),256,[0,256])
    
    max_waarde_hist = max(y)
    cum,base = cumulutief_histogram(img,max_waarde_hist)

    plt.subplot(3,x,pos_cum_his+1)
    plt.title('Cumulatief histogram')
    plt.plot(base[:-1], cum, c='green')

    avg_intensity = np.mean(img)
    print('avg_intensity',avg_intensity)
    positie +=1

    pos_hist = positie+x
    pos_cum_his = positie+x+x
    plt.subplot(3,x,positie+1)
    plt.title('Image na addaptive histogram equalization')
    plt.imshow(img_hist,cmap='gray', vmin=0, vmax=255)

    plt.subplot(3,x,pos_hist+1)
    plt.title('Histogram')
    y,_,_ = plt.hist(img_hist.ravel(),256,[0,256])
    
    max_waarde_hist = max(y)
    cum,base = cumulutief_histogram(img_hist,max_waarde_hist)

    plt.subplot(3,x,pos_cum_his+1)
    plt.title('Cumulatief histogram')
    plt.plot(base[:-1], cum, c='green')

    avg_intensity = np.mean(img_hist)
    print('avg_intensity',avg_intensity)
    positie +=1

    pos_hist = positie+x
    pos_cum_his = positie+x+x
    plt.subplot(3,x,positie+1)
    plt.title('Image histogram equalization')
    plt.imshow(img_gamma,cmap='gray', vmin=0, vmax=255)

    plt.subplot(3,x,pos_hist+1)
    plt.title('Histogram')
    y,_,_ = plt.hist(img_gamma.ravel(),256,[0,256])
    max_waarde_hist = max(y)
    cum,base = cumulutief_histogram(img_gamma,max_waarde_hist)

    plt.subplot(3,x,pos_cum_his+1)
    plt.title('Cumulatief histogram')
    plt.plot(base[:-1], cum, c='green')

    avg_intensity = np.mean(img_gamma)
    print('avg_intensity',avg_intensity)
    positie +=1
    plt.show()

def cumulutief_histogram(image,max_waarde_hist):
    values, base = np.histogram(image, bins=40)
    #evaluate the cumulative
    cumulative = np.cumsum(values)
    
    cum_pro = (cumulative/cumulative[-1])*max_waarde_hist
    # plot the cumulative function
    # plt.plot(base[:-1], cum_pro, c='green')

    # plt.show()
    return cum_pro, base

def show_img_hist_cum_titels_1(img):
    """
        Geef een array mee van images
        Deze zullen worden afgebeeld samen met hun histogram
    """
    x=1
    plt.figure(figsize=(15,12))
    positie = 0
           
    pos_hist = positie+x
    plt.subplot(2,x,positie+1)
    plt.title('Input image')
    plt.imshow(img,cmap='gray', vmin=0, vmax=255)

    plt.subplot(2,x,pos_hist+1)
    plt.title('Histogram')
    y,x,_ = plt.hist(img.ravel(),256,[0,256])
    # maximum = max(img.ravel())
    max_waarde_hist = max(y)
    # print('max',maximum)
    
    cum,base = cumulutief_histogram(img,max_waarde_hist)
    # cum = cum*maximum

    # plt.subplot(3,x,pos_cum_his+1)
    # plt.title('Cumulatief histogram')
    print('base',base[:-1])
    plt.plot(base[:-1], cum, c='green')

    avg_intensity = np.mean(img)
    print('avg_intensity',avg_intensity)
    plt.show()

def show_img_hist_cum_titels_3(img,img_hist,img_gamma):
    """
        Geef een array mee van images
        Deze zullen worden afgebeeld samen met hun histogram
    """
    plt.figure(figsize=(15,12))
           
    plt.subplot(2,3,1)
    plt.title('Input image')
    plt.imshow(img,cmap='gray', vmin=0, vmax=255)

    plt.subplot(2,3,4)
    plt.title('Histogram')
    y,_,_ = plt.hist(img.ravel(),256,[0,256])
    max_waarde_hist = max(y)
    cum,base = cumulutief_histogram(img,max_waarde_hist)
    plt.plot(base[:-1], cum, c='green')

    avg_intensity = np.mean(img)
    print('avg_intensity',avg_intensity)

    plt.subplot(2,3,2)
    plt.title('Input image')
    plt.imshow(img_hist,cmap='gray', vmin=0, vmax=255)

    plt.subplot(2,3,5)
    plt.title('Histogram')
    y,_,_ = plt.hist(img_hist.ravel(),256,[0,256])
    max_waarde_hist = max(y)
    cum,base = cumulutief_histogram(img_hist,max_waarde_hist)
    plt.plot(base[:-1], cum, c='green')

    avg_intensity = np.mean(img_hist)
    print('avg_intensity',avg_intensity)

    plt.subplot(2,3,3)
    plt.title('Input image')
    plt.imshow(img_gamma,cmap='gray', vmin=0, vmax=255)

    plt.subplot(2,3,6)
    plt.title('Histogram')
    y,_,_ = plt.hist(img_gamma.ravel(),256,[0,256])
    max_waarde_hist = max(y)
    cum,base = cumulutief_histogram(img_gamma,max_waarde_hist)
    plt.plot(base[:-1], cum, c='green')

    avg_intensity = np.mean(img_gamma)
    print('avg_intensity',avg_intensity)

    plt.show()

def maak_grid(image,blad):
    """Maakt een grid op een foto
    Gewoon gebruikt om een afbeelding te maken voor in het verslags

    Arguments:
        image {[type]} -- [description]
        blad {[type]} -- [description]
    """
    i=0
    debug = False
    image = image[0:600,0:800]
    j=0
    while i<49:
        i+=1
        j = 0
        while j<37:
            j+=1
            color = (0, 0, 255)
            x = i*16
            y = j*16
            cv2.rectangle(image, (x,y), (x+1, y+1), color, 2)

    plt.figure(figsize=(15,5))
    plt.imshow(image)
    plt.title('img_normaal')
    plt.title(blad['filepath'])    
    # plt.grid()
    plt.show()

def beeld_een_set_anchor_boxen_af(image,blad):
    """Wordt gebruikt om de set van 9 anchor boxen af te beelden
    Gewoon gebruikt om een afbeelding te maken voor in het verslag

    Arguments:
        image {[type]} -- [description]
        blad {[type]} -- [description]
    """
    i=0
    debug = False
    image = image[0:600,0:800]
    anchor_box_scales = [64, 128, 256]
    anchor_box_ratios =  [[1, 1], [1./math.sqrt(2), 2./math.sqrt(2)], [2./math.sqrt(2), 1./math.sqrt(2)]]

    for box_scale in anchor_box_scales:
        i+=1
        if i == 1:
            color = (0, 0, 255)
        if i == 2:
            color = (0, 255, 0)
        if i == 3:
            color = (255, 0, 0)
        for box_ratio in anchor_box_ratios:
            x = 400
            y = 300
            sc = box_scale/2
            x1 = int(x - sc*box_ratio[0])
            y1 = int(y - sc*box_ratio[1])
            x2 = int(x + sc*box_ratio[0])
            y2 = int(y + sc*box_ratio[1])
            cv2.rectangle(image, (x1,y1), (x2, y2), color, 2)

    plt.figure(figsize=(15,5))
    plt.imshow(image)
    plt.title('img_normaal')
    plt.title(blad['filepath'])    
    # plt.grid()
    plt.show()

def maak_anchor_boxen_grid(image,blad):
    """Wordt gebruikt om alle anchor boxen af te beelden. 
    Maar is niet zo nuttig

    Arguments:
        image {[type]} -- [description]
        blad {[type]} -- [description]
    """
    image = image[0:600,0:800]
    anchor_box_scales = [64, 128, 256]
    # anchor_box_ratios =  [[1, 1], [1./math.sqrt(2), 2./math.sqrt(2)], [2./math.sqrt(2), 1./math.sqrt(2)]]
    anchor_box_ratios = [[1, 1], [0.75,0.75], [1.25,1.25]]
    i=0
    j=0
    aantal_bboxen = 0
    while i<49:
        i+=1
        j = 0
        while j<37:
            j+=1
            # color = (0, 0, 255)
            x = i*16
            y = j*16
            kleur = 0
            for box_scale in anchor_box_scales:
                kleur+=1
                if kleur == 1:
                    color = (0, 0, 255)
                if kleur == 2:
                    color = (0, 255, 0)
                if kleur == 3:
                    color = (255, 0, 0)
                for box_ratio in anchor_box_ratios:
                    sc = box_scale/2
                    x1 = int(x - sc*box_ratio[0])
                    y1 = int(y - sc*box_ratio[1])
                    x2 = int(x + sc*box_ratio[0])
                    y2 = int(y + sc*box_ratio[1])
                    if x1>0 and y1>0 and x2<800 and y2<600:
                        cv2.rectangle(image, (x1,y1), (x2, y2), color, 1)
                        aantal_bboxen+=1
    print('aantal_bboxen',aantal_bboxen)
    plt.figure(figsize=(15,5))
    plt.imshow(image)
    plt.title('img_normaal')
    plt.title(blad['filepath'])    
    # plt.grid()
    plt.show()

### De hoofdfuncties

def regel_x(x_snijden,all_data,counted_data,data_path_nieuwe_foto,data_path_foto,data_path_text,data_path_opslaag_plaats,zet_naar_grijswaarde,img_norm,training):
    """ Zal alles regelen:

        Werkingspinciepe:
            1) Roep snijt_alles_in_4() op
                Deze functie zal binnen een plantsoort alle afbeeldingen in 4 snijden en het aantal stomata tellen en teruggeven
                Is dit aantal stomata groter dan x_snijden (200) dan stopt de functie hier
                Is het kleiner dan x_snijden dan gaan we naar 2
            2) Roep volgende_augmentatie() op
                Deze functie zal de afbeelding horizontaal, verticaal spiegelen of draaien. Of een combinatie van de 3 opties
                En vervolgens de gespiegelde, gedraaide afbeelding meegeven aan snijt_alles_in_4()
                snijt_alles_in_4() zal de afbeelding dan weer in 4 snijden en het aantal stomata teruggeven 

                volgende_augmentatie() wordt opgeroepen tot het aantal_stomata > x_snijden
                    Maar met een maxima van 7 keer. Dan zijn alle mogelijke spiegelingen en draaiingen uitgevoerd
            
            3) Roep rotate_en_snij() op
                Deze functie doet hetzelfde als snijt_alles_in_4() maar zal de afbeelding nu x graden roteren en vervolgens op zoek gaan naar een rechthoek van 600x800
                Dit betekend dat er vaak maar 1 rechthoek wordt gevonden uit elke geroteerde afbeelding

                Deze functie zal in een while lus opgeroepen worden totdat het aantal_stomata > x_snijden

    
    Arguments:
        all_data {lijst[string,array[middelpunt]]} -- een array waarbij elke afbeelding is opgelsaan met de middelpunten van elke stomata
        counted_data {lijst[string,int,array[namen]]} -- Een lijst hiervan. Dus met alle planten in 
                                            string = plantnaam. Dus de basis naam van ene plant zonder blad_vlak.jpg
                                            int = count: Aantal stomata van deze plant
                                            array[namen]: Een array van alle specifieke namen met blad_vlak.jpg
        data_path_nieuwe_foto {string} -- path waar de nieuwe foto wordt opgeslagen
        data_path_foto {string} -- path waar de foto zich nu bevind
        data_path_text {string} -- path waar het text file wordt opgeslagen
        data_path_opslaag_plaats {string} -- path waar de foto wordt opgeslagen op jupyter hub
    """
    # text_path = path waar nieuw text file word opgeslaan
    input_user = False      # Of we zelf de grootte van de mondjes willen bepalen

    text_path = data_path_nieuwe_foto + data_path_text
    text_w = open(text_path, "w+")
    planten_soort = []
    H_filp = False
    V_flip = False
    rotate = 0
    i=0
    #aantal_augmentaties = 1
    augment = [H_filp,V_flip,rotate]
    # print('counted_data',counted_data)
    aantal_lijnen=0
    
    for lijn in counted_data:
        #print('lijn',lijn)
    ################################# PAS OP ##################################
    ##################### Door de if wordt niet alle data genomen #############
    ############## Nu gewoon op True gezet. We willen toch alle data ##########
        print('lijn',lijn['count']) 
        if True:    #lijn['count']>5 and lijn['count']<15:
            H_filp = False
            V_flip = False
            rotate = 0        
            augment = [H_filp,V_flip,rotate]
            aantal = 0
            planten_soort = ophalen_planten(all_data,lijn)
            # print('all_data:',all_data)
            # print('lijn: ',lijn)
            # for x in planten_soort:
            #     print('planten_soort:',x)#['filepath'])
            bbox_grootte = 120
            if input_user == True:
                image_aug, blad_aug = augmentatie(planten_soort[0],data_path_foto,[False,False,0],False)
                beeld_groters_bboxen_met_h_b_af(image_aug,blad_aug,4)     
                bbox_grootte = input("Type something to test this out: ")
                # Note that in version 3, the print() function
                # requires the use of parenthesis.
                print("Is this what you just said? ", bbox_grootte)
                zeker = input("Are you sure: ")
                while zeker != 'y':
                    bbox_grootte = input("Type something to test this out: ")
                    print("Is this what you just said? ", bbox_grootte)
                    zeker = input("Are you sure: ")
            # else:
            #     bbox_grootte = 
            bbox_grootte = int(bbox_grootte)
            # print('planten_soort: ',planten_soort[0])
            #print('lijn: ',lijn)
            #print(aantal)
            #print('i_cut_4:',i)
            i+=1
            debug = False
            momenteel = snijt_alles_in_4(x_snijden,planten_soort,data_path_foto,data_path_nieuwe_foto,data_path_opslaag_plaats,text_w,augment,zet_naar_grijswaarde,img_norm,debug,bbox_grootte,training)
            
            if True:
                aantal += momenteel
                print('aantal',aantal)
                # if aantal<150:
                #     debug = True
                # else:
                #     debug = False
                if aantal == 0:
                    print('aantal is NUL')
                    print('planten_soort',planten_soort)
                    print('lijn: ',lijn)
                if aantal>0:
                    aantal_augmentaties = 1
                    while aantal<x_snijden and aantal_augmentaties<7:         # Wanneer er meerdere permutaties nodig zijn. Doe dan deze augmentaties
                        # if aantal_augmentaties > 1:
                        #     debug = True
                        momenteel = volgende_augmentatie(x_snijden,planten_soort,data_path_foto,data_path_nieuwe_foto,data_path_opslaag_plaats,text_w,augment,aantal_augmentaties,zet_naar_grijswaarde,img_norm,debug,bbox_grootte,training)
                        aantal += momenteel
                        aantal_augmentaties += 1
                        print('volgede_augementatie',aantal_augmentaties)
                        print('aantal',aantal)
                        # for x in planten_soort:
                        #     print('planten_soort:',x['filepath'])

                    i_rotate = 1
                    while aantal<x_snijden:  
                        print('ROTATIE!!!!!!!!!!')
                        # debug = True                        
                        augment[0] = False                   
                        augment[1] = False
                        if i_rotate > 15 and i_rotate<30:
                            augment[0] = True
                            # debug = True
                        elif i_rotate > 30:
                            augment[1] = True

                        angle = i_rotate*25
                        momenteel = rotate_en_snij(x_snijden,planten_soort,data_path_foto,data_path_nieuwe_foto,data_path_opslaag_plaats,text_w,augment,angle,zet_naar_grijswaarde,img_norm,debug,bbox_grootte,training)
                        aantal += momenteel            
                        print('aantal',aantal)
                        # for x in planten_soort:
                        #     print('planten_soort:',x['filepath'])
                        # rotate en snij er 1 uit
                        print('i_rotate: ',i_rotate)
                        i_rotate+=1
                        # if i_rotate>100:
                        #     print('planten_soort',planten_soort)
                        #     print('lijn: ',lijn)
                        #     print('data_path_foto',data_path_foto)
            #### TE DOEN (al gedaan)
            # Ik heb al iets gemaakt dat een tekening in 4 snijt: snijt_alles_in_4()
            # Deze functie zal stopen met tekeningen in 4 te snijden wanneer er meer dan x_snijden (200) huidmondjes zijn uitgesneden
            # Dus als een plant 200 of meer huidmondjes heeft is het allemaal goed
            # Nu moet ik nog extra augmentaties doen voor planten met minder huidmondjes
            ### Dus zoals hieronder maar dan beter
        
            # while aantal<x_snijden and aantal_augmentaties<7:         # Wanneer er meerdere permutaties nodig zijn. Doe dan deze augmentaties
            #     momenteel = volgende_augmentatie(x_snijden,planten_soort,data_path_foto,data_path_nieuwe_foto,data_path_opslaag_plaats,text_w,augment,aantal_augmentaties)
            #     aantal += momenteel
            #     aantal_augmentaties += 1
            #     print('aantal',aantal)

            # Maak hier nog een while van
        aantal_lijnen += 1
        #angle = 45
            

    text_w.close()

def volgende_augmentatie(x_snijden,planten_soort,data_path_foto,data_path_nieuwe_foto,data_path_opslaag_plaats,text_w,augment,aantal_augmentaties,zet_naar_grijswaarde,img_norm,debug,bbox_grootte,training):
    H_filp = False
    V_flip = False
    rotate = 0        
    augment = [H_filp,V_flip,rotate]
    print('aantal_augmentaties',aantal_augmentaties)
    print('augment',augment)
    if aantal_augmentaties == 1:
        augment[0] = True
    if aantal_augmentaties == 2:
        augment[1] = True
    if aantal_augmentaties == 3:
        augment[0] = True
        augment[1] = True
    if aantal_augmentaties == 4:
        augment[2] = 1
        augment[0] = True
    if aantal_augmentaties == 5:
        augment[2] = 1
        augment[1] = True
    if aantal_augmentaties == 6:
        augment[2] = 1
        augment[0] = True
        augment[1] = True
    print('augment',augment)
    aantal = snijt_alles_in_4(x_snijden,planten_soort,data_path_foto,data_path_nieuwe_foto,data_path_opslaag_plaats,text_w,augment,zet_naar_grijswaarde,img_norm,debug,bbox_grootte,training)
    return aantal

def snijt_alles_in_4(x_snijden,planten_soort,data_path_foto,data_path_nieuwe_foto,data_path_opslaag_plaats,text_w,augment,zet_naar_grijswaarde,img_norm,debug,bbox_grootte,training):    
    """Hier zullen afbeeldingen in 4 worden gesneden
        Er zal gestopt worden wanneer er meer dan x_snijden (200) huidmondjes zijn uitgesneden
        Het is mogelijk om aan augmentatie te doen met de parameter augment
        De bboxen worden bijgewerkt. De afbeelding word opgeslagen en er wordt naar een tekst document geschreven 

        Werkingsprinciepe:
        1) vraag image_info op
                Met: co_in_twee_snijden(images,data_path_foto)
                image_info {list} -- list{filename_oud,filename_nieuw,uitsnij_co[x1,x2,y1,y2],lijst{bboxes[x,y]}}
        2) Vraag image_uitgesneden op
                Met: uitsnijden_figuur(info_foto_rechts,data_path_foto)
                image_uitgesneden {image} -- een uitgesneden image
        3) Sla image op
                Met: opslaan_image(info_foto_links,uitgesneden_links, data_path_nieuwe_foto)
        4) Vraag co_bboxen op (image_info_x1_x2_y1_y2)
                Met: co_box(info_foto_links)
                image_info_x1_x2_y1_y2{lijst} -- list{filename_oud,filename_nieuw,lijst{bboxes[x1,x2,y1,y2]}}
        5) Schrijf naar een text file
                Met: schrijven_text_file_x1_x2_y1_y2(image_info_x1_x2_y1_y2,text_w,data_path_opslaag_plaats)

    
    Arguments:
        x_snijden {int} -- aantl huidmondjes we minimaal/maximaal per soort willen 
        planten_soort {list{string,bboxes[]}} -- lijst van alle specifieke bladeren binnen een planten soort. Elk blad met zijn bboxes
        data_path_foto {[type]} -- [description]
        data_path_nieuwe_foto {[type]} -- [description]
        data_path_opslaag_plaats {string} -- plaats waar de foto wordt opgeslaan in jupyter hub 
        text_w {text document} -- document waarin foto met boxes enzo wordt opgeslaan 
        augment {array} -- [H_flip,V_flip,rotate]: Hier zal worden weergegeven ofdat er aan augmentatie wordt gedaan [Boolean,Boolean,int]
    
    Returns:
        count -- een int: Het aantal huidmondjes dat er van deze plantensoort verwerkt zijn
    """
    # H_filp = augment[0]
    # V_flip = augment[1]
    # rotate = augment[2]
    count = 0
    # training = True
    #debug = True
    for blad in planten_soort:
        print('count',count)
        print('blad',blad['filepath'])
        bbox_grootte = int(blad['grootte_bbox'])
        if(count<x_snijden):
            print('HIER')
            # Hier moet elke afbeelding in 4 worden gesneden  
            i=0
            #data_path_foto_test = data_path_foto + blad['filepath']
            blad_aug = copy.deepcopy(blad)
            # if debug == True:
            # print('blad:',blad)
            image_aug, blad_aug = augmentatie(blad_aug,data_path_foto,augment,debug)   

            
            # maak_anchor_boxen_grid(image_aug, blad_aug)

            if debug == True:
                beeld_bboxen_met_h_b_af(image_aug,blad_aug,image_aug) 
            
            # if debug == True:
            #     print("AUGMENT GEDAAN") 
            #     print('blad1.0:',blad)
            #     print('blad_aug',blad_aug)
            if zet_naar_grijswaarde == True:               
                image_aug = cv2.cvtColor(image_aug, cv2.COLOR_RGB2GRAY)  
            if img_norm == True:
                image_aug = normalize(image_aug) 
            # print('blad aug:',blad)
            # if debug == True:
            #     print('blad2:',blad)
            #     print('blad_aug',blad_aug)
            while i<4:
                image_info = co_stuk_vier(blad_aug,image_aug,i,augment)
                if len(image_info['bboxes']) > 0:
                    img_uitgesneden = uitsnijden_figuur_image(image_info,image_aug) 
                    if training == True:
                        # print('TRAINING!!!!!!!!')
                        img_uitgesneden = normaliseer_training(img_uitgesneden,debug)  
                        img_uitgesneden, image_info, stretch = stretch_image_en_co(image_info,img_uitgesneden)
                    
                    else:
                        stretch = [1,1]
                    image_info = bewerk_image_info(image_info,img_uitgesneden,bbox_grootte)
                    # print('Vlak voor opslaan')
                    if len(image_info['bboxes']) > 0:
                        opslaan_image(image_info,img_uitgesneden, data_path_nieuwe_foto)     
                        # print('image_info: ',image_info)
                        #show_img_hist_x([img_uitgesneden])
                        image_info_x1_x2_y1_y2 = co_box(image_info,bbox_grootte,stretch)
                        if debug == True:
                            k=1
                            beeld_bboxen_af(image_info_x1_x2_y1_y2,img_uitgesneden,image_aug)
                        schrijven_text_file_x1_x2_y1_y2(image_info_x1_x2_y1_y2,text_w,data_path_opslaag_plaats)
                
                i+=1        
            count = count + count_blad(blad_aug)
            
            # print('count2',count)
            
            i=blad
    
    # print('count',count)
    # print('count',count)
    # print('count',count)
    return count

def rotate_en_snij(x_snijden,planten_soort,data_path_foto,data_path_nieuwe_foto,data_path_opslaag_plaats,text_w,augment,angle,zet_naar_grijswaarde,img_norm,debug,bbox_grootte,training):
    """Hier zullen afbeeldingen in 4 worden gesneden
        Er zal gestopt worden wanneer er meer dan x_snijden (200) huidmondjes zijn uitgesneden
        Het is mogelijk om aan augmentatie te doen met de parameter augment
        De bboxen worden bijgewerkt. De afbeelding word opgeslagen en er wordt naar een tekst document geschreven 
    
    Arguments:
        x_snijden {int} -- aantl huidmondjes we minimaal/maximaal per soort willen 
        planten_soort {list{string,bboxes[]}} -- lijst van alle specifieke bladeren binnen een planten soort. Elk blad met zijn bboxes
        data_path_foto {[type]} -- [description]
        data_path_nieuwe_foto {[type]} -- [description]
        data_path_opslaag_plaats {string} -- plaats waar de foto wordt opgeslaan in jupyter hub 
        text_w {text document} -- document waarin foto met boxes enzo wordt opgeslaan 
        augment {array} -- [H_flip,V_flip,rotate]: Hier zal worden weergegeven ofdat er aan augmentatie wordt gedaan [Boolean,Boolean,int]
        angle {int} -- De hoek waaronder er gedraaid wordt
        zet_naar_grijswaarde {Boolean} -- Of er omgezet wordt naar grijswaarde. Als dit True is dan zal dat gebeuren
        img_norm {Boolean} -- Of er genormaliseerd wordt
        debug {Boolean} -- Als we aan het debuggen zijn zal dit True zijn
        bbox_grootte {int} -- Hoe groot de bboxen zijn
        training {Boolean} -- Als we training data hebben dan zullen we stretchen en het histogram aanpassen. Dit gebeurd als training = True
    
    Returns:
        count -- een int: Het aantal huidmondjes dat er van deze plantensoort verwerkt zijn
    """
    
    count = 0
    #debug = True
    # training = True
    for blad in planten_soort:
        # print('blad',blad)
        bbox_grootte = int(blad['grootte_bbox'])
        if(count<x_snijden):
            # Hier moet elke afbeelding in 4 worden gesneden  
            i=0
            # print('blad voor aug en rot',blad)
            #data_path_foto_test = data_path_foto + blad['filepath']
            image_aug, blad = augmentatie(blad,data_path_foto,augment,debug)
             
            if zet_naar_grijswaarde == True:               
                image_aug = cv2.cvtColor(image_aug, cv2.COLOR_RGB2GRAY)  
            # show_img_hist_x([image_aug])
            if img_norm == True:
                image_aug = normalize(image_aug)   
            image_rot, blad = rotate_bound(image_aug, blad,angle) 
              
            
            # print('blad na rot',blad)
            startpunt = True
            start_co = [0,0]
            x_gevonden_stuk = 0
            while startpunt == True:
                startpunt,co_beginpunt = vind_800_pix_horizontaal(image_rot,start_co)
                start_co = [co_beginpunt[0],co_beginpunt[1]+601]
                
                if startpunt == True:
                    image_info = co_stuk_rotate(blad,image_aug,image_rot,augment,angle,co_beginpunt,x_gevonden_stuk)
                    
                    if len(image_info['bboxes']) > 0:
                        img_uitgesneden = uitsnijden_figuur_image(image_info,image_rot)  
                        # average_intensity = np.mean(img_uitgesneden)
                        if training == True:
                            img_uitgesneden = normaliseer_training(img_uitgesneden,debug)  
                            img_uitgesneden, image_info, stretch = stretch_image_en_co(image_info,img_uitgesneden)
                        else:
                            stretch = [1,1]

                        image_info = bewerk_image_info(image_info,img_uitgesneden,bbox_grootte,debug)                        
                        if len(image_info['bboxes']) > 0:
                            opslaan_image(image_info,img_uitgesneden, data_path_nieuwe_foto)                                                 
                            # opslaan_image(image_info,img_uitgesneden, data_path_nieuwe_foto)     
                            image_info_x1_x2_y1_y2 = co_box(image_info,bbox_grootte,stretch)                     
                            #print('image_info: ',image_info)
                            if debug == True:
                                print('image_info:',image_info)
                                print('len(image_info',len(image_info['bboxes']))
                                beeld_bboxen_af(image_info_x1_x2_y1_y2,img_uitgesneden,image_rot)
                            schrijven_text_file_x1_x2_y1_y2(image_info_x1_x2_y1_y2,text_w,data_path_opslaag_plaats)
                            # print('count',count)
                            count = count + count_image_info(image_info)                            
                            # print('count',count)
                        else:
                            print('FOTO WORDT NIET OPGESLAAN')
                    x_gevonden_stuk += 1
                    # Te doen: Eignelijk is de te doen van hieronder al uitgevoert
                    # Nu gewoon de rest afwerken. Image_info is juist -> mss nog is dubbelchecken
                    # En dus foto uitknippen enzo
                    
                    # Te doen: Hier hebben we nu de start coordinaten gevonden in start_co.
                    # Dit voor alle mogelijk uitgesneden figuren
                    # Nu met co_stu_rotate moeten we de nieuwe naam maken
                    # En ook de juiste bboxes vinden
    return count


def vergelijk_array(all_data,array_ingelezen_lijst):
    array_model_2 = [['Euphorbia heterodoxa B', 0.2956521739130435], ['Ada glumacea', 0.9318181818181818], ['Aerides multiflorum', 0.9423076923076923], ['Euphorbia neostolonifera B', 0.8346456692913387], ['Euphorbia balsamifera B', 0.8737864077669903], ['Calla palustris', 0.7706422018348623], ['Pinguicula emarginata', 0.9047619047619047], ['Stelis argentata', 0.9484536082474228], ['Avena sativa', 0.8791208791208791], ['Nepenthes veitchii', 0.9761904761904762], ['Euphorbia rhizophora B', 0.9565217391304348], ['Pinellia ternata', 0.9523809523809523], ['Saccharum officinarum', 0.8000000000000002], ['Allium moly B', 0.7], ['Phragmipedium longifolium', 0.8571428571428572], ['Barkeria', 0.967741935483871], ['Angraecum calceolus', 0.8767123287671232], ['Carapa procera', 0.9504950495049506], ['Myosoton aquaticum', 0.9230769230769231], ['Garcinia punctata', 0.7777777777777778], ['Odontoglossum nobile', 0.9894736842105264], ['Euphorbia heteropodum B', 0.9876543209876543], ['Euphorbia wildii B', 0.9629629629629629], ['Euphorbia californica B', 0.9090909090909091], ['Roscoea cautleoides', 0.96], ['Sarcoglottis speciosa', 0.9411764705882352], ['Sarcochilus fitzgeraldii', 0.5217391304347826], ['Jacquiniella equitantifolia', 0.898876404494382], ['Restrepiella ophiocephala', 0.5476190476190476], ['Aristolochia clementitis', 0.6419753086419753], ['Oncidium sphegiferum', 0.8205128205128205], ['Tamus communis', 0.98989898989899], ['Scaphyglottis ', 0.9647058823529412], ['Gossypium barbadense', 0.9142857142857143], ['Euphorbia laro B', 0.9532710280373832], ['Mascillariella acerata', 0.851063829787234], ['Euphorbia atropurpurea B', 0.04964539007092199], ['Bullophylum apodum', 0.84], ['Habenaria medusa', 0.7749999999999999], ['Masdevallia barleana', 0.854368932038835], ['Brassia sp', 0.9514563106796117], ['Pentaclethra macrophylla', 0.6947368421052633], ['Malva sylvestris', 0.8869565217391303], ['Celtis mildbraedii', 0.8108108108108109], ['Aptenia cordifolia', 0.8292682926829269], ['Octorneria bauenlla', 0.9047619047619047], ['Ipomoea cairica', 0.8181818181818182], ['Stokesia laevis', 0.8807339449541284], ['Promenaea stapelioides', 0.9072164948453608], ['Brasiliorchis picta', 0.9538461538461539], ['Angraecum florulentum', 0.9333333333333333], ['Paphiopedilum randsii', 0.7294117647058823], ['Hedera helix', 0.9777777777777777], ['Rubus arcticus', 0.8717948717948718], ['Amorphophallus titanum', 0.7619047619047618], ['Lannea welwitschii', 0.5581395348837208], ['Calanthe hattorii', 0.8395061728395061], ['Petersianthus macrocarpus', 0.9827586206896551], ['Neofinetia falcata', 0.9310344827586207], ['Poa pratensis', 0.6857142857142857], ['Erythrophleum suaveolens', 0.8666666666666667], ['Alstroemeria aurea', 0.8484848484848485], ['Platycerium bifurcatum', 0.8421052631578948], ['Chloris gayana', 0.6495726495726496], ['Prosthechea squalida', 0.9019607843137256], ['Strombosiopsis tetrandra', 0.8852459016393444], ['Chloris pychnotrix', 0.33333333333333337], ['Hydnophytum formicarum', 0.8674698795180724], ['Strychnos spinosa', 0.5984251968503936], ['Oxalis fontana', 0.7540983606557378], ['Ipomoea vagans', 0.8467153284671534], ['Euphorbia nivulia B', 0.7272727272727274], ['Heliamphora ciliata', 0.9367088607594937], ['Lilium regale', 0.5691056910569106], ['Musa basjoo', 0.9402985074626865], ['Eryngium campestre', 0.875], ['Eria globifera', 0.6966292134831461], ['Polyalthia suaveolens', 0.6984126984126984], ['Stevia rebaudiana', 0.9210526315789475], ['Trichilia gigliana', 0.9310344827586207], ['Potentilla reptans', 0.7301587301587302], ['Odenbloglosum ', 0.96875], ['Entandrophragma utile', 0.9719626168224299], ['Geitonoplesium cymosum', 0.5106382978723404], ['Camaridium cucullatum', 0.8297872340425533], ['Gentiana dinarica', 0.9767441860465116], ['Prosthechea spondiada', 0.9719626168224299], ['Euphorbia matabelensis', 0.44642857142857145], ['Lamarckia aurea', 0.8799999999999999], ['Cola griseiflora', 0.9423076923076924], ['Astilbe japonica', 0.8636363636363636], ['Arpophyllum giganteum', 0.8529411764705883], ['Ficus elastica', 0.904109589041096], ['Strychnos cocculoides', 0.6222222222222223], ['Diospyros mespiliformis', 0.5504587155963303], ['Rhyncholaelia glauca', 0.8600000000000001], ['Diospyros bipindensis', 0.6610169491525424], ['Euphorbia spinescens B', 0.7450980392156863], ['Irvingia grandifolia', 0.5454545454545454], ['Prioria oxyphylla', 0.7534246575342465], ['Ajuga reptans', 0.708860759493671], ['Mentha aquatica', 0.9508196721311476], ['Prioria balsamifera', 0.7228915662650603], ['Trilepisium madagascariense', 0.9142857142857143], ['Ricinodendron heudelotii', 0.9302325581395349], ['Mammea africana', 0.9791666666666666], ['Alpinia sanderae', 0.5102040816326531], ['Diospyros kirkii', 0.7575757575757576], ['Lythrum portula', 0.8048780487804879], ['Gaultheria procumbens', 0.9850746268656716], ['Lannea schweinfurthii Bidgood 1759', 0.7692307692307693], ['Nymphaea Director G (B)', 0.7619047619047619], ['Entandrophragma candollei', 0.8837209302325582]]
    
    # model 6 op deel_1_tot_5_zonder_augment
    array_model_6 = [['Paphiopedilum randsii', 0.8070175438596492], ['Platycerium bifurcatum', 0.8541666666666667], ['Prosthechea spondiada', 0.8367346938775511], ['Ipomoea vagans', 0.6376811594202899], ['Hedera helix', 0.9203539823008849], ['Aristolochia clementitis', 0.6883116883116882], ['Euphorbia neostolonifera B', 0.7079646017699114], ['Promenaea stapelioides', 0.7796610169491525], ['Jacquiniella equitantifolia', 0.8247422680412372], ['Petersianthus macrocarpus', 0.6122448979591837], ['Poa pratensis', 0.28], ['Masdevallia barleana', 0.8478260869565216], ['Tamus communis', 0.6666666666666666], ['Lythrum portula', 0.8363636363636363], ['Euphorbia heteropodum B', 0.88659793814433], ['Sarcoglottis speciosa', 0.9306930693069307], ['Lannea welwitschii', 0.45045045045045046], ['Ada glumacea', 0.968421052631579], ['Saccharum officinarum', 0.4220183486238532], ['Euphorbia californica B', 0.2165605095541401], ['Octorneria bauenlla', 0.5789473684210525], ['Nymphaea Director G (B)', 0.5507246376811594], ['Euphorbia laro B', 0.7889908256880733], ['Sarcochilus fitzgeraldii', 0.28915662650602403], ['Gentiana dinarica', 0.9256198347107439], ['Bullophylum apodum', 0.8941176470588236], ['Heliamphora ciliata', 0.888888888888889], ['Polyalthia suaveolens', 0.6578947368421053], ['Restrepiella ophiocephala', 0.2211055276381909], ['Amorphophallus titanum', 0.6415094339622641], ['Nepenthes veitchii', 0.9894736842105264], ['Strychnos spinosa', 0.7999999999999999], ['Musa basjoo', 0.6724137931034482], ['Camaridium cucullatum', 0.9318181818181818], ['Pinellia ternata', 0.5205479452054794], ['Calla palustris', 0.5555555555555555], ['Oxalis fontana', 0.3350253807106599], ['Habenaria medusa', 0.7241379310344827], ['Euphorbia rhizophora B', 0.711111111111111], ['Lilium regale', 0.35000000000000003], ['Rhyncholaelia glauca', 0.5048543689320388], ['Mentha aquatica', 0.8493150684931507], ['Arpophyllum giganteum', 0.9855072463768115], ['Neofinetia falcata', 0.9354838709677419], ['Alstroemeria aurea', 0.5853658536585367], ['Celtis mildbraedii', 0.6333333333333333], ['Ipomoea cairica', 0.5], ['Geitonoplesium cymosum', 0.7234042553191489], ['Euphorbia heterodoxa B', 0.14728682170542637], ['Prosthechea squalida', 0.8461538461538461], ['Aerides multiflorum', 0.9259259259259259], ['Odontoglossum nobile', 0.9545454545454545], ['Gossypium barbadense', 0.6944444444444444], ['Stokesia laevis', 0.8461538461538461], ['Euphorbia matabelensis', 0.19999999999999998], ['Malva sylvestris', 0.8674698795180723], ['Ficus elastica', 0.8688524590163935], ['Chloris gayana', 0.33043478260869563], ['Brassia sp', 0.9059829059829059], ['Eria globifera', 0.5825242718446602], ['Pinguicula emarginata', 0.576271186440678], ['Irvingia grandifolia', 0.19047619047619047], ['Lamarckia aurea', 0.6896551724137931], ['Stelis argentata', 0.9230769230769231], ['Angraecum calceolus', 0.6117647058823529], ['Strombosiopsis tetrandra', 0.3829787234042553], ['Aptenia cordifolia', 0.6736842105263159], ['Euphorbia balsamifera B', 0.53125], ['Hydnophytum formicarum', 0.684931506849315], ['Phragmipedium longifolium', 0.9069767441860465], ['Myosoton aquaticum', 0.8888888888888891], ['Stevia rebaudiana', 0.8108108108108109], ['Euphorbia nivulia B', 0.41379310344827586], ['Euphorbia wildii B', 0.6666666666666666], ['Prioria oxyphylla', 0.2735042735042735], ['Allium moly B', 0.5217391304347827], ['Angraecum florulentum', 0.8888888888888888], ['Euphorbia atropurpurea B', 0.27027027027027023], ['Oncidium sphegiferum', 0.9484536082474228], ['Eryngium campestre', 0.6666666666666666], ['Avena sativa', 0.0909090909090909], ['Odenbloglosum ', 0.9866666666666666], ['Barkeria', 0.8045977011494252], ['Pentaclethra macrophylla', 0.0588235294117647], ['Roscoea cautleoides', 0.8775510204081632], ['Cola griseiflora', 0.9249999999999999], ['Entandrophragma utile', 0.9473684210526316], ['Garcinia punctata', 0.3529411764705882], ['Euphorbia spinescens B', 0.44155844155844154], ['Mascillariella acerata', 0.8037383177570094], ['Alpinia sanderae', 0.3191489361702128], ['Strychnos cocculoides', 0.42500000000000004], ['Diospyros mespiliformis', 0.5714285714285714], ['Ajuga reptans', 0.7339449541284404], ['Scaphyglottis ', 0.9557522123893805], ['Rubus arcticus', 0.45714285714285713], ['Diospyros bipindensis', 0.8867924528301887], ['Calanthe hattorii', 0.6666666666666666], ['Trichilia gigliana', 0.8631578947368421], ['Theobroma cacao', 0.4597701149425288], ['Astilbe japonica', 0.14285714285714285], ['Gaultheria procumbens', 0.9538461538461539], ['Erythrophleum suaveolens', 0.6756756756756757], ['Carapa procera', 0.8925619834710744], ['Ricinodendron heudelotii', 0.5945945945945946], ['Mammea africana', 0.7246376811594203], ['Brasiliorchis picta', 0.9589041095890412], ['Prioria balsamifera', 0.5], ['Lannea acida', 0.45000000000000007], ['Chloris pychnotrix', 0.18918918918918917], ['Potentilla reptans', 0.4470588235294118], ['Trilepisium madagascariense', 0.9333333333333333], ['Diospyros kirkii', 0.42857142857142855], ['Lannea schweinfurthii Bidgood 1759', 0.9199999999999999], ['Entandrophragma candollei', 0.819672131147541]]
    
    array_model_5 = [['Euphorbia heterodoxa B', 0.27096774193548384], ['Ada glumacea', 0.8915662650602411], ['Aerides multiflorum', 0.9433962264150944], ['Euphorbia neostolonifera B', 0.8382352941176471], ['Euphorbia balsamifera B', 0.9904761904761905], ['Calla palustris', 0.9541284403669724], ['Pinguicula emarginata', 0.7640449438202247], ['Stelis argentata', 0.9591836734693877], ['Avena sativa', 0.7865168539325844], ['Nepenthes veitchii', 0.9534883720930233], ['Euphorbia rhizophora B', 0.9166666666666666], ['Pinellia ternata', 0.9523809523809523], ['Saccharum officinarum', 0.8854961832061069], ['Allium moly B', 0.8596491228070176], ['Phragmipedium longifolium', 0.8750000000000001], ['Barkeria', 0.8080808080808081], ['Angraecum calceolus', 0.6185567010309279], ['Carapa procera', 0.9795918367346939], ['Myosoton aquaticum', 0.9108910891089108], ['Garcinia punctata', 0.6582278481012658], ['Odontoglossum nobile', 0.9791666666666666], ['Euphorbia heteropodum B', 0.9249999999999999], ['Euphorbia wildii B', 0.9908256880733944], ['Euphorbia californica B', 0.8915662650602411], ['Roscoea cautleoides', 0.9142857142857143], ['Sarcoglottis speciosa', 0.988235294117647], ['Sarcochilus fitzgeraldii', 0.4545454545454545], ['Jacquiniella equitantifolia', 0.924731182795699], ['Restrepiella ophiocephala', 0.6813186813186813], ['Aristolochia clementitis', 0.8671328671328671], ['Oncidium sphegiferum', 0.9111111111111111], ['Tamus communis', 0.9333333333333333], ['Scaphyglottis ', 0.8764044943820225], ['Gossypium barbadense', 0.8571428571428571], ['Euphorbia laro B', 0.9636363636363636], ['Mascillariella acerata', 0.7200000000000001], ['Euphorbia atropurpurea B', 0.41176470588235287], ['Bullophylum apodum', 0.631578947368421], ['Habenaria medusa', 0.860759493670886], ['Masdevallia barleana', 0.9272727272727272], ['Brassia sp', 0.9215686274509803], ['Pentaclethra macrophylla', 0.8118811881188118], ['Malva sylvestris', 0.9152542372881356], ['Celtis mildbraedii', 0.7777777777777778], ['Aptenia cordifolia', 0.8974358974358975], ['Octorneria bauenlla', 0.898876404494382], ['Ipomoea cairica', 0.8918918918918919], ['Stokesia laevis', 0.9454545454545454], ['Promenaea stapelioides', 0.9090909090909091], ['Brasiliorchis picta', 0.8592592592592593], ['Angraecum florulentum', 0.8695652173913043], ['Paphiopedilum randsii', 0.7179487179487178], ['Hedera helix', 0.9534883720930233], ['Rubus arcticus', 0.891566265060241], ['Amorphophallus titanum', 0.8035714285714286], ['Lannea welwitschii', 0.7142857142857143], ['Calanthe hattorii', 0.7472527472527473], ['Petersianthus macrocarpus', 0.9107142857142858], ['Neofinetia falcata', 0.9508196721311476], ['Poa pratensis', 0.8311688311688312], ['Erythrophleum suaveolens', 0.7619047619047619], ['Alstroemeria aurea', 0.8043478260869564], ['Platycerium bifurcatum', 0.8351648351648352], ['Chloris gayana', 0.7777777777777778], ['Prosthechea squalida', 0.8727272727272727], ['Strombosiopsis tetrandra', 0.8796680497925311], ['Chloris pychnotrix', 0.39999999999999997], ['Hydnophytum formicarum', 0.7070707070707071], ['Strychnos spinosa', 0.6466165413533834], ['Oxalis fontana', 0.8405797101449276], ['Ipomoea vagans', 0.8609271523178809], ['Euphorbia nivulia B', 0.8860759493670887], ['Heliamphora ciliata', 0.8863636363636365], ['Lilium regale', 0.5981308411214953], ['Musa basjoo', 0.9037037037037037], ['Eryngium campestre', 0.9391304347826087], ['Eria globifera', 0.7964601769911505], ['Polyalthia suaveolens', 0.8064516129032259], ['Stevia rebaudiana', 0.8433734939759038], ['Trichilia gigliana', 0.9821428571428571], ['Potentilla reptans', 0.675], ['Odenbloglosum ', 0.9523809523809523], ['Entandrophragma utile', 0.9629629629629629], ['Geitonoplesium cymosum', 0.8760330578512396], ['Camaridium cucullatum', 0.8478260869565218], ['Gentiana dinarica', 0.9655172413793104], ['Prosthechea spondiada', 0.859504132231405], ['Euphorbia matabelensis', 0.42276422764227645], ['Lamarckia aurea', 0.8421052631578947], ['Cola griseiflora', 0.888888888888889], ['Astilbe japonica', 0.8181818181818181], ['Arpophyllum giganteum', 0.9444444444444445], ['Ficus elastica', 0.8717948717948718], ['Strychnos cocculoides', 0.7397260273972602], ['Diospyros mespiliformis', 0.6915887850467289], ['Rhyncholaelia glauca', 0.7179487179487181], ['Diospyros bipindensis', 0.8347826086956522], ['Euphorbia spinescens B', 0.9090909090909091], ['Irvingia grandifolia', 0.32727272727272727], ['Prioria oxyphylla', 0.7215189873417721], ['Ajuga reptans', 0.7948717948717948], ['Mentha aquatica', 0.923076923076923], ['Prioria balsamifera', 0.5319148936170213], ['Trilepisium madagascariense', 0.9444444444444444], ['Ricinodendron heudelotii', 0.8740740740740741], ['Mammea africana', 0.9183673469387755], ['Alpinia sanderae', 0.6461538461538462], ['Diospyros kirkii', 0.8529411764705882], ['Lythrum portula', 0.896551724137931], ['Gaultheria procumbens', 0.9166666666666667], ['Lannea schweinfurthii Bidgood 1759', 0.7924528301886792], ['Nymphaea Director G (B)', 0.7999999999999999], ['Entandrophragma candollei', 0.8148148148148148]]

    array_correct = []
    array_fout = []
    for namen_2 in array_model_2:
        naam_2 = namen_2[0]
        correct = False
        for namen_6 in array_model_5:
            naam_6 = namen_6[0]
            if naam_2 == naam_6:
                correct = True
        if correct == True:
            array_correct.append(naam_2)
        else:
            array_fout.append(naam_2)
    print('array_correct',array_correct)    
    print('array_correct',len(array_correct))
    print('array_fout',array_fout)
    
    print('array_fout',len(array_fout))
        



def tellen_huidmondjes(all_data,array_ingelezen_lijst):
    # model 2
    # array_met_F1_scores = [['Euphorbia heterodoxa B', 0.2956521739130435], ['Ada glumacea', 0.9318181818181818], ['Aerides multiflorum', 0.9423076923076923], ['Euphorbia neostolonifera B', 0.8346456692913387], ['Euphorbia balsamifera B', 0.8737864077669903], ['Calla palustris', 0.7706422018348623], ['Pinguicula emarginata', 0.9047619047619047], ['Stelis argentata', 0.9484536082474228], ['Avena sativa', 0.8791208791208791], ['Nepenthes veitchii', 0.9761904761904762], ['Euphorbia rhizophora B', 0.9565217391304348], ['Pinellia ternata', 0.9523809523809523], ['Saccharum officinarum', 0.8000000000000002], ['Allium moly B', 0.7], ['Phragmipedium longifolium', 0.8571428571428572], ['Barkeria', 0.967741935483871], ['Angraecum calceolus', 0.8767123287671232], ['Carapa procera', 0.9504950495049506], ['Myosoton aquaticum', 0.9230769230769231], ['Garcinia punctata', 0.7777777777777778], ['Odontoglossum nobile', 0.9894736842105264], ['Euphorbia heteropodum B', 0.9876543209876543], ['Euphorbia wildii B', 0.9629629629629629], ['Euphorbia californica B', 0.9090909090909091], ['Roscoea cautleoides', 0.96], ['Sarcoglottis speciosa', 0.9411764705882352], ['Sarcochilus fitzgeraldii', 0.5217391304347826], ['Jacquiniella equitantifolia', 0.898876404494382], ['Restrepiella ophiocephala', 0.5476190476190476], ['Aristolochia clementitis', 0.6419753086419753], ['Oncidium sphegiferum', 0.8205128205128205], ['Tamus communis', 0.98989898989899], ['Scaphyglottis ', 0.9647058823529412], ['Gossypium barbadense', 0.9142857142857143], ['Euphorbia laro B', 0.9532710280373832], ['Mascillariella acerata', 0.851063829787234], ['Euphorbia atropurpurea B', 0.04964539007092199], ['Bullophylum apodum', 0.84], ['Habenaria medusa', 0.7749999999999999], ['Masdevallia barleana', 0.854368932038835], ['Brassia sp', 0.9514563106796117], ['Pentaclethra macrophylla', 0.6947368421052633], ['Malva sylvestris', 0.8869565217391303], ['Celtis mildbraedii', 0.8108108108108109], ['Aptenia cordifolia', 0.8292682926829269], ['Octorneria bauenlla', 0.9047619047619047], ['Ipomoea cairica', 0.8181818181818182], ['Stokesia laevis', 0.8807339449541284], ['Promenaea stapelioides', 0.9072164948453608], ['Brasiliorchis picta', 0.9538461538461539], ['Angraecum florulentum', 0.9333333333333333], ['Paphiopedilum randsii', 0.7294117647058823], ['Hedera helix', 0.9777777777777777], ['Rubus arcticus', 0.8717948717948718], ['Amorphophallus titanum', 0.7619047619047618], ['Lannea welwitschii', 0.5581395348837208], ['Calanthe hattorii', 0.8395061728395061], ['Petersianthus macrocarpus', 0.9827586206896551], ['Neofinetia falcata', 0.9310344827586207], ['Poa pratensis', 0.6857142857142857], ['Erythrophleum suaveolens', 0.8666666666666667], ['Alstroemeria aurea', 0.8484848484848485], ['Platycerium bifurcatum', 0.8421052631578948], ['Chloris gayana', 0.6495726495726496], ['Prosthechea squalida', 0.9019607843137256], ['Strombosiopsis tetrandra', 0.8852459016393444], ['Chloris pychnotrix', 0.33333333333333337], ['Hydnophytum formicarum', 0.8674698795180724], ['Strychnos spinosa', 0.5984251968503936], ['Oxalis fontana', 0.7540983606557378], ['Ipomoea vagans', 0.8467153284671534], ['Euphorbia nivulia B', 0.7272727272727274], ['Heliamphora ciliata', 0.9367088607594937], ['Lilium regale', 0.5691056910569106], ['Musa basjoo', 0.9402985074626865], ['Eryngium campestre', 0.875], ['Eria globifera', 0.6966292134831461], ['Polyalthia suaveolens', 0.6984126984126984], ['Stevia rebaudiana', 0.9210526315789475], ['Trichilia gigliana', 0.9310344827586207], ['Potentilla reptans', 0.7301587301587302], ['Odenbloglosum ', 0.96875], ['Entandrophragma utile', 0.9719626168224299], ['Geitonoplesium cymosum', 0.5106382978723404], ['Camaridium cucullatum', 0.8297872340425533], ['Gentiana dinarica', 0.9767441860465116], ['Prosthechea spondiada', 0.9719626168224299], ['Euphorbia matabelensis', 0.44642857142857145], ['Lamarckia aurea', 0.8799999999999999], ['Cola griseiflora', 0.9423076923076924], ['Astilbe japonica', 0.8636363636363636], ['Arpophyllum giganteum', 0.8529411764705883], ['Ficus elastica', 0.904109589041096], ['Strychnos cocculoides', 0.6222222222222223], ['Diospyros mespiliformis', 0.5504587155963303], ['Rhyncholaelia glauca', 0.8600000000000001], ['Diospyros bipindensis', 0.6610169491525424], ['Euphorbia spinescens B', 0.7450980392156863], ['Irvingia grandifolia', 0.5454545454545454], ['Prioria oxyphylla', 0.7534246575342465], ['Ajuga reptans', 0.708860759493671], ['Mentha aquatica', 0.9508196721311476], ['Prioria balsamifera', 0.7228915662650603], ['Trilepisium madagascariense', 0.9142857142857143], ['Ricinodendron heudelotii', 0.9302325581395349], ['Mammea africana', 0.9791666666666666], ['Alpinia sanderae', 0.5102040816326531], ['Diospyros kirkii', 0.7575757575757576], ['Lythrum portula', 0.8048780487804879], ['Gaultheria procumbens', 0.9850746268656716], ['Lannea schweinfurthii Bidgood 1759', 0.7692307692307693], ['Nymphaea Director G (B)', 0.7619047619047619], ['Entandrophragma candollei', 0.8837209302325582]]
    
    # model 6 op deel_1_tot_5_zonder_augment
    # array_met_F1_scores = [['Paphiopedilum randsii', 0.8070175438596492], ['Platycerium bifurcatum', 0.8541666666666667], ['Prosthechea spondiada', 0.8367346938775511], ['Ipomoea vagans', 0.6376811594202899], ['Hedera helix', 0.9203539823008849], ['Aristolochia clementitis', 0.6883116883116882], ['Euphorbia neostolonifera B', 0.7079646017699114], ['Promenaea stapelioides', 0.7796610169491525], ['Jacquiniella equitantifolia', 0.8247422680412372], ['Petersianthus macrocarpus', 0.6122448979591837], ['Poa pratensis', 0.28], ['Masdevallia barleana', 0.8478260869565216], ['Tamus communis', 0.6666666666666666], ['Lythrum portula', 0.8363636363636363], ['Euphorbia heteropodum B', 0.88659793814433], ['Sarcoglottis speciosa', 0.9306930693069307], ['Lannea welwitschii', 0.45045045045045046], ['Ada glumacea', 0.968421052631579], ['Saccharum officinarum', 0.4220183486238532], ['Euphorbia californica B', 0.2165605095541401], ['Octorneria bauenlla', 0.5789473684210525], ['Nymphaea Director G (B)', 0.5507246376811594], ['Euphorbia laro B', 0.7889908256880733], ['Sarcochilus fitzgeraldii', 0.28915662650602403], ['Gentiana dinarica', 0.9256198347107439], ['Bullophylum apodum', 0.8941176470588236], ['Heliamphora ciliata', 0.888888888888889], ['Polyalthia suaveolens', 0.6578947368421053], ['Restrepiella ophiocephala', 0.2211055276381909], ['Amorphophallus titanum', 0.6415094339622641], ['Nepenthes veitchii', 0.9894736842105264], ['Strychnos spinosa', 0.7999999999999999], ['Musa basjoo', 0.6724137931034482], ['Camaridium cucullatum', 0.9318181818181818], ['Pinellia ternata', 0.5205479452054794], ['Calla palustris', 0.5555555555555555], ['Oxalis fontana', 0.3350253807106599], ['Habenaria medusa', 0.7241379310344827], ['Euphorbia rhizophora B', 0.711111111111111], ['Lilium regale', 0.35000000000000003], ['Rhyncholaelia glauca', 0.5048543689320388], ['Mentha aquatica', 0.8493150684931507], ['Arpophyllum giganteum', 0.9855072463768115], ['Neofinetia falcata', 0.9354838709677419], ['Alstroemeria aurea', 0.5853658536585367], ['Celtis mildbraedii', 0.6333333333333333], ['Ipomoea cairica', 0.5], ['Geitonoplesium cymosum', 0.7234042553191489], ['Euphorbia heterodoxa B', 0.14728682170542637], ['Prosthechea squalida', 0.8461538461538461], ['Aerides multiflorum', 0.9259259259259259], ['Odontoglossum nobile', 0.9545454545454545], ['Gossypium barbadense', 0.6944444444444444], ['Stokesia laevis', 0.8461538461538461], ['Euphorbia matabelensis', 0.19999999999999998], ['Malva sylvestris', 0.8674698795180723], ['Ficus elastica', 0.8688524590163935], ['Chloris gayana', 0.33043478260869563], ['Brassia sp', 0.9059829059829059], ['Eria globifera', 0.5825242718446602], ['Pinguicula emarginata', 0.576271186440678], ['Irvingia grandifolia', 0.19047619047619047], ['Lamarckia aurea', 0.6896551724137931], ['Stelis argentata', 0.9230769230769231], ['Angraecum calceolus', 0.6117647058823529], ['Strombosiopsis tetrandra', 0.3829787234042553], ['Aptenia cordifolia', 0.6736842105263159], ['Euphorbia balsamifera B', 0.53125], ['Hydnophytum formicarum', 0.684931506849315], ['Phragmipedium longifolium', 0.9069767441860465], ['Myosoton aquaticum', 0.8888888888888891], ['Stevia rebaudiana', 0.8108108108108109], ['Euphorbia nivulia B', 0.41379310344827586], ['Euphorbia wildii B', 0.6666666666666666], ['Prioria oxyphylla', 0.2735042735042735], ['Allium moly B', 0.5217391304347827], ['Angraecum florulentum', 0.8888888888888888], ['Euphorbia atropurpurea B', 0.27027027027027023], ['Oncidium sphegiferum', 0.9484536082474228], ['Eryngium campestre', 0.6666666666666666], ['Avena sativa', 0.0909090909090909], ['Odenbloglosum ', 0.9866666666666666], ['Barkeria', 0.8045977011494252], ['Pentaclethra macrophylla', 0.0588235294117647], ['Roscoea cautleoides', 0.8775510204081632], ['Cola griseiflora', 0.9249999999999999], ['Entandrophragma utile', 0.9473684210526316], ['Garcinia punctata', 0.3529411764705882], ['Euphorbia spinescens B', 0.44155844155844154], ['Mascillariella acerata', 0.8037383177570094], ['Alpinia sanderae', 0.3191489361702128], ['Strychnos cocculoides', 0.42500000000000004], ['Diospyros mespiliformis', 0.5714285714285714], ['Ajuga reptans', 0.7339449541284404], ['Scaphyglottis ', 0.9557522123893805], ['Rubus arcticus', 0.45714285714285713], ['Diospyros bipindensis', 0.8867924528301887], ['Calanthe hattorii', 0.6666666666666666], ['Trichilia gigliana', 0.8631578947368421], ['Theobroma cacao', 0.4597701149425288], ['Astilbe japonica', 0.14285714285714285], ['Gaultheria procumbens', 0.9538461538461539], ['Erythrophleum suaveolens', 0.6756756756756757], ['Carapa procera', 0.8925619834710744], ['Ricinodendron heudelotii', 0.5945945945945946], ['Mammea africana', 0.7246376811594203], ['Brasiliorchis picta', 0.9589041095890412], ['Prioria balsamifera', 0.5], ['Lannea acida', 0.45000000000000007], ['Chloris pychnotrix', 0.18918918918918917], ['Potentilla reptans', 0.4470588235294118], ['Trilepisium madagascariense', 0.9333333333333333], ['Diospyros kirkii', 0.42857142857142855], ['Lannea schweinfurthii Bidgood 1759', 0.9199999999999999], ['Entandrophragma candollei', 0.819672131147541]]

    # model 5 op deel_1_tot_5

    array_met_F1_scores = [['Euphorbia heterodoxa B', 0.27096774193548384], ['Ada glumacea', 0.8915662650602411], ['Aerides multiflorum', 0.9433962264150944], ['Euphorbia neostolonifera B', 0.8382352941176471], ['Euphorbia balsamifera B', 0.9904761904761905], ['Calla palustris', 0.9541284403669724], ['Pinguicula emarginata', 0.7640449438202247], ['Stelis argentata', 0.9591836734693877], ['Avena sativa', 0.7865168539325844], ['Nepenthes veitchii', 0.9534883720930233], ['Euphorbia rhizophora B', 0.9166666666666666], ['Pinellia ternata', 0.9523809523809523], ['Saccharum officinarum', 0.8854961832061069], ['Allium moly B', 0.8596491228070176], ['Phragmipedium longifolium', 0.8750000000000001], ['Barkeria', 0.8080808080808081], ['Angraecum calceolus', 0.6185567010309279], ['Carapa procera', 0.9795918367346939], ['Myosoton aquaticum', 0.9108910891089108], ['Garcinia punctata', 0.6582278481012658], ['Odontoglossum nobile', 0.9791666666666666], ['Euphorbia heteropodum B', 0.9249999999999999], ['Euphorbia wildii B', 0.9908256880733944], ['Euphorbia californica B', 0.8915662650602411], ['Roscoea cautleoides', 0.9142857142857143], ['Sarcoglottis speciosa', 0.988235294117647], ['Sarcochilus fitzgeraldii', 0.4545454545454545], ['Jacquiniella equitantifolia', 0.924731182795699], ['Restrepiella ophiocephala', 0.6813186813186813], ['Aristolochia clementitis', 0.8671328671328671], ['Oncidium sphegiferum', 0.9111111111111111], ['Tamus communis', 0.9333333333333333], ['Scaphyglottis ', 0.8764044943820225], ['Gossypium barbadense', 0.8571428571428571], ['Euphorbia laro B', 0.9636363636363636], ['Mascillariella acerata', 0.7200000000000001], ['Euphorbia atropurpurea B', 0.41176470588235287], ['Bullophylum apodum', 0.631578947368421], ['Habenaria medusa', 0.860759493670886], ['Masdevallia barleana', 0.9272727272727272], ['Brassia sp', 0.9215686274509803], ['Pentaclethra macrophylla', 0.8118811881188118], ['Malva sylvestris', 0.9152542372881356], ['Celtis mildbraedii', 0.7777777777777778], ['Aptenia cordifolia', 0.8974358974358975], ['Octorneria bauenlla', 0.898876404494382], ['Ipomoea cairica', 0.8918918918918919], ['Stokesia laevis', 0.9454545454545454], ['Promenaea stapelioides', 0.9090909090909091], ['Brasiliorchis picta', 0.8592592592592593], ['Angraecum florulentum', 0.8695652173913043], ['Paphiopedilum randsii', 0.7179487179487178], ['Hedera helix', 0.9534883720930233], ['Rubus arcticus', 0.891566265060241], ['Amorphophallus titanum', 0.8035714285714286], ['Lannea welwitschii', 0.7142857142857143], ['Calanthe hattorii', 0.7472527472527473], ['Petersianthus macrocarpus', 0.9107142857142858], ['Neofinetia falcata', 0.9508196721311476], ['Poa pratensis', 0.8311688311688312], ['Erythrophleum suaveolens', 0.7619047619047619], ['Alstroemeria aurea', 0.8043478260869564], ['Platycerium bifurcatum', 0.8351648351648352], ['Chloris gayana', 0.7777777777777778], ['Prosthechea squalida', 0.8727272727272727], ['Strombosiopsis tetrandra', 0.8796680497925311], ['Chloris pychnotrix', 0.39999999999999997], ['Hydnophytum formicarum', 0.7070707070707071], ['Strychnos spinosa', 0.6466165413533834], ['Oxalis fontana', 0.8405797101449276], ['Ipomoea vagans', 0.8609271523178809], ['Euphorbia nivulia B', 0.8860759493670887], ['Heliamphora ciliata', 0.8863636363636365], ['Lilium regale', 0.5981308411214953], ['Musa basjoo', 0.9037037037037037], ['Eryngium campestre', 0.9391304347826087], ['Eria globifera', 0.7964601769911505], ['Polyalthia suaveolens', 0.8064516129032259], ['Stevia rebaudiana', 0.8433734939759038], ['Trichilia gigliana', 0.9821428571428571], ['Potentilla reptans', 0.675], ['Odenbloglosum ', 0.9523809523809523], ['Entandrophragma utile', 0.9629629629629629], ['Geitonoplesium cymosum', 0.8760330578512396], ['Camaridium cucullatum', 0.8478260869565218], ['Gentiana dinarica', 0.9655172413793104], ['Prosthechea spondiada', 0.859504132231405], ['Euphorbia matabelensis', 0.42276422764227645], ['Lamarckia aurea', 0.8421052631578947], ['Cola griseiflora', 0.888888888888889], ['Astilbe japonica', 0.8181818181818181], ['Arpophyllum giganteum', 0.9444444444444445], ['Ficus elastica', 0.8717948717948718], ['Strychnos cocculoides', 0.7397260273972602], ['Diospyros mespiliformis', 0.6915887850467289], ['Rhyncholaelia glauca', 0.7179487179487181], ['Diospyros bipindensis', 0.8347826086956522], ['Euphorbia spinescens B', 0.9090909090909091], ['Irvingia grandifolia', 0.32727272727272727], ['Prioria oxyphylla', 0.7215189873417721], ['Ajuga reptans', 0.7948717948717948], ['Mentha aquatica', 0.923076923076923], ['Prioria balsamifera', 0.5319148936170213], ['Trilepisium madagascariense', 0.9444444444444444], ['Ricinodendron heudelotii', 0.8740740740740741], ['Mammea africana', 0.9183673469387755], ['Alpinia sanderae', 0.6461538461538462], ['Diospyros kirkii', 0.8529411764705882], ['Lythrum portula', 0.896551724137931], ['Gaultheria procumbens', 0.9166666666666667], ['Lannea schweinfurthii Bidgood 1759', 0.7924528301886792], ['Nymphaea Director G (B)', 0.7999999999999999], ['Entandrophragma candollei', 0.8148148148148148]]


    # print(array_met_F1_scores)

    counted_data = count_stomata_eenmalig(array_ingelezen_lijst)
    # Print grootte box
    # for x in counted_data:
    #     # print(x)
    #     geprint = 'naam:'+ x['plantnaam'] + '   count:' + str(x['count'])
    #     print('counted_data: ', geprint)
    #     planten_soort = ophalen_planten(all_data,x)
    #     i = 0
    #     for soort_p in planten_soort:
    #         if i == 0:
    #             print('grootte_bbox',soort_p['grootte_bbox'])
    #             i+=1

    ###################### Print aantal boxen ##################################
    # Print aantal boxen
    # ar_gem_boxen = []
    # for x in counted_data:
    #     # print(x)
    #     geprint = 'naam:'+ x['plantnaam'] + '   count:' + str(x['count'])
    #     print('counted_data: ', geprint)
    #     planten_soort = ophalen_planten(all_data,x)
    #     i = 0
    #     tel = 0
    #     aantal = 0
    #     for soort_p in planten_soort:
    #         aantal += len(soort_p['bboxes'])
    #         tel += 1
            
    #         # if i == 0:
    #         #     print('aantal boxen',len(soort_p['bboxes']))
    #             # print(soort_p['filepath'])
    #             # i+=1
    #     # print('aantal',aantal)
    #     # print('tel',tel)
    #     # print('gemiddeld_aantal_boxen',aantal/(4*tel))
    #     # print('tel',tel)
    #     ar_gem_boxen.append([x['plantnaam'],aantal/(4*tel),tel])
    # for i in ar_gem_boxen:
    #     print(i[0])
    # # for i in ar_gem_boxen:
    # #     print(i[0])
    # #     print(i[1])
    # # print('Einde')
    # for i in ar_gem_boxen:
    #     print(i[1])

    #####################F1-score en naam###################################

    # for x in counted_data:
    #     geprint =  x['plantnaam'] 
    #     print('-',geprint)
    #     for naam in array_met_F1_scores:
    #         if naam[0] == x['plantnaam']:
    #             print(naam[1])

    for x in counted_data:
        geprint =  x['plantnaam'] 
        print(geprint)

    for x in counted_data:
        # geprint =  x['plantnaam'] 
        tel = 0
        for naam in array_met_F1_scores:
            if naam[0] == x['plantnaam']:
                print(naam[1])
                tel += 1
        if tel == 0:
            print(x['plantnaam'])

    ####################### Aantal bboxen #################################                
                           
    # for x in counted_data:
    #     geprint =   str(x['count'])
    #     print(geprint)
    # for x in counted_data:
    #     planten_soort = ophalen_planten(all_data,x)
    #     i = 0
    #     for soort_p in planten_soort:
    #         if i == 0:
    #             print(soort_p['grootte_bbox'])
    #             i+=1

### Main

def main():
    """
        Dit is de engiste methode waar er parameters zullen aangepast worden.
        Lijst: bevat de naam van het gebruikte tekst file
        Data path: Bevat het pad naar het text file en de afbeeldingen
        Soort data: Welke data is het (training, validatie of test): Zal gebruikt worden om de uitgeknipte afbeeldingen naar een correcte map te schrijven
    """
    uitknippen_data = False
    tellen_mondjes = False
    rotate = False
    stomata_200 = True
    zet_naar_grijswaarde = True # Moet grijze foto zijn of hij kan niet normalizeren
    img_norm = True
    training = False
    x_snijden = 200
#### Training weinig0huidmondjes
    # lijst = 'Anthonotha_weinig_huidmondjes.txt'
#### TRAINING DATA
    # lijst = '20180713_Anthonotha-Trilepsium_set1.txt'
    # data_path = '../data-20200402T082725Z-001/data/training_set/'
    # path_nieuwe_foto = '../data-20200402T082725Z-001/data/augmentatie/training/in_stukken_test/'
    # data_path_text = 'data_in_stukken_test.txt'
    # data_path_opslaag_plaats = '../../data/augmentatie/in_stukken_test/'
# #### Nieuwe set
#     lijst = 'deel_3_validatie_set.txt'
#     data_locatie_txt = '../data-20200402T082725Z-001/data/augmentatie/training/text_file/'
#     data_locatie_foto = '../data-20200402T082725Z-001/data/20200427_Trainingset/'
#     path_nieuwe_foto = '../data-20200402T082725Z-001/data/augmentatie/training/deel_3_validatie_set/'
#     data_path_text = 'deel_3_validatie_set.txt'
#     data_path_opslaag_plaats = '../../data/augmentatie/deel_3_validatie_set/'
#### Test set
    lijst = 'deel_1.txt'
    data_locatie_txt = '../data-20200402T082725Z-001/data/augmentatie/training/text_file/finale_opdeling_zonder_normalisatie/'
    data_locatie_foto = '../data-20200402T082725Z-001/data/20200427_Trainingset/'
    path_nieuwe_foto = '../data-20200402T082725Z-001/data/augmentatie/training/test/'
    data_path_text = 'deel_4_3.txt'
    data_path_opslaag_plaats = '../../data/augmentatie/test/'
#### Validatie data    
    # lijst = 'validation.txt'
    # data_path = '../data-20200402T082725Z-001/data/validation/samen_gezet/'
    # path_nieuwe_foto = '../data-20200402T082725Z-001/data/augmentatie/validation/links_rechts/'
    # data_path_text = 'validation_augmentatie.txt'
    # data_path_opslaag_plaats = '../../data/augmentatie/links_rechts_validation/'
   
    data_path_lijst = data_locatie_txt+lijst
    

    array_ingelezen_lijst = inlezen_lijst(data_path_lijst)
    #print('array: ',array_ingelezen_lijst)
    all_data = vind_bbox(array_ingelezen_lijst,data_locatie_foto)
    # print('all_data',all_data)
    if stomata_200 == True:
        counted_data = count_stomata_eenmalig(array_ingelezen_lijst)
        # print('counted_data: ',counted_data)
        regel_x(x_snijden,all_data,counted_data,path_nieuwe_foto,data_locatie_foto,data_path_text,data_path_opslaag_plaats,zet_naar_grijswaarde,img_norm,training)

    if rotate == True:
        all_data = vind_bbox(array_ingelezen_lijst,data_locatie_foto)
    if tellen_mondjes == True:
        tellen_huidmondjes(all_data,array_ingelezen_lijst)
    if False:
        vergelijk_array(all_data,array_ingelezen_lijst)
        # counted_data = count_stomata_eenmalig(array_ingelezen_lijst)
        # for lijn in counted_data:            
        #     planten_soort = ophalen_planten(all_data,lijn)
        #     print('lijn:      ',lijn)
        #     print('planten_soort     ',planten_soort)

    if uitknippen_data == True:
        all_data = vind_bbox(array_ingelezen_lijst,data_locatie_foto)
        regel_alles_links_rechts(all_data,path_nieuwe_foto,data_locatie_foto,data_path_text,data_path_opslaag_plaats)
    

main()


""""
Documentatie
    img_info: {'filename_oud': 'Gilbertiodendron dewevrei_G5-11_blad3-vlak2.jpg', 'filename_nieuw': 'LB_H_V_1_Gilbertiodendron dewevrei_G5-11_blad3-vlak2.jpg', 
                        'uitsnij_co': {'x1': 0, 'y1': 0, 'x2': 600, 'y2': 800}, 'bboxes': [{'x': 348, 'y': 688}, {'x': 379, 'y': 163}, {'x': 200, 'y': 65}]}

    blad {'filepath': 'Ipomaea eriocarpa Faulkner 2718_blad1-vlak1.jpg', 'bboxes': [{'x': 303, 'y': 279}, {'x': 768, 'y': 307}, {'x': 434, 'y': 510}, {'x': 118, 'y': 577}, {'x': 74, 'y': 894}, {'x': 597, 'y': 970}, {'x': 917, 'y': 1129}, {'x': 1240, 'y': 1157}, {'x': 1180, 'y': 420}, {'x': 851, 'y': 546}, {'x': 1546, 'y': 284}]}

Hoe dubbelchecken:
"""