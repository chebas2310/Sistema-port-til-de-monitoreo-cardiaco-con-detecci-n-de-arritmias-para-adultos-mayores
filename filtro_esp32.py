import serial
import numpy as np
from scipy.signal import butter, filtfilt, find_peaks
import time
import threading
from collections import deque

class ECGProcessor:
    def __init__(self, port='COM8', baudrate=115200):
        try:
            self.ser = serial.Serial(
                port=port,
                baudrate=baudrate,
                timeout=1,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE
            )
            time.sleep(2)  # Esperar inicialización ESP32
        except Exception as e:
            print(f"Error abriendo puerto {port}: {e}")
            return
        
        self.bpm = 0
        self.raw_signal = deque(maxlen=200)
        self.filtered_signal = deque(maxlen=200)
        self.running = True
        
        # Mismo procesamiento que con Arduino
        self.sampling_rate = 50
        self.lowcut = 0.5
        self.highcut = 15.0
        
        self.b, self.a = self.butter_bandpass()
        
        print("Procesador ECG para ESP32 iniciado")
        print(f"Puerto: {port}")
        
    def butter_bandpass(self):
        nyquist = 0.5 * self.sampling_rate
        low = max(0.01, self.lowcut / nyquist)
        high = min(0.49, self.highcut / nyquist)
        
        b, a = butter(2, [low, high], btype='band')
        return b, a
    
    def bandpass_filter(self, data):
        try:
            if len(data) > max(len(self.a), len(self.b)) * 3:
                data_array = np.array(data, dtype=float)
                filtered = filtfilt(self.b, self.a, data_array)
                return filtered.tolist()
        except Exception as e:
            print(f"Error en filtro: {e}")
        return data
    
    def simple_baseline_removal(self, data):
        if len(data) > 10:
            window = min(25, len(data))
            baseline = np.convolve(data, np.ones(window)/window, mode='same')
            corrected = np.array(data) - baseline
            return corrected.tolist()
        return data
    
    def detect_peaks_simple(self, signal):
        if len(signal) < 20:
            return []
        
        signal_array = np.array(signal)
        
        # Si señal muy plana, no hay picos
        if np.std(signal_array) < 5:
            return []
        
        mean_val = np.mean(signal_array)
        std_val = np.std(signal_array)
        height_threshold = mean_val + std_val * 0.8
        
        try:
            peaks, _ = find_peaks(
                signal_array, 
                height=height_threshold,
                distance=int(self.sampling_rate * 0.6),
                prominence=std_val * 0.5
            )
            return peaks
        except:
            return []
    
    def calculate_bpm(self, peaks):
        if len(peaks) < 2:
            return 0
        
        try:
            intervals = np.diff(peaks) / self.sampling_rate
            valid_intervals = intervals[(intervals > 0.4) & (intervals < 2.0)]
            
            if len(valid_intervals) < 1:
                return 0
            
            avg_interval = np.mean(valid_intervals)
            bpm = 60.0 / avg_interval
            
            if 40 <= bpm <= 180:
                return int(bpm)
            
        except Exception as e:
            pass
            
        return 0
    
    def read_serial_line(self):
        try:
            if self.ser.in_waiting > 0:
                raw_data = self.ser.readline()
                
                try:
                    line = raw_data.decode('utf-8').strip()
                except UnicodeDecodeError:
                    try:
                        line = raw_data.decode('ascii', errors='ignore').strip()
                    except:
                        return None
                
                # Limpiar y validar número
                cleaned_line = ''.join(char for char in line if char.isdigit() or char == '-')
                
                if cleaned_line and cleaned_line != '-':
                    return cleaned_line
                    
        except Exception as e:
            print(f"Error leyendo serial: {e}")
            
        return None
    
    def process_ecg(self):
        print("Iniciando procesamiento ESP32...")
        sample_count = 0
        
        while self.running:
            try:
                line = self.read_serial_line()
                
                if line:
                    try:
                        raw_value = int(line)
                        
                        # ESP32 envía 0-1023 (escalado)
                        if 0 <= raw_value <= 1023:
                            self.raw_signal.append(raw_value)
                            sample_count += 1
                            
                            # Procesar cada 50 muestras
                            if sample_count >= 50 and len(self.raw_signal) >= 50:
                                baseline_removed = self.simple_baseline_removal(list(self.raw_signal))
                                filtered = self.bandpass_filter(baseline_removed)
                                
                                if filtered and len(filtered) == len(baseline_removed):
                                    self.filtered_signal.clear()
                                    self.filtered_signal.extend(filtered)
                                    
                                    peaks = self.detect_peaks_simple(list(self.filtered_signal))
                                    
                                    if len(peaks) >= 2:
                                        new_bpm = self.calculate_bpm(peaks)
                                        
                                        if new_bpm > 0:
                                            if self.bpm == 0:
                                                self.bpm = new_bpm
                                            else:
                                                self.bpm = int(0.8 * self.bpm + 0.2 * new_bpm)
                                    
                                    # Enviar BPM al ESP32
                                    try:
                                        self.ser.write(f"{self.bpm}\n".encode('utf-8'))
                                    except:
                                        pass
                                    
                                    print(f"Muestra: {sample_count:4d} | RAW: {raw_value:4d} | BPM: {self.bpm:3d} | Picos: {len(peaks)}")
                                
                                sample_count = 0
                                
                    except ValueError:
                        pass
                    except Exception as e:
                        print(f"Error procesando dato: {e}")
                
                time.sleep(0.005)
                
            except Exception as e:
                print(f"Error en procesamiento: {e}")
                time.sleep(0.1)
    
    def start_processing(self):
        if hasattr(self, 'ser') and self.ser.is_open:
            self.thread = threading.Thread(target=self.process_ecg)
            self.thread.daemon = True
            self.thread.start()
            return True
        return False
    
    def stop(self):
        self.running = False
        if hasattr(self, 'ser') and self.ser.is_open:
            self.ser.close()

def list_serial_ports():
    import serial.tools.list_ports
    ports = serial.tools.list_ports.comports()
    available_ports = []
    
    print("Puertos seriales disponibles:")
    for i, port in enumerate(ports):
        print(f"  {i+1}. {port.device} - {port.description}")
        available_ports.append(port.device)
    
    return available_ports

if __name__ == "__main__":
    print("=== PROCESADOR ECG PARA ESP32 ===")
    
    available_ports = list_serial_ports()
    
    if not available_ports:
        print("No se encontraron puertos seriales.")
        exit()
    
    port = available_ports[0]
    print(f"\nUsando puerto: {port}")
    
    processor = ECGProcessor(port=port)
    
    try:
        if processor.start_processing():
            print("\nProcesamiento activo. Presiona Ctrl+C para detener.")
            print("Esperando datos del ESP32...")
            
            while True:
                time.sleep(1)
                
    except KeyboardInterrupt:
        print("\nDeteniendo aplicación...")
        processor.stop()