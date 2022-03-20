#! /usr/bin/python
# -*- coding: iso-8859-15 -*
#----------------------------------------------------------------
# Publica datos de Datalogger UTN en TB por MQTT/TLS
#
# Ing. Marcelo Castello 
#
# Universidad Tecnológica Nacional - Facultad Regional Rosario
#
# Rosario - Argentina
#
# 1/11/2019
# Revisión UNPA -  R.Oliva 03.2021
#---------------------------------------------------------------

print'   ___  ___ ___     _   _ _____ _  _ '
print'  / _ \| __/ __|___| | | |_   _| \| |'
print' | (_) | _|\__ \___| |_| | | | | .` |'
print'  \___/|___|___/    \___/  |_| |_|\_|'
print'   Revisión 03.2021 - UNPA-UARG      '
print'                                     '

from modbus_class import DModbus
import json, xlsxwriter
from datetime import datetime
from time import mktime
import argparse,sys,os
import ConfigParser, datetime, time

import paho.mqtt.client as mqttClient
from mqtt_tls_class import DMqttTls

#--Gestion de argumentos
namescript=os.path.basename(__file__).split('.py')[0]
parser=argparse.ArgumentParser ( description= 'Lee datos del datalogger protocolo MODBUS', prog=namescript, epilog='OES-UTN Rosario. Marcelo Castello castello.marcelo@gmail.com')
parser.add_argument('-V','--version', action='version', version='%(prog)s V 1.0 Modbus Client TCP',help='Muestra la version del programa')
#parser.add_argument('-v','--verbosity', action='count',help='Incrementa el nivel de verbosidad')
parser.add_argument('--conf', action='store_true',help='Archivo de configuracion')
parser.add_argument("-dl","--IP_datalogger", help="IP del datalogger a leer")
parser.add_argument("-p","--tcp_port", help="Puerto TCP del datalogger a leer")
parser.add_argument("-u","--unidad", help="Identificacion del datalogger a leer")
parser.add_argument("-rm","--registros", help="Archivo de registros Modbus")
parser.add_argument("-sr","--referencia", help="Referencia registro Modbus T real")
parser.add_argument("-c","--cantidad", help="Cantidad registros Modbus a leer T real")
parser.add_argument('--wm', action='store_true',help='Escribe uno o varios registros')
parser.add_argument('--sd', action='store_true',help='Lee datos de sd')
parser.add_argument('--tr', action='store_true',help='Publica datos en tiempo real')
parser.add_argument('--proc', action='store_true',help='Publica datos procesados')
parser.add_argument('--var', action='store_true',help='Publica variables internas')
parser.add_argument('-d','--dia',help='dia a leer en SD')
parser.add_argument('-m','--mes',help='mes a leer en SD')
parser.add_argument('-a','--ano',help='ano a leer en SD')
parser.add_argument("-ca","--cacert", help="Archivo de certificado")
parser.add_argument("-dev","--device", help="Nombre del dispositivo (Tb)")
parser.add_argument("-br","--broker", help="IP del broker")
parser.add_argument("-pm","--tls_mqtt", help="Puerto TLS para MQTT")
parser.add_argument("-t","--topic", help="Topic de publicacion para Tb")

args=parser.parse_args()
configuracion=args.conf

if (configuracion):
   #-- Parseo de archivo de configuracion
   try:
      Config = ConfigParser.ConfigParser()
      Config.read(namescript+".conf")
      #--Seccion Datalogger
      ip_datalogger = Config.get('Datalogger','ip_datalogger')
      port = Config.get('Datalogger','port_datalogger')
      unidad=int(Config.get('Datalogger','unidad'))
      start_reg_tr=int(Config.get('Datalogger','start_reg_tr'))
      cant_tr=int(Config.get('Datalogger','cantidad_tr'))
      start_reg_proc=int(Config.get('Datalogger','start_reg_proc'))
      cant_proc=int(Config.get('Datalogger','cantidad_proc'))
      start_reg_var=int(Config.get('Datalogger','start_reg_var'))
      cant_var=int(Config.get('Datalogger','cantidad_var'))
      rm_file=Config.get('Datalogger','rm_file')
      #--Seccion Dispositivo
      devname = Config.get('Dispositivo','devname')
      #--Seccion Thingsboard
      broker=Config.get('Thingsboard','broker')
      tls_mqtt_port=Config.get('Thingsboard','tls_mqtt_port')
      certfile=Config.get('Thingsboard','cert_file')
      topic=Config.get('Thingsboard','topic')
   except:
      print 'Error al leer el archivo de configuración'
      sys.exit()
   #--Parsea argumentos obligatorios
   wm=args.wm
   sd=args.sd
   tr=args.tr
   proc=args.proc
   var=args.var
else:
   ip_datalogger=args.IP_datalogger
   port=int(args.tcp_port)
   unidad=int(args.unidad)
   start_reg_tr=int(args.referencia)
   cant_tr=int(args.cantidad)
   rm_file=args.registros
   wm=False
   sd=False
   tr=False
   proc=False
   wm=args.wm
   sd=args.sd
   tr=args.tr
   proc=args.proc
   var=args.var
   if (args.dia==None):
      dia=''
   else:
      dia=int(args.dia)
   if (args.mes==None):
      mes=''
   else:
      mes=int(args.mes)
   if (args.ano==None):
      ano=''
   else:
      ano=int(args.ano)

   certfile=args.cacert
   devname=args.device
   broker=args.broker
   tls_mqtt_port=args.tls_mqtt
   topic=args.topic



#--Abre archivos de etiquetas y registros Modbus
try:
   with open(rm_file+'.json') as file_d:
      data=json.load(file_d)
   modregs_int_sys=data['V internas']
   modregs_udato=data['Udato']
   modregs_treal=data['Tiempo real']
   modregs_proc=data['Procesados']
except:
   print 'Error en la apertura del archivo de registros modbus'
   sys.exit(1)

 #--Conexión con datalogger
try:
   datalogger=DModbus()
   ret=datalogger.conectar(ip_datalogger,unidad,port)
   if (not ret):
      print 'Error en la conexión con el dispositivo remoto'
      sys.exit(1)
  #--Conexión con datalogger OK	  
   print 'OK conexión con CR1000'  
except:
   #print 'Error en la conexión con el dispositivo remoto'
   sys.exit(1)

#-- Conexión con broker Thingsboard
try:
   Tb=DMqttTls()
   print 'Parametros TB- 1) devname:'
   print devname
   print 'TB- 2) broker:'
   print broker
   print 'TB- 3) tls_mqtt_port:'
   print tls_mqtt_port
   print 'TB- 4) certfile:'
   print certfile
   print 'Datos para connect:'
   tbc=Tb.connect(devname,broker,tls_mqtt_port,certfile)
   print 'tbc result:'
   print tbc
except:
   print 'No se pudo conectar al broker'
   sys.exit(1)

#-------------- F U N C I O N E S -------------

#-- Lectura de datos de memoria SD
def lee_sd(dia,mes,ano,start_reg):
   print '------------------------------------'
   print 'Lee datos en SD'
   cant=len(modregs_proc)#38 	#-Cantidad de registros a leer
   fila=1

   #--Abre la hoja de cálculo
   libro_sd = xlsxwriter.Workbook('datos_sd_'+str(dia)+'_'+str(mes)+'_'+str(ano)+'.xlsx')
   hoja_sd = libro_sd.add_worksheet('Datos de sd')


   #--Escribe las etiquetas en archivo xls
   for j in range(0,cant):
      hoja_sd.write(0,j,modregs_proc[str(start_reg+j)])

   #--Lee  registros de la sd del datalogger (1 dia=144 registros)
   for nseq in range(0,143):
      rec=datalogger.read_records(dia,mes,ano,nseq)
      print rec
      if (rec==0):
         print 'No hay datos en SD'
      if rec!='~*':
         #--Guarda en xlsx
         for j in range(0,cant):
            hoja_sd.write(fila,j,rec[j])
         fila=fila+1
      else:
         break
   libro_sd.close()

#-- Lectura de variables internas
def pub_var(start_reg,cant):
   print '------------------------------------'
   print 'Lee datos en tiempo real y publica en Tb'
   sal=[]
   #--Obtiene los datos
   rec=datalogger.read(start_reg,cant)

   #--Publica en Tb
   for i in range(0,cant):
      sal.append({modregs_int_sys[str(start_reg+i)]:rec[i]})
   Tb.Publish(topic,json.dumps(sal))


#-- Lectura de datos en tiempo real
def pub_tr(start_reg,cant):
   print '------------------------------------'
   print 'Lee datos en tiempo real y publica en Tb'
   sal=[]
   #--Obtiene los datos
   rec=datalogger.read(start_reg,cant)

   #--Publica en Tb
   for i in range(0,cant):
      #Tb.Publish(topic,json.dumps({modregs_treal[str(start_reg+i)]:float(rec[i])}))
      #print {modregs_treal[str(start_reg+i)]:float(rec[i])}
      #time.sleep(1)
      sal.append({modregs_treal[str(start_reg+i)]:float(rec[i])})
   print sal
   #Tb.Publish("v1/devices/me/telemetry",'{"TempInver":23.1}')
   Tb.Publish(topic,json.dumps(sal))

#-- Lectura de datos procesados
def pub_proc(start_reg,cant):
   print '------------------------------------'
   print 'Publica datos procesados en Tb'
   sal={}
   sal['ts']=[]
   sal['values']=[]
   sub={}

   #--Obtiene los datos
   rec=datalogger.read(start_reg,cant)
   recu=datalogger.readUdato(40033,6)
   diau=recu[0]
   mesu=recu[1]
   anou=recu[2]
   horau=recu[3]
   minuu=recu[4]
   segu=recu[5]
   dt=datetime.datetime(anou,mesu,diau,horau,minuu,segu)
   ts=int((mktime(dt.timetuple()) + dt.microsecond/1000000.0)*1000)
   sal['ts']=ts

   #--Publica en Tb
   for i in range(0,cant):
      sub.update({modregs_proc[str(start_reg+i)]+'_proc':rec[i]})

   #print diau,mesu,anou,horau,minuu,segu
   #sal['ts']=int(datetime.datetime(anou,diau,mesu,horau,minuu,segu).strftime('%s'))
   sal['values']=sub
   Tb.Publish(topic,json.dumps(sal))
   print json.dumps(sal)

#--Lectura de fecha/hora de ultimo dato procesado
def lee_udato():
   print '------------------------------------'
   print 'Lee fecha hora ultimo dato procesado'
   print datalogger.readUdato()

#--------------- BUCLE PRINCIPAL --------------
if (wm):
   escribe_multi()
   sys.exit(0)
if (sd):
   if (dia=='' or mes=='' or ano==''):
      print 'Debe ingresar dia,mes y año de lectura'
      sys.exit(0)
   lee_sd(dia,mes,ano,40001)
   sys.exit(0)
if (tr):
   pub_tr(start_reg_tr,cant_tr)
   sys.exit(0)
if (proc):
   pub_proc(start_reg_proc,cant_proc)
   sys.exit(0)
if (var):
   pub_var(start_reg_var,cant_var)
   sys.exit(0)

print 'No se especificó ninguna acción'
print 'Especificar argumento'
print '--proc, --tr, o --sd'
sys.exit(0)
