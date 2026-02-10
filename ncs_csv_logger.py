# -*- coding: utf-8 -*-
"""
Módulo de Registro CSV para NCS Clock
Guarda un historial de todos los fichajes en formato CSV
"""

import os
import csv
from datetime import datetime
from pathlib import Path


class FichajeCSVLogger:
    """Gestiona el registro de fichajes en un archivo CSV."""
    
    def __init__(self, archivo_csv="fichajes.csv"):
        """
        Inicializa el logger CSV.
        
        Args:
            archivo_csv: Nombre del archivo CSV (por defecto: fichajes.csv)
        """
        self.archivo_csv = archivo_csv
        self.fieldnames = [
            "fecha",
            "hora_entrada",
            "hora_salida",
            "total_horas",
            "jornada",
            "extra_ausencia",
            "observaciones"
        ]
        
        # Crear el archivo si no existe
        self._inicializar_archivo()
    
    def _inicializar_archivo(self):
        """Crea el archivo CSV con las cabeceras si no existe."""
        if not os.path.exists(self.archivo_csv):
            with open(self.archivo_csv, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=self.fieldnames)
                writer.writeheader()
            print(f"✅ Archivo CSV creado: {self.archivo_csv}")
    
    def _leer_registros(self):
        """Lee todos los registros del CSV."""
        if not os.path.exists(self.archivo_csv):
            return []
        
        registros = []
        with open(self.archivo_csv, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                registros.append(row)
        return registros
    
    def _escribir_registros(self, registros):
        """Escribe todos los registros al CSV."""
        with open(self.archivo_csv, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=self.fieldnames)
            writer.writeheader()
            writer.writerows(registros)
    
    def obtener_registro_hoy(self):
        """
        Obtiene el registro del día actual.
        
        Returns:
            dict o None: El registro de hoy si existe, None si no
        """
        fecha_hoy = datetime.now().strftime("%Y-%m-%d")
        registros = self._leer_registros()
        
        for registro in reversed(registros):  # Buscar desde el final (más reciente)
            if registro["fecha"] == fecha_hoy:
                return registro
        
        return None
    
    def registrar_entrada(self, hora_entrada, observaciones=""):
        """
        Registra una entrada (fichaje de entrada).
        
        Args:
            hora_entrada: Hora de entrada (formato HH:MM:SS)
            observaciones: Observaciones opcionales
        """
        fecha_hoy = datetime.now().strftime("%Y-%m-%d")
        registros = self._leer_registros()
        
        # Buscar si ya existe un registro de hoy
        registro_hoy = None
        indice_hoy = None
        for i, registro in enumerate(reversed(registros)):
            if registro["fecha"] == fecha_hoy:
                registro_hoy = registro
                indice_hoy = len(registros) - 1 - i
                break
        
        if registro_hoy:
            # Actualizar registro existente
            registros[indice_hoy]["hora_entrada"] = hora_entrada
            if observaciones:
                obs_anterior = registros[indice_hoy].get("observaciones", "")
                registros[indice_hoy]["observaciones"] = f"{obs_anterior} | ENTRADA: {observaciones}".strip(" | ")
            print(f"📝 Actualizado registro de hoy: entrada a las {hora_entrada}")
        else:
            # Crear nuevo registro
            nuevo_registro = {
                "fecha": fecha_hoy,
                "hora_entrada": hora_entrada,
                "hora_salida": "",
                "total_horas": "",
                "jornada": "",
                "extra_ausencia": "",
                "observaciones": observaciones
            }
            registros.append(nuevo_registro)
            print(f"📝 Nuevo registro creado: entrada a las {hora_entrada}")
        
        self._escribir_registros(registros)
    
    def registrar_salida(self, hora_salida, presencia="", jornada="", extra="", observaciones=""):
        """
        Registra una salida (fichaje de salida).
        
        Args:
            hora_salida: Hora de salida (formato HH:MM:SS)
            presencia: Total de horas de presencia (formato HH:MM)
            jornada: Jornada laboral (formato HH:MM)
            extra: Horas extra o ausencia
            observaciones: Observaciones opcionales
        """
        fecha_hoy = datetime.now().strftime("%Y-%m-%d")
        registros = self._leer_registros()
        
        # Buscar el registro de hoy
        registro_hoy = None
        indice_hoy = None
        for i, registro in enumerate(reversed(registros)):
            if registro["fecha"] == fecha_hoy:
                registro_hoy = registro
                indice_hoy = len(registros) - 1 - i
                break
        
        if registro_hoy:
            # Actualizar registro existente
            registros[indice_hoy]["hora_salida"] = hora_salida
            registros[indice_hoy]["total_horas"] = presencia
            registros[indice_hoy]["jornada"] = jornada
            registros[indice_hoy]["extra_ausencia"] = extra
            
            if observaciones:
                obs_anterior = registros[indice_hoy].get("observaciones", "")
                registros[indice_hoy]["observaciones"] = f"{obs_anterior} | SALIDA: {observaciones}".strip(" | ")
            
            print(f"📝 Actualizado registro de hoy: salida a las {hora_salida}")
            print(f"   Total horas trabajadas: {presencia}")
            print(f"   {extra}")
        else:
            # No hay entrada previa, crear registro solo con salida
            nuevo_registro = {
                "fecha": fecha_hoy,
                "hora_entrada": "",
                "hora_salida": hora_salida,
                "total_horas": presencia,
                "jornada": jornada,
                "extra_ausencia": extra,
                "observaciones": f"⚠️ Salida sin entrada previa | {observaciones}".strip(" | ")
            }
            registros.append(nuevo_registro)
            print(f"⚠️  Registro de salida sin entrada previa a las {hora_salida}")
        
        self._escribir_registros(registros)
    
    def registrar_fichaje(self, tipo, hora, presencia="", jornada="", extra="", observaciones=""):
        """
        Registra un fichaje (entrada o salida).
        
        Args:
            tipo: "ENTRADA" o "SALIDA"
            hora: Hora del fichaje (formato HH:MM:SS)
            presencia: Total de horas de presencia (formato HH:MM)
            jornada: Jornada laboral (formato HH:MM)
            extra: Horas extra o ausencia
            observaciones: Observaciones opcionales
        """
        if tipo.upper() == "ENTRADA":
            self.registrar_entrada(hora, observaciones)
        elif tipo.upper() == "SALIDA":
            self.registrar_salida(hora, presencia, jornada, extra, observaciones)
        else:
            print(f"⚠️  Tipo de fichaje desconocido: {tipo}")
    
    def mostrar_resumen_mes(self, mes=None, año=None):
        """
        Muestra un resumen de los fichajes del mes.
        
        Args:
            mes: Mes (1-12), None para el mes actual
            año: Año, None para el año actual
        """
        if mes is None:
            mes = datetime.now().month
        if año is None:
            año = datetime.now().year
        
        registros = self._leer_registros()
        
        # Filtrar registros del mes
        registros_mes = []
        for registro in registros:
            fecha = datetime.strptime(registro["fecha"], "%Y-%m-%d")
            if fecha.month == mes and fecha.year == año:
                registros_mes.append(registro)
        
        if not registros_mes:
            print(f"No hay registros para {mes:02d}/{año}")
            return
        
        print("=" * 80)
        print(f"RESUMEN DEL MES {mes:02d}/{año}")
        print("=" * 80)
        print(f"{'Fecha':<12} {'Entrada':<10} {'Salida':<10} {'Total':<10} {'Jornada':<10} {'Extra/Aus.':<15}")
        print("-" * 80)
        
        for registro in registros_mes:
            fecha = registro["fecha"]
            entrada = registro["hora_entrada"] or "--:--"
            salida = registro["hora_salida"] or "--:--"
            total = registro["total_horas"] or "--:--"
            jornada = registro["jornada"] or "--:--"
            extra = registro["extra_ausencia"] or "--"
            
            print(f"{fecha:<12} {entrada:<10} {salida:<10} {total:<10} {jornada:<10} {extra:<15}")
        
        print("=" * 80)
        print(f"Total de días registrados: {len(registros_mes)}")
        print("=" * 80)


# Función de prueba standalone
if __name__ == "__main__":
    print("Probando el módulo de registro CSV...")
    
    logger = FichajeCSVLogger("fichajes_test.csv")
    
    # Simular entrada
    logger.registrar_entrada("09:03:45", "Entrada automática")
    
    # Simular salida
    logger.registrar_salida("18:15:30", "09:12", "08:00", "Extr. 01:12", "Salida automática")
    
    # Mostrar resumen
    logger.mostrar_resumen_mes()
    
    print("\n✅ Prueba completada. Revisa el archivo 'fichajes_test.csv'")
