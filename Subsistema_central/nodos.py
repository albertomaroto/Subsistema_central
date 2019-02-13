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

def handle_connection(connection, address):
	nodo = None
	lineas_vacias = 0
	while True:
		try:
			bytes_datos = connection.recv(2048) #tiene que fallar aqui en el recv 
			datos = bytes_datos.decode()
			if not datos.strip() == "":
				#print(datos)
				lineas_vacias = 0
				paquete=datos.split("\n\n")
				cabecera=paquete[0]
				metodo=cabecera[0:cabecera.index(" ")]
				slash=cabecera.index("/")
				peticion=cabecera[slash+1:cabecera.index(" ",slash,cabecera.index("HTTP"))]
				
				if metodo.upper() == "GET": 
				
					if peticion.lower() == "resource":
						print("RESOURCE: INICIO %s" %address[0])
						info = json.loads(paquete[1])
						objetivo = None
						try:
							objetivo = Nodo.objects.get(pk=info["MAC"]) 
						except Nodo.DoesNotExist:
							print("No existe!!")
							connection.send("HTTP/1.1 404 NOT FOUND\n".encode())
						if objetivo != None and objetivo.tipo.upper().startswith("SENSOR"):
							medidas = objetivo.medida_set.all().order_by("-fecha_toma")[0:2] #revisar esto
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
								nota = objetivo.nota_set.all()[0] #nuevamente revisar :)
								diccionario["NOTA"]=nota.nota
							respuesta="HTTP 200 OK\n\n"
							respuesta+=(json.dumps(diccionario,ensure_ascii=False))
							connection.send(respuesta.encode())
							print("RESOURCE: FIN %s" %address[0])
					else: connection.send("HTTP/1.1 400 BAD REQUEST\n".encode())
					
				elif metodo.upper() == "POST":
				
					if peticion.lower() == "medidas":
						print("MEDIDAS: INICIO %s" %address[0])
						try: 	#para controlar NaN en JSON, producen excepción
							medidas = json.loads(paquete[1])
							for medida in medidas["MEDIDAS"]:
								nodo.medida_set.create(parametro=medida["MEDIDA"],valor=medida["VALOR"],unidad=medida["UNIDAD"],fecha_toma=timezone.now())
							connection.send("HTTP/1.1 200 OK\n".encode())
							print("MEDIDAS: FIN %s" %address[0])
						except Exception as e:
							connection.send("HTTP/1.1 400 BAD REQUEST\n".encode())
							print("MEDIDAS: EXCEPCION %s" %address[0])
						
					elif peticion.lower() == "newnode":
						print("NEWNODE: INICIO %s" %address[0])
						info = json.loads(paquete[1]) #paquete[1] -> el cuerpo del mensaje
						if (Nodo.objects.filter(pk=info["MAC"]).count() > 0):
							print("Ya existe, no se añade, solo actualizando info") #actualizar info por si un marcador lo convierten en sensor/viceversa o ha cambiado su IP
							nodo = Nodo.objects.get(pk=info["MAC"])
							nodo.ip = address[0]
							nodo.tipo = info["TIPO"]
							nodo.nombre = info["NOMBRE"]
							nodo.activo = True
						else: 	
							print("Añadiendo nodo a la BD")
							nodo = Nodo(mac=info["MAC"], ip=address[0], tipo=info["TIPO"], nombre=info["NOMBRE"], activo=True)				
						nodo.save()	
						connection.send("HTTP/1.1 200 OK\n".encode())
						print("NEWNODE: FINAL %s" %address[0])
					
					elif peticion.lower() == "heartbeat":
						print("HEARTBEAT: INICIO %s" %address[0])
						connection.send("HTTP/1.1 200 OK\n".encode())
						print("HEARTBEAT: FINAL %s" %address[0])
					
					else: connection.send("HTTP/1.1 400 BAD REQUEST\n".encode())
				
				
				else: connection.send(("HTTP/1.1 405 Method Not Allowed").encode())
			else:
				lineas_vacias += 1
				if(lineas_vacias > 3): #consideramos socket cerrado
					print("Conexion cerrada! (%s)" %(address[0]))
					if (nodo != None):
						nodo.activo=False #podria ser este el error, que estaba como nodo.estado cuando ese campo dejo de exisitir?
						nodo.save()
					connection.close()
					break
				
		except Exception as e:
			print("Try global")
			print(e)
			try: #intento resolver el control C
				if (nodo != None):
					nodo.activo=False 
					nodo.save()
			except Exception as e:
				print("Try interior: %s" %e)
			connection.close()
			return
			#exit(0)
			#break
 
def listen():
	time.sleep(0.5) #muy rara vez se cuelga SOLO en windows 10, se hace que empiece a escuchar cuando este todo levantado
	connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	connection.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	connection.bind(('0.0.0.0', 6900))
	connection.listen(20)
	while True:
		current_connection, address = connection.accept()
		current_connection.settimeout(63)
		thread = threading.Thread(target=handle_connection,args=(current_connection,address))
		thread.start()
		
def iniciar_servidor_nodos():
	print("Iniciando servidor")
	thread = threading.Thread(target=listen, args=())
	thread.start()
		
				