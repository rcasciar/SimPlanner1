"""
Data models for the lab scheduling application.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Set, Tuple
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

@dataclass
class Laboratory:
    """Class representing a laboratory session"""
    id: int
    name: str
    duration_minutes: int
    min_students: int  # Dimensione minima del sottogruppo
    max_students: int  # Dimensione massima del sottogruppo
    allowed_rooms: List[str]
    is_small_capacity: bool = False  # Laboratori che richiedono gruppi più piccoli
    num_subgroups: int = 5  # Numero di sottogruppi in cui dividere gli studenti totali (5 per lab normali, 8 per lab piccoli)
    
    def __repr__(self):
        return f"{self.name} ({self.duration_minutes}min)"
        
    def get_group_type_description(self) -> str:
        """Restituisce una descrizione del tipo di gruppo per questo laboratorio"""
        if self.is_small_capacity:
            return "Piccola Capacità (8-10 studenti per gruppo)"
        else:
            return "Capacità Standard (12-15 studenti per gruppo)"

@dataclass
class Room:
    """Class representing a room"""
    name: str
    capacity: int
    divisible: bool = False
    divisions: int = 1
    
    def __repr__(self):
        return self.name

@dataclass
class TimeSlot:
    """Class representing a time slot"""
    day: int  # 0-13 for the 14 days
    start_time: datetime
    end_time: datetime
    
    def __repr__(self):
        day_names = ["Day 1", "Day 2", "Day 3", "Day 4", "Day 5", 
                     "Day 6", "Day 7", "Day 8", "Day 9", "Day 10",
                     "Day 11", "Day 12", "Day 13", "Day 14"]
        return f"{day_names[self.day]} {self.start_time.strftime('%H:%M')} - {self.end_time.strftime('%H:%M')}"
    
    def overlaps(self, other: 'TimeSlot') -> bool:
        """Check if this time slot overlaps with another"""
        if self.day != other.day:
            return False
        return max(self.start_time, other.start_time) < min(self.end_time, other.end_time)
    
    def duration_minutes(self) -> int:
        """Get the duration of this time slot in minutes"""
        delta = self.end_time - self.start_time
        return int(delta.total_seconds() / 60)

@dataclass
class ScheduledLab:
    """Class representing a scheduled laboratory session"""
    lab: Laboratory
    room: Room
    time_slot: TimeSlot
    students: List[int]  # List of student IDs
    
    def __repr__(self):
        return f"{self.lab.name} in {self.room.name} at {self.time_slot}"

class ScheduleData:
    """Class containing all schedule data and helper methods"""
    
    def __init__(self, total_students: int = 75):
        self.total_students = total_students
        self.laboratories = self._create_laboratories()
        self.rooms = self._create_rooms()
        self.scheduled_labs: List[ScheduledLab] = []
        self.device_manager = LabDeviceManager()
        # Lista di laboratori personalizzati aggiunti dall'utente
        self.custom_labs: List[Laboratory] = []
        # Lista di ID laboratori selezionati per lo scheduling
        self.selected_lab_ids: List[int] = []
        # Inizializza con tutti i laboratori selezionati
        self.selected_lab_ids = [lab.id for lab in self.laboratories]
    
    def add_custom_lab(self, name: str, duration_minutes: int, min_students: int, max_students: int, 
                       allowed_rooms: List[str], is_small_capacity: bool = False, num_subgroups: int = 5) -> Laboratory:
        """
        Aggiunge un laboratorio personalizzato alla lista
        
        Args:
            name: Nome del laboratorio
            duration_minutes: Durata in minuti (150, 300 o 450)
            min_students: Numero minimo di studenti
            max_students: Numero massimo di studenti
            allowed_rooms: Lista di nomi di aule consentite
            is_small_capacity: Se è un laboratorio a capacità ridotta
            num_subgroups: Numero di sottogruppi in cui dividere gli studenti (default: 5)
            
        Returns:
            Il laboratorio appena creato
        """
        # Calcola il prossimo ID disponibile (dopo labs predefiniti + custom)
        next_id = 17 + len(self.custom_labs)
        
        # Creare il nuovo laboratorio
        new_lab = Laboratory(
            id=next_id,
            name=name,
            duration_minutes=duration_minutes,
            min_students=min_students,
            max_students=max_students,
            allowed_rooms=allowed_rooms,
            is_small_capacity=is_small_capacity,
            num_subgroups=num_subgroups
        )
        
        # Aggiungi alla lista dei laboratori personalizzati
        self.custom_labs.append(new_lab)
        
        # Aggiungi all'elenco di laboratori totali
        self.laboratories.append(new_lab)
        
        # Seleziona automaticamente il nuovo laboratorio
        self.selected_lab_ids.append(next_id)
        
        return new_lab
    
    def get_all_labs_with_selection(self) -> List[Tuple[Laboratory, bool]]:
        """
        Restituisce tutti i laboratori disponibili con informazione se sono selezionati
        
        Returns:
            Lista di tuple (laboratorio, selezionato)
        """
        return [(lab, lab.id in self.selected_lab_ids) for lab in self.laboratories]
    
    def get_selected_labs(self) -> List[Laboratory]:
        """
        Restituisce solo i laboratori selezionati per lo scheduling
        
        Returns:
            Lista di laboratori selezionati
        """
        return [lab for lab in self.laboratories if lab.id in self.selected_lab_ids]
    
    def set_lab_selection(self, lab_id: int, selected: bool) -> None:
        """
        Imposta lo stato di selezione di un laboratorio
        
        Args:
            lab_id: ID del laboratorio
            selected: True se selezionato, False altrimenti
        """
        if selected and lab_id not in self.selected_lab_ids:
            self.selected_lab_ids.append(lab_id)
        elif not selected and lab_id in self.selected_lab_ids:
            self.selected_lab_ids.remove(lab_id)
        
    def _create_laboratories(self) -> List[Laboratory]:
        """Create all laboratory sessions based on requirements"""
        # Calcola il numero di studenti per gruppo
        group_size = 12  # Dimensione target del gruppo (come da esempio)
        
        # Per gruppi molto piccoli, usa valori speciali
        if self.total_students <= 12:
            # Con pochi studenti, tutti fanno un gruppo unico
            min_students_regular = 1
            max_students_regular = self.total_students
            min_students_small = 1
            max_students_small = self.total_students
        # Per gruppi più grandi, usa la suddivisione in gruppi come da esempio
        else:
            # Calcola quanti gruppi creare (circa 6-8 gruppi totali)
            num_groups = max(6, min(8, self.total_students // group_size + (1 if self.total_students % group_size > 0 else 0)))
            students_per_group = max(8, min(12, self.total_students // num_groups))
            
            min_students_regular = max(8, students_per_group - 2)  # Minimo leggermente inferiore
            max_students_regular = min(15, students_per_group + 2)  # Massimo leggermente superiore
            
            min_students_small = max(4, students_per_group // 2)
            max_students_small = min(10, students_per_group - 2)
        
        # Lista dei laboratori basati sui requisiti specifici
        all_rooms = ["Florence", "Esercitazione 1", "Esercitazione 2", "Leininger 1", "Leininger 2", "Leininger 3"]
        small_rooms = ["Florence", "Esercitazione 1", "Esercitazione 2"]
        
        labs = [
            # 12 laboratori con capacità 12-15 studenti (come richiesto dal cliente)
            Laboratory(id=1, name="Igiene mani", duration_minutes=150, 
                      min_students=12, max_students=15, 
                      allowed_rooms=all_rooms),
            
            Laboratory(id=2, name="Gestione DPI", duration_minutes=150, 
                      min_students=12, max_students=15, 
                      allowed_rooms=all_rooms),
            
            Laboratory(id=3, name="Ergonomia", duration_minutes=150, 
                      min_students=12, max_students=15, 
                      allowed_rooms=all_rooms),
            
            Laboratory(id=4, name="Mobilizzazione", duration_minutes=300, 
                      min_students=12, max_students=15, 
                      allowed_rooms=all_rooms),
            
            Laboratory(id=5, name="Cura di sé", duration_minutes=300, 
                      min_students=12, max_students=15, 
                      allowed_rooms=all_rooms),
            
            Laboratory(id=6, name="Gestione ferita chirurgica", duration_minutes=150, 
                      min_students=12, max_students=15, 
                      allowed_rooms=all_rooms),
            
            Laboratory(id=7, name="Gestione lesioni cutanee", duration_minutes=150, 
                      min_students=12, max_students=15, 
                      allowed_rooms=all_rooms),
            
            Laboratory(id=8, name="Rilevazione PV", duration_minutes=300, 
                      min_students=12, max_students=15, 
                      allowed_rooms=all_rooms),
            
            Laboratory(id=9, name="Gestione dispositivi di eliminazione urinaria", duration_minutes=300, 
                      min_students=12, max_students=15, 
                      allowed_rooms=all_rooms),
            
            Laboratory(id=10, name="Venipuntura", duration_minutes=150, 
                      min_students=12, max_students=15, 
                      allowed_rooms=all_rooms),
            
            Laboratory(id=11, name="Ragionamento diagnostico", duration_minutes=450, 
                      min_students=12, max_students=15, 
                      allowed_rooms=all_rooms),
            
            Laboratory(id=12, name="Valutazione ABC", duration_minutes=150, 
                      min_students=12, max_students=15, 
                      allowed_rooms=all_rooms),
            
            # 4 laboratori con capacità 8-10 studenti (da programmare alla fine)
            # Questi laboratori hanno 8 gruppi fissi invece di 5
            Laboratory(id=13, name="Gestione mobilizzazione", duration_minutes=150, 
                      min_students=8, max_students=10, 
                      allowed_rooms=small_rooms, is_small_capacity=True, num_subgroups=8),
            
            Laboratory(id=14, name="Gestione terapia", duration_minutes=150, 
                      min_students=8, max_students=10, 
                      allowed_rooms=small_rooms, is_small_capacity=True, num_subgroups=8),
            
            Laboratory(id=15, name="Valutazione respiratoria", duration_minutes=150, 
                      min_students=8, max_students=10, 
                      allowed_rooms=small_rooms, is_small_capacity=True, num_subgroups=8),
            
            Laboratory(id=16, name="Valutazione cardiocircolatoria", duration_minutes=150, 
                      min_students=8, max_students=10, 
                      allowed_rooms=small_rooms, is_small_capacity=True, num_subgroups=8),
        ]
        return labs
    
    def _create_rooms(self) -> List[Room]:
        """Create all rooms based on requirements"""
        rooms = [
            Room(name="Florence", capacity=15),
            Room(name="Esercitazione 1", capacity=15),
            Room(name="Esercitazione 2", capacity=15),
            # Leininger is divisible into 3 rooms of 15 each
            Room(name="Leininger 1", capacity=15),
            Room(name="Leininger 2", capacity=15),
            Room(name="Leininger 3", capacity=15),
        ]
        return rooms
    
    def get_student_schedule(self, student_id: int) -> List[ScheduledLab]:
        """Get the schedule for a specific student"""
        return [lab for lab in self.scheduled_labs if student_id in lab.students]
    
    def get_room_schedule(self, room_name: str) -> List[ScheduledLab]:
        """Get the schedule for a specific room"""
        return [lab for lab in self.scheduled_labs if lab.room.name == room_name]
    
    def get_lab_schedule(self, lab_id: int) -> List[ScheduledLab]:
        """Get the schedule for a specific laboratory"""
        return [slab for slab in self.scheduled_labs if slab.lab.id == lab_id]
    
    def get_day_schedule(self, day: int) -> List[ScheduledLab]:
        """Get the schedule for a specific day"""
        return [lab for lab in self.scheduled_labs if lab.time_slot.day == day]

    def get_data_frame(self) -> pd.DataFrame:
        """Convert scheduled labs to a DataFrame for visualization"""
        data = []
        
        # Nomi dei giorni in italiano
        days = ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì"]
        
        # Nomi dei mesi in italiano
        mesi_italiani = {
            1: "Gennaio", 2: "Febbraio", 3: "Marzo", 4: "Aprile",
            5: "Maggio", 6: "Giugno", 7: "Luglio", 8: "Agosto",
            9: "Settembre", 10: "Ottobre", 11: "Novembre", 12: "Dicembre"
        }
        
        # Data di inizio (1 maggio 2025)
        start_date = datetime(2025, 5, 1)
        
        for slab in self.scheduled_labs:
            # Calculate actual day of the week (0-4 for Mon-Fri)
            week = slab.time_slot.day // 5
            weekday_idx = slab.time_slot.day % 5
            weekday = days[weekday_idx]
            
            # Calcola la data effettiva
            actual_date = start_date + timedelta(days=slab.time_slot.day)
            
            # Formatta la data come "GG Mese AAAA" in italiano
            giorno = actual_date.day
            mese = mesi_italiani[actual_date.month]
            anno = actual_date.year
            date_str = f"{giorno} {mese} {anno}"
            
            data.append({
                "Lab": slab.lab.name,
                "Room": slab.room.name,
                "Day": slab.time_slot.day,
                "Date": date_str,
                "Start": slab.time_slot.start_time.strftime("%H:%M"),
                "End": slab.time_slot.end_time.strftime("%H:%M"),
                "Students": len(slab.students),
                "Duration": slab.lab.duration_minutes
            })
        
        return pd.DataFrame(data)


@dataclass
class Device:
    """Class representing a device used in labs"""
    name: str
    description: str = ""
    
    def __repr__(self):
        return self.name


@dataclass
class DeviceRequirement:
    """Class representing the requirement of a device for a lab"""
    device: Device
    quantity: int
    
    def __repr__(self):
        return f"{self.device.name}: {self.quantity}"


@dataclass
class DeviceInventory:
    """Class representing the inventory of devices"""
    devices: Dict[str, int] = field(default_factory=dict)
    alert_threshold: int = 50
    
    def add_device(self, device_name: str, quantity: int) -> None:
        """Add a device to the inventory"""
        if device_name in self.devices:
            self.devices[device_name] += quantity
        else:
            self.devices[device_name] = quantity
    
    def use_device(self, device_name: str, quantity: int) -> bool:
        """Use a device from the inventory"""
        if device_name not in self.devices:
            return False
        
        if self.devices[device_name] < quantity:
            return False
        
        self.devices[device_name] -= quantity
        return True
    
    def check_low_inventory(self) -> List[Tuple[str, int]]:
        """Check for devices with low inventory"""
        return [(name, qty) for name, qty in self.devices.items() if qty <= self.alert_threshold]
    
    def get_inventory_level(self, device_name: str) -> int:
        """Get the current inventory level for a device"""
        return self.devices.get(device_name, 0)
    
    def to_dataframe(self) -> pd.DataFrame:
        """Convert inventory to a DataFrame"""
        data = [{"Dispositivo": name, "Quantità": qty} for name, qty in self.devices.items()]
        return pd.DataFrame(data)


@dataclass
class CompletedLab:
    """Class representing a completed lab session"""
    scheduled_lab: ScheduledLab
    completed_date: datetime
    is_completed: bool = False
    
    def __repr__(self):
        return f"{self.scheduled_lab.lab.name} completed on {self.completed_date.strftime('%Y-%m-%d')}"


class LabDeviceManager:
    """Class to manage lab devices and inventory"""
    
    def __init__(self):
        self.devices: Dict[str, Device] = {}
        self.lab_device_requirements: Dict[int, List[DeviceRequirement]] = {}
        self.inventory = DeviceInventory()
        self.completed_labs: List[CompletedLab] = []
    
    def add_device(self, name: str, description: str = "") -> Device:
        """Add a new device type"""
        device = Device(name=name, description=description)
        self.devices[name] = device
        return device
    
    def add_device_requirement(self, lab_id: int, device_name: str, quantity: int) -> bool:
        """Add a device requirement for a lab"""
        if device_name not in self.devices:
            return False
            
        device = self.devices[device_name]
        requirement = DeviceRequirement(device=device, quantity=quantity)
        
        if lab_id not in self.lab_device_requirements:
            self.lab_device_requirements[lab_id] = []
            
        self.lab_device_requirements[lab_id].append(requirement)
        return True
        
    def get_lab_requirements(self, lab_id: int) -> List[DeviceRequirement]:
        """Get the device requirements for a lab"""
        return self.lab_device_requirements.get(lab_id, [])
    
    def update_inventory(self, device_name: str, quantity: int) -> bool:
        """Update the inventory for a device"""
        if device_name not in self.devices:
            return False
            
        self.inventory.add_device(device_name, quantity)
        return True
        
    def mark_lab_completed(self, scheduled_lab: ScheduledLab) -> Tuple[bool, List[str]]:
        """Mark a lab as completed and update inventory"""
        # Check if already completed
        for completed in self.completed_labs:
            if (completed.scheduled_lab.lab.id == scheduled_lab.lab.id and 
                completed.scheduled_lab.time_slot.day == scheduled_lab.time_slot.day and
                completed.scheduled_lab.time_slot.start_time == scheduled_lab.time_slot.start_time):
                return False, ["Lab già segnato come completato"]
        
        # Get the requirements for this lab
        requirements = self.get_lab_requirements(scheduled_lab.lab.id)
        if not requirements:
            # No device requirements for this lab
            completed_lab = CompletedLab(
                scheduled_lab=scheduled_lab,
                completed_date=datetime.now(),
                is_completed=True
            )
            self.completed_labs.append(completed_lab)
            return True, []
            
        # Check and update inventory
        error_messages = []
        success = True
        
        for req in requirements:
            # Calculate total quantity needed
            total_quantity = req.quantity * len(scheduled_lab.students)
            
            # Try to use devices
            if not self.inventory.use_device(req.device.name, total_quantity):
                current_qty = self.inventory.get_inventory_level(req.device.name)
                error_messages.append(
                    f"Quantità insufficiente di {req.device.name}: richiesti {total_quantity}, disponibili {current_qty}"
                )
                success = False
        
        if success:
            # Log the completed lab
            completed_lab = CompletedLab(
                scheduled_lab=scheduled_lab,
                completed_date=datetime.now(),
                is_completed=True
            )
            self.completed_labs.append(completed_lab)
            
        return success, error_messages
        
    def check_low_inventory_alerts(self) -> List[Tuple[str, int]]:
        """Check for devices with low inventory levels"""
        return self.inventory.check_low_inventory()

    def get_device_dataframe(self) -> pd.DataFrame:
        """Get the devices as a DataFrame"""
        data = [{"Nome": device.name, "Descrizione": device.description} 
                for device in self.devices.values()]
        return pd.DataFrame(data)
        
    def get_lab_requirements_dataframe(self) -> pd.DataFrame:
        """Get the lab requirements as a DataFrame"""
        data = []
        for lab_id, requirements in self.lab_device_requirements.items():
            for req in requirements:
                data.append({
                    "Lab ID": lab_id,
                    "Dispositivo": req.device.name,
                    "Quantità per Studente": req.quantity
                })
        return pd.DataFrame(data)
        
    def get_inventory_dataframe(self) -> pd.DataFrame:
        """Get the inventory as a DataFrame"""
        return self.inventory.to_dataframe()
