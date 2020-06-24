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
# import imutils

# READ ME: PAS OP: Als we naar het text file schrijvan dan moet dit [x1,y1,x2,y2] zijn

"""
    De werking uitgelegd
    1) Afgebeeld: Een foto met de bboxen aangeduid in verschillende groottes.
        Gevraagd: Kies groote bbox: - (int)
                                    - Vul hier in hoe groot de bboxen zullen zijn
    
    Deze (2) zal geloopt worden tot je door alle afbeeldingen van een plantensoort bent
    2) Afgebeeld: Een foto met alle bboxen aangeduid in de juist grootte.
                    Dit om een overview te geven of de coordinaten wat juist zijn
        Gevraagd: Zijn de bboxen goed?
            Opties: - op: Ik wil de afbeelding graag opnieuw zien
                    - ok: Ja de bboxen zijn goed sla deze allemaal op
                    - del: Verwijder de afbeelding -> De bboxen zijn zeer slecht en van deze soort zijn er toch genoeg huidmondjes.
                    - sommige: De meeste bboxen zijn goed ik wil er gewoon sommige aanpassen
                    - 'alle rest': De bboxen zijn niet goed en we gaan ze 1 voor 1 overlopen
            
    3)          Hoe gaan al deze opties door:
                1) op: Hier zal de afbeelding gewoon opnieuw worden afgebeeld en kan je erna opnieuw een optie kiezen
                        - Geen verdere onderverdeling
                        - ga terug naar (2)
                2) ok: Hier zullen alle bboxen worden ingelezen
                        - Geen verdere onderverdeling 
                        - ga naar (4)
                3) del: - Geen verdere onderverdeling
                4) sommige: Tip: Elke keer je op de afbeelding klikt wordt dat punt opgeslaan. Dit geld ook wanneer je inzoomd
                            Afgebeeld: Een afbeelding met alle huidmondjes op afgebeeld
                            Gevraagd: 
                            Te doen:    In het ideale geval:
                                        1) zoom in op het huidmondje dat je wilt aanpassen
                                        2) Selecteer het midden van de karder rond dit mondje (dus het punt dat momenteel als midden wordt beschouwd)
                                        3) Selecteer het echte midden van dit mondje
                                        4) Sluit de afbeelding
                                        Werking achter de schermen:
                                            - Er wordt een array opgeslaan met alle punten die werden aangeduid
                                            - We willen hier punt 2 en 3 van Te doen in krijgen
                                            - In een volgende stap zal er gevraagd worden wat deze 2 punten waren
                                            - Erna zal op zoek gegaan worden in de array 'blad' en zal punt 2 vervangen worden door punt 3
                            Gevraagd: Welke coordinaten wil je?
                            Opties: Hier moet je ',' meegeven. De andere opties zijn voor wanneer je alle huidmondje wil aanpassen/opnieuw wil opslaan

                            Gevraagd: Welke coordinaten wil je
                            Opties: int,int
                                    - Je moet hier 2 keer een int meegeven. Dit zal zijn waardat het originele en nieuwe midden is opgeslaan bij de eerste fase van te doen
                                    - In het ideale geval: zal je hier dus 1,2 meegeven
                                            Extra uitleg:   Dit omdat de coordinaten op index 0 werden gebruikt om in te zoemen
                                                            En die op index 1 dus werden gebruikt voor het originele midden
                                                            En op index 2 werden gebruikt voor het nieuwe midden
                                    - In het niet ideale geval ga je eens moeten kijken op welke plaats de nodige coordinaten zich bevinden
                            Tip: Hier worden aangepaste huidmondjes niet direct naar de txt file geschreven maar veranderd in de originele array
                                
                            Gevraagd: zijn de bboxen goed
                            Optie:  - sommig    -> Wanneer je een volgend huidmondje wilt bekijken
                                    - op        -> Als je toch beslist om
                                    Eigenlijk kan je hier alleen voor simm 
                                Op het einde ga je terug naar (2) en zal je daar 'ok' moeten schrijven
                        Einde van sommige: Ga terug naar (2)

    4) Wanneer je alle bestaande huidmondjes hebt aangepast krijg je nu de optie om er extra bij te voegen
        Gevraagd: Bboxen toevoegen?
        Opties: Ja,nee
                - Ja: ja ik wil graag bboxen toevoegen
                        - Afgebeeld: Een afbeelding met alle bboxen die er momenteel zijn 
                        - Te doen: - Zoals bij 'sommige' kan je weer klikken op de afbeelding om punten aan te duiden
                                        Hier kan je zo veel nieuwe punten aanduiden als je wilt.
                                        Pas wel op dat je onthoud op welke index deze punten zich bevinden
                                   - sluit de foto
                        - Gevraagd: Welke plaats wil je opslaan
                        - Opties: Zelfde als bij sommige. Kies de indexen van de plaatsen die je wilt opslaan
                                    Bv: 1,5,6
                        Nu zal je terug naar (4) gaan
                - Nee: Nu wordt er terug naar (1) of (2) gegaan

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
        test = test[0:4]

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
        # print('filename',filename)
        print('test: ',data_path_foto+filename)
        if os.path.isfile(data_path_foto+filename):
            print('hey')
            if filename not in all_imgs:            
                all_imgs[filename] = {}
                all_imgs[filename]['filepath'] = lijn[3]
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
    
    return image_rot, blad_aug

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

def geef_bboxen_h_b_terug(image,blad,bbox_grootte):
    i=0
    debug = False
    print('bbox_grootte',bbox_grootte)
    bbox_grootte = bbox_grootte/2
    image_flip = image
    for boxen in blad['bboxes']:
        gt_x1, gt_x2 = boxen['x']-bbox_grootte, boxen['x']+bbox_grootte
        gt_y1, gt_y2 =  boxen['y']-bbox_grootte, boxen['y']+bbox_grootte
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

    return image_flip

def beeld_bboxen_met_h_b_af(image,blad,bbox_grootte):    
    i=0
    debug = False
    print('bbox_grootte',bbox_grootte)
    bbox_grootte = bbox_grootte/2
    image_flip = copy.deepcopy(image)
    for boxen in blad['bboxes']:
        gt_x1, gt_x2 = boxen['x']-bbox_grootte, boxen['x']+bbox_grootte
        gt_y1, gt_y2 =  boxen['y']-bbox_grootte, boxen['y']+bbox_grootte
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

    # plt.figure(figsize=(15,9))
    plt.imshow(image_flip)
    plt.title(blad['filepath'])    
    plt.grid()
    plt.show()

def beeld_bbox_af(image,boxen,bbox_grootte):
    debug = False
    image_flip = copy.deepcopy(image)
    bbox_grootte = bbox_grootte/2
    gt_x1, gt_x2 = boxen['x']-bbox_grootte, boxen['x']+bbox_grootte
    gt_y1, gt_y2 =  boxen['y']-bbox_grootte, boxen['y']+bbox_grootte
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

    # plt.figure(figsize=(15,9))
    plt.imshow(image_flip)  
    plt.grid()
    plt.show()

def beeld_groters_bboxen_met_h_b_af(image,blad,aantal):    
    i=0
    extra_image = copy.deepcopy(image)
    debug = False
    lijst_i = [1,2,4,8]
    while i<aantal:        
        nummer = lijst_i[i]
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
                cv2.putText(image, 'gt bbox', (gt_x1, gt_y1-5), cv2.FONT_HERSHEY_DUPLEX, 0.7, color, 1)
                cv2.rectangle(image, (gt_x1, gt_y1), (gt_x2, gt_y2), color, 2)
                cv2.circle(image, (int((gt_x1+gt_x2)/2), int((gt_y1+gt_y2)/2)), 3, color, -1)
            else:                
                cv2.putText(extra_image, 'gt bbox', (gt_x1, gt_y1-5), cv2.FONT_HERSHEY_DUPLEX, 0.7, color, 1)
                cv2.rectangle(extra_image, (gt_x1, gt_y1), (gt_x2, gt_y2), color, 2)
                cv2.circle(extra_image, (int((gt_x1+gt_x2)/2), int((gt_y1+gt_y2)/2)), 3, color, -1)
        i+=1


    # plt.figure(figsize=(15,9))
    plt.subplot(1,2,1)
    plt.imshow(image)
    plt.title('img_normaal')
    plt.subplot(1,2,2)
    plt.imshow(extra_image)
    plt.title(blad['filepath'])    
    plt.grid()
    plt.show()

### Schrijven text file en opslaan image

def schrijven_text_file_blad(blad,text_w,bbox_grootte):
    """Zal de middelpunten van de huidmondjes naar een textfile schrijven 
    
    Arguments:
        image_info {list} -- list{filename_oud,filename_nieuw,uitsnij_co[x1,x2,y1,y2],lijst{bboxes[x,y]}}
                            filename_oud: naam van originele image
                            filename_nieuw: Naam van uitgesneden image. Bv met links_ voor
                            uitsnij_co: De coordinaten van de hoekpunten van het deel dat zal worden uitgesneden
                            lijst{bboxes}: Een lijst van de coordinaten van het middelpunt van de huidmondjes die tot het uitgesneeden deel behoren
        text_w {text file} -- de text file
    """
    #print('image_info[filename_nieuw]',image_info['filename_nieuw'])'
    print('test')
    
    text_w.write('wtf')

    for lijn in blad['bboxes']:
        text_w.write(str(lijn['x']) + ';' + str(lijn['y']) + ';'+ blad['filepath'] + ';' + str(bbox_grootte) + ";" +'\n')
        # schrijf_een_lijn(lijn['x'],lijn['y'],text_w,blad['filepath'],bbox_grootte)

def vind_zijde_bbox(planten_soort,data_path_foto):  
    print('plant_soort',planten_soort)  
    print('data_path_foto',data_path_foto)  
    image_aug, blad_aug = augmentatie(planten_soort[0],data_path_foto,[False,False,0],False)
    beeld_groters_bboxen_met_h_b_af(image_aug,blad_aug,3)     
    bbox_grootte = input("Grootte van de bbox: ")
    # Note that in version 3, the print() function
    # requires the use of parenthesis.
    print("Is this what you just said? ", bbox_grootte)
    zeker = input("Are you sure (+,o (opnieuw)): ")
    while zeker != '+':
        if zeker == 'o':            
            beeld_groters_bboxen_met_h_b_af(image_aug,blad_aug,3)   
            einde_click()

        bbox_grootte = input("Probeer opnieuw: ")
        print("Is this what you just said? ", bbox_grootte)
        zeker = input("Are you sure: ")
    bbox_grootte = int(bbox_grootte)
    return bbox_grootte

def begin_click_toevoegen():
    global coords
    
    print('coordinaten',coords)
    
    co = []
    gewenst = index_gewenste_coordinaten()    
    ge = []
    if gewenst == 'goed':
        i = 0
        print('iii',i)
        while i<len(coords):
            ge.append(i)
            print('i',i)
            i+=1
    else:
        ge = re.split(',',gewenst)  
    # ge = re.split(',',gewenst)   
    co = []
    for index in ge:
        co.append([int(coords[int(index)][0]) , int(coords[int(index)][1])])
    return co


def begin_click():
    global coords
    
    print('coordinaten',coords)
    # gewenst = welke_coordinaten()     
    co = []
    # if gewenst == 'toevoegen':
    #     gewenst = index_gewenste_coordinaten()
    #     ge = re.split(',',gewenst)   
    #     co = []
    #     for index in ge:
    #         co.append([int(coords[int(index)][0]) , int(coords[int(index)][1])])
    #     return co

    # if gewenst == ',':
    
    print('len coordinaten',len(coords))
    gewenst = index_gewenste_coordinaten()
    ge = []
    print('gewenst',gewenst)
    if gewenst == 'goed':
        i = 0
        print('iii',i)
        while i<len(coords):
            ge.append(i)
            print('i',i)
            i+=1
    else:
        ge = re.split(',',gewenst)        
    print('ge',ge)
    co = []
    for index in ge:
        co.append([int(coords[int(index)][0]) , int(coords[int(index)][1])])
    return co



def einde_click():
    global coords
    print('coords',coords)
    del coords[:]
    print('coords',coords)
    fig = plt.figure(figsize=(15,9))
    cid = fig.canvas.mpl_connect('button_press_event', onclick)
    
def x_y_box(image,bbox,bbox_grootte):    
    i = 0 
    # beeld_bbox_af(image,bbox,bbox_grootte) 
    # coordinaten = []
    # coordinaten = begin_click()    
    # einde_click()
    # print('coordinaten',coordinaten)
    # if len(coordinaten) == 1:
    #     # Optie om coordinaten te houden
    #     houden = input("Wil je coordinaten behouden (-): ")
    #     if houden == '-':
    #         coordinaten = [bbox['x'], bbox['y']]
    #     else:
    #         while len(coordinaten) != 2:
    #             bbox_co = input("Coordinaten middelpunt: ")
    #             # Note that in version 3, the print() function
    #             # requires the use of parenthesis.
    #             print("Is this what you just said? ", bbox_co)
    #             zeker = input("Are you sure (+,o): ")
    #             while zeker != '+':        
    #                 if zeker == 'o':
    #                     beeld_bbox_af(image,bbox,int(bbox_grootte) )
    #                     einde_click()
    #                 bbox_co = input("Probeer coordinaten opnieuw: ")
    #                 print("Is this what you just said? ", bbox_co)
    #                 zeker = input("Are you sure: ")

    #             if bbox_co == '-':
    #                 coordinaten = [bbox['x'], bbox['y']]
    #             else:    
    #                 coordinaten = re.split(" ",bbox_co)
    # print('coordinaten',coordinaten)
    # return coordinaten

def schrijf_een_lijn(x,y,text_w,foto_naam,bbox_grootte):
    text_w.writelines(str(x) + ';' + str(y) + ';'+ foto_naam + ';' + str(bbox_grootte) + ";" +'\n')

def vraag_bboxen_toevoegen():
    bbox_toevoegen = input("bboxen toevoegen (ja,nee): ")
    # Note that in version 3, the print() function
    # requires the use of parenthesis.
    print("Is this what you just said?  ", bbox_toevoegen)
    zeker = input("Are you sure (+): ")
    while zeker != '+':  
        bbox_toevoegen = input("Opnieuw bboxen toevoegen (ja,nee): ")
        print("Is this what you just said? ", bbox_toevoegen)
        zeker = input("Are you sure (+): ")      
    return bbox_toevoegen

def index_gewenste_coordinaten():
    bbox_toevoegen = input("Welke plaats wil je opslaan: ")
    # Note that in version 3, the print() function
    # requires the use of parenthesis.
    print("Is this what you just said?  ", bbox_toevoegen)
    zeker = input("Are you sure (+): ")
    while zeker != '+':  
        bbox_toevoegen = input("Welke plaats wil je opslaan: ")
        print("Is this what you just said? ", bbox_toevoegen)
        zeker = input("Are you sure (+): ")      
    return bbox_toevoegen

def welke_coordinaten():
    bbox_toevoegen = input("welke coordinaten wil je (0,1,2,g): ")
    # Note that in version 3, the print() function
    # requires the use of parenthesis.
    print("Is this what you just said?  ", bbox_toevoegen)
    zeker = input("Are you sure (+): ")
    while zeker != '+':  
        bbox_toevoegen = input("welke coordinaten wil je (0,1,2,g): ")
        print("Is this what you just said? ", bbox_toevoegen)
        zeker = input("Are you sure (+): ")      
    return bbox_toevoegen

def goede_bboxen():
    i=1
    bbox_okee = input("ok,del,sommige: ")
    # Note that in version 3, the print() function
    # requires the use of parenthesis.
    print("Is this what you just said?  ", bbox_okee)
    zeker = input("Are you sure (+): ")
    while zeker != '+':  
        bbox_okee = input("ok,del,sommige: ")
        print("Is this what you just said? ", bbox_okee)
        zeker = input("Are you sure (+): ")      
    return bbox_okee

def bbox_toevoegen(image,blad,bbox_grootte):
    coordinaten = [0]
    while len(coordinaten) != 2:
        bbox_co = input("Coordinaten nieuwe bbox: ")
        # Note that in version 3, the print() function
        # requires the use of parenthesis.
        print("Is this what you just said? ", bbox_co)
        zeker = input("Are you sure (+,o): ")
        while zeker != '+':   
            if zeker == 'o':
                beeld_bboxen_met_h_b_af(image,blad,bbox_grootte)
                einde_click()
            bbox_co = input("Probeer coordinaten nieuwe box opnieuw: ")
            print("Is this what you just said? ", bbox_co)
            zeker = input("Are you sure: ")
   
        coordinaten = re.split(" ",bbox_co)
        print('coordinaten',coordinaten)
    return coordinaten

fig = plt.figure(figsize=(15,9)) 
coords = []
def onclick(event):
    # global ix, iy
    ix, iy = event.xdata, event.ydata
    print('x,y',ix,iy)
    global coords
    coords.append([ix, iy])
    print('coords',coords)
    
    if len(coords) == 3:
        fig.canvas.mpl_disconnect(cid)
    print('p')
    return coords

cid = fig.canvas.mpl_connect('button_press_event', onclick)


def overloop_plantsoort(planten_soort,bbox_grootte,text_w,aantal_mondjes,data_path_foto):
    i=0
    print('aantal',aantal_mondjes)  
    for blad in planten_soort:        
        image, blad_aug = augmentatie(blad,data_path_foto,[False,False,0],False)

        image_goed = 'op'

        while image_goed == 'op':
            beeld_bboxen_met_h_b_af(image,blad,bbox_grootte)            
            einde_click()            
            bbox_okee = input("Wil je bbox_grootte aanpassen? (ja,nee): ")
            if bbox_okee == 'ja':  
                bbox_grootte = input("Nieuwe bbox grootte: ")    
                zeker = input("Are you sure (+): ")
                while zeker != '+':  
                    bbox_grootte = input("Nieuwe bbox grootte: ")    
                    zeker = input("Are you sure (+): ")                
                bbox_grootte = int(bbox_grootte)   
            image_goed = goede_bboxen()
        
        een_fout = True
        aantal_fouten = 0
        while een_fout == True:
            een_fout = False
            try:
                if image_goed == 'ok':
                    print('hier')
                    for lijn in blad['bboxes']:
                        text_w.writelines(str(lijn['x']) + ';' + str(lijn['y']) + ';'+ blad['filepath'] + ';' + str(bbox_grootte) + ";" +'\n')
                    #     schrijf_een_lijn(lijn['x'],lijn['y'],text_w,blad['filepath'],bbox_grootte)
                elif image_goed == 'del':
                    print('foto wordt verwijderd')
                elif image_goed == 'sommige' or image_goed == 's':
                    while image_goed == 'sommige' or image_goed == 's':
                        # Hier als je maar enkele wilt veranderen
                        beeld_bboxen_met_h_b_af(image,blad,bbox_grootte)
                        coordinaten = []
                        coordinaten = begin_click()
                        aantal_aanpassingen = 0
                        while aantal_aanpassingen < len(coordinaten):
                            x_origineel = coordinaten[aantal_aanpassingen][0]
                            y_origineel = coordinaten[aantal_aanpassingen][1]
                            for bbox in blad['bboxes']:
                                verschil_x = abs(bbox['x']-x_origineel)
                                verschil_y = abs(bbox['y']-y_origineel)
                                if verschil_x<20 and verschil_y<20:
                                    bbox['x'] = coordinaten[aantal_aanpassingen+1][0]
                                    bbox['y'] = coordinaten[aantal_aanpassingen+1][1] 
                            aantal_aanpassingen += 2
                        einde_click()
                        image_goed = goede_bboxen()
                    # Voeg hier de hele lijst toe
                    for lijn in blad['bboxes']:
                        text_w.writelines(str(lijn['x']) + ';' + str(lijn['y']) + ';'+ blad['filepath'] + ';' + str(bbox_grootte) + ";" +'\n')
            except:
                print("PAS OP, foutje gemaakt")                  
                if aantal_fouten<3:
                    een_fout = True
                else:
                    een_fout = False

                einde_click()
                aantal_fouten += 1
                            

        # else:
        #     for bbox in blad['bboxes']:
        #         x,y = x_y_box(image,bbox,bbox_grootte)             
        #         schrijf_een_lijn(x,y,text_w,blad['filepath'],bbox_grootte)
        
        bboxen_toevoegen = vraag_bboxen_toevoegen()

        while bboxen_toevoegen == 'ja':
            # beeld_bboxen_met_h_b_af(image,blad,bbox_grootte)
            global coords
            beeld_bboxen_met_h_b_af(image,blad,bbox_grootte)
            # img = geef_bboxen_h_b_terug(image,blad,bbox_grootte)
            
            # plt.imshow(img)
            # plt.title(blad['filepath'])    
            # plt.grid()
            # plt.show()

            try:                
                coordinaten = []
                coordinaten = begin_click_toevoegen()
                print('coordinatne',coordinaten)
                for co in coordinaten:
                    print('tt')
                    blad['bboxes'].append({'x':int(co[0]),'y':int(co[1])})
                    schrijf_een_lijn(int(co[0]),int(co[1]),text_w,blad['filepath'],bbox_grootte)
                
                einde_click()
            except:
                print('fout bij het toevoegen')
            # # elif gewenst == '':
            # #     ge = 1
            # #     x,y = coords[ge][0] , coords[ge][1]
            # #     print('x,y: ',x,y)          
            # #     schrijf_een_lijn(x,y,text_w,blad['filepath'],bbox_grootte

            # print('coords',coords)
            # del coords[:]
            # print('coords',coords)
            # fig = plt.figure(figsize=(15,9))
            # cid = fig.canvas.mpl_connect('button_press_event', onclick)
            # # x,y = bbox_toevoegen(image,blad,bbox_grootte)   
            # # print('x,y: ',x,y)          
            # # schrijf_een_lijn(x,y,text_w,blad['filepath'],bbox_grootte)
        
            bboxen_toevoegen = vraag_bboxen_toevoegen()


def regel_x(x_snijden,all_data,counted_data,data_path_nieuwe_foto,data_path_foto,data_path_text,zet_naar_grijswaarde,img_norm,training):
    """ Zal alles regelen:

    
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
    input_user = True      # Of we zelf de grootte van de mondjes willen bepalen

    text_path = data_path_nieuwe_foto + data_path_text
    text_w = open(text_path, "w+")
    planten_soort = []
   
    aantal_lijnen=0
    
    for lijn in counted_data:

        aantal_mondjes = lijn['count']  
        print('aantal_mondjes',aantal_mondjes)    
        print('all_data',all_data)  
        print('lijn',lijn)            
        planten_soort = ophalen_planten(all_data,lijn)
        bbox_grootte = 120
        if input_user == True:
            
            print('plant_soort',planten_soort)  
            print('data_path_foto',data_path_foto)  
            bbox_grootte = vind_zijde_bbox(planten_soort,data_path_foto)
            fig = plt.figure(figsize=(15,9))
        overloop_plantsoort(planten_soort,bbox_grootte,text_w,aantal_mondjes,data_path_foto)
            
        aantal_lijnen += 1
        #angle = 45
            

    text_w.close()


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
    training = True
    x_snijden = 200
#### Training weinig huidmondjes
    # lijst = 'Anthonotha_weinig_huidmondjes.txt'
#### TRAINING DATA
    # lijst = '20180713_Anthonotha-Trilepsium_set1.txt'
    # data_path = '../data-20200402T082725Z-001/data/training_set/'
    # path_nieuwe_foto = '../data-20200402T082725Z-001/data/augmentatie/training/in_stukken_test/'
    # data_path_text = 'data_in_stukken_test.txt'
#### Nieuwe set
    lijst = 'deel_1.txt' # Naam van text file waar we de data uit halen + data path
    extra_path_lijst = ''
    data_path = '../data-20200402T082725Z-001/data/augmentatie/training/text_file/test/' # Algemene standaard data path. Waar de afbeeldingen staan opgeslaan 
    path_nieuwe_foto = '../data-20200402T082725Z-001/data/augmentatie/training/text_file/test/t/'
    data_locatie_foto = '../data-20200402T082725Z-001/data/20200427_Trainingset/'
  
    # data_path_text = '20200427_Trainingset_deel_1_5.txt' # Naam van het nieuwe text file
    data_path_text = lijst
#### Validatie data    
    # lijst = 'validation.txt'
    # data_path = '../data-20200402T082725Z-001/data/validation/samen_gezet/'
    # path_nieuwe_foto = '../data-20200402T082725Z-001/data/augmentatie/validation/links_rechts/'
    # data_path_text = 'validation_augmentatie.txt'

    data_path_lijst = data_path+extra_path_lijst+lijst
    

    array_ingelezen_lijst = inlezen_lijst(data_path_lijst)
    # print('array_ingelezen_lijst',array_ingelezen_lijst)
    print('data_path',data_path)
    all_data = vind_bbox(array_ingelezen_lijst,data_locatie_foto)
    # print('all_data',all_data)
    if stomata_200 == True:
        counted_data = count_stomata_eenmalig(array_ingelezen_lijst)
        # print('counted_data',counted_data)
        regel_x(x_snijden,all_data,counted_data,path_nieuwe_foto,data_locatie_foto,data_path_text,zet_naar_grijswaarde,img_norm,training)

   

main()


""""
Documentatie
    img_info: {'filename_oud': 'Gilbertiodendron dewevrei_G5-11_blad3-vlak2.jpg', 'filename_nieuw': 'LB_H_V_1_Gilbertiodendron dewevrei_G5-11_blad3-vlak2.jpg', 
                        'uitsnij_co': {'x1': 0, 'y1': 0, 'x2': 600, 'y2': 800}, 'bboxes': [{'x': 348, 'y': 688}, {'x': 379, 'y': 163}, {'x': 200, 'y': 65}]}

    blad {'filepath': 'Ipomaea eriocarpa Faulkner 2718_blad1-vlak1.jpg', 'bboxes': [{'x': 303, 'y': 279}, {'x': 768, 'y': 307}, {'x': 434, 'y': 510}, {'x': 118, 'y': 577}, {'x': 74, 'y': 894}, {'x': 597, 'y': 970}, {'x': 917, 'y': 1129}, {'x': 1240, 'y': 1157}, {'x': 1180, 'y': 420}, {'x': 851, 'y': 546}, {'x': 1546, 'y': 284}]}

    lijn van counted_data
    lijn:  {'plantnaam': 'Nepenthes veitchii', 'count': 7, 'filepath': ['Nepenthes veitchii_1990-928DODO_leaf1-field1.jpg', 'Nepenthes veitchii_1990-928DODO_leaf1-field2.jpg', 'Nepenthes veitchii_1990-928DODO_leaf1-field3.jpg']}
Hoe dubbelchecken:
"""