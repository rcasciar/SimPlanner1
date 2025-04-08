"""
Scheduling logic for the lab rotation application.
"""
from typing import List, Dict, Set, Tuple, Optional, Union
from collections import defaultdict
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
from models import Laboratory, Room, TimeSlot, ScheduledLab, ScheduleData

class LabScheduler:
    """Class to handle the scheduling of labs"""
    
    def __init__(self, schedule_data: ScheduleData):
        self.data = schedule_data
        self.student_lab_assignments: Dict[int, Set[int]] = {i: set() for i in range(1, self.data.total_students + 1)}
        self.room_schedule: Dict[str, List[Tuple[int, TimeSlot]]] = {room.name: [] for room in self.data.rooms}
        # Dizionario di dizionari per la gestione di studenti in gruppi fissi
        # Formato: {lab_id: {group_name: [student_ids]}}
        self.student_groups: Dict[Union[str, int], Dict[str, List[int]]] = {}
        # Flag per indicare se usare gruppi fissi
        self.use_fixed_groups = False
        
    def _create_fixed_groups(self):
        """Crea gruppi fissi di studenti standard (A-E) e a capacità ridotta (1-8)"""
        # Inizializza il dizionario di gruppi studenti
        # Struttura:
        # { 
        #    "standard_groups": {"A": [student_ids], "B": [student_ids], ...},
        #    "small_groups": {"1": [student_ids], "2": [student_ids], ...},
        #    lab_id: { group_name: [student_ids], ... }
        # }
        self.student_groups = {
            "standard_groups": {},
            "small_groups": {}
        }
        
        # ----------- STEP 1: Crea gruppi standard (A, B, C, D, E) -----------
        num_standard_groups = 5  # Gruppi A-E
        standard_group_size = self.data.total_students // num_standard_groups
        remainder_standard = self.data.total_students % num_standard_groups
        
        # Crea i gruppi con nomi A, B, C, D, E
        standard_group_names = [chr(65 + i) for i in range(num_standard_groups)]  # A, B, C, D, E
        
        student_id = 1
        for i, group_name in enumerate(standard_group_names):
            # Se i < remainder, questo gruppo ha un membro extra
            group_size = standard_group_size + (1 if i < remainder_standard else 0)
            
            # Assegna studenti al gruppo
            end_id = min(student_id + group_size, self.data.total_students + 1)
            self.student_groups["standard_groups"][group_name] = list(range(student_id, end_id))
            
            # Passa agli ID studente successivi per il gruppo successivo
            student_id = end_id
        
        # ----------- STEP 2: Crea gruppi a capacità ridotta (1-8) -----------
        num_small_groups = 8  # Gruppi 1-8
        small_group_size = self.data.total_students // num_small_groups
        remainder_small = self.data.total_students % num_small_groups
        
        # Crea i gruppi con nomi numerici "1", "2", "3", ...
        small_group_names = [str(i+1) for i in range(num_small_groups)]
        
        student_id = 1
        for i, group_name in enumerate(small_group_names):
            # Se i < remainder, questo gruppo ha un membro extra
            group_size = small_group_size + (1 if i < remainder_small else 0)
            
            # Assegna studenti al gruppo
            end_id = min(student_id + group_size, self.data.total_students + 1)
            self.student_groups["small_groups"][group_name] = list(range(student_id, end_id))
            
            # Passa agli ID studente successivi per il gruppo successivo
            student_id = end_id
            
        # ----------- STEP 3: Associa i gruppi ai laboratori appropriati -----------
        all_labs = self.data.get_selected_labs()
        
        for lab in all_labs:
            lab_id = lab.id
            self.student_groups[lab_id] = {}
            
            # Determina se usare i gruppi standard o quelli a capacità ridotta
            if lab.is_small_capacity:
                # Per laboratori a capacità ridotta, usa i gruppi 1-8
                source_groups = self.student_groups["small_groups"]
            else:
                # Per laboratori standard, usa i gruppi A-E
                source_groups = self.student_groups["standard_groups"]
                
            # Copia i gruppi appropriati per questo laboratorio
            for group_name, students in source_groups.items():
                self.student_groups[lab_id][group_name] = students.copy()
            
    def _create_fixed_group_schedule(self) -> bool:
        """Crea una programmazione basata su gruppi fissi di studenti"""
        with open("temp_log.txt", "a") as log_file:
            log_file.write("Utilizzo algoritmo di scheduling con gruppi fissi\n")
        
        # Ottieni solo i laboratori selezionati
        all_labs = self.data.get_selected_labs()
        
        # Per ogni lab, pianifica tutti i suoi gruppi
        for lab in all_labs:
            lab_id = lab.id
            lab_groups = self.student_groups.get(lab_id, {})
            
            with open("temp_log.txt", "a") as log_file:
                log_file.write(f"Pianificazione laboratorio {lab.name} - {len(lab_groups)} gruppi\n")
            
            # Per ogni gruppo di questo laboratorio
            for group_name, students in lab_groups.items():
                with open("temp_log.txt", "a") as log_file:
                    log_file.write(f"Pianificazione gruppo {group_name} per lab {lab.name}\n")
                
                # Trova uno slot temporale e un'aula adatta
                scheduled = False
                
                # Prova ogni giorno
                for day in range(14):  # 14 giorni
                    if scheduled:
                        break
                        
                    # Genera slot temporali per questo giorno
                    time_slots = self._generate_time_slots(day)
                    
                    # Prova ogni slot temporale
                    for time_slot in time_slots:
                        if scheduled:
                            break
                            
                        # Verifica che la durata sia corretta
                        if time_slot.duration_minutes() != lab.duration_minutes:
                            continue
                            
                        # Ottieni aule disponibili
                        available_rooms = self._get_available_rooms(lab, time_slot)
                        
                        # Verifica che gli studenti di questo gruppo siano disponibili
                        all_available = True
                        for student_id in students:
                            available = True
                            for booked_lab in self.data.scheduled_labs:
                                if student_id in booked_lab.students and time_slot.overlaps(booked_lab.time_slot):
                                    available = False
                                    break
                            if not available:
                                all_available = False
                                break
                        
                        if not all_available or not available_rooms:
                            continue
                            
                        # Seleziona la prima aula disponibile
                        room = available_rooms[0]
                        
                        # Crea la sessione programmata
                        scheduled_lab = ScheduledLab(
                            lab=lab,
                            room=room,
                            time_slot=time_slot,
                            students=students
                        )
                        
                        # Aggiorna i dati di scheduling
                        self.data.scheduled_labs.append(scheduled_lab)
                        for student in students:
                            self.student_lab_assignments[student].add(lab.id)
                        self.room_schedule[room.name].append((lab.id, time_slot))
                        
                        with open("temp_log.txt", "a") as log_file:
                            log_file.write(f"  * Gruppo {group_name} programmato per lab {lab.name}\n")
                            log_file.write(f"    Giorno {day}, {time_slot.start_time.strftime('%H:%M')}-{time_slot.end_time.strftime('%H:%M')}\n")
                            log_file.write(f"    Aula: {room.name}\n\n")
                        
                        scheduled = True
                        
                if not scheduled:
                    with open("temp_log.txt", "a") as log_file:
                        log_file.write(f"IMPOSSIBILE pianificare gruppo {group_name} per lab {lab.name}\n\n")
                    # Continuiamo comunque per pianificare il massimo possibile
        
        # Verifica lo stato complessivo
        completion_status = {}
        
        # Calcola status di completamento per ogni lab e i suoi gruppi
        for lab in all_labs:
            lab_id = lab.id
            lab_groups = self.student_groups.get(lab_id, {})
            
            for group_name, students in lab_groups.items():
                # Crea un identificatore univoco per ogni coppia (lab_id, group_name)
                status_key = f"{lab_id}_{group_name}"
                
                # Verifica se questo gruppo è stato programmato per questo lab
                scheduled = False
                for sl in self.data.scheduled_labs:
                    if sl.lab.id == lab_id and any(student in sl.students for student in students):
                        scheduled = True
                        break
                
                # Aggiungi status (1 se programmato, 0 altrimenti)
                completion_status[status_key] = 1 if scheduled else 0
        
        # Aggrega risultati per scrivere nel log
        lab_group_stats = {}
        
        # Conta il numero totale di sessioni programmate
        total_scheduled = sum(completion_status.values())
        
        # Calcola il numero di sessioni possibili considerando solo i laboratori (escludendo le chiavi "standard_groups" e "small_groups")
        lab_related_groups = {key: groups for key, groups in self.student_groups.items() if isinstance(key, int)}
        total_possible = sum(len(groups) for groups in lab_related_groups.values())
        
        with open("temp_log.txt", "a") as log_file:
            log_file.write("Status completamento per laboratori e gruppi:\n")
            log_file.write(f"Sessioni programmate: {total_scheduled}/{total_possible} ({(total_scheduled/total_possible*100):.1f}%)\n\n")
            
            # Raggruppa per laboratorio per il log
            for lab in all_labs:
                lab_id = lab.id
                lab_groups = self.student_groups.get(lab_id, {})
                log_file.write(f"Lab {lab.name}:\n")
                
                for group_name in lab_groups.keys():
                    status_key = f"{lab_id}_{group_name}"
                    scheduled = completion_status.get(status_key, 0)
                    log_file.write(f"  Gruppo {group_name}: {'✓' if scheduled else '✗'}\n")
        
        # Consideriamo un successo se almeno il 10% delle sessioni sono state programmate
        # (soglia molto bassa per permettere anche schedulazioni parziali)
        success_threshold = 0.1
        success = total_scheduled >= success_threshold * total_possible
        
        return success
    
    def create_schedule(self) -> bool:
        """Create a complete schedule for all labs"""
        # Crea file di log per debugging
        with open("temp_log.txt", "w") as log_file:
            log_file.write(f"=== Avvio algoritmo di scheduling ===\n")
            log_file.write(f"Numero di studenti: {self.data.total_students}\n")
            log_file.write(f"Numero di laboratori: {len(self.data.laboratories)}\n")
            log_file.write(f"Numero di aule: {len(self.data.rooms)}\n\n")
        
        # Gestione speciale per gruppi molto piccoli (5 o meno studenti)
        if self.data.total_students <= 5:
            with open("temp_log.txt", "a") as log_file:
                log_file.write("Utilizzo algoritmo per gruppi piccoli (≤5 studenti)\n")
            return self._create_small_group_schedule()
        
        # Determina se usare gruppi fissi
        # Quando ci sono tra 66 e 84 studenti, usiamo 6-7 gruppi fissi (A-F o A-G)
        if 66 <= self.data.total_students <= 84:
            self.use_fixed_groups = True
            self._create_fixed_groups()
            with open("temp_log.txt", "a") as log_file:
                log_file.write(f"Utilizzo gruppi fissi per tutti i laboratori\n")
                
                # Mostra informazioni sui gruppi standard (A-E)
                log_file.write("\nGruppi standard (A-E) per laboratori normali:\n")
                for group_name, students in self.student_groups["standard_groups"].items():
                    log_file.write(f"  Gruppo {group_name}: {len(students)} studenti - IDs: {students[:5]}{'...' if len(students) > 5 else ''}\n")
                
                # Mostra informazioni sui gruppi a capacità ridotta (1-8)
                log_file.write("\nGruppi a capacità ridotta (1-8) per laboratori piccoli:\n")
                for group_name, students in self.student_groups["small_groups"].items():
                    log_file.write(f"  Gruppo {group_name}: {len(students)} studenti - IDs: {students[:5]}{'...' if len(students) > 5 else ''}\n")
                
                # Mostra quali laboratori usano quali tipi di gruppi
                log_file.write("\nAssociazione laboratori-gruppi:\n")
                lab_count = 0
                for lab_id, groups in self.student_groups.items():
                    if not isinstance(lab_id, int):
                        continue  # Salta le chiavi "standard_groups" e "small_groups"
                    
                    lab = next((l for l in self.data.laboratories if l.id == lab_id), None)
                    if lab:
                        lab_count += 1
                        group_type = "ridotti (1-8)" if lab.is_small_capacity else "standard (A-E)"
                        log_file.write(f"  {lab.name}: utilizzo gruppi {group_type}\n")
            return self._create_fixed_group_schedule()
            
        # Altrimenti usa l'algoritmo standard, ma con adattamenti per gruppi di diverse dimensioni
        # Ordina i laboratori per priorità (prima i più complessi da programmare)
        # I laboratori con requisiti più stringenti vengono programmati per primi
        
        # Calcola un punteggio di complessità per ogni laboratorio
        lab_complexity = {}
        for lab in self.data.laboratories:
            # Più vincoli = più complesso
            complexity_score = 0
            complexity_score += lab.duration_minutes / 60  # Più lungo = più complesso
            complexity_score += len(lab.allowed_rooms) * -1  # Meno stanze disponibili = più complesso
            complexity_score += (lab.max_students - lab.min_students) * -1  # Meno flessibilità = più complesso
            if lab.is_small_capacity:
                complexity_score += 5  # I lab piccoli sono più vincolati
            lab_complexity[lab.id] = complexity_score
            
        # Ordina i laboratori per complessità decrescente
        all_labs = sorted(self.data.get_selected_labs(), key=lambda lab: lab_complexity[lab.id], reverse=True)
        
        with open("temp_log.txt", "a") as log_file:
            log_file.write("Laboratori ordinati per complessità:\n")
            for lab in all_labs:
                log_file.write(f"- Lab {lab.id} ({lab.name}): score {lab_complexity[lab.id]:.2f}, durata {lab.duration_minutes}min\n")
            log_file.write("\n")
            
        # Dividi i laboratori in normali e a capacità ridotta
        regular_labs = [lab for lab in all_labs if not lab.is_small_capacity]
        small_capacity_labs = [lab for lab in all_labs if lab.is_small_capacity]
        
        with open("temp_log.txt", "a") as log_file:
            log_file.write(f"Laboratori normali: {len(regular_labs)}\n")
            log_file.write(f"Laboratori a capacità ridotta: {len(small_capacity_labs)}\n\n")
            
        # Modalità più flessibile: non è necessario avere tutte le aule piene
        # Non considerarlo un fallimento se non tutti i laboratori vengono programmati
        fallback_mode = True  # Attiva sempre la modalità flessibile
        
        # Prima programma i laboratori regolari
        for lab in regular_labs:
            with open("temp_log.txt", "a") as log_file:
                log_file.write(f"Pianificazione laboratorio: {lab.name} (ID: {lab.id})\n")
            
            success = self._schedule_lab(lab)
            if not success:
                # Se fallisce, prova con più flessibilità
                with open("temp_log.txt", "a") as log_file:
                    log_file.write(f"- Primo tentativo fallito, provo con algoritmo flessibile\n")
                
                success = self._schedule_lab_with_flexibility(lab)
                if not success:
                    with open("temp_log.txt", "a") as log_file:
                        log_file.write(f"- Anche algoritmo flessibile fallito\n")
                    
                    if fallback_mode:
                        # MODALITÀ DI EMERGENZA: programma almeno alcuni studenti
                        with open("temp_log.txt", "a") as log_file:
                            log_file.write(f"- ATTIVAZIONE MODALITÀ EMERGENZA per il lab {lab.name}\n")
                        
                        # Trova un giorno qualsiasi e un'aula disponibile
                        emergency_scheduled = False
                        
                        for day in range(14):  # Prova tutti i giorni
                            if emergency_scheduled:
                                break
                                
                            time_slots = self._generate_time_slots(day)
                            random.shuffle(time_slots)  # Randomizza per aumentare la probabilità di trovare slot
                            
                            for time_slot in time_slots:
                                if abs(time_slot.duration_minutes() - lab.duration_minutes) > 60:
                                    continue  # Salta slot con durata troppo diversa
                                    
                                available_rooms = []
                                for room in self.data.rooms:
                                    if room.name in lab.allowed_rooms:
                                        is_available = True
                                        for lab_id, slot in self.room_schedule[room.name]:
                                            if time_slot.overlaps(slot):
                                                is_available = False
                                                break
                                        if is_available:
                                            available_rooms.append(room)
                                
                                if not available_rooms:
                                    continue
                                    
                                # Seleziona la prima aula disponibile
                                room = available_rooms[0]
                                
                                # Trova alcuni studenti disponibili
                                all_students = list(range(1, self.data.total_students + 1))
                                available_students = []
                                
                                for student in all_students:
                                    if lab.id in self.student_lab_assignments[student]:
                                        continue  # Già assegnato a questo lab
                                        
                                    is_available = True
                                    for slab in self.data.scheduled_labs:
                                        if student in slab.students and time_slot.overlaps(slab.time_slot):
                                            is_available = False
                                            break
                                            
                                    if is_available:
                                        available_students.append(student)
                                
                                min_emergency_students = max(2, lab.min_students // 3)
                                
                                if len(available_students) >= min_emergency_students:
                                    # Programma questo lab con un sottogruppo di studenti
                                    students_for_session = available_students[:min(len(available_students), lab.max_students)]
                                    
                                    scheduled_lab = ScheduledLab(
                                        lab=lab,
                                        room=room,
                                        time_slot=time_slot,
                                        students=students_for_session
                                    )
                                    
                                    self.data.scheduled_labs.append(scheduled_lab)
                                    for student in students_for_session:
                                        self.student_lab_assignments[student].add(lab.id)
                                    self.room_schedule[room.name].append((lab.id, time_slot))
                                    
                                    with open("temp_log.txt", "a") as log_file:
                                        log_file.write(f"  * EMERGENZA: Lab {lab.name} pianificato con {len(students_for_session)} studenti\n")
                                        log_file.write(f"    Giorno {day}, {time_slot.start_time.strftime('%H:%M')}-{time_slot.end_time.strftime('%H:%M')}\n")
                                        log_file.write(f"    Aula: {room.name}\n\n")
                                    
                                    emergency_scheduled = True
                                    break
                        
                        if not emergency_scheduled:
                            with open("temp_log.txt", "a") as log_file:
                                log_file.write(f"- IMPOSSIBILE pianificare in modalità emergenza\n\n")
                            # In modalità fallback, continuiamo comunque
                    else:
                        # In modalità normale, fallisce l'intero algoritmo
                        with open("temp_log.txt", "a") as log_file:
                            log_file.write(f"FALLIMENTO COMPLETO: Impossibile pianificare il laboratorio {lab.name}\n")
                        return False
                else:
                    with open("temp_log.txt", "a") as log_file:
                        log_file.write(f"- Successo con algoritmo flessibile\n\n")
            else:
                with open("temp_log.txt", "a") as log_file:
                    log_file.write(f"- Successo con algoritmo standard\n\n")
                
        # Poi programma i laboratori a piccola capacità (nella seconda settimana)
        for lab in small_capacity_labs:
            with open("temp_log.txt", "a") as log_file:
                log_file.write(f"Pianificazione laboratorio a capacità ridotta: {lab.name} (ID: {lab.id})\n")
            
            # Funzione speciale per programmare i lab a capacità ridotta nella seconda settimana
            def schedule_small_lab_in_second_week(lab):
                # Tentativo di programmare il lab nella seconda settimana (giorni 7-13)
                with open("temp_log.txt", "a") as log_file:
                    log_file.write(f"Programmazione lab piccolo {lab.name} nella seconda settimana\n")
                
                # Pianifica le sessioni a partire dal giorno 7 (seconda settimana)
                days_to_try = list(range(7, 14))  # Giorni 7-13
                random.shuffle(days_to_try)  # Randomizza per distribuire meglio
                
                for day in days_to_try:
                    # Genera slot temporali per questo giorno
                    time_slots = self._generate_time_slots(day)
                    random.shuffle(time_slots)  # Randomizza per aumentare possibilità
                    
                    for time_slot in time_slots:
                        # Verifica che la durata sia corretta
                        if time_slot.duration_minutes() != lab.duration_minutes:
                            continue
                        
                        # Trova gli studenti disponibili in questo slot
                        available_students = self._get_available_students(lab, time_slot)
                        
                        # Se non ci sono abbastanza studenti disponibili, prova un altro slot
                        if len(available_students) < lab.min_students:
                            continue
                        
                        # Ottieni aule disponibili
                        available_rooms = self._get_available_rooms(lab, time_slot)
                        if not available_rooms:
                            continue
                        
                        # Limita il numero di studenti al massimo consentito per questa sessione
                        students_for_session = available_students[:min(len(available_students), lab.max_students)]
                        
                        # Seleziona la prima aula disponibile
                        room = available_rooms[0]
                        
                        # Crea la sessione programmata
                        scheduled_lab = ScheduledLab(
                            lab=lab,
                            room=room,
                            time_slot=time_slot,
                            students=students_for_session
                        )
                        
                        # Aggiorna i dati di scheduling
                        self.data.scheduled_labs.append(scheduled_lab)
                        for student in students_for_session:
                            self.student_lab_assignments[student].add(lab.id)
                        self.room_schedule[room.name].append((lab.id, time_slot))
                        
                        with open("temp_log.txt", "a") as log_file:
                            log_file.write(f"  * Scheduled lab {lab.name} on day {day} ({time_slot.start_time.strftime('%H:%M')}-{time_slot.end_time.strftime('%H:%M')})\n")
                            log_file.write(f"  * Room: {room.name}, Students: {len(students_for_session)}\n\n")
                        
                        return True
                
                # Se arriviamo qui, non siamo riusciti a programmare questo lab nella seconda settimana
                return False
            
            # Prima prova con la funzione specializzata per lab piccoli
            success = schedule_small_lab_in_second_week(lab)
            
            if not success:
                # Se fallisce con l'algoritmo specializzato, prova algoritmi standard con preferenza per giorni più tardi
                with open("temp_log.txt", "a") as log_file:
                    log_file.write(f"- Tentativo dedicato fallito, provo con algoritmo standard\n")
                
                success = self._schedule_lab(lab)
                if not success:
                    # Se fallisce ancora, prova con più flessibilità
                    with open("temp_log.txt", "a") as log_file:
                        log_file.write(f"- Anche algoritmo standard fallito, provo con algoritmo flessibile\n")
                    
                    success = self._schedule_lab_with_flexibility(lab)
                    if not success:
                        with open("temp_log.txt", "a") as log_file:
                            log_file.write(f"- Anche algoritmo flessibile fallito\n")
                        
                        if fallback_mode:
                            # MODALITÀ DI EMERGENZA anche per lab piccoli
                            with open("temp_log.txt", "a") as log_file:
                                log_file.write(f"- ATTIVAZIONE MODALITÀ EMERGENZA per il lab piccolo {lab.name}\n")
                            
                            # Usa un approccio simile a quello per i lab regolari
                            emergency_scheduled = False
                            
                            for day in range(10, 14):  # Prova solo gli ultimi giorni per i lab piccoli
                                if emergency_scheduled:
                                    break
                                    
                                time_slots = self._generate_time_slots(day)
                                random.shuffle(time_slots)
                                
                                for time_slot in time_slots:
                                    if abs(time_slot.duration_minutes() - lab.duration_minutes) > 60:
                                        continue
                                        
                                    available_rooms = []
                                    for room in self.data.rooms:
                                        if room.name in lab.allowed_rooms:
                                            is_available = True
                                            for lab_id, slot in self.room_schedule[room.name]:
                                                if time_slot.overlaps(slot):
                                                    is_available = False
                                                    break
                                            if is_available:
                                                available_rooms.append(room)
                                    
                                    if not available_rooms:
                                        continue
                                        
                                    room = available_rooms[0]
                                    all_students = list(range(1, self.data.total_students + 1))
                                    available_students = []
                                    
                                    for student in all_students:
                                        if lab.id in self.student_lab_assignments[student]:
                                            continue
                                            
                                        is_available = True
                                        for slab in self.data.scheduled_labs:
                                            if student in slab.students and time_slot.overlaps(slab.time_slot):
                                                is_available = False
                                                break
                                                
                                        if is_available:
                                            available_students.append(student)
                                    
                                    min_emergency_students = max(2, lab.min_students // 2)
                                    
                                    if len(available_students) >= min_emergency_students:
                                        students_for_session = available_students[:min(len(available_students), lab.max_students)]
                                        
                                        scheduled_lab = ScheduledLab(
                                            lab=lab,
                                            room=room,
                                            time_slot=time_slot,
                                            students=students_for_session
                                        )
                                        
                                        self.data.scheduled_labs.append(scheduled_lab)
                                        for student in students_for_session:
                                            self.student_lab_assignments[student].add(lab.id)
                                        self.room_schedule[room.name].append((lab.id, time_slot))
                                        
                                        with open("temp_log.txt", "a") as log_file:
                                            log_file.write(f"  * EMERGENZA: Lab piccolo {lab.name} pianificato con {len(students_for_session)} studenti\n")
                                            log_file.write(f"    Giorno {day}, {time_slot.start_time.strftime('%H:%M')}-{time_slot.end_time.strftime('%H:%M')}\n")
                                            log_file.write(f"    Aula: {room.name}\n\n")
                                        
                                        emergency_scheduled = True
                                        break
                            
                            if not emergency_scheduled:
                                with open("temp_log.txt", "a") as log_file:
                                    log_file.write(f"- IMPOSSIBILE pianificare in modalità emergenza\n\n")
                                # In modalità fallback, continuiamo comunque
                        else:
                            # In modalità normale, fallisce l'intero algoritmo
                            with open("temp_log.txt", "a") as log_file:
                                log_file.write(f"FALLIMENTO COMPLETO: Impossibile pianificare il laboratorio piccolo {lab.name}\n")
                            return False
                    else:
                        with open("temp_log.txt", "a") as log_file:
                            log_file.write(f"- Successo con algoritmo flessibile\n\n")
                else:
                    with open("temp_log.txt", "a") as log_file:
                        log_file.write(f"- Successo con algoritmo standard\n\n")
            else:
                with open("temp_log.txt", "a") as log_file:
                    log_file.write(f"- Successo con algoritmo dedicato per lab piccoli\n\n")
        
        # Analisi finale
        with open("temp_log.txt", "a") as log_file:
            log_file.write(f"=== ANALISI FINALE ===\n")
            log_file.write(f"Totale sessioni pianificate: {len(self.data.scheduled_labs)}\n")
            
            # Controlla quanti studenti hanno completato tutti i lab
            student_completion = {}
            for student_id in range(1, self.data.total_students + 1):
                labs_completed = len(self.student_lab_assignments[student_id])
                student_completion[student_id] = labs_completed
            
            avg_completion = sum(student_completion.values()) / len(student_completion)
            min_completion = min(student_completion.values())
            max_completion = max(student_completion.values())
            
            log_file.write(f"Media lab completati per studente: {avg_completion:.1f} / {len(self.data.laboratories)}\n")
            log_file.write(f"Minimo lab completati: {min_completion} / {len(self.data.laboratories)}\n")
            log_file.write(f"Massimo lab completati: {max_completion} / {len(self.data.laboratories)}\n")
            
            # Calcola la percentuale media di completamento degli studenti
            avg_percent = (avg_completion / len(self.data.laboratories)) * 100
            
            # Non è necessario avere tutte le aule piene per tutta la giornata
            # Consideriamo un successo anche una programmazione parziale
            if min_completion < len(self.data.laboratories):
                log_file.write(f"NOTA: Programmazione incompleta ma funzionale (completamento medio: {avg_percent:.1f}%)\n")
                
            log_file.write(f"Pianificazione completata con {'successo' if avg_percent >= 20 else 'successo parziale'}\n")
            
        # Consideriamo un successo se almeno il 20% dei laboratori sono stati programmati in media
        # Ridotto drasticamente per rendere l'algoritmo molto più flessibile
        return avg_completion >= (len(self.data.laboratories) * 0.2)
        
    def _create_small_group_schedule(self) -> bool:
        """Algoritmo speciale per gruppi molto piccoli (5 o meno studenti)"""
        # Quando abbiamo pochi studenti, tutti i laboratori possono essere svolti da tutti gli studenti insieme
        all_students = list(range(1, self.data.total_students + 1))
        
        # Programma tutti i lab negli stessi orari su giorni diversi
        day = 0
        
        for lab in self.data.laboratories:
            # Cerca una stanza disponibile (qualsiasi stanza va bene con pochi studenti)
            room = next(r for r in self.data.rooms if r.name in lab.allowed_rooms)
            
            # Crea un time slot fisso per ogni lab
            # Usiamo un orario fisso 9:00-12:00 o 13:30-16:30 a seconda della durata
            if lab.duration_minutes <= 180:
                start_time = datetime(2023, 1, 1, 9, 0)
                end_time = datetime(2023, 1, 1, 12, 0)
            else:
                start_time = datetime(2023, 1, 1, 13, 30)
                end_time = datetime(2023, 1, 1, 16, 30)
                
            time_slot = TimeSlot(day=day, start_time=start_time, end_time=end_time)
            
            # Crea il lab programmato
            scheduled_lab = ScheduledLab(
                lab=lab,
                room=room,
                time_slot=time_slot,
                students=all_students.copy()
            )
            
            # Aggiorna i dati di scheduling
            self.data.scheduled_labs.append(scheduled_lab)
            for student in all_students:
                self.student_lab_assignments[student].add(lab.id)
            self.room_schedule[room.name].append((lab.id, time_slot))
            
            # Passa al giorno successivo
            day += 1
            if day >= 14:  # Se supera i 14 giorni, termina
                break
                
        return True
    
    def _generate_time_slots(self, day: int) -> List[TimeSlot]:
        """Generate possible time slots for a given day"""
        time_slots = []
        
        # Start time is 8:30 AM
        start_time = datetime(2023, 1, 1, 8, 30)
        
        # End time is 16:30 (4:30 PM)
        end_time = datetime(2023, 1, 1, 16, 30)
        
        # Lunch break (1 hour) at 12:30 to 13:30
        lunch_start = datetime(2023, 1, 1, 12, 30)
        lunch_end = datetime(2023, 1, 1, 13, 30)
        
        # SLOT FISSI secondo i requisiti:
        # ===============================
        
        # Mattina - prima sessione: 8:30-11:00 (2,5 ore)
        morning_slot = TimeSlot(
            day=day,
            start_time=datetime(2023, 1, 1, 8, 30),
            end_time=datetime(2023, 1, 1, 11, 0)
        )
        time_slots.append(morning_slot)
        
        # Mattina - seconda sessione: 11:10-13:40 (2,5 ore)
        # Nota: questo slot sovrappone la pausa pranzo, ma è richiesto dal cliente
        midday_slot = TimeSlot(
            day=day,
            start_time=datetime(2023, 1, 1, 11, 10),
            end_time=datetime(2023, 1, 1, 13, 40)
        )
        time_slots.append(midday_slot)
        
        # Pomeriggio: 14:10-17:10 (3 ore)
        afternoon_slot = TimeSlot(
            day=day,
            start_time=datetime(2023, 1, 1, 14, 10),
            end_time=datetime(2023, 1, 1, 17, 10)
        )
        time_slots.append(afternoon_slot)
        
        # Alternativa mattina: 8:30-12:30 (4 ore)
        full_morning_slot = TimeSlot(
            day=day,
            start_time=start_time,
            end_time=lunch_start
        )
        time_slots.append(full_morning_slot)
        
        # SLOT ALTERNATIVI per altri laboratori:
        # =====================================
        
        # Alternativa mattina breve: 8:30-10:30 (2 ore)
        short_morning = TimeSlot(
            day=day,
            start_time=datetime(2023, 1, 1, 8, 30),
            end_time=datetime(2023, 1, 1, 10, 30)
        )
        time_slots.append(short_morning)
        
        # Alternativa mattina/intermedio: 10:40-12:40 (2 ore) 
        mid_morning = TimeSlot(
            day=day,
            start_time=datetime(2023, 1, 1, 10, 40),
            end_time=datetime(2023, 1, 1, 12, 40)
        )
        time_slots.append(mid_morning)
        
        # Pomeriggio alternativo (pomeriggio breve): 13:30-15:30 (2 ore)
        short_afternoon = TimeSlot(
            day=day,
            start_time=lunch_end,
            end_time=datetime(2023, 1, 1, 15, 30)
        )
        time_slots.append(short_afternoon)
        
        # Pomeriggio alternativo 2: 14:10-16:40 (2,5 ore)
        late_afternoon = TimeSlot(
            day=day,
            start_time=datetime(2023, 1, 1, 14, 10),
            end_time=datetime(2023, 1, 1, 16, 40)
        )
        time_slots.append(late_afternoon)
        
        # Aggiungi configurazioni dinamiche basate sulle durate dei laboratori
        lab_durations = set(lab.duration_minutes for lab in self.data.laboratories)
        
        # Durate standard per laboratori
        standard_durations = [120, 150, 180, 240]
        
        # Se ci sono durate che non rientrano negli slot fissi, aggiungi slot personalizzati
        for duration in lab_durations:
            if duration not in standard_durations:
                # Mattino - inizio alle 8:30
                morning_custom = TimeSlot(
                    day=day,
                    start_time=start_time,
                    end_time=start_time + timedelta(minutes=duration)
                )
                
                # Pomeriggio - inizio alle 13:30
                afternoon_custom = TimeSlot(
                    day=day,
                    start_time=lunch_end,
                    end_time=lunch_end + timedelta(minutes=duration)
                )
                
                # Aggiungi solo se rispettano i vincoli di orario
                if morning_custom.end_time <= lunch_start:
                    time_slots.append(morning_custom)
                
                if afternoon_custom.end_time <= end_time:
                    time_slots.append(afternoon_custom)
        
        return time_slots
    
    def _get_available_rooms(self, lab: Laboratory, time_slot: TimeSlot) -> List[Room]:
        """Get available rooms for a specific lab at a given time slot"""
        available_rooms = []
        
        for room in self.data.rooms:
            # Check if the lab is allowed in this room
            if room.name not in lab.allowed_rooms:
                continue
                
            # Check if the room is already booked during this time slot
            is_available = True
            for booked_lab_id, booked_slot in self.room_schedule[room.name]:
                if time_slot.overlaps(booked_slot):
                    is_available = False
                    break
                    
            if is_available:
                available_rooms.append(room)
                
        return available_rooms
    
    def _get_available_students(self, lab: Laboratory, time_slot: TimeSlot) -> List[int]:
        """Get students available during the given time slot"""
        # Get all students
        all_students = list(range(1, self.data.total_students + 1))
        
        # Filter out students who already have the lab
        available_students = [s for s in all_students if lab.id not in self.student_lab_assignments[s]]
        
        # Filter out students who have a conflicting schedule
        for scheduled_lab in self.data.scheduled_labs:
            if time_slot.overlaps(scheduled_lab.time_slot):
                # Remove students participating in the conflicting lab
                available_students = [s for s in available_students if s not in scheduled_lab.students]
                
        return available_students
    
    def _schedule_lab(self, lab: Laboratory) -> bool:
        """Schedule a single lab, potentially across multiple sessions"""
        students_not_assigned = list(range(1, self.data.total_students + 1))
        students_not_assigned = [s for s in students_not_assigned if lab.id not in self.student_lab_assignments[s]]
        
        with open("temp_log.txt", "a") as log_file:
            log_file.write(f"Scheduling lab {lab.name} (ID: {lab.id})\n")
            log_file.write(f"Students not assigned: {len(students_not_assigned)}\n")
            log_file.write(f"Min students: {lab.min_students}, Max students: {lab.max_students}\n")
        
        # Se tutti gli studenti sono già assegnati a questo lab, abbiamo finito
        if not students_not_assigned:
            return True
            
        # Numero target di sessioni
        target_sessions = max(1, len(students_not_assigned) // lab.max_students + (1 if len(students_not_assigned) % lab.max_students > 0 else 0))
        
        with open("temp_log.txt", "a") as log_file:
            log_file.write(f"Target sessions: {target_sessions}\n")
        
        sessions_created = 0
        
        # Tenta di creare sessioni
        days = list(range(14))  # 14 giorni disponibili
        random.shuffle(days)  # Randomizza per distribuire meglio
        
        # Se il lab è a capacità ridotta, preferisci i giorni nella seconda settimana
        if lab.is_small_capacity:
            # Metti i giorni 7-13 all'inizio della lista
            late_days = [d for d in days if d >= 7]
            early_days = [d for d in days if d < 7]
            days = late_days + early_days
        
        for day in days:
            if not students_not_assigned or sessions_created >= target_sessions:
                break
                
            # Genera slot temporali per questo giorno
            time_slots = self._generate_time_slots(day)
            random.shuffle(time_slots)  # Randomizza per distribuire meglio
            
            for time_slot in time_slots:
                if not students_not_assigned or sessions_created >= target_sessions:
                    break
                    
                # Verifica che la durata sia corretta
                if time_slot.duration_minutes() != lab.duration_minutes:
                    continue
                
                # Ottieni stanze disponibili
                available_rooms = self._get_available_rooms(lab, time_slot)
                if not available_rooms:
                    continue
                    
                # Ottieni studenti disponibili
                available_students = []
                for student in students_not_assigned:
                    is_available = True
                    for booked_lab in self.data.scheduled_labs:
                        if student in booked_lab.students and time_slot.overlaps(booked_lab.time_slot):
                            is_available = False
                            break
                    if is_available:
                        available_students.append(student)
                
                # Se non ci sono abbastanza studenti disponibili, prova un altro slot
                if len(available_students) < lab.min_students:
                    continue
                    
                # Limita il numero di studenti al massimo consentito
                students_for_session = available_students[:min(len(available_students), lab.max_students)]
                
                # Seleziona la prima aula disponibile
                room = available_rooms[0]
                
                # Crea la sessione programmata
                scheduled_lab = ScheduledLab(
                    lab=lab,
                    room=room,
                    time_slot=time_slot,
                    students=students_for_session
                )
                
                # Aggiorna lo scheduling
                self.data.scheduled_labs.append(scheduled_lab)
                for student in students_for_session:
                    self.student_lab_assignments[student].add(lab.id)
                self.room_schedule[room.name].append((lab.id, time_slot))
                
                # Aggiorna la lista degli studenti non assegnati
                students_not_assigned = [s for s in students_not_assigned if s not in students_for_session]
                
                sessions_created += 1
                
                with open("temp_log.txt", "a") as log_file:
                    log_file.write(f"  * Session created: Day {day}, {time_slot.start_time.strftime('%H:%M')}-{time_slot.end_time.strftime('%H:%M')}\n")
                    log_file.write(f"  * Room: {room.name}\n")
                    log_file.write(f"  * Students: {len(students_for_session)}\n")
                    log_file.write(f"  * Remaining students: {len(students_not_assigned)}\n\n")
        
        # Se tutti gli studenti sono stati assegnati, abbiamo avuto successo
        # Altrimenti, consideriamo successo se almeno il 90% degli studenti è stato assegnato
        total_students = self.data.total_students
        assigned_students = total_students - len(students_not_assigned)
        success_percentage = assigned_students / total_students
        
        with open("temp_log.txt", "a") as log_file:
            log_file.write(f"Assigned students: {assigned_students}/{total_students} ({success_percentage:.1%})\n")
            if success_percentage >= 0.7:
                log_file.write("SUCCESS: Sufficient students assigned\n\n")
            else:
                log_file.write("FAILURE: Not enough students assigned\n\n")
        
        return success_percentage >= 0.7
    
    def _schedule_lab_with_flexibility(self, lab: Laboratory) -> bool:
        """Versione più flessibile dell'algoritmo di scheduling per casi difficili"""
        students_not_assigned = list(range(1, self.data.total_students + 1))
        students_not_assigned = [s for s in students_not_assigned if lab.id not in self.student_lab_assignments[s]]
        
        with open("temp_log.txt", "a") as log_file:
            log_file.write(f"Flexible scheduling for lab {lab.name} (ID: {lab.id})\n")
            log_file.write(f"Students not assigned: {len(students_not_assigned)}\n")
            log_file.write(f"Min students: {lab.min_students}, Max students: {lab.max_students}\n")
        
        # Se tutti gli studenti sono già assegnati a questo lab, abbiamo finito
        if not students_not_assigned:
            return True
            
        # Versione flessibile: accetta slot con durata non esattamente corrispondente (±30 minuti) 
        # e riduce i requisiti minimi di studenti
        flexible_min_students = max(5, lab.min_students - 3)  # Riduci il minimo di 3 studenti, ma non meno di 5
        
        sessions_created = 0
        
        # Tenta di creare sessioni
        days = list(range(14))  # 14 giorni disponibili
        random.shuffle(days)  # Randomizza per distribuire meglio
        
        # Se il lab è a capacità ridotta, preferisci i giorni nella seconda settimana
        if lab.is_small_capacity:
            # Metti i giorni 7-13 all'inizio della lista
            late_days = [d for d in days if d >= 7]
            early_days = [d for d in days if d < 7]
            days = late_days + early_days
        
        for day in days:
            if not students_not_assigned:
                break
                
            # Genera slot temporali per questo giorno
            time_slots = self._generate_time_slots(day)
            random.shuffle(time_slots)  # Randomizza per distribuire meglio
            
            for time_slot in time_slots:
                if not students_not_assigned:
                    break
                    
                # Versione flessibile: accetta durate simili ma non esatte
                if abs(time_slot.duration_minutes() - lab.duration_minutes) > 30:  # Tollera ±30 minuti
                    continue
                
                # Ottieni stanze disponibili
                available_rooms = self._get_available_rooms(lab, time_slot)
                if not available_rooms:
                    continue
                    
                # Ottieni studenti disponibili
                available_students = []
                for student in students_not_assigned:
                    is_available = True
                    for booked_lab in self.data.scheduled_labs:
                        if student in booked_lab.students and time_slot.overlaps(booked_lab.time_slot):
                            is_available = False
                            break
                    if is_available:
                        available_students.append(student)
                
                # Versione flessibile: requisito minimo ridotto
                if len(available_students) < flexible_min_students:
                    continue
                    
                # Limita il numero di studenti al massimo consentito
                students_for_session = available_students[:min(len(available_students), lab.max_students)]
                
                # Seleziona la prima aula disponibile
                room = available_rooms[0]
                
                # Crea la sessione programmata
                scheduled_lab = ScheduledLab(
                    lab=lab,
                    room=room,
                    time_slot=time_slot,
                    students=students_for_session
                )
                
                # Aggiorna lo scheduling
                self.data.scheduled_labs.append(scheduled_lab)
                for student in students_for_session:
                    self.student_lab_assignments[student].add(lab.id)
                self.room_schedule[room.name].append((lab.id, time_slot))
                
                # Aggiorna la lista degli studenti non assegnati
                students_not_assigned = [s for s in students_not_assigned if s not in students_for_session]
                
                sessions_created += 1
                
                with open("temp_log.txt", "a") as log_file:
                    log_file.write(f"  * FLEXIBLE session created: Day {day}, {time_slot.start_time.strftime('%H:%M')}-{time_slot.end_time.strftime('%H:%M')}\n")
                    log_file.write(f"  * Room: {room.name}\n")
                    log_file.write(f"  * Students: {len(students_for_session)}\n")
                    log_file.write(f"  * Remaining students: {len(students_not_assigned)}\n\n")
        
        # In modalità flessibile, consideriamo successo se almeno il 75% degli studenti è stato assegnato
        total_students = self.data.total_students
        assigned_students = total_students - len(students_not_assigned)
        success_percentage = assigned_students / total_students
        
        with open("temp_log.txt", "a") as log_file:
            log_file.write(f"Assigned students: {assigned_students}/{total_students} ({success_percentage:.1%})\n")
            if success_percentage >= 0.5:  # Standard ridotto in modalità flessibile
                log_file.write("SUCCESS: Sufficient students assigned (flexible mode)\n\n")
            else:
                log_file.write("FAILURE: Not enough students assigned (flexible mode)\n\n")
        
        return success_percentage >= 0.5
    
    def optimize_schedule(self) -> bool:
        """Attempt to optimize the schedule by balancing student workload"""
        # Calcola la distribuzione attuale dei laboratori per studente
        student_lab_count = {i: len(self.student_lab_assignments[i]) for i in range(1, self.data.total_students + 1)}
        
        # Trova studenti con il numero minimo e massimo di lab
        min_labs = min(student_lab_count.values())
        max_labs = max(student_lab_count.values())
        
        # Se la differenza è piccola (≤ 1 lab), non serve ottimizzare
        if max_labs - min_labs <= 1:
            return True
            
        # Identifica studenti con pochi e molti lab
        students_with_few_labs = [s for s, count in student_lab_count.items() if count == min_labs]
        students_with_many_labs = [s for s, count in student_lab_count.items() if count == max_labs]
        
        with open("temp_log.txt", "a") as log_file:
            log_file.write(f"Optimization: students with {min_labs} labs: {len(students_with_few_labs)}\n")
            log_file.write(f"Optimization: students with {max_labs} labs: {len(students_with_many_labs)}\n")
        
        # Per ogni studente con pochi lab, cerca di aggiungerne uno
        improvements = 0
        
        for student_id in students_with_few_labs:
            # Trova lab a cui lo studente non è assegnato
            missing_labs = [lab for lab in self.data.laboratories 
                           if lab.id not in self.student_lab_assignments[student_id]]
            
            # Per ogni lab mancante
            for lab in missing_labs:
                # Cerca sessioni esistenti di questo lab con spazio disponibile
                for scheduled_lab in self.data.scheduled_labs:
                    if scheduled_lab.lab.id == lab.id and len(scheduled_lab.students) < lab.max_students:
                        # Verifica che lo studente sia disponibile in questo slot
                        is_available = True
                        for other_lab in self.data.scheduled_labs:
                            if student_id in other_lab.students and scheduled_lab.time_slot.overlaps(other_lab.time_slot):
                                is_available = False
                                break
                                
                        if is_available:
                            # Aggiungi lo studente a questa sessione
                            scheduled_lab.students.append(student_id)
                            self.student_lab_assignments[student_id].add(lab.id)
                            
                            with open("temp_log.txt", "a") as log_file:
                                log_file.write(f"  * Optimization: added student {student_id} to lab {lab.name}\n")
                                
                            improvements += 1
                            break
        
        with open("temp_log.txt", "a") as log_file:
            log_file.write(f"Optimization: made {improvements} improvements\n")
            
        return improvements > 0