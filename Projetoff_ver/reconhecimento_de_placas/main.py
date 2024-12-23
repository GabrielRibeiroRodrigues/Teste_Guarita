from ultralytics import YOLO
import cv2
import numpy as np
import matplotlib.pyplot as plt
import keyboard  
from sort.sort import Sort
from util import ler_carro, ler_placas, verificar_camera, salvar_no_postgres, salvar_registro_frequencia, verificar_placa_registrada
import psycopg2
from datetime import datetime
import os

data_e_hora_atuais = datetime.now()
data_e_hora_em_texto = data_e_hora_atuais.strftime('%d/%m/%Y %H:%M:%S')

results = {}
mot_tracker = Sort()

conexao = psycopg2.connect(
    dbname="pci_transito",
    user="postgres",
    password="123456",
    host="localhost",
    port="5432"
)
cursor = conexao.cursor()

detector_carro = YOLO('yolov8n.pt')
detector_placa = YOLO("C:\\Users\\12265587630\\Desktop\\best (4).pt")
cap = cv2.VideoCapture("C:\\Users\\12265587630\\Desktop\\paulo\\fff.mp4")
porta = 3
veiculos = [2, 3, 5, 7]  
confianca_detectar_carro = 0.0  
confianca_gravar_texto = 0.0
frame_nmr = -1
ret = True
intervalo_frames = 1 
intervalo_espera = 30
registro_placas = {}

output_folder = "C:\\Users\\12265587630\\Desktop\\Projetoff_ver\\img_placas_detectadas"
if not os.path.exists(output_folder):
    os.makedirs(output_folder)
    output_folder = "C:\\Users\\12265587630\\Desktop\\Projetoff_ver\\img_placas_detectadas"
if not os.path.exists(output_folder):
    os.makedirs(output_folder)
plt.ion()  
fig, ax = plt.subplots()


while ret:
    for i in range(intervalo_frames):
        frame_nmr += 1
        ret, frame = cap.read()
        if not ret or frame is None:
            print(f"Não foi possível ler o frame {frame_nmr}.")
            break
    if frame is None:
        continue
    results[frame_nmr] = {}

    # Detecção de veículos usando o modelo de veículos
    detections_veiculos = detector_carro(frame)[0]
    veiculos_detectados = []
    for detection in detections_veiculos.boxes.data.tolist():
        x1, y1, x2, y2, confianca_atual, class_id = detection
        if confianca_atual >= confianca_detectar_carro and int(class_id) in veiculos:
            veiculos_detectados.append([x1, y1, x2, y2, confianca_atual])
    print(f"Frame {frame_nmr} - Veículos detectados: {veiculos_detectados}")

    # Rastrear veículos
    if veiculos_detectados:
        track_ids = mot_tracker.update(np.asarray(veiculos_detectados))
    else:
        track_ids = []
        print(f"Frame {frame_nmr} - Nenhum veículo detectado")

    # Detecção de placas usando o modelo de placas
    detections_placas = detector_placa(frame)[0]
    placas_detectadas = []
    for detection in detections_placas.boxes.data.tolist():
        x1, y1, x2, y2, confianca_atual, class_id = detection
        if confianca_atual >= confianca_detectar_carro:
            placas_detectadas.append([x1, y1, x2, y2, confianca_atual])
    print(f"Frame {frame_nmr} - Placas detectadas: {placas_detectadas}")

    # Atribuir as placas aos veículos detectados
    for placa in placas_detectadas:
        x1, y1, x2, y2, confianca_atual = placa
        print(f"Placa detectada no frame {frame_nmr} com coordenadas: ({x1}, {y1}), ({x2}, {y2}) e confiança {confianca_atual}")

        # Verificar qual veículo corresponde à placa
        xcar1, ycar1, xcar2, ycar2, car_id = ler_carro(placa, track_ids)

        if car_id != -1:
            # Verificação de limites
            if (0 <= x1 < frame.shape[1] and 0 <= x2 < frame.shape[1] and
                0 <= y1 < frame.shape[0] and 0 <= y2 < frame.shape[0]):
                # Recortar a placa para processamento
                placa_carro_crop = frame[int(y1):int(y2), int(x1):int(x2)]
                placa_carro_crop_gray = cv2.cvtColor(placa_carro_crop, cv2.COLOR_BGR2GRAY)
                _, placa_carro_crop_thresh = cv2.threshold(placa_carro_crop_gray, 64, 255, cv2.THRESH_BINARY_INV)

                # Ler o texto da placa
                texto_detectado, confianca_texto_detectado = ler_placas(placa_carro_crop_thresh)
                print(f"Texto da placa detectado: {texto_detectado}, Confiança: {confianca_texto_detectado}")
                if(texto_detectado is None):
                    i = i + 1
                    filename = os.path.join(output_folder, f"{i}.jpg")
                    i = i + 1
                    if not os.path.isfile(filename):
                      cv2.imwrite(filename, placa_carro_crop)
                if texto_detectado is not None and confianca_texto_detectado > confianca_gravar_texto:
                    salvar_no_postgres(frame_nmr, car_id, texto_detectado, confianca_texto_detectado)
                    
                    # Verificar se a placa já está registrada
                    
                    info = verificar_placa_registrada(texto_detectado, cursor)
                    registro = verificar_camera(porta,cursor)
                    if info:
                        salvar_registro_frequencia(data_e_hora_em_texto, texto_detectado, registro)

                        print(f"A placa {texto_detectado} já está registrada.")
                        print(f"Proprietário: {info['proprietario']}, Veículo: {info['veiculo']}, Cor do Veículo: {info['cor']}")
                    else:
                        print(f"A placa {texto_detectado} não está registrada.")

                    results[frame_nmr][car_id] = {
                        'car': {'bbox': [xcar1, ycar1, xcar2, ycar2]},
                        'placa': {
                            'bbox': [x1, y1, x2, y2],
                            'text': texto_detectado,
                            'bbox_score': confianca_atual,
                            'text_score': confianca_texto_detectado
                        }
                    }
                    
            else:
                print(f"Coordenadas de recorte fora dos limites: ({x1}, {y1}), ({x2}, {y2})")
        else:
            print("Nenhum veículo correspondente à placa foi detectado.")

   
    ax.clear()
    ax.imshow(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))  
    ax.axis('off')  

    # Desenhar bounding boxes para veículos detectados
    for veh in veiculos_detectados:
        x1, y1, x2, y2, score = veh
        rect = plt.Rectangle((x1, y1), x2 - x1, y2 - y1, fill=False, color='blue', linewidth=2)
        ax.add_patch(rect)

    # Desenhar bounding boxes para placas detectadas
    for placa in placas_detectadas:
        x1, y1, x2, y2, score = placa
        rect = plt.Rectangle((x1, y1), x2 - x1, y2 - y1, fill=False, color='red', linewidth=2)
        ax.add_patch(rect)

    plt.pause(0.00001)  # Pausa para atualizar a visualização

    
    if keyboard.is_pressed('q'):
        break  

cap.release()
plt.close(fig)


