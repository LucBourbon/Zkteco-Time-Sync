# Zkteco-Time-Sync

Programa para sincronizar la hora de los relojes biométricos (huelleros) **ZKTeco** conectados por red local o VPN.

> **Compatibilidad:** este proyecto está diseñado únicamente para equipos ZKTeco **legacy** que utilizan el protocolo propietario del **Standalone SDK (`ZKEMKeeper`)**, normalmente mediante TCP/UDP en el puerto **4370**. No es compatible con los modelos actuales gestionados por servidor, como **SenseFace**.

Incluye dos herramientas:

| Programa | Archivo | Uso |
|---|---|---|
| **Sincronizador automático** | `sincronizar.py` → `ZKTeco_Sincronizador.exe` | Sin ventana. Pone en todos los huelleros la hora actual de la PC. Ideal para el Programador de tareas de Windows. |
| **Sincronizador manual** | `sincronizar manual version.py` → `SincronizarManual.exe` | Con ventana. Permite elegir fecha y hora a mano, o usar la hora de la PC con un botón. |

Ambos leen la lista de equipos desde `dispositivos.json` y escriben lo que pasa en `sincronizador_log.txt`.

---

## Descarga

Descarga el `.zip` más reciente desde **Releases** (en la página del repositorio), descomprímelo en una carpeta fija (p. ej. `C:\ZKTecoSync\`) y sigue los pasos de abajo.

## 1. Requisitos

- **Windows** (usa el SDK COM de ZKTeco, no funciona en Linux/Mac).
- **SDK de ZKTeco** (`zkemkeeper.dll` y sus DLL acompañantes) **registrado** en el sistema. Ver paso 2.
- La PC debe poder llegar al huellero por red (misma red o VPN) en el puerto **4370** (TCP/UDP).
- Para ejecutar desde el código fuente: **Python de 32 bits** (la DLL de ZKTeco es de 32 bits; con Python de 64 bits no funciona).

## 2. Registrar el SDK de ZKTeco (una sola vez por PC)

Las DLL del SDK (32 bits) vienen en la carpeta `sdk/`. Pertenecen a ZKTeco y forman parte de su **Standalone SDK**, que es libre y se puede descargar desde su repositorio oficial: https://github.com/ZKTeco/Standalone-SDK

1. Clic derecho en **`registrar_sdk.bat`** → **Ejecutar como administrador**.
2. Debe terminar con "Listo. SDK de ZKTeco registrado correctamente."

El `.bat` copia `sdk\*.dll` a `C:\Windows\SysWOW64\` (o `System32` en Windows de 32 bits) y registra `zkemkeeper.dll` con `regsvr32`. Para hacerlo a mano:

```cmd
copy sdk\*.dll C:\Windows\SysWOW64\
C:\Windows\SysWOW64\regsvr32.exe C:\Windows\SysWOW64\zkemkeeper.dll
```

> Aunque uses los `.exe`, este paso es obligatorio: el programa crea el objeto `ZKEMKeeper.ZKEM.1`, que solo existe si la DLL está registrada.

## 3. Configurar los huelleros: `dispositivos.json`

Coloca `dispositivos.json` **en la misma carpeta que el programa** (`.exe` o `.py`). Un objeto por huellero:

```json
[
    {"ip": "192.168.18.205", "puerto": 4370, "numero_maquina": 1},
    {"ip": "10.8.0.15",      "puerto": 4370, "numero_maquina": 1}
]
```

| Campo | Qué es |
|---|---|
| `ip` | IP del huellero (en el equipo: Menú → Comunicación → Red/Ethernet). |
| `puerto` | Puerto de comunicación, normalmente `4370`. |
| `numero_maquina` | Nº de dispositivo (Device ID), normalmente `1`. |

Cuidado con el formato JSON: comas entre objetos, sin coma después del último, comillas dobles.

## 4. Uso

### Sincronizador automático (`ZKTeco_Sincronizador.exe`)

Doble clic. No muestra ventana: recorre todos los equipos del JSON, les pone la hora de la PC y termina. El resultado queda en `sincronizador_log.txt`.

**Programarlo para que corra solo (recomendado, p. ej. diario):**

1. Abre **Programador de tareas** → *Crear tarea básica*.
2. Desencadenador: *Diariamente* (a la hora que prefieras).
3. Acción: *Iniciar un programa* → selecciona `ZKTeco_Sincronizador.exe`.
4. **Importante:** en *Iniciar en (opcional)* pon la carpeta donde está el `.exe` (p. ej. `C:\ZKTecoSync\`). Si no, el programa no encuentra `dispositivos.json` y el log se escribe en otra parte.

> Asegúrate de que la hora de la PC sea correcta (sincronizada con internet), porque esa es la hora que se copia a los huelleros.

### Sincronizador manual (`SincronizarManual.exe`)

1. Abre el programa.
2. Elige una opción:
   - **Sincronizar con la Hora del Equipo**: pone la hora actual de la PC.
   - **Sincronizar Hora Seleccionada**: elige fecha, hora (HH) y minutos (MM) y presiona el botón. Los segundos se ponen en `00`.
3. El cuadro de texto muestra el resultado por cada equipo y el total sincronizado (`X/Y`).

## 5. Solución de problemas

Revisa `sincronizador_log.txt` (o el cuadro de texto del programa manual).

| Mensaje | Causa probable | Solución |
|---|---|---|
| `Error al crear el objeto ZKEMKeeper` | SDK no registrado, o Python de 64 bits. | Repite el paso 2. Usa Python de 32 bits. |
| `Error al conectar con <IP>. Código de error: ...` | IP incorrecta, equipo apagado, sin red/VPN, firewall bloqueando el 4370. | Haz `ping <IP>`, revisa la VPN y el firewall, verifica la IP en el huellero. |
| `No se pudo sincronizar la hora ... Código de error: ...` | Conectó pero el equipo rechazó el cambio. | Verifica `numero_maquina`; si el huellero tiene contraseña de comunicación (Comm Key), quítala o ponla en 0. |
| `El archivo 'dispositivos.json' no se encontró` / el `.exe` se cierra sin hacer nada | El JSON no está junto al programa (o falta *Iniciar en* en la tarea programada). | Pon `dispositivos.json` en la misma carpeta. |
| `Error de JSON` | El archivo tiene un error de formato. | Valídalo en https://jsonlint.com |

## 6. Para desarrolladores

### Ejecutar desde el código

Con **Python 3 de 32 bits**:

```cmd
pip install pywin32 PyQt5
python sincronizar.py
python "sincronizar manual version.py"
```

### Generar los `.exe` y el paquete para entregar

Con **Python 3 de 32 bits**:

```cmd
pip install pyinstaller pywin32 PyQt5
empaquetar.bat
```

`empaquetar.bat` compila ambos `.exe` y arma `release\ZKTeco-Time-Sync.zip` con todo lo necesario: los dos `.exe`, `sdk\`, `registrar_sdk.bat`, `dispositivos.json` y este README. Ese `.zip` es el que se sube a **GitHub → Releases** para que los usuarios lo descarguen.

Notas:
- Los `.exe` no incluyen la DLL: en cada PC donde se usen hay que correr `registrar_sdk.bat` una vez.
- `SincronizarManual.spec` usa el hook de `hooks/hook-pywin32.py`.
- El script se detiene si detecta Python de 64 bits, porque el `.exe` resultante no podría usar la DLL.

### Archivos

```
sincronizar.py                  # Versión automática (hora de la PC)
sincronizar manual version.py   # Versión con interfaz (PyQt5)
dispositivos.json               # Lista de huelleros
ZKTeco_Sincronizador.spec       # Build PyInstaller (automático)
SincronizarManual.spec          # Build PyInstaller (manual)
hooks/hook-pywin32.py           # Hook de PyInstaller para pywin32
sdk/                            # DLL del SDK de ZKTeco (32 bits)
registrar_sdk.bat               # Instala y registra el SDK (como administrador)
empaquetar.bat                  # Genera los .exe y el .zip de entrega
sincronizador_log.txt           # Log (se genera solo)
```
