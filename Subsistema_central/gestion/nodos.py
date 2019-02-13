import socket, threading
import os
import django
import sys
sys.path.append('../')
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "subsistema_central.settings")
django.setup()
import json
from django.utils import timezone
from gestion.models import Nodo
import time
import configparser

ip_escuchar = None
puerto = None
max_conexiones = None
timeout_conexion = None

def configurar():
	global ip_escuchar, puerto, max_conexiones, timeout_conexion
	config = configparser.ConfigParser()
	try:
		config.read(os.getcwd() + '/config.conf')
		ip_escuchar = config.get('CONEXION', 'ip_escuchar')
		puerto = int(config.get('CONEXION', 'puerto'))
		max_conexiones = int(config.get('CONEXION', 'max_conexiones'))
		timeout_conexion = int(config.get('CONEXION', 'timeout_conexion'))
	except Exception as e:
		print("Error cargando la configuracion. ¿Está el fichero 'config.conf' disponible en el directorio raiz de la aplicaicón?")
		exit(0)
		
def handle_connection(connection, address):
	nodo = None
	lineas_vacias = 0
	while True:
		try:
			bytes_datos = connection.recv(2048)
			datos = bytes_datos.decode()
			if not datos.strip() == "":
				lineas_vacias = 0
				paquete=datos.split("\n\n")
				cabecera=paquete[0]
				print("%s (%s)" %(cabecera, address[0]))
				metodo=cabecera[0:cabecera.index(" ")]
				slash=cabecera.index("/")
				peticion=cabecera[slash+1:cabecera.index(" ",slash,cabecera.index("HTTP"))]
				
				if metodo.upper() == "GET": 
				
					if peticion.lower() == "resource":
						info = json.loads(paquete[1])
						objetivo = None
						try:
							objetivo = Nodo.objects.get(pk=info["MAC"]) 
						except Nodo.DoesNotExist:
							print("No existe!!")
							connection.send("HTTP/1.1 404 NOT FOUND\n".encode())
						if objetivo != None and objetivo.tipo.upper().startswith("SENSOR"):
							medidas = objetivo.medida_set.all().order_by("-fecha_toma")[0:2] 
							lista=[]
							for medida in medidas:
								diccionario={}
								diccionario["PARAMETRO"]=medida.parametro
								diccionario["VALOR"]=medida.valor
								diccionario["UNIDAD"]=medida.unidad
								lista.append(diccionario)
							envio={}
							envio["TIPO"]="MEDIDAS"
							envio["MEDIDAS"]=lista
							respuesta="HTTP 200 OK\n\n"
							respuesta+=(json.dumps(envio,ensure_ascii=False)) #para aceptar caracteres no ascii
							connection.send(respuesta.encode())
						elif objetivo != None and objetivo.tipo.upper() == "MARCADOR":
							diccionario={}
							diccionario["TIPO"]="NOTA"
							diccionario["NOTA"]=""
							if objetivo.nota_set.all().count() > 0:
								nota = objetivo.nota_set.all()[objetivo.nota_set.all().count()-1] #nuevamente revisar, en toeria ahora OK :)
								diccionario["NOTA"]=nota.nota
							respuesta="HTTP 200 OK\n\n"
							respuesta+=(json.dumps(diccionario,ensure_ascii=False))
							connection.send(respuesta.encode())
					else: connection.send("HTTP/1.1 400 BAD REQUEST\n".encode())
					
				elif metodo.upper() == "POST":
				
					if peticion.lower() == "medidas":
						try: 	#para controlar NaN en JSON, producen excepción
							medidas = json.loads(paquete[1])
							for medida in medidas["MEDIDAS"]:
								nodo.medida_set.create(parametro=medida["MEDIDA"],valor=medida["VALOR"],unidad=medida["UNIDAD"],fecha_toma=timezone.now())
							connection.send("HTTP/1.1 200 OK\n".encode())
						except Exception as e:
							connection.send("HTTP/1.1 400 BAD REQUEST\n".encode())
							print("MEDIDAS: EXCEPCION %s: NAN" %address[0])
						
					elif peticion.lower() == "newnode":
						info = json.loads(paquete[1]) #paquete[1] -> el cuerpo del mensaje
						if (Nodo.objects.filter(pk=info["MAC"]).count() > 0): #ya existe, actualizar info
							nodo = Nodo.objects.get(pk=info["MAC"])
							nodo.ip = address[0]
							nodo.tipo = info["TIPO"]
							nodo.nombre = info["NOMBRE"]
							nodo.activo = True
						else: 	#alta en BD
							nodo = Nodo(mac=info["MAC"], ip=address[0], tipo=info["TIPO"], nombre=info["NOMBRE"], activo=True)				
						nodo.save()	
						connection.send("HTTP/1.1 200 OK\n".encode())
					
					elif peticion.lower() == "heartbeat":
						connection.send("HTTP/1.1 200 OK\n".encode())
					
					else: connection.send("HTTP/1.1 400 BAD REQUEST\n".encode())
				
				else: connection.send(("HTTP/1.1 405 Method Not Allowed").encode())
			else:
				lineas_vacias += 1
				if(lineas_vacias > 3): #consideramos socket cerrado
					print("Conexion cerrada! (%s)" %(address[0]))
					if (nodo != None):
						nodo.activo=False 
						nodo.save()
					connection.close()
					break
				
		except Exception as e:
			print("Try global")
			print(e)
			try: 
				if (nodo != None):
					nodo.activo=False 
					nodo.save()
			except Exception as e:
				print("Try interior: %s" %e)
			connection.close()
			return
 
def listen():
	global ip_escuchar, puerto, max_conexiones, timeout_conexion
	connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	connection.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	connection.bind((ip_escuchar, puerto))
	connection.listen(max_conexiones)
	while True:
		current_connection, address = connection.accept()
		current_connection.settimeout(timeout_conexion)
		thread = threading.Thread(target=handle_connection,args=(current_connection,address))
		thread.start()
	
def baja_nodos():
	nodos = Nodo.objects.all()
	for nodo in nodos:
		nodo.activo=False
		nodo.save()
	
def iniciar_servidor_nodos():
	configurar()
	baja_nodos()
	thread = threading.Thread(target=listen, args=())
	thread.start()
		
				