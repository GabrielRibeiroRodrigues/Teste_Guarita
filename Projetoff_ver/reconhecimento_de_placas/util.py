import string
import easyocr
import pandas as pd



reader = easyocr.Reader(['en'], gpu=False)


#Conversões de caracteres nao esperados para esperados se estiver na lista
dict_char_to_int = {'O': '0',
                    'I': '1',
                    'J': '3',
                    'A': '4',
                    'G': '6',
                    'S': '5',
                    }

dict_int_to_char = {'0': 'O',
                    '1': 'I',
                    '3': 'J',
                    '4': 'A',
                    '6': 'G',
                    '5': 'S',
                    'H': 'W'}


def write_csv(results, output_path):
    with open(output_path, 'w') as f:
        f.write('{},{},{},{},{}\n'.format('frame_nmr', 'car_id',
                                                'license_plate_bbox_score', 'license_number',
                                                'license_number_score'))

        for frame_nmr in results.keys():
            for car_id in results[frame_nmr].keys():
                print(results[frame_nmr][car_id])
                if 'car' in results[frame_nmr][car_id].keys() and \
                   'placa' in results[frame_nmr][car_id].keys() and \
                   'text' in results[frame_nmr][car_id]['placa'].keys():
                    f.write('{},{},{},{},{}\n'.format(frame_nmr,
                                                            car_id,
                                                            
                                                            results[frame_nmr][car_id]['placa']['bbox_score'],
                                                            results[frame_nmr][car_id]['placa']['text'],
                                                            results[frame_nmr][car_id]['placa']['text_score'])
                            )
        f.close()


import re

def license_complies_format(text):
      
    if len(text) != 7:
        return False
    
    
    

    # Teste
    if (text[0] in string.ascii_uppercase or text[0] in dict_int_to_char.keys()) and \
       (text[1] in string.ascii_uppercase or text[1] in dict_int_to_char.keys()) and \
       (text[2] in ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9'] or text[2] in dict_char_to_int.keys()) and \
       (text[3] in ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9'] or text[3] in dict_char_to_int.keys()) and \
       (text[4] in string.ascii_uppercase or text[4] in dict_int_to_char.keys()) and \
       (text[5] in string.ascii_uppercase or text[5] in dict_int_to_char.keys()) and \
       (text[6] in string.ascii_uppercase or text[6] in dict_int_to_char.keys()):
        return True
     

    #Formato padrão
    if (text[0] in string.ascii_uppercase or text[0] in dict_int_to_char.keys()) and \
       (text[1] in string.ascii_uppercase or text[1] in dict_int_to_char.keys()) and \
       (text[2] in string.ascii_uppercase or text[2] in dict_int_to_char.keys()) and \
       (text[3] in ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9'] or text[3] in dict_char_to_int.keys()) and \
       (text[4] in ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9'] or text[4] in dict_char_to_int.keys()) and \
       (text[5] in ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9'] or text[5] in dict_char_to_int.keys()) and \
       (text[6] in ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9'] or text[6] in dict_char_to_int.keys()):
        return True
    #Formato Mercosul
    if (text[0] in string.ascii_uppercase or text[0] in dict_int_to_char.keys()) and \
       (text[1] in string.ascii_uppercase or text[1] in dict_int_to_char.keys()) and \
       (text[2] in string.ascii_uppercase or text[2] in dict_int_to_char.keys()) and \
       (text[3] in ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9'] or text[3] in dict_char_to_int.keys()) and \
       (text[4] in string.ascii_uppercase or text[4] in dict_int_to_char.keys()) and \
       (text[5] in ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9'] or text[5] in dict_char_to_int.keys()) and \
       (text[6] in ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9'] or text[6] in dict_char_to_int.keys()):
        return True
    

    return False

def format_license(text):
    license_plate_ = ''

    # O mapeamento agora depende da posição dos caracteres
    for j in range(7):
        # Se estivermos nas posições das letras (para ambos os formatos)
        if j in [0, 1, 2]:
            # Tentar mapear o caractere como uma letra, usando o dicionário de conversão de números para letras
            if text[j] in dict_int_to_char:
                license_plate_ += dict_int_to_char[text[j]]
            else:
                license_plate_ += text[j]

        # Se estivermos nas posições que podem ser números (para ambos os formatos)
        elif j == 3:
            # Posição 3 pode ser um número em ambos os formatos
            if text[j] in dict_char_to_int:
                license_plate_ += dict_char_to_int[text[j]]
            else:
                license_plate_ += text[j]

        # Posição 4 pode ser uma letra (no formato `AAA1A23`) ou um número (no formato `AAA1234`)
        elif j == 4:
            if text[j] in string.ascii_uppercase or text[j] in dict_int_to_char:
                # Mapear letra para número, se aplicável
                if text[j] in dict_int_to_char:
                    license_plate_ += dict_int_to_char[text[j]]
                else:
                    license_plate_ += text[j]
            elif text[j] in dict_char_to_int:
                # Mapear número para letra, se aplicável
                license_plate_ += dict_char_to_int[text[j]]
            else:
                license_plate_ += text[j]

        # Posições 5 e 6 sempre podem ser números (em ambos os formatos)
        elif j in [5, 6]:
            if text[j] in dict_char_to_int:
                license_plate_ += dict_char_to_int[text[j]]
            else:
                license_plate_ += text[j]

    return license_plate_


#Lê os caracteres que estão na placa
def read_license_plate(license_plate_crop):
    detections = reader.readtext(license_plate_crop)

    for detection in detections:
        bbox, text, score = detection

        text = text.upper().replace(' ', '')

        if license_complies_format(text):
            return format_license(text), score

    return None, None


def get_car(placa, vehicle_track_ids):
    x1, y1, x2, y2, score, class_id = (*placa, None)

    foundIt = False
    for j in range(len(vehicle_track_ids)):
        xcar1, ycar1, xcar2, ycar2, car_id = vehicle_track_ids[j]

        if x1 > xcar1 and y1 > ycar1 and x2 < xcar2 and y2 < ycar2:
            car_indx = j
            foundIt = True
            break

    if foundIt:
        return vehicle_track_ids[car_indx]

    return -1, -1, -1, -1, -1

def carrega_placas_registradas(csv_path):
    placas_reg = pd.read_csv(csv_path)
    placas_dict = {}
    for index, row in placas_reg.iterrows():
          placas_dict[row['placa']] = {'proprietario': row['proprietario'], 'veiculo': row['veiculo'],'cor': row['cor']}
    return placas_dict


