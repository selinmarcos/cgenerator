import flask
from flask import request, jsonify
import pandas as pd
from datetime import datetime as dt
from flask_cors import CORS, cross_origin
import openai
import requests
import base64
import tkinter as tk
import time
import re
import json
from unidecode import unidecode
from tkinter import ttk
from PIL import Image

# openai.api_key = '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'


app = flask.Flask(__name__)
CORS(app)

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        generate_content()
        return "CONTENIDO GENERADO"
    else:
        return "SERVIDOR FLASK ESPERANDO PARAMENTROS"
def generate_content():
    data = request.get_json()

    if data['keywords']:
        keywords = data['keywords'].strip()
        keyword_list = keywords.split('\n')
        textGuia = data['textGuia'].strip()
        url = data['url']
        user = data['user']
        password = data['password']   
        openai.api_key = data['apikey']
        category = data['category']
        tag = data['tag']
        author = data['author']
    else:
        print('ERRORRRRRRRRRR')    
        

   
    # url = 'https://tramitesbolivia.webmasterbolivia.com/wp-json/wp/v2'  # Obtener la URL desde la entrada
    # user = 'tramitesbolivia'  # Obtener el usuario desde la entrada
    # password = 'iN2S GZah 2Eqq pTqJ hqSr bAhV'  # Obtener la contraseña desde la entrada
    
    creds = user + ':' + password
    token = base64.b64encode(creds.encode())
    header = {'Authorization': 'Basic ' + token.decode('utf-8')}

    for keyword in keyword_list:
        h1 = keyword.strip()
         #Funcion para conseguir el formato URL de la imagenes que se van a generar con Magic Post Thumbnail
        def limpiar_url(texto):
            # Quitar acentos
            texto = unidecode(texto)
            
            # Reemplazar la letra "ñ" por "n"
            texto = texto.replace('ñ', 'n').replace('Ñ', 'n')
            
            # Eliminar caracteres especiales y espacios
            texto = re.sub(r'[^a-zA-Z0-9]+', ' ', texto)
            
            # Convertir a minúsculas y eliminar espacios adicionales
            texto = texto.lower().strip()
            
            # Reemplazar espacios por guiones
            texto = texto.replace(' ', '-')
            
            return texto
        urlFormat = limpiar_url(h1)
    #GENERANDO IMAGEN DALLE
        #prompt para generar el prompt de dalle3
        def generarImg():      
            promptDalle3 = f"Crea un prompt elaborado de 2 lineas para Dalle(es un generador de imagenes con ia), debes generar el prompt en base a este titulo:{h1}. no debes poner el titulo tal cual sino que crear una imagen que tenga relacion con el titulo "
            messagesDalle3 = [{"role": "system", "content": promptDalle3},]

            chat0 = openai.ChatCompletion.create(
            model="gpt-3.5-turbo", messages=messagesDalle3
            )
            replyDalle3 = chat0.choices[0].message.content
            print(f"PROMPT DALLE3: {replyDalle3}")

            #generando imagen dalle3
            responseD = openai.Image.create(            
            prompt=replyDalle3,
            n=1,
            size="512x512"
            )

            image_url = responseD['data'][0]['url']

            # Descargar la imagen y guardarla en un archivo local
            responseD = requests.get(image_url)
            if responseD.status_code == 200:
                # Generar el nombre del archivo de forma dinámica
                image_filename = f"{urlFormat}.jpg"
                with open(image_filename, 'wb') as f:
                    # Abrir la imagen generada
                    f.write(responseD.content)
                    generated_image = Image.open(image_filename)

                    # Comprimir la imagen con una calidad específica
                    generated_image.save(image_filename, optimize=True, quality=60)

                    print("Imagen descargada exitosamente como", image_filename)

                    media = {'file': open(image_filename, 'rb')}  # Traemos la variable imagen
                    image = requests.post(url + '/media', headers=header, files=media)
                    print(image)
                    # Extrayendo postid para la featured image
                    imgId = json.loads(image.content.decode('utf-8'))['id']
                    # Realizamos doble  .post para primero poder subir la imagen y después ponerle los atributos...
                    postm = {
                        'title': urlFormat,
                        # 'caption': h1,
                        'description': h1,
                        'alt_text': h1
                    }
                    req = requests.post(url + '/media/' + str(imgId), headers=header, json=postm)
                    print(req)
                    print(imgId)
            else:
                print("Error al descargar la imagen:", responseD.status_code)    
   
        # generarImg()  
        if textGuia == "":
         insertInfo = ""
        else:
         insertInfo = "y debe estar construido en base a esta informacion: " + textGuia + ". Pero ojo no te limites a esta informacion, si no que puedes agregar mas informacion relevante, y crear subitulos relevantes tambien en base a la informacion que te di."
        prompt1 = """Escribe como un experto SEO un artículo para un blog. Sigue estas directrices:
                        1. resuelve la intención de búsqueda de un usuario que quiere saber: """ + h1 + """
                        2. el post deberá tener una extensión de 1500 palabras (o la maxima extension posible) debe ser lo mas detallado y largo posible.
                        3. la palabra clave principal para las optimizaciones SEO es """ + h1 + """
                        4. puedes usar tantos H2 y H3 como creas necesario para satisfacer la intención de búsqueda del artículo, no es necesario que los optimices todos para palabras clave.
                        5. Utiliza texto en negritas para resaltar las keywords principales o partes importantes para lo cual encapsula dentro la etiqueta strong <strong> TEXTO EN NEGRITA </strong>, tambien utiliza tablas, listas ordenadas y desordenadas, todo lo que sea necesario para responder la intencion de busqueda.
                        6. el artículo debe ser informacional."""+insertInfo+"""
                        7. Maximiza la retención del usuario, para que terminen de leer el artículo, usa un loop abierto al inicio para generar intriga.
                        8. No añadas contenido que no aporte valor, no inventes datos, todo el artículo debe ser útil.
                        9. Utiliza un lenguaje directo y sencillo, que entienda un niño de 10 años.
                        10. Por ultimo no olvides poner negritas para resaltar las partes importantes y keywords principales en los parrafos.

                        por favor entregame los resultados en bloques de gutenberg es decir para los parrafos usa:
                        <!-- wp:paragraph -->
                        <p> </p>
                        <!-- /wp:paragraph -->
                        importante:recuerda que cada parrafo <p> individualmente debe tener un <!-- /wp:paragraph -->

                        para los h2 usa:
                        <!-- wp:heading -->
                        <h2 class="wp-block-heading"> </h2>
                        <!-- /wp:heading -->

                        para los h3 usa:
                        <!-- wp:heading {"level":3} -->
                        <h3 class="wp-block-heading"> </h3>
                        <!-- /wp:heading -->
                        (no olvides agregar el {"level":3} porque si lo olvidas me dara error)

                        para las negritas usa:
                        <strong> </strong>

                        tambien quiero pedirte que no uses las palabras "Introduccion:" y "Conclusiones:"como sueles hacer,
                        tampoco le pongas "H1:", "H2:" etc al principio.

                        Recuerda que debe ser un articulo lo mas elaborado posible te repito que debe ser muy largo.(lo maximo que puedas)
                        Recuerda tambien que primero debe ir el parrafo SEO optimizado antes que cualquier Header.
                        y por ultimo no sobreoptimizes mucho, recuerda que lo mas importante es que la web resuelva la intencion de busqueda.
                        """

        messages = [
            {"role": "system", "content": prompt1},
        ]
        print(prompt1)
        while True:
            try:
            
                chat = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo", messages=messages
                )
                reply = chat.choices[0].message.content
                print(f"ChatGPT-CONTENT: {reply}")

        #GENERANDO METATITLE
                def metaTitleFunc():
                    promptMetaTitle = f'Crea una meta title optimizada de acuerdo a los siguientes parametros:\n\
                                    1. Debe tener una longitud de entre 50 a 60 caracteres como máximo\n\
                                    2. Debe estar optimizada para la keyword: {h1}\n\
                                    3. IMPORANTE ! En lugar de poner el año (2020,2021,2022,2023 etc) siempre pon: %%currentyear%%  \n\
                                    4. NO pongas comillas al principio ni al final\n\
                                    5. NO pongas tags # \n\
                                    6. NO debe ser una metatitle que ofrece servicios sino un metatitle informacional llamativo.\n\
                                    7. La keyword principal siempre debe ir al principio.\n\
                                    8. Debes usar mayusculas o capitalización en modo título segun veas conveniente'

                    messagesMetaTitle = [
                        {"role": "system", "content": promptMetaTitle},
                    ]

                    chatM = openai.ChatCompletion.create(
                        model="gpt-3.5-turbo", messages=messagesMetaTitle
                    )
                    replyMetaTitle = chatM.choices[0].message.content
                    print(f"ChatGPT-META TITLE: {replyMetaTitle}")
                    return replyMetaTitle
        #GENERANDO EL METADESCRIPTION

                promptMetaDescription = f'Crea una meta description optimizada de acuerdo a los siguientes parametros:\n\
                                1. Debe tener una longitud de entre 120 a 140 caracteres\n\
                                2. Debe estar optimizada para la keyword: {h1}\n\
                                3. IMPORANTE ! En lugar de poner el año (2021, 2022, 2023 etc)por favor siempre pon: %%currentyear%%\n\
                                4. NO pongas comillas al principio ni al final\n\
                                5. NO pongas tags # \n\
                                6. NO debe ser una metadescription que ofrece servicios sino un metadescription informacional llamativo.\n\
                                7. NO olvides que no debe sobrepasar los 140 caracteres esto es muy importante'

                messagesMetaDescription = [
                    {"role": "system", "content": promptMetaDescription},
                ]

                chat2 = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo", messages=messagesMetaDescription
                )
                replyMetaDescription = chat2.choices[0].message.content
                print(f"ChatGPT-META DESCRIPTION: {replyMetaDescription}")

        #SCRIPT PARA GENERAR PREGUNTAS FRECUENTES
  
                def faqs():
                    promptFaq = '''Crea una seccion de preguntas frecuentes con al menos 5 preguntas y respuestas (las respuestas no deben ser muy largas) sobre ''' + h1 +'''.\n\
                        1.para titulo de las preguntas frecuentes usa esta estructura: <!-- wp:heading {"style":{"color":{"text":"#e6680d"}}} -->
                        <h2 class="wp-block-heading has-text-color" style="color:#e6680d">Preguntas Frecuentes | ''' + h1.title() +''' [year_actual]</h2>
                        <!-- /wp:heading -->  \n\ 
                            ponle un color #1F2955.
                        nota: pon [year_actual] tal cual ya que es un shortcode. 
                        2.para las preguntas usa estas etiquetas de wordpress:  <!-- wp:heading {"level":3} -->
                            <h3 class="wp-block-heading"> </h3>
                            <!-- /wp:heading --> 
                        3. para las respuestas usa estas etiquetas de wordpress:<!-- wp:paragraph -->
                            <p> </p>
                            <!-- /wp:paragraph -->
                    
                        4. Crea el JSON-LD correspondiente a las faq aqui tienes las estructura:
                        <!-- wp:html -->
                            <script type="application/ld+json">
                                {
                                "@context": "https://schema.org",
                                "@type": "FAQPage",
                                "mainEntity": [
                                {
                                "@type": "Question",
                                "name": " ",
                                "acceptedAnswer": {
                                    "@type": "Answer",
                                    "text": " "
                                }
                            
                                ]
                                }
                                </script>
                        <!-- /wp:html -->  '''
                    
                    
                    messagesFaq = [
                        {"role": "system", "content": promptFaq},
                    ]

                    chat3 = openai.ChatCompletion.create(
                        model="gpt-3.5-turbo", messages=messagesFaq
                    )
                    replyFaq = chat3.choices[0].message.content
                    print(f"ChatGPT-PREGUNTAS FRECUENTES: {replyFaq}")
                    return replyFaq

        #SCRIPT PARA INSERTAR IMAGEN EN MEDIO DEL POST
                codigo_insertar = '''       
                    <figure class="wp-block-image aligncenter size-large is-resized">
                            <img src="https://theamericanvisa.us/wp-content/uploads/2023/11/'''+ urlFormat +'''.jpg" alt="'''+ h1 +'''" width="444" height="313"/>
                    </figure>      
                    '''
                def insertar_codigo(cadena, codigo):
                # Buscar la posición de la primera coincidencia
                    posicion = cadena.find('<!-- /wp:heading -->')

                    # Insertar el código después de la coincidencia
                    if posicion != -1:
                        cadena = cadena[:posicion + len('<!-- /wp:heading -->')] + codigo + cadena[posicion + len('<!-- /wp:heading -->'):]

                    return cadena
                # Insertar el código en la cadena original
                cadena_resultante = insertar_codigo(reply, codigo_insertar)

                # print(cadena_resultante) 



        # INSERTANDO EL POST
                def verificar_contenido(contenido):
                    # Verifica si contiene al menos dos párrafos
                    num_parrafos = contenido.count("<!-- wp:paragraph -->")
                    
                    # Verifica si contiene al menos dos encabezados H2
                    num_h2 = contenido.count("<!-- wp:heading -->") + contenido.count('<!-- wp:heading {"level":2} -->')
                    
                    # Verifica si la palabra "SEO" está presente en el contenido
                    if "SEO" in contenido:
                        return False  # Si encuentra "SEO", devuelve False para reiniciar el bucle
                    # Personaliza estas condiciones según tus requisitos específicos
                    return num_parrafos >= 2 and num_h2 >= 2
                
                # # Verificar la longitud de h1
                # title = ''
                if len(h1) < 37:
                    # Ejecutar metaTitleFunc solo si la longitud es mayor que 51
                    print('IMPRIMIMOS CARACTERES LONGITUD: '+str(len(h1)))
                    title = metaTitleFunc()
                else:
                    # Si la longitud es 51 o menor, simplemente asignar h1
                    # title = str(h1)+' %%currentyear%%'
                    title = str(h1)
                if verificar_contenido(reply):
                    post = {
                        'title': h1,
                        # 'content': cadena_resultante + str(replyFaq), #con imagen dalle
                        # 'content': reply + str(faqs()), #sin imagen
                        'content': reply, #sin imagen

                        # 'status': 'publish',
                        'status': 'draft',
                        'categories': [category],#107 himnos,
                        # 'author': author,
                        # 'tags': [tag],  # Lista de etiquetas
                        # 'featured_media': imgId,
                        'yoast_meta': {
                        'yoast_wpseo_focuskw': h1,   
                        'yoast_wpseo_title': title, 
                        # 'yoast_wpseo_title': h1+' %%currentyear%%',
                        'yoast_wpseo_metadesc': replyMetaDescription,
                   },
                    }
                    r = requests.post(url + '/posts', headers=header, json=post)
                    print(r)
                    break
                else:
                    # El contenido no es válido, vuelve a ejecutar el bucle con la misma consulta
                    print("El contenido generado no es válido. Reintentando la consulta...")
                    time.sleep(5)
                    continue
            except Exception as e:
                print("Error:", e)
                print("Reintentando la consulta...")
                time.sleep(5)  # Agregar un retraso de 30 segundos entre intentos
                continue  # Reintentar el bucle while si hay un error
  
    return jsonify({"respuesta": data})

@app.route('/status', methods=['GET'])
def server_status():
    return "SERVIDOR FLASK CORRIENDO"

if __name__ == '__main__':
    app.run(debug=True, port=7774)