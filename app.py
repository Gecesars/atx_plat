import os
#import folium
import requests
import json
#import itur
from math import radians, cos, sin, asin, sqrt, degrees
from sklearn.linear_model import LinearRegression
from scipy.constants import c
import math
import pycraf
import astropy
from pycraf import pathprof,antenna, conversions as cnv
from astropy import units as u
from pycraf.pathprof import SrtmConf
import numpy as np
#import geopandas as gpd
import matplotlib
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from PIL import Image
from reportlab.lib.utils import ImageReader
#import boto3
matplotlib.use('Agg') 
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.colors import Normalize
from matplotlib.cm import ScalarMappable
from matplotlib.colors import ListedColormap
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.table import Table
from shapely.geometry import Point, Polygon
from geopy.distance import geodesic
from geopy.point import Point
#import rasterio
import geojson
import io
import base64
#from rasterio.mask import mask
from flask import Flask, request, redirect, render_template, url_for, jsonify, flash,current_app, send_file, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
#from werkzeug.security import generate_password_hash, check_password_hash
import googlemaps
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError
# Importar db e login_manager do arquivo de extensões
from extensions import db, login_manager
# Importação do modelo User
from user import User
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
#import webbrowser
from threading import Timer
from astropy.config import get_config_dir
from flask import Flask
from flask_cors import CORS
#import gzip
from scipy.integrate import simpson
from scipy.ndimage import gaussian_filter1d
from scipy.interpolate import interp1d,CubicSpline
#from icecream import ic

# Restante da aplicação ...







def create_app():
    app = Flask(__name__)
    CORS(app)
    app.config['database'] = 'teste'
    # app.secret_key = 'uma_chave_secreta_muito_segura'
    # SECRET_KEY = 'uma_chave_secreta_muito_segura'
    app.secret_key = os.environ.get('SECRET_KEY')
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'minha_chave_secreta')
    # Configuração do SQLAlchemy
    uri = os.getenv("DATABASE_URL", 'sqlite:///users.db')
    if uri.startswith("postgres://"):
        uri = uri.replace("postgres://", "postgresql://", 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = uri
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Inicializar extensões com o app
    db.init_app(app)
    Migrate(app, db)
    login_manager.init_app(app)
  #  AIzaSyA4jwMwkN9aIuRvxV498PsmV_dJnpWQ1TY
    gmaps = googlemaps.Client(key='AIzaSyA4jwMwkN9aIuRvxV498PsmV_dJnpWQ1TY')
    api_key = "AIzaSyA4jwMwkN9aIuRvxV498PsmV_dJnpWQ1TY"
    google_api_key = "AIzaSyA4jwMwkN9aIuRvxV498PsmV_dJnpWQ1TY"
     #inicializa o diretório temporário para armazenar os arquivos hgt


    # Definir o carregador de usuário para Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))



    

    # Rotas
    @app.route('/')
    def inicio():
        return render_template('inicio.html')

    @app.route('/sensors')
    def sensors():
        return render_template('sensors2.html')
    # Rotas
    @app.route('/index')
    def index():
        return render_template('index.html')

    @app.route('/antena')
    @login_required
    def antena():
        return render_template('antena.html')

    @app.route('/calcular-cobertura')
    @login_required  # Se necessário, exija que o usuário esteja logado para acessar esta página
    def calcular_cobertura():
        return render_template('calcular_cobertura.html')

    @app.route('/save-map-image', methods=['POST'])
    def save_map_image():
        data = request.get_json()
        image_data = data['image']
        user = current_user

        # Decodificar a imagem base64 e salvar no banco de dados
        if image_data:

            image_data = base64.b64decode(image_data.split(',')[1])
            user.cobertura_img = image_data
            db.session.commit()

        return jsonify({"message": "Imagem salva com sucesso"})


    # Defina o diretório base para as imagens
    BASE_DIR = os.path.join(os.getcwd(), 'static', 'SOLID_PRT_ASM', 'PNGS')

    @app.route('/list_files/<path:folder>', methods=['GET'])
    def list_files(folder):
        folder_path = os.path.join(BASE_DIR, folder)
        if os.path.exists(folder_path) and os.path.isdir(folder_path):
            files = [f for f in os.listdir(folder_path) if f.lower().endswith('.png')]
            return jsonify(files)
        else:
            return jsonify([]), 404

    @app.route('/static/SOLID_PRT_ASM/PNGS/<path:filename>', methods=['GET'])
    def serve_file(filename):
        return send_from_directory(BASE_DIR, filename) 

    @app.route('/calculos-rf')
    @login_required  # Se necessário, exija que o usuário esteja logado para acessar esta página
    def calculos_rf():
        return render_template('calculos-rf.html')

    @app.route('/gerar-relatorio', methods=['GET'])
    @login_required
    def download_report():
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter
        
        # Função para adicionar texto ao PDF
        def add_text(text, y_offset=20):
            nonlocal y_position
            c.drawString(50, y_position, text)
            y_position -= y_offset

        # Função para adicionar imagens
        def add_image(image_data, y_offset=200, image_width=600):
            nonlocal y_position
            if image_data:
                image_stream = io.BytesIO(image_data)
                try:
                    img = Image.open(image_stream)
                    img_reader = ImageReader(img)
                    # Ajustar largura e altura mantendo a proporção
                    aspect_ratio = img.width / img.height
                    image_height = image_width / aspect_ratio

                    # Centralizar a imagem na página
                    image_x = (width - image_width) / 2
                    image_y = y_position - image_height - 20  # 20 é a margem adicional

                    # Verificar se a nova posição y está abaixo do limite da página
                    if image_y < 50:  # Supondo uma margem inferior de 50 unidades
                        c.showPage()  # Cria uma nova página
                        y_position = height - 50  # Restaurar a posição inicial no topo da nova página
                        image_y = y_position - image_height - 20  # Recalcular a posição y da imagem na nova página

                    c.drawImage(img_reader, image_x, image_y, width=image_width, height=image_height, preserveAspectRatio=True, mask='auto')
                    y_position = image_y - 10  # Atualizar a posição y para o próximo conteúdo
                except Exception as e:
                    print(f"Erro ao adicionar imagem: {e}")
                finally:
                    image_stream.close()



        user = current_user
        y_position = height - 50  # Iniciar do topo da página

        # Adicionar campos de texto
        fields = [
            f"Frequência: {user.frequencia} MHz",
            f"Altura do centro de fase da antena: {user.tower_height} m",
            f"Total de Perdas: {user.total_loss} dB",
            f"Potência de Transmissão: {user.transmission_power} Watts",
            f"Ganho da Antena: {user.antenna_gain} dBi",
            f"Direção da Antena: {user.antenna_direction}°",
            f"Tilt Elétrico: {user.antenna_tilt}°",
            f"Latitude: {user.latitude}",
            f"Longitude: {user.longitude}",
            f"Serviço: {user.servico}",
            f"Notas: {user.notes or 'Nenhuma nota disponível.'}"
        ]

        for field in fields:
            add_text(field, 15)  # Menor espaçamento vertical entre campos de texto

        # Adicionar imagens
        add_image(user.antenna_pattern_img_dia_H, 100)
        add_image(user.antenna_pattern_img_dia_V, 100)
        add_image(user.cobertura_img, 100)
        add_image(user.perfil_img, 100)

        # Finalizar o PDF
        c.showPage()
        c.save()
        buffer.seek(0)

        return send_file(buffer, as_attachment=True, download_name='relatorio.pdf', mimetype='application/pdf')


    @app.route('/calculate-distance', methods=['POST'])
    def calculate_distance():
        # Substitua pela sua chave da API do Google
      #  google_api_key = os.environ.get('GOOGLE_MAPS_API_KEY')
    
        data = request.get_json()
        start = data['start']
        end = data['end']
    
        start_str = f"{start['lat']},{start['lng']}"
        end_str = f"{end['lat']},{end['lng']}"
    
        # URL da Google Maps Distance Matrix API
        url = "https://maps.googleapis.com/maps/api/distancematrix/json"
    
        # Parâmetros para a requisição à API
        params = {
           'origins': start_str,
           'destinations': end_str,
           'key': google_api_key
        }
    
        response = requests.get(url, params=params)
    
        if response.status_code == 200:
            distance_matrix_data = response.json()
        
            # Verifique a resposta da API e extraia a distância
            if distance_matrix_data['rows'][0]['elements'][0]['status'] == 'OK':
                distance = distance_matrix_data['rows'][0]['elements'][0]['distance']['value']  # Distância em metros
                return jsonify({'distance': distance})
            else:
                return jsonify({'error': 'Não foi possível calcular a distância.'}), 400
        else:
            return jsonify({'error': 'Falha na requisição à Google Maps Distance Matrix API.'}), response.status_code

    @app.route('/mapa')
    @login_required
    def mapa():
        # Verifica se o usuário logado tem coordenadas definidas
        if current_user.latitude is None or current_user.longitude is None:
            # Se não houver coordenadas, redireciona com uma mensagem de erro
            flash('Por favor, defina a posição da torre primeiro.', 'error')
            return redirect(url_for('alguma_rota_para_definir_coordenadas'))
        else:
            # Se houver coordenadas, prepara o mapa
            start_coords = {
                "lat": current_user.latitude,
                "lng": current_user.longitude
            }
            return render_template('mapa.html', start_coords=start_coords)


    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            # Processa o login
            username = request.form['username']
            password = request.form['password']
            user = User.query.filter_by(username=username).first()

            if user is None:
                error = 'Usuário não existe.'
                return render_template('index.html', error=error)
            elif not user.check_password(password):
                error = 'Senha incorreta.'
                return render_template('index.html', error=error)

            login_user(user)  # flask-login
            return redirect(url_for('home'))
    
        # Se for uma solicitação GET, renderiza a página de login
        return render_template('index.html')

    


    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if request.method == 'POST':
            username = request.form['username']
            email = request.form['email']
            password = request.form['password']

            # Verifica se o nome de usuário ou o e-mail já existem
            existing_user = User.query.filter_by(username=username).first()
            existing_email = User.query.filter_by(email=email).first()

            if existing_user:
                return render_template('register.html', error="Usuário já existe.")
            if existing_email:
                return render_template('register.html', error="E-mail já cadastrado.")

            # Se não existir, cria o novo usuário
            new_user = User(username=username, email=email)
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()

            return redirect(url_for('index'))

        return render_template('register.html')


    @app.route('/home')
    @login_required
    def home():
        return render_template('home.html')




    
    @app.route('/map')
    def map_view():
        start_coords = (-23.550520, -46.633308)  # Example coordinates
        folium_map = folium.Map(location=start_coords, zoom_start=12)
    # Add any other configurations to the map as needed

    # The _repr_html_() method generates the necessary HTML to render the map
        map_html = folium_map._repr_html_()

    # Pass the map HTML directly to the template
        return render_template('map.html', map_html=map_html)


    # @app.route('/fetch-elevation', methods=['POST'])
    # def fetch_elevation():
        
    #     path_data = request.json['path']
    #     path_str = '|'.join([f"{lat},{lng}" for lat, lng in path_data])
    #     url = f"https://maps.googleapis.com/maps/api/elevation/json?path={path_str}&samples=256&key={google_api_key}"

    #     response = requests.get(url)
    #     if response.status_code == 200:
    #         elevation_data = response.json()
    #         return jsonify(elevation_data)
    #     else:
    #         return jsonify({"error": "Failed to fetch elevation data"}), 500


    @app.route('/carregar_imgs', methods=['GET'])
    def carregar_imgs():
        user_id = current_user.id  # Asumindo que você está usando Flask-Login ou um sistema similar
        user = User.query.get(user_id)
        direction = user.antenna_direction
        tilt = user.antenna_tilt


        if user.antenna_pattern:
            file_content = user.antenna_pattern.decode('latin1')  # Decodifica o conteúdo binário salvo

           # ic('file content: ', file_content)
            # Processando o conteúdo do arquivo
            parts = file_content.split('999')
            horizontal_lines = parts[0].splitlines()[1:361]
            horizontal_data = np.array([float(line.split(',')[1].strip()) for line in horizontal_lines if line.strip()])

            vertical_lines = parts[1].splitlines()[3:]
            vertical_data_list = []
            for line in vertical_lines:
                if line.strip().startswith('180'):
                    break
                vertical_data_list.append(float(line.split(',')[1].strip()))

            vertical_data = np.array(vertical_data_list)

            # Interpolação e suavização dos dados horizontais
            original_azimutes = np.linspace(0, 360, len(horizontal_data), endpoint=False)
            #interpolated_azimutes = np.arange(0, 360, 0.1)
            #interpolated_data_h = np.interp(interpolated_azimutes, original_azimutes, horizontal_data)
            #smoothed_data_h = gaussian_filter1d(interpolated_data_h, sigma=2)

            # Interpolação e suavização dos dados verticais
            angles = np.linspace(-90, 90, len(vertical_data), endpoint=True)
            #new_angles = np.arange(-90, 90.1, 0.1)
            #interpolated_data_v = np.interp(new_angles, angles, vertical_data)
            #smoothed_data_v = gaussian_filter1d(interpolated_data_v, sigma=2)

            # Convertendo para E/Emax
            horizontal_data = 10 ** (horizontal_data / 20)
            vertical_data = 10 ** (vertical_data / 20)

            # Geração das imagens
            if direction != None:
                 # Calcula os dados rotacionados
                rotation_index = int(direction / (360 / len(horizontal_data)))
                rotated_data = np.roll(horizontal_data, rotation_index)
                horizontal_image_base64 = generate_dual_polar_plot(horizontal_data,rotated_data,direction)
            else: 
                horizontal_image_base64 = generate_polar_plot(horizontal_data)
            if tilt != None:
                vertical_image_base64 = generate_dual_rectangular_plot(vertical_data, angles, tilt)
            else:
                vertical_image_base64 = generate_rectangular_plot(vertical_data)
            return jsonify({
                'fileContent': file_content,
                'horizontal_image_base64': horizontal_image_base64,
                'vertical_image_base64': vertical_image_base64
            })

# Assegure-se de que generate_polar_plot e generate_rectangular_plot estão corretamente definidas

    @app.route('/salvar_diagrama', methods=['POST'])
    def salvar_diagrama():
        if 'file' not in request.files:
            return jsonify({'error': 'No file part'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400

        direction = request.form.get('direction')
        tilt = request.form.get('tilt')

        # Converte para float se possível, senão define como None
        try:
            direction = float(direction) if direction and direction.strip() != '' else None
        except ValueError:
            direction = None

        try:
            tilt = float(tilt) if tilt and tilt.strip() != '' else None
        except ValueError:
            tilt = None

        user_id = current_user.id
        user = User.query.get(user_id)
        if user:
            file_content = file.read()  # Lê o conteúdo do arquivo
            file.seek(0)  # Reposiciona o ponteiro do arquivo para o início

            # Salva também a direção e o tilt
            user.antenna_pattern = file_content
            user.antenna_direction = direction
            user.antenna_tilt = tilt

            db.session.commit()  # Salva o conteúdo no banco de dados
            return jsonify({'message': 'File and settings saved successfully'})
        else:
            return jsonify({'error': 'User not found'}), 404




    @app.route('/upload_diagrama', methods=['POST'])
    def gerardiagramas():

        tilt = request.form.get('tilt', type=float)


        direction = request.form.get('direction', type=float)  # Recebendo a direção do formulário

        file = request.files.get('file')
        if file:
            response = salvar_diagrama()
            if response.status_code != 200:
                # Se não conseguiu salvar, retorna a resposta da função salvar_diagrama
                  return response
            file_content = file.stream.read().decode('latin1')  # Lê o conteúdo como Latin1 para evitar erros de UTF-8 com caracteres especiais

            # Suponha que sejam os dados horizontais e verticais separados por "999"
            parts = file_content.split('999')
            horizontal_lines = parts[0].splitlines()[1:361]  # Supõe 360 linhas de dados horizontais
            horizontal_data = np.array([float(line.split(',')[1].strip()) for line in horizontal_lines if line.strip()])
           # horizontal_data = np.array([float(line.split(',')[1]) for line in parts[0].splitlines()[1:361] if line])
           # vertical_data = np.array([float(line.split(',')[1]) for line in parts[1].splitlines()[2:] if line])  # Começa duas linhas após "999"
           # Processando dados verticais
            vertical_lines = parts[1].splitlines()[3:]  # Começa depois das linhas '2, 181' e '0'
            vertical_data_list = []
            for line in vertical_lines:
                if line.strip().startswith('180'):  # Para ao encontrar a linha com '180'
                    break
                vertical_data_list.append(float(line.split(',')[1].strip()))

            vertical_data = np.array(vertical_data_list)


            original_points_h = len(horizontal_data)
            original_azimutes = np.linspace(0, 360, original_points_h, endpoint=False)



       

            # Aplicando suavização gaussiana


           # Gerar ângulos para interpolação V
            angles_v = np.linspace(-90, 90, len(vertical_data), endpoint=True)



            


            # Convertendo para E/Emax
            horizontal_data = 10 ** (horizontal_data / 20)
            vertical_data = 10 ** (vertical_data / 20)

            # Geração das imagens
            if direction == None:
                horizontal_image_base64 = generate_polar_plot(horizontal_data)
            else:
                rotation_index = int(direction / (360 / len(horizontal_data)))
                rotated_data = np.roll(horizontal_data, rotation_index)
                horizontal_image_base64 = generate_dual_polar_plot(horizontal_data, rotated_data, direction)


            if tilt == None:
               vertical_image_base64 = generate_rectangular_plot(vertical_data)
            #print(horizontal_image_base64)
            else:
                vertical_image_base64 = generate_dual_rectangular_plot(vertical_data, angles_v, tilt)


            return jsonify({
                'horizontal_image_base64': horizontal_image_base64,
                'vertical_image_base64': vertical_image_base64
            })

        return jsonify({'error': 'No file provided'}), 400




    def generate_polar_plot(data):
          # Converter azimutes de graus para radianos
        azimutes = np.linspace(0, 2 * np.pi, len(data))
        # Configurar o gráfico polar
        fig = plt.figure(figsize=(10, 10))
        ax = plt.subplot(111, polar=True)
        ax.plot(azimutes, data, label='Horizontal Radiation Pattern')

        # Adicionar cálculos e legendas de HPBW e Front Back Ratio
        threshold = 0.707
        indices = np.where(data <= threshold)[0]
        if len(indices) > 1:
            idx_first = indices[0]
            idx_last = indices[-1]
            ax.plot([azimutes[idx_first], azimutes[idx_first]], [0, data[idx_first]], 'k-', linewidth=2)
            ax.plot([azimutes[idx_last], azimutes[idx_last]], [0, data[idx_last]], 'k-', linewidth=2)
            angle_first_deg = np.degrees(azimutes[idx_first])
            angle_last_deg = np.degrees(azimutes[idx_last])
            hpbw = 360 - angle_last_deg + angle_first_deg
            ax.text(0.97, 0.99, f'HPBW: {hpbw:.2f}°', transform=ax.transAxes, horizontalalignment='left', verticalalignment='top', bbox=dict(facecolor='white', alpha=0.8))
            front_attenuation = data[np.argmin(np.abs(azimutes - 0))]
            back_attenuation = data[np.argmin(np.abs(azimutes - np.pi))]
            fbr = 20 * math.log10(front_attenuation / back_attenuation)

            ax.text(0.97, 0.95, f'F_B Ratio: {fbr:.2f} dB', transform=ax.transAxes, horizontalalignment='left', verticalalignment='top', bbox=dict(facecolor='white', alpha=0.8))
         # Calcular e adicionar legenda de Peak-to-Peak
        peak_to_peak_db = np.ptp(data)  # ptp() retorna a diferença entre o máximo e o mínimo
        ax.text(0.97, 0.91, f'Peak2Peak: {peak_to_peak_db:.2f} E/Emax', transform=ax.transAxes, horizontalalignment='left', verticalalignment='top', bbox=dict(facecolor='white', alpha=0.8))

        # Calcular e adicionar legenda de diretividade
        directivity_dB = calculate_directivity(data,'h')
            # Prepare data for saving
        data_table = [{"azimuth": f"{azimuth}°", "gain": f"{gain:.2f}"} for azimuth, gain in zip(azimutes, data)]

        # Save the data to the database
        current_user.antenna_pattern_data_h = json.dumps(data_table)
        db.session.commit()
        ax.text(0.97, 0.87, f'Directivity: {directivity_dB:.2f} dB', transform=ax.transAxes, horizontalalignment='left', verticalalignment='top', bbox=dict(facecolor='white', alpha=0.8))

        # Configurações adicionais do gráfico
        ax.set_theta_zero_location('N')  # Norte como 0 graus
        ax.set_theta_direction(-1)  # Direção horária
        ax.set_title('E/Emax')
        plt.ylim(0, 1)
        plt.grid(True)

         # Salva a figura em um buffer em memória e codifica em base64
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png', bbox_inches='tight')
        img_buffer.seek(0)
        current_user.antenna_pattern_img_dia_H = img_buffer.getvalue()
        db.session.commit()
        img_buffer.seek(0)
        img_base64 = base64.b64encode(img_buffer.getvalue()).decode('utf-8')
        img_buffer.close()
        plt.close(fig)
        return img_base64

    def generate_dual_polar_plot(original_data, rotated_data, direction):
        azimutes = np.linspace(0, 2 * np.pi, len(original_data))

        fig = plt.figure(figsize=(10, 10))
        ax = plt.subplot(111, polar=True)
        ax.plot(azimutes, original_data, linestyle='dashed', color='red', label='Original Pattern')
        ax.plot(azimutes, rotated_data, color='blue', label=f'Rotated Pattern to {direction}°')

        # Adicionar cálculos e legendas como na função original
        threshold = 0.707
        indices = np.where(original_data <= threshold)[0]
        if len(indices) > 1:
            idx_first = indices[0]
            idx_last = indices[-1]
            ax.plot([azimutes[idx_first], azimutes[idx_first]], [0, original_data[idx_first]], 'k-', linewidth=2)
            ax.plot([azimutes[idx_last], azimutes[idx_last]], [0, original_data[idx_last]], 'k-', linewidth=2)
            angle_first_deg = np.degrees(azimutes[idx_first])
            angle_last_deg = np.degrees(azimutes[idx_last])
            hpbw = 360 - angle_last_deg + angle_first_deg
            ax.text(0.97, 0.99, f'HPBW: {hpbw:.2f}°', transform=ax.transAxes, horizontalalignment='left', verticalalignment='top', bbox=dict(facecolor='white', alpha=0.8))

        # Front-to-Back Ratio Calculation
        front_attenuation = original_data[np.argmin(np.abs(azimutes - 0))]
        back_attenuation = original_data[np.argmin(np.abs(azimutes - np.pi))]
        fbr = 20 * math.log10(front_attenuation / back_attenuation)
        ax.text(0.97, 0.95, f'F_B Ratio: {fbr:.2f} dB', transform=ax.transAxes, horizontalalignment='left', verticalalignment='top', bbox=dict(facecolor='white', alpha=0.8))

        # Peak-to-Peak Calculation
        peak_to_peak_db = np.ptp(original_data)
        ax.text(0.97, 0.91, f'Peak2Peak: {peak_to_peak_db:.2f} E/Emax', transform=ax.transAxes, horizontalalignment='left', verticalalignment='top', bbox=dict(facecolor='white', alpha=0.8))

        # Directivity Calculation
        directivity_dB = calculate_directivity(original_data, 'h')
        ax.text(0.97, 0.87, f'Directivity: {directivity_dB:.2f} dB', transform=ax.transAxes, horizontalalignment='left', verticalalignment='top', bbox=dict(facecolor='white', alpha=0.8))
        # Prepare data for saving
        data_table = [{"azimuth": f"{azimuth}°", "gain": f"{gain:.2f}"} for azimuth, gain in zip(azimutes, rotated_data)]

        # Save the data to the database
        current_user.antenna_pattern_data_h_modified = json.dumps(data_table)
        db.session.commit()
        # Additional settings
        ax.set_theta_zero_location('N')  # Set North as 0 degrees
        ax.set_theta_direction(-1)  # Clockwise
        ax.set_title('Antenna Horizontal Radiation Pattern')
        plt.ylim(0, 1)
        ax.grid(True)
        ax.legend(loc='upper left')

        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png', bbox_inches='tight')
        img_buffer.seek(0)
        current_user.antenna_pattern_img_dia_H = img_buffer.getvalue()
        db.session.commit()
        img_base64 = base64.b64encode(img_buffer.getvalue()).decode('utf-8')
        img_buffer.close()
        plt.close()

        return img_base64



    def generate_rectangular_plot(data):
        # Gerar ângulos para a plotagem
        angles = np.linspace(-90, 90, len(data), endpoint=True)
    
        # Criar figura
        plt.figure(figsize=(10, 9))
    
        # Normalizar os dados para que o máximo seja 1
        data_normalized = data / np.max(data)
    
        # Calcular diretividade
        directivity_dB = calculate_directivity(data_normalized, 'v')
            # Prepare data for saving
        data_table = [{"Elevacao": f"{azimuth}°", "gain": f"{gain:.2f}"} for azimuth, gain in zip(angles, data_normalized)]

        # Save the data to the database
        current_user.antenna_pattern_data_v = json.dumps(data_table)
        db.session.commit()
        # Adicionar cálculos e legendas de HPBW para o diagrama vertical
        threshold = 0.707
        indices = np.where(data >= threshold)[0]
        if len(indices) > 1:
            idx_first = indices[0]
            idx_last = indices[-1]
            angle_first_deg = angles[idx_first]
            angle_last_deg = angles[idx_last]
            hpbw = angle_last_deg - angle_first_deg  # HPBW calculado como a diferença angular entre os dois pontos que cruzam o limiar

        # Plotar os dados normalizados
        
        plt.plot(angles, data_normalized, label=f'Elevation (Directivity: {directivity_dB:.2f} dB)')
    
        # Encontrar o primeiro mínimo após o máximo central
        max_index = np.argmax(data_normalized)
        right_data = data_normalized[max_index:]  # Considerar apenas a parte à direita do máximo
    
        # Encontrar e anotar o primeiro mínimo significativo à direita do máximo para nullFill

        for i in range(max_index + 1, len(data) - 1):
            if data[i] < data[i-1] and data[i] < data[i+1]:
                plt.annotate(f'First Null at {angles[i]:.1f}° ({data[i]*100:.1f}%)',
                                xy=(angles[i], data[i]),
                                xytext=(0, -40),
                                textcoords='offset points',
                                arrowprops=dict(arrowstyle='->', color='green'),
                                ha='center', va='top')
                break
    
        # Adicionar anotações para o primeiro nulo
        # Adicionar anotações para o primeiro nulo
        # plt.annotate(f'First Null: {first_null_angle:.1f}° ({first_null_value*100:.1f}%)',
        #              xy=(first_null_angle, first_null_value),
        #              xytext=(0, 50),  # Posiciona o texto acima do ponto com um deslocamento de 50 unidades
        #              textcoords='offset points', 
        #              arrowprops=dict(arrowstyle='->', color='red'),
        #              ha='center', va='bottom', bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="b", lw=2))
    
        plt.annotate(f'HPBW: {hpbw:.2f}°', xy=(0.95, 0.95), xycoords='axes fraction', ha='right', va='top',
                 bbox=dict(boxstyle="round", fc="white", ec="black"))
        # Encontrar o valor de E/Emax no ângulo 0
        value_at_zero_angle = data_normalized[np.abs(angles).argmin()]
    
        # Adicionar anotação para o valor de E/Emax no ângulo 0
        plt.annotate(f'E/Emax at 0°: {value_at_zero_angle*100:.1f}%',
                     xy=(0, value_at_zero_angle),
                     xytext=(0, -40),  # Posiciona o texto abaixo do ponto com um deslocamento de 40 unidades
                     textcoords='offset points', 
                     arrowprops=dict(arrowstyle='->', color='blue'),
                     ha='center', va='top', bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="b", lw=2))

        # Configurações do gráfico
        plt.xlabel('Elevation Angle (degrees)')
        plt.ylabel('E/Emax')
        plt.title('Elevation Pattern')
        plt.ylim(0, 1)  # Limitar o eixo Y
        plt.grid(True)
        plt.legend()

        # Salvar gráfico em buffer e codificar em base64
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', bbox_inches='tight')
        plt.close()
        buffer.seek(0)
        current_user.antenna_pattern_img_dia_V = buffer.getvalue()
        db.session.commit()
        buffer.seek(0)
        img_base64 = base64.b64encode(buffer.read()).decode('utf-8')
        buffer.close()
        
        return img_base64

    def generate_dual_rectangular_plot(original_data, angles, tilt=None):
        # Normalizar os dados para que o máximo seja 1
        data_normalized = original_data / np.max(original_data)

        # Cria cópia dos dados para modificação
        modified_data = np.copy(data_normalized)
        threshold = 0.707
        indices = np.where(modified_data >= threshold)[0]
        if len(indices) > 1:
            idx_first = indices[0]
            idx_last = indices[-1]
            angle_first_deg = angles[idx_first]
            angle_last_deg = angles[idx_last]
            hpbw = angle_last_deg - angle_first_deg  # HPBW calculado como a diferença angular entre os dois pontos que cruzam o limiar

        # Aplicar tilt se fornecido
        if tilt is not None:

            rotation_index = int((tilt / 180) * len(modified_data))
            modified_data = np.roll(modified_data, rotation_index)

           
        # Recalcular diretividade após aplicação do tilt
        directivity_dB_mod = calculate_directivity(modified_data, 'v')
            # Prepare data for saving
        data_table = [{"Elevacao": f"{azimuth}°", "gain": f"{gain:.2f}"} for azimuth, gain in zip(angles, modified_data)]

        # Save the data to the database
        current_user.antenna_pattern_data_v_modified = json.dumps(data_table)
        db.session.commit()
            # Aplicar nullFill se fornecido
                # Aplicar nullFill se fornecido
        # if nullFill is not None:
        max_index = np.argmax(modified_data)
        #     # Buscar primeiro ponto de inflexão após o máximo
        for i in range(max_index + 1, len(modified_data) - 1):
           if modified_data[i] < modified_data[i - 1] and modified_data[i] < modified_data[i + 1]:
              min_index = i
              break
           else:
                min_index = max_index  # Se não encontrar, usa o máximo como fallback

        directivity_dB_mod = calculate_directivity(modified_data, 'v')
        directivity_dB = calculate_directivity(data_normalized, 'v')

        plt.figure(figsize=(10, 9))
        plt.plot(angles, data_normalized, 'r--', label=f'Original Elevation Pattern (Directivity: {directivity_dB:.2f} dB)')
        plt.plot(angles, modified_data, 'b-', label=f'Modified Elevation Pattern (Directivity: {directivity_dB_mod:.2f} dB)')


        # Adicionar anotações para os dados modificados se aplicável
        max_index = np.argmax(modified_data)
        plt.annotate(f'Max at {angles[max_index]:.1f}° ({modified_data[max_index]*100:.1f}%)',
                    xy=(angles[max_index], modified_data[max_index]),
                    xytext=(50, 30),  # Deslocamento do texto
                    textcoords='offset points',
                    arrowprops=dict(arrowstyle='->', color='blue'),
                    ha='center')

        plt.annotate(f'HPBW: {hpbw:.2f}°', xy=(0.95, 0.95), xycoords='axes fraction', ha='right', va='top',
                 bbox=dict(boxstyle="round", fc="white", ec="black"))

        # Encontrar e anotar o primeiro mínimo significativo à direita do máximo para nullFill

        for i in range(max_index + 1, len(modified_data) - 1):
            if modified_data[i] < modified_data[i-1] and modified_data[i] < modified_data[i+1]:
                plt.annotate(f'First Null at {angles[i]:.1f}° ({modified_data[i]*100:.1f}%)',
                                xy=(angles[i], modified_data[i]),
                                xytext=(0, -60),
                                textcoords='offset points',
                                arrowprops=dict(arrowstyle='->', color='green'),
                                ha='center', va='top')
                break

        # Encontrar o valor de E/Emax no ângulo 0
        value_at_zero_angle = modified_data[np.abs(angles).argmin()]
    
        # Adicionar anotação para o valor de E/Emax no ângulo 0
        plt.annotate(f'E/Emax at 0°: {value_at_zero_angle*100:.1f}%',
                     xy=(0, value_at_zero_angle),
                     xytext=(0, -40),  # Posiciona o texto abaixo do ponto com um deslocamento de 40 unidades
                     textcoords='offset points', 
                     arrowprops=dict(arrowstyle='->', color='blue'),
                     ha='center', va='top', bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="b", lw=2))  

        plt.xlabel('Elevation Angle (degrees)')
        plt.ylabel('E/Emax')
        plt.title('Dual Elevation Pattern Comparison')
        plt.legend()
        plt.ylim(0, 1)
        plt.grid(True)

        # Salvar gráfico em buffer e codificar em base64
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', bbox_inches='tight')
        plt.close()
        buffer.seek(0)   
        current_user.antenna_pattern_img_dia_V = buffer.getvalue()
        db.session.commit()
        buffer.seek(0)
        img_base64 = base64.b64encode(buffer.read()).decode('utf-8')
        buffer.close()
        
        return img_base64


   
   

    def calculate_directivity(smoothed_data,tipo):

        if tipo == 'h':

            # Normalizar a potência
            power_normalized = smoothed_data / np.max(smoothed_data)
            # Converter azimutes de graus para radianos
            azimutes = np.linspace(0, 2 * np.pi, len(smoothed_data))
            # Integrar a potência normalizada sobre todos os ângulos, usando argumentos de palavras-chave
            integral = simpson(y=power_normalized, x=azimutes)
            # Calcular diretividade
            directivity = 2 * np.pi / integral  # Correção aplicando 2*pi para considerar a integral sobre o círculo completo
            # Converter diretividade para dB
            directivity_dB = 10 * np.log10(directivity)
            return directivity_dB
        elif tipo == 'v':
            # Gerar ângulos para interpolação
            angles = np.linspace(-90, 90, len(smoothed_data), endpoint=True)
            #new_angles = np.arange(-90, 90.1, 0.1)
            #interpolated_data = np.interp(new_angles, angles, smoothed_data)
            power_normalized = smoothed_data / np.max(smoothed_data)
            # Converter ângulos de graus para radianos
            radians = np.deg2rad(angles)
            # Integrar a potência normalizada sobre os ângulos, usando argumentos nomeados
            integral = simpson(y=power_normalized, x=radians)
            # Calcular diretividade
            directivity = np.pi / integral  # Usando π já que os dados cobrem apenas um semi-círculo
            # Converter diretividade para dB
            directivity_dB = 10 * np.log10(directivity)
            return directivity_dB

    @app.route('/update-notes', methods=['POST'])
    @login_required
    def update_notes():
        notes = request.form.get('notes')  # Pega as notas do corpo da requisição POST
        if notes is not None:
            current_user.notes = notes  # Atualiza as notas do usuário atual
            db.session.commit()  # Salva a alteração no banco de dados
            return jsonify({'message': 'Notas atualizadas com sucesso!'}), 200
        else:
            return jsonify({'error': 'Nenhuma nota fornecida.'}), 400

    @app.route('/fetch-elevation', methods=['POST'])
    def fetch_elevation():
        try:
           path_data = request.json['path']
          # path_str = '|'.join([f"{lat},{lng}" for lat, lng in path_data])
           path_str = '|'.join([f"{point['lat']},{point['lng']}" for point in path_data])
           url = f"https://maps.googleapis.com/maps/api/elevation/json?path={path_str}&samples=256&key={google_api_key}"

           response = requests.get(url)
           if response.status_code == 200:
               elevation_data = response.json()
            #    print(path_str)
            #    print(path_data)
            #    print(elevation_data)
               return jsonify(elevation_data)
           else:
               current_app.logger.error('Erro na API de Elevação: Status code {}'.format(response.status_code))
            #    print(path_str)
            #    print(path_data)
               return jsonify({"error": "Failed to fetch elevation data"}), 500
        except Exception as e:
            current_app.logger.error('Erro ao processar /fetch-elevation: {}'.format(e))

            return jsonify({"error": "Internal server error"}), 500


   

    def adjust_center_for_coverage(lon_center, lat_center, radius_km):
        """
        Ajusta as coordenadas do centro da mancha de cobertura usando a biblioteca Geopy.
    
        :param lon_center: Longitude do centro em graus.
        :param lat_center: Latitude do centro em graus.
        :param radius_km: Raio da cobertura em quilômetros.
        :return: Coordenadas ajustadas do centro (lon, lat).
        """
        # Geopy utiliza a ordem (latitude, longitude)
        original_location = (lat_center.to(u.deg).value, lon_center.to(u.deg).value)
        northern_point = geodesic(kilometers=radius_km).destination(original_location, bearing=0)
    
        # Retorna as coordenadas ajustadas
        return northern_point.longitude, northern_point.latitude


    def generate_coverage_image(lons, lats, _total_atten, radius_km, lon_center, lat_center):
        fig, ax = plt.subplots()
        atten_db = _total_atten.to(u.dB).value 
        #print(atten_db) # Converte atenuação para dB
        levels = np.linspace(atten_db.min(), atten_db.max(), 100)
        cim = ax.contourf(lons, lats, atten_db, levels=levels, cmap='rainbow')

        cax = fig.add_axes([0.85, 0.15, 0.05, 0.7])  # [posição x, posição y, largura, altura]
        cbar = plt.colorbar(cim, cax=cax, orientation='vertical', label='Atenuação [dB]')
    

        # Raio da Terra em quilômetros
        earth_radius_km = 6371.0

        # Raio em graus para latitude precisa de correção de latitude
        radius_degrees_lat = radius_km / (earth_radius_km * (np.pi/180))

        # Raio em graus para longitude precisa de correção de latitude
        radius_degrees_lon = radius_km / (earth_radius_km * np.cos(np.radians(lat_center.to(u.deg).value)) * (np.pi/180))

        # As coordenadas ajustadas do centro não precisam ser modificadas aqui, pois já são fornecidas corretamente
        lon_center_adjusted = lon_center.to(u.deg).value
        lat_center_adjusted = lat_center.to(u.deg).value
       # ax.set_xlim(lon_center.to(u.deg).value - radius_degrees_lon, lon_center.to(u.deg).value + radius_degrees_lon)
       # ax.set_ylim(lat_center.to(u.deg).value - radius_degrees_lat, lat_center.to(u.deg).value + radius_degrees_lat)
        # Desenha um círculo para representar a área de cobertura
        circle = plt.Circle((lon_center_adjusted, lat_center_adjusted),
                    max(radius_degrees_lon, radius_degrees_lat),
                    color='red', fill=False, linestyle='--')
        ax.add_artist(circle)


        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png', transparent=True)
        img_buffer.seek(0)
        plt.close(fig)

        return img_buffer


    def calculate_bearing(lat1, lng1, lat2, lng2):
        lat1, lng1, lat2, lng2 = map(math.radians, [lat1, lng1, lat2, lng2])
        dLon = lng2 - lng1
        x = math.sin(dLon) * math.cos(lat2)
        y = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(dLon)
        initial_bearing = math.atan2(x, y)
        initial_bearing = math.degrees(initial_bearing)
        compass_bearing = (initial_bearing + 360) % 360

        return compass_bearing






    def get_magnetic_declination(lat, lon):
        # URL da API NCEI
        url = "https://www.ngdc.noaa.gov/geomag-web/calculators/calculateDeclination"
        
        # Parâmetros da API
        params = {
            'lat1': lat,
            'lon1': lon,
            'resultFormat': 'json',
            'epoch': '2024.5'  # Usando o ano atual como exemplo
        }

        # Requisição à API
        response = requests.get(url, params=params)
        
        # Verifica se a requisição foi bem-sucedida
        if response.status_code == 200:
            data = response.json()
            return data['result'][0]['declination']
        else:
            return None



    def fresnel_zone_radius(d1, d2, wavelength):
        """
        Calcula o raio da primeira zona de Fresnel.
        d1: Distância do transmissor até o ponto de interesse (m)
        d2: Distância do receptor até o ponto de interesse (m)
        wavelength: Comprimento de onda (m)
        """
        return np.sqrt(wavelength * d1 * d2 / (d1 + d2))



    @app.route('/gerar_img_perfil', methods=['POST'])
    def gerar_img_perfil():
        data = request.get_json()
        start_coords = data['path'][0]
        end_coords = data['path'][1]
        path = data['path']
        Ptx_W = current_user.transmission_power
        G_tx_dBi = current_user.antenna_gain
        G_rx_dbi = current_user.rx_gain
        frequency = current_user.frequencia
        totalloss = current_user.total_loss
        pattern = current_user.antenna_pattern
        direction = current_user.antenna_direction
        tilt = current_user.antenna_tilt

        # Cálculo da direção
        direction_rx = calculate_bearing(start_coords['lat'], start_coords['lng'], end_coords['lat'], end_coords['lng'])
        Gtx_direction_rx = G_tx_dBi
        if pattern is not None:
            file_content = pattern.decode('latin1')
            parts = file_content.split('999')
            horizontal_lines = parts[0].splitlines()[1:361]
            horizontal_data = np.array([float(line.split(',')[1].strip()) for line in horizontal_lines if line.strip() and len(line.split(',')) > 1])

            vertical_lines = parts[1].splitlines()[1:181]  # Supondo que os dados verticais estejam na segunda parte e têm 181 linhas de -90 a 90
            vertical_data = np.array([float(line.split(',')[1].strip()) for line in vertical_lines if line.strip() and len(line.split(',')) > 1])

            # Aplicar tilt ao diagrama vertical
            if tilt is not None:
                tilt_index = int((tilt) / (360 / len(vertical_data)))
                vertical_data = np.roll(vertical_data, -tilt_index)

            # Rotacionar os dados se a direção for especificada
            if direction is not None:
                rotation_index = int((direction) / (360 / len(horizontal_data)))
                horizontal_data = np.roll(horizontal_data, rotation_index)

            # Encontrar o ganho na direção do receptor
            Gtx_direction_rx = horizontal_data[int(direction_rx) % 360]
            G_tx_dBi = G_tx_dBi + Gtx_direction_rx

        print('dados diagrama h:', horizontal_data, len(horizontal_data))
        print('ganho na direção:', Gtx_direction_rx)

        if frequency < 100:
            frequency = 100

        frequency = (frequency / 1000) * u.GHz

        P_dBm = 10 * math.log10(Ptx_W / 0.001)  # Dividindo por 0.001 converte watts para miliwatts
        # Conversão de potência de transmissão e ganho de antena para dB
        P_tx_dBm = P_dBm * (u.dB(u.mW))
        G_tx_dBi = G_tx_dBi * (u.dB)
        erp = P_dBm + G_tx_dBi.value - totalloss

        # Extrai as coordenadas do transmissor (TX) e do receptor (RX)
        tx_coords = path[0]
        rx_coords = path[1]

        # Converte as coordenadas em Quantities do astropy
        lon_tx, lat_tx = float(tx_coords['lng']) * u.deg, float(tx_coords['lat']) * u.deg
        lon_rx, lat_rx = float(rx_coords['lng']) * u.deg, float(rx_coords['lat']) * u.deg

        temperature = 293.15 * u.K
        pressure = 1013. * u.hPa
        time_percent = 40 * u.percent
        zone_t, zone_r = pathprof.CLUTTER.UNKNOWN, pathprof.CLUTTER.UNKNOWN

        # Define a configuração do SRTM
        with SrtmConf.set(
            srtm_dir='./SRTM',
            download='missing',
            server='viewpano'
        ):
            # Calcula o perfil de altura usando pyprof.pathprof
            profile = pathprof.srtm_height_profile(
                lon_tx, lat_tx,
                lon_rx, lat_rx,
                step=1 * u.m  # Quantidade de passos/pontos entre TX e RX
            )

            # Desempacota os dados da tupla
            longitudes, latitudes, total_distance, distances, heights, angle1, angle2, additional_data = profile

        h_rg = current_user.rx_height * u.m
        h_tg = current_user.tower_height * u.m
        # Preparação dos dados para o gráfico
        distances_km = distances.to(u.km)  # Converte as distâncias para quilômetros
        heights_m = heights.to(u.m)  # Converte as altitudes para metros
        hprof_step = 1 * u.m

        results = pathprof.losses_complete(
            frequency,
            temperature,
            pressure,
            lon_tx, lat_tx,
            lon_rx, lat_rx,
            h_tg, h_rg,
            hprof_step,
            time_percent,
            zone_t=zone_t, zone_r=zone_r,
        )

        print(results['L_b_corr'])
        print(erp)
        rx_position_km = distances_km[-1].value
        sinal_recebido = erp + G_rx_dbi - results['L_b_corr'].value[0] if isinstance(results['L_b_corr'].value, np.ndarray) else erp - results['L_b_corr'].value

        # Gera o gráfico com matplotlib
        fig, ax = plt.subplots(figsize=(15, 8))
        ax.fill_between(distances_km.to_value(u.km), heights_m.to_value(u.m), color='saddlebrown', alpha=0.7)
        ax.plot(distances_km, heights_m, color='darkgreen')

        # Linha vertical na posição do TX e RX
        ax.vlines(0, heights_m[0].value, heights_m[0].value + h_tg.value, color='red', linewidth=2, label='Torre de Transmissão')
        ax.vlines(distances_km[-1].value, heights_m[-1].value, heights_m[-1].value + h_rg.value, color='red', linewidth=2, label='Receptor')

        # Traçado do sinal do TX ao RX
        ax.plot([0, rx_position_km], [heights_m[0].value + h_tg.value, heights_m[-1].value + h_rg.value], color='blue', linestyle='--', label='Caminho do Sinal')

        # Cálculo da zona de Fresnel
        n_points = 100
        x = np.linspace(0, rx_position_km, n_points)
        fresnel_radius = np.sqrt((1 / (4 * np.pi * frequency.to_value(u.Hz))) * (x * (rx_position_km - x) / rx_position_km) * 1e12)  # Em metros

        fresnel_top = np.linspace((heights_m[0].value + h_tg.value), (heights_m[-1].value + h_rg.value), n_points) + fresnel_radius
        fresnel_bottom = np.linspace((heights_m[0].value + h_tg.value), (heights_m[-1].value + h_rg.value), n_points) - fresnel_radius

        # Plotando a primeira zona de Fresnel
        ax.plot(x, fresnel_top, 'm--', label='Topo da Primeira Zona de Fresnel')
        ax.plot(x, fresnel_bottom, 'm:', label='Fundo da Primeira Zona de Fresnel')


        # Adiciona uma caixa de texto para as anotações
        annotation_text = (
            f'ERP: {erp:.2f} dBm\nDireção RX: {direction_rx:.2f} Graus\n'
            f'Direção RX Magnético: {direction_rx:.2f} Graus\n'
            f'Ângulo entre TX e RX: {angle1:.2f} Graus\n'
            f'Ganho na Direção: {Gtx_direction_rx:.2f} dB\n'
            f'Nível de Sinal: {sinal_recebido:.2f} dBm / {sinal_recebido + 107:.2f} dBμV/m\n'
            f'Total Loss: {results["L_b_corr"].value[0]:.2f} dB\nDistância: {distances_km[-1].to_value(u.km):.2f} Km\n'
        )

        # Ajuste a posição das anotações no gráfico
        ax.text(0.5, 0.5, annotation_text, transform=ax.transAxes, fontsize=11,
                verticalalignment='center', horizontalalignment='center', bbox=dict(boxstyle='round,pad=0.3', edgecolor='black', facecolor='lightyellow'))

        ax.set_xlabel('Distância (km)')
        ax.set_ylabel('Elevação (m)')
        ax.set_title('Perfil de Elevação com Sinal de Transmissão')
        plt.grid(True, which="both", ls="--")
        ax.legend()

        # Salva a figura em um buffer em memória e codifica em base64
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png', bbox_inches='tight')
        img_buffer.seek(0)
        current_user.perfil_img = img_buffer.getvalue()
        db.session.commit()
        img_buffer.seek(0)
        img_base64 = base64.b64encode(img_buffer.read()).decode('utf-8')
        img_buffer.close()
        plt.close(fig)

        return jsonify({"image": img_base64})



    def generate_signal_level_image(lons, lats, _total_atten, radius_km, lon_center, lat_center, Ptx_W, g_total, min_val, max_val, loss):
        user_id = current_user.id
        user = User.query.get(user_id)
        direction = user.antenna_direction
        ganho = user.antenna_gain

        if user.antenna_pattern:
            file_content = user.antenna_pattern.decode('latin1')
            parts = file_content.split('999')
            horizontal_lines = parts[0].splitlines()[1:361]
            horizontal_data = np.array([float(line.split(',')[1].strip()) for line in horizontal_lines if line.strip()])

            lon_center = lon_center.to(u.deg).value if hasattr(lon_center, 'unit') else lon_center
            lat_center = lat_center.to(u.deg).value if hasattr(lat_center, 'unit') else lat_center

            lon_grid, lat_grid = np.meshgrid(lons, lats)
            azimutes_grid = np.degrees(np.arctan2(lon_grid - lon_center, lat_grid - lat_center)) % 360  # Ajuste aqui
            azimutes_indices = np.round(azimutes_grid).astype(int)
            azimutes_indices = np.where(azimutes_indices == 360, 0, azimutes_indices)

            if direction is not None:
                rotation_index = int((direction) / (360 / len(horizontal_data)))  # Ajuste aqui para direção
                horizontal_data = np.roll(horizontal_data, rotation_index)

            antenna_gain_grid = horizontal_data[azimutes_indices] * u.dB

        fig, ax = plt.subplots(figsize=(6, 6))

        P_dBm = 10 * math.log10(Ptx_W / 0.001)
        P_tx_dBm = P_dBm * (u.dB(u.mW))
        ganho = ganho * (u.dB)
        signal_levels = P_tx_dBm.value + ganho.value + antenna_gain_grid.value - loss - _total_atten.to(u.dB).value

       # print('ganho: ', antenna_gain_grid, 'direção: ', direction)

        if min_val is None or max_val is None:
            min_val = -80
            max_val = -20

        try:
            min_val = float(min_val) if min_val is not None else np.nanmin(signal_levels)
            max_val = float(max_val) if max_val is not None else np.nanmax(signal_levels)
        except ValueError:
            raise ValueError("Os valores de mínimo e máximo devem ser numéricos.")

        if min_val >= max_val:
            raise ValueError("O valor mínimo deve ser menor que o valor máximo.")

        lon_center = lon_center.to(u.deg).value if isinstance(lon_center, u.Quantity) else lon_center
        lat_center = lat_center.to(u.deg).value if isinstance(lat_center, u.Quantity) else lat_center

        dados = _total_atten.shape[0]
        delta = radius_km / 111
        lon_grid, lat_grid = np.meshgrid(
            np.linspace(lon_center - delta, lon_center + delta, num=dados),
            np.linspace(lat_center - delta, lat_center + delta, num=dados)
        )

        dist = np.sqrt((lon_grid - lon_center) ** 2 + (lat_grid - lat_center) ** 2)
        earth_radius_km = 6371.0
        dist_km = dist * (np.pi / 180) * earth_radius_km
        signal_levels[dist_km > radius_km] = np.nan

        levels = np.linspace(min_val, max_val, 100)
        mesh = ax.pcolormesh(lon_grid, lat_grid, signal_levels, cmap='rainbow', shading='auto', vmin=min_val, vmax=max_val)

        polar_dimension = min(fig.get_size_inches()) * radius_km / (radius_km * 20)
        ax_inset = fig.add_axes([(1.034 - polar_dimension) / 2,
                                (1 - polar_dimension) / 2,
                                polar_dimension, polar_dimension], polar=True)

        ax_inset.set_theta_zero_location('N')
        ax_inset.set_theta_direction(-1)

        ax_inset.set_aspect('equal', adjustable='box')
        azimutes = np.linspace(0, 2 * np.pi, len(horizontal_data))
        ax_inset.plot(azimutes, horizontal_data, linestyle='dashed', color='black', label='Antenna Pattern')

        # Adição dos valores dos ganhos de 15 em 15 graus
        for i in range(0, 360, 15):
            angle = np.radians(i)
            radius = horizontal_data[i]
            ax_inset.text(angle, radius + 1, f'{radius:.1f}', fontsize=8, ha='center', va='center', color='blue')

        ax_inset.set_xticks([])
        ax_inset.set_yticks([])
        ax_inset.spines['polar'].set_visible(False)

        for spine in ax.spines.values():
            spine.set_visible(False)

        ax.set_xticks([])
        ax.set_yticks([])
        ax.xaxis.label.set_visible(False)
        ax.yaxis.label.set_visible(False)

        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png', transparent=True)
        img_buffer.seek(0)
        image_base64 = base64.b64encode(img_buffer.read()).decode('utf-8')
        plt.close(fig)

        fig_colorbar, ax_colorbar = plt.subplots(figsize=(6, 1))
        plt.colorbar(mesh, cax=ax_colorbar, orientation='horizontal')
        ax_colorbar.set_title('Nível de Sinal [dBm]')
        ax_colorbar.margins(0.1)
        fig_colorbar.tight_layout()
        colorbar_buffer = io.BytesIO()
        fig_colorbar.savefig(colorbar_buffer, format='png', transparent=True)
        colorbar_buffer.seek(0)
        colorbar_base64 = base64.b64encode(colorbar_buffer.read()).decode('utf-8')
        plt.close(fig_colorbar)

        return image_base64, colorbar_base64





 
    def create_attenuation_dict(lons, lats, attenuation):
        attenuation_dict = {}
        print(attenuation.shape)
        if attenuation.shape == (len(lats), len(lons)):
            for i in range(len(lats)):
                for j in range(len(lons)):
                    key = f"({lats[i]}, {lons[j]})"
                    # Converter o valor de atenuação para float
                    attenuation_dict[key] = float(attenuation[i, j].value)
        else:
            raise ValueError("A dimensão do array de atenuação não corresponde ao número de latitudes e longitudes.")
        
        return attenuation_dict

    
    def calculate_geodesic_bounds(lon, lat, radius_km):
        # Cria um ponto com as coordenadas
        central_point = (lat, lon)

        # Calcula os pontos nos quatro limites utilizando o raio especificado
        north = geodesic(kilometers=radius_km).destination(central_point, bearing=0)
        south = geodesic(kilometers=radius_km).destination(central_point, bearing=180)
        east = geodesic(kilometers=radius_km).destination(central_point, bearing=90)
        west = geodesic(kilometers=radius_km).destination(central_point, bearing=270)

        # Retorna os limites calculados
        return {"north": north.latitude, "south": south.latitude, "east": east.longitude, "west": west.longitude}
    # Dados
    radii = np.array([20, 40, 60, 100, 300]).reshape(-1, 1)  # em km
    delta_lat = np.array([-0.002316, -0.002324, -0.005666, -0.011404, -0.034283])  # em graus
    delta_lon = np.array([0.006451, 0.013683, 0.018373, 0.030432, 0.090573])  # em graus

    # Modelos de regressão
    model_lat = LinearRegression().fit(radii, delta_lat)
    model_lon = LinearRegression().fit(radii, delta_lon)

    def adjust_center(radius_km, center_lat, center_lon):
        # Calcula os ajustes preditos
        adj_lat = model_lat.predict(np.array([[radius_km]]))[0]
        adj_lon = model_lon.predict(np.array([[radius_km]]))[0]
        scale_factor_lat = 1
        scale_factor_log = 1

        if radius_km in range(0,21):
           scale_factor_lat = 1.9
           scale_factor_log = 0.95

        elif radius_km in range(21,31):
            scale_factor_lat = 1.4
            scale_factor_log = 0.93
        elif radius_km in range(31,41):
            scale_factor_lat = 1.28
            scale_factor_log = 1
        elif radius_km in range(41,51):
             scale_factor_lat = 1.21
             scale_factor_log = 1.03
        elif radius_km in range(51,61):
             scale_factor_lat = 1.19
             scale_factor_log = .97
        elif radius_km in range(61,71):
             scale_factor_lat = 1.17
             scale_factor_log = 1.025
        elif radius_km in range(71,101):
             scale_factor_lat = 1.1
             scale_factor_log = 1.027
        # Aplica os ajustes ao centro
        new_lat = center_lat - adj_lat*scale_factor_lat
        new_lon = center_lon - adj_lon*scale_factor_log
    
        return new_lat, new_lon
   #funções para retornar os arquivos srtm
    

    def determine_hgt_files(bounds):
        files_hgt = []
        lat_start = int(math.floor(bounds['south']))
        lat_end = int(math.ceil(bounds['north']))
        lon_start = int(math.floor(bounds['west']))
        lon_end = int(math.ceil(bounds['east']))
    
        for lat in range(lat_start, lat_end):
            for lon in range(lon_start, lon_end):
                lat_prefix = 'N' if lat >= 0 else 'S'
                lon_prefix = 'E' if lon >= 0 else 'W'
                filename = f"{lat_prefix}{abs(lat):02d}{lon_prefix}{abs(lon):03d}.hgt"
                files_hgt.append(filename)
    
        return files_hgt


 
   

    @app.route('/calculate-coverage', methods=['POST'])
    def calculate_coverage():
        # Supondo que você esteja usando SQLAlchemy para buscar dados do usuário
        # user = User.query.get(current_user)
        # if not user:
        #     return jsonify({"error": "Usuário não encontrado"}), 404
        data = request.get_json()
        # Supondo que a classe User tem os campos necessários
        loss = current_user.total_loss
        Ptx_W = current_user.transmission_power
        ganho_total = current_user.transmission_power
        Gtx_dbi = current_user.antenna_gain
        Grx_dBi = current_user.rx_gain
        long = current_user.longitude 
        lati = current_user.latitude
        raio_para_adj = data.get('radius')
        #ajusta o centro :
        new_center_lat, new_center_lon = adjust_center(raio_para_adj, lati, long)

        lon_rt = new_center_lon * u.deg
        lat_rt = new_center_lat * u.deg
        frequency = current_user.frequencia
        if frequency < 100: 
             frequency = 100

        frequency = (frequency/1000) * u.GHz

        h_rt = current_user.rx_height * u.m
        print(h_rt)
        h_wt = current_user.tower_height * u.m
        polarization = 1
        version = 16
        
        min_valu = data.get('minSignalLevel')
        max_valu = data.get('maxSignalLevel')
        raio = data['radius']*1.26* u.km
        radius_km = data.get('radius')*1.26
        if radius_km/1.26 in range(0, 41):
           res = 1  # Resolução para raios de 0 a 20 km
        elif radius_km/1.26 in range(41, 61):
           res = 5  # Resolução para raios de 21 a 50 km
        elif radius_km/1.26 in range(61, 80):
           res = 8  # Resolução para raios de 21 a 50 km
        # Adicione mais condições conforme necessário
        else:
            res = 10  # Resolução padrão para raios acima de 50 km


        map_resolution = res* u.arcsec# 
        
        bounds = calculate_geodesic_bounds(new_center_lon, new_center_lat, radius_km)
        #print(bounds)
         # Definindo bounds da colorbar acima da mancha
         # Converter a altura da colorbar para graus
        km_per_degree = 111.32  # Aproximadamente quantos graus corresponde a 1km na latitude média
        colorbar_height_deg = 0.01 / km_per_degree  # Convertendo 1km em graus
        colorbar_height = 0.005  # Aproximadamente 1km em graus, ajuste conforme necessário
        colorbar_bounds = {
          'north': bounds['north'],#+ colorbar_height_deg, #+ (0.005 / km_per_degree),  # Adiciona cerca de 100px acima em graus
          'south': bounds['north'],# + colorbar_height_deg,
          'east': bounds['east'],
          'west': bounds['west']
        }
        
        # print(min_valu)
        # print(max_valu)
        temperature = 293.15 * u.K
        pressure = 1013. * u.hPa
        timepercent = 40 * u.percent
        modelo = current_user.propagation_model
        if modelo == 'modelo1':
           zone_t, zone_r = pathprof.CLUTTER.URBAN,pathprof.CLUTTER.URBAN
        elif modelo == 'modelo2':
             zone_t, zone_r = pathprof.CLUTTER.SUBURBAN,pathprof.CLUTTER.SUBURBAN
        elif modelo == 'modelo3':
             zone_t, zone_r = pathprof.CLUTTER.TROPICAL_FOREST,pathprof.CLUTTER.TROPICAL_FOREST
        elif modelo == 'modelo4':
             zone_t, zone_r = pathprof.CLUTTER.CONIFEROUS_TREES,pathprof.CLUTTER.CONIFEROUS_TREES
        elif modelo == 'modelo5':
             zone_t, zone_r = pathprof.CLUTTER.UNKNOWN,pathprof.CLUTTER.UNKNOWN

        raio_km = (data.get('radius'))  # Supõe um raio padrão de 10km se não for especificado
        circunferencia_terra_km = 40075.0

        # Calcula a extensão em graus
        extensao_graus = (raio_km / circunferencia_terra_km) * 360

        # Define o tamanho do mapa como sendo o dobro da extensão calculada
        map_size_lon = map_size_lat = extensao_graus * u.deg
        # Suponha que 'bounds' já esteja calculado
        bounds_s3 = {
         'north': bounds['north'],
         'south': bounds['south'], 
         'east': bounds['east'],
         'west': bounds['west']
        }
        

       # print(srtm_data)
    # Se necessário, aqui você pode adicionar lógica para processar os dados carregados

        # Cria um cache de perfil de altura (pode demorar um pouco)
       # map_size_lon = map_size_lat = (2 * raio.to(u.deg, equivalencies=u.dimensionless_angles()))
        with pathprof.SrtmConf.set(
                srtm_dir='./SRTM',
                download='missing',
                server='viewpano'
                ):

                   hprof_cache = pathprof.height_map_data(
                   lon_rt, lat_rt,
                   map_size_lon, map_size_lat,
                   map_resolution=map_resolution,
                   zone_t=zone_t, zone_r=zone_r,
                     )
        #print(lon_rt.value,lat_rt.value)
        # Calcula a atenuação
        results = pathprof.atten_map_fast(
            freq=frequency ,  # Garantir que a unidade está em GHz
            temperature=temperature,  # Temperatura em Kelvin
            pressure=pressure,  # Pressão em hectopascal
            h_tg=h_wt,  # Altura do transmissor em metros
            h_rg=h_rt,  # Altura do receptor em metros
            timepercent=timepercent * u.percent,  # Percentual de tempo em percentagem
            hprof_data=hprof_cache,  # Dados do perfil de altura
            polarization=polarization,  # Polarização, horizontal (0) ou vertical (1)
            version=version,  # Versão da recomendação ITU-R P.452
            base_water_density=7.5 * u.g / u.m**3  # Densidade base de vapor de água, se necessário ajustar
        )

    
        _lons = hprof_cache['xcoords']
        _lats = hprof_cache['ycoords']
        _total_atten = results['L_b']  # atenuação total
        # print(results['L_b'])
        # print(results['L_b0p'])
        # print(results['L_bd'])
       #attenuation_dict = create_attenuation_dict(_lons, _lats, _total_atten)
        P_dBm = 10 * math.log10(Ptx_W / 0.001)  # Dividindo por 0.001 converte watts para miliwatts
        # Conversão de potência de transmissão e ganho de antena para dB
        P_tx_dBm = P_dBm*(u.dB(u.mW))
        Gtx_dbi = Gtx_dbi*(u.dB)
        Loss_dB = loss*(u.dB)

        signal_levelsdic = P_tx_dBm.value + Gtx_dbi.value - Loss_dB.value - _total_atten.to(u.dB).value
        
        signal_level_dict = {}
        
        if signal_levelsdic.shape == (len(_lats), len(_lons)):
            for i in range(len(_lats)):
                for j in range(len(_lons)):
                    key = f"({_lats[i]}, {_lons[j]})"
                    # Garante que o valor é um float antes de adicionar ao dicionário
                    signal_level_dict[key] = float(signal_levelsdic[i,j])

        
        


       # img_buffer = generate_coverage_image(_lons, _lats, _total_atten, radius_km, lon_rt, lat_rt)
        image_base64, colorbar_base64 = generate_signal_level_image(_lons, _lats, _total_atten, radius_km, lon_rt, lat_rt, Ptx_W, ganho_total, min_valu, max_valu,loss)

        return jsonify({"image": image_base64,"colorbar": colorbar_base64, "bounds": bounds,"colorbar_bounds":colorbar_bounds, "signal_level_dict": signal_level_dict})
        


    @app.route('/salvar-dados', methods=['POST'])
    def salvar_dados():

        try:
           data = request.json  # Acessar os dados JSON enviados pelo frontend
           print(data)
           # Buscar o usuário atual
           user = User.query.get(current_user.id)
    
           if not user:
               return jsonify({'error': 'Usuário não encontrado.'}), 404
        
           # Atualiza o usuário com os novos dados
           user.propagation_model = data.get('propagationModel')
           user.frequencia = float(data.get('frequency'))
           user.tower_height = float(data.get('towerHeight'))
           user.rx_height = float(data.get('rxHeight'))
           user.rx_gain = float(data.get('rxGain'))
           user.total_loss = float(data.get('Total_loss'))
           user.transmission_power = float(data.get('transmissionPower'))
           user.antenna_gain = float(data.get('antennaGain'))
           user.latitude = float(data.get('latitude'))
           user.longitude = float(data.get('longitude'))
           user.servico = data.get('service')

           db.session.commit()

           # Retorno de sucesso
           return jsonify({'message': 'Dados salvos com sucesso!'}), 200
        except SQLAlchemyError as e:
            db.session.rollback()
            # Retorno em caso de erro
            return jsonify({'error': 'Erro ao salvar os dados: ' + str(e)}), 500

    @app.route('/visualizar-dados-salvos')
    def visualizar_dados_salvos():
        user_id = current_user.id
        dados_salvos = User.query.filter_by(id=user_id).first()

        if dados_salvos:
            image_data = {
                'perfil_img': base64.b64encode(dados_salvos.perfil_img).decode('utf-8') if dados_salvos.perfil_img else None,
                'cobertura_img': base64.b64encode(dados_salvos.cobertura_img).decode('utf-8') if dados_salvos.cobertura_img else None,
                'antenna_pattern_img_dia_H': base64.b64encode(dados_salvos.antenna_pattern_img_dia_H).decode('utf-8') if dados_salvos.antenna_pattern_img_dia_H else None,
                'antenna_pattern_img_dia_V': base64.b64encode(dados_salvos.antenna_pattern_img_dia_V).decode('utf-8') if dados_salvos.antenna_pattern_img_dia_V else None,
            }
        else:
            image_data = {
                'perfil_img': None,
                'cobertura_img': None,
                'antenna_pattern_img_dia_H': None,
                'antenna_pattern_img_dia_V': None,
            }

        return render_template('dados_salvos.html', dados_salvos=dados_salvos, image_data=image_data)


    # @app.route('/visualizar-dados')
    # def visualizar_dados():
    #     dados_salvos = User.query.filter_by(user_id=current_user.id).all()
    #     return render_template('dados_user.html', dados_salvos=dados_salvos)

    @app.route('/carregar-dados', methods=['GET'])
    def carregar_dados():
        try:
            # Supondo que você esteja usando Flask-Login para gerenciar sessões de usuário
            # e que a variável 'current_user' seja o usuário logado
            user = User.query.get(current_user.id)

            if not user:
                return jsonify({'error': 'Usuário não encontrado.'}), 404

            # Preparar os dados do usuário para serem enviados
            user_data = {
                'username': user.username,
                'email': user.email,
                'propagationModel': user.propagation_model,
                'frequency': user.frequencia,
                'towerHeight': user.tower_height,
                'rxHeight': user.rx_height,
                'Total_loss': user.total_loss,
                'transmissionPower': user.transmission_power,
                'antennaGain': user.antenna_gain,
                'rxGain': user.rx_gain,

                'latitude': user.latitude,
                'longitude': user.longitude,
                'serviceType': user.servico,
                
                'nomeUsuario': user.username
            }

            return jsonify(user_data), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500



    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        return redirect(url_for('index'))

    return app


app = create_app()
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
