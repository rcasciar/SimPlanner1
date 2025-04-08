"""
Scheduling logic for the lab rotation application.
"""
from typing import List, Dict, Set, Tuple, Optional
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
        # Dizionario per la gestione di studenti in gruppi fissi
        self.student_groups: Dict[str, List[int]] = {}
        # Flag per indicare se usare gruppi fissi
        self.use_fixed_groups = False
        
    def _create_fixed_groups(self):
        """Crea gruppi fissi di studenti (A-F o A-G)"""
        # Calcola il numero di gruppi e la dimensione di ciascun gruppo
        num_groups = 7 if self.data.total_students > 75 else 6
        target_group_size = self.data.total_students // num_groups
        
        # Se la divisione non è esatta, alcuni gruppi avranno uno studente in più
        remainder = self.data.total_students % num_groups
        
        # Crea i gruppi con nomi A, B, C, D, E, F, (G)
        group_names = [chr(65 + i) for i in range(num_groups)]  # 'A', 'B', 'C', ...
        
        student_id = 1
        for i, group_name in enumerate(group_names):
            # Se i < remainder, questo gruppo ha un membro extra
            group_size = target_group_size + (1 if i < remainder else 0)
            self.student_groups[group_name] = list(range(student_id, student_id + group_size))
            student_id += group_size
            
    def _create_fixed_group_schedule(self) -> bool:
        """Crea una programmazione basata su gruppi fissi di studenti"""
        with open("temp_log.txt", "a") as log_file:
            log_file.write("Utilizzo algoritmo di scheduling con gruppi fissi\n")
        
        # Ottieni solo i laboratori selezionati
        all_labs = self.data.get_selected_labs()
        
        # Per ogni combinazione di (gruppo, lab), crea una sessione
        for group_name, students in self.student_groups.items():
            for lab in all_labs:
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
        for group_name, students in self.student_groups.items():
            lab_count = 0
            for lab in all_labs:
                if any(lab.id in self.student_lab_assignments[student] for student in students):
                    lab_count += 1
            completion_status[group_name] = lab_count
        
        with open("temp_log.txt", "a") as log_file:
            log_file.write("Status completamento per gruppo:\n")
            for group_name, count in completion_status.items():
                percentage = (count / len(all_labs)) * 100
                log_file.write(f"Gruppo {group_name}: {count}/{len(all_labs)} lab completati ({percentage:.1f}%)\n")
        
        # Consideriamo un successo se almeno l'80% dei lab sono stati programmati per ogni gruppo
        success_threshold = 0.8
        success = all(count >= success_threshold * len(all_labs) for count in completion_status.values())
        
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
                log_file.write(f"Utilizzo gruppi fissi: {len(self.student_groups)} gruppi\n")
                for group_name, students in self.student_groups.items():
                    log_file.write(f"  Gruppo {group_name}: {len(students)} studenti\n")
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
        all_labs = sorted(self.data.laboratories, key=lambda lab: lab_complexity[lab.id], reverse=True)
        
        with open("temp_log.txt", "a") as log_file:
            log_file.write("Laboratori ordinati per complessità:\n")
            for lab in all_labs:
                log_file.write(f"- Lab {lab.id} ({lab.name}): score {lab_complexity[lab.id]:.2f}, durata {lab.duration_minutes}min\n")
            log_file.write("\n")
        
        # Modalità più flessibile: non è necessario avere tutte le aule piene
        # Non considerarlo un fallimento se non tutti i laboratori vengono programmati
        fallback_mode = True  # Attiva sempre la modalità flessibile
        
        # Prima programma i laboratori regolari
        regular_labs = [lab for lab in all_labs if not lab.is_small_capacity]
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
                
        # Poi programma i laboratori a piccola capacità che devono essere alla fine
        small_labs = [lab for lab in all_labs if lab.is_small_capacity]
        
        # Modifica la funzione _schedule_lab per i laboratori a piccola capacità
        # in modo da iniziare dal giorno 7 (ultima settimana) per garantire
        # che siano programmati alla fine del periodo di rotazione
        def _schedule_small_capacity_lab(lab):
            # Algoritmo identico a _schedule_lab ma inizia dal giorno 7
            with open("temp_log.txt", "a") as log_file:
                log_file.write(f"Scheduling small capacity lab {lab.name} (ID: {lab.id})\n")
                log_file.write(f"Min students: {lab.min_students}, Max students: {lab.max_students}\n")
            
            # Tenta di creare sessioni separate per gruppi di studenti
            # Divide gli studenti in gruppi in base alla capacità massima del laboratorio
            all_students = list(range(1, self.data.total_students + 1))
            students_not_assigned = [s for s in all_students if lab.id not in self.student_lab_assignments[s]]
            
            if len(students_not_assigned) == 0:
                # Tutti gli studenti sono già assegnati a questo lab
                return True
            
            # Mescola gli studenti per diversificare le assegnazioni
            random.shuffle(students_not_assigned)
            
            # Pianifica le sessioni a partire dal giorno 7 (seconda settimana)
            # cioè gli ultimi 5 giorni del periodo di 14 giorni
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
                    
                    # Rimuovi gli studenti assegnati dalla lista
                    students_not_assigned = [s for s in students_not_assigned if s not in students_for_session]
                    
                    # Se tutti gli studenti sono stati assegnati, abbiamo finito
                    if len(students_not_assigned) == 0:
                        return True
            
            # Se arriviamo qui, alcuni studenti non sono stati assegnati
            # Se almeno l'80% degli studenti è stato assegnato, consideriamo un successo parziale
            students_assigned = self.data.total_students - len(students_not_assigned)
            if students_assigned >= 0.8 * self.data.total_students:
                with open("temp_log.txt", "a") as log_file:
                    log_file.write(f"  * Partial success: {students_assigned}/{self.data.total_students} students assigned\n\n")
                return True
            
            return False
        
        for lab in small_labs:
            with open("temp_log.txt", "a") as log_file:
                log_file.write(f"Pianificazione laboratorio a capacità ridotta: {lab.name} (ID: {lab.id})\n")
            
            success = _schedule_small_capacity_lab(lab)
            if not success:
                # Se fallisce, prova con l'algoritmo originale come fallback
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
                
            log_file.write(f"Pianificazione completata con {'successo' if avg_percent >= 85 else 'successo parziale'}\n")
            
        # Consideriamo un successo se almeno l'85% dei laboratori sono stati programmati in media
        return avg_completion >= (len(self.data.laboratories) * 0.85)
        
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
        
        # Pomeriggio: 13:30-16:30 (3 ore)
        afternoon_slot = TimeSlot(
            day=day,
            start_time=lunch_end,
            end_time=end_time
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
        
        with open("temp_log.txt", "a") as log_file:
            log_file.write(f"Slot fissi generati per il giorno {day}: {len(time_slots)}\n")
            log_file.write(f"Durate laboratori disponibili: {sorted(lab_durations)}\n")
        
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
        
        with open("temp_log.txt", "a") as log_file:
            log_file.write(f"Totale slot temporali generati per il giorno {day}: {len(time_slots)}\n")
            
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
        students_to_schedule = [s for s in range(1, self.data.total_students + 1) 
                               if lab.id not in self.student_lab_assignments[s]]
        
        # Adattamento per gruppi piccoli di studenti
        if self.data.total_students <= 10:
            # Riduzione del requisito minimo di studenti per gruppi piccoli
            adjusted_min_students = min(lab.min_students, max(1, self.data.total_students // 2))
        else:
            adjusted_min_students = lab.min_students
        
        # Keep scheduling sessions until all students have been assigned
        while students_to_schedule:
            success = False
            
            # Try each day
            for day in range(14):  # 14 days
                # Generate possible time slots for this day
                time_slots = self._generate_time_slots(day)
                
                # Try each time slot
                for time_slot in time_slots:
                    # Skip if time slot duration doesn't match lab duration
                    if time_slot.duration_minutes() != lab.duration_minutes:
                        continue
                        
                    # Get available rooms
                    available_rooms = self._get_available_rooms(lab, time_slot)
                    
                    # Try each room
                    for room in available_rooms:
                        # Get available students
                        available_students = [s for s in students_to_schedule if s in 
                                            self._get_available_students(lab, time_slot)]
                        
                        # Per gruppi piccoli, usiamo il minimo adattato
                        if len(available_students) < adjusted_min_students:
                            continue
                            
                        # Determine how many students to assign (up to max capacity)
                        students_to_assign = available_students[:min(len(available_students), lab.max_students)]
                        
                        # Create the scheduled lab
                        scheduled_lab = ScheduledLab(
                            lab=lab,
                            room=room,
                            time_slot=time_slot,
                            students=students_to_assign
                        )
                        
                        # Update scheduling data
                        self.data.scheduled_labs.append(scheduled_lab)
                        for student in students_to_assign:
                            self.student_lab_assignments[student].add(lab.id)
                        self.room_schedule[room.name].append((lab.id, time_slot))
                        
                        # Remove assigned students from the pool
                        students_to_schedule = [s for s in students_to_schedule if s not in students_to_assign]
                        
                        success = True
                        break
                    
                    if success or not students_to_schedule:
                        break
                
                if success or not students_to_schedule:
                    break
            
            # Se abbiamo pochissimi studenti totali e abbiamo già programmato almeno un laboratorio
            # possiamo considerarlo un successo anche se non abbiamo programmato tutti gli studenti
            if not success and students_to_schedule:
                if self.data.total_students <= 5 and any(lab.id in labs for labs in self.student_lab_assignments.values()):
                    return True
                return False
        
        return True
    
    def _schedule_lab_with_flexibility(self, lab: Laboratory) -> bool:
        """Versione più flessibile dell'algoritmo di scheduling per casi difficili"""
        students_to_schedule = [s for s in range(1, self.data.total_students + 1) 
                              if lab.id not in self.student_lab_assignments[s]]
        
        # Modalità più flessibile - usa aumento progressivo della flessibilità
        # Prima prova con requisito minimo ridotto del 20%
        adjusted_min_students = max(1, int(lab.min_students * 0.8))
        
        # Calcola il numero minimo di sessioni necessarie
        min_sessions_needed = len(students_to_schedule) // lab.max_students
        if len(students_to_schedule) % lab.max_students > 0:
            min_sessions_needed += 1
            
        # Allocazione prioritaria: studenti con meno laboratori vengono assegnati per primi
        priority_students = sorted(
            students_to_schedule, 
            key=lambda s: len(self.student_lab_assignments[s])
        )
        
        # Massimo numero di tentativi per evitare cicli infiniti
        max_attempts = 20
        attempt = 0
        
        # Teniamo traccia delle sessioni programmate per questo laboratorio
        lab_sessions_scheduled = 0
        
        while students_to_schedule and attempt < max_attempts:
            success = False
            attempt += 1
            
            # Aggiungi progressivamente più flessibilità ad ogni tentativo
            flex_factor = min(0.9, 0.5 + (attempt * 0.1))
            current_min_students = max(1, int(adjusted_min_students * flex_factor))
            
            # Prova in ordine giorni futuri prima di giorni passati 
            # (preferisci programmare verso la fine delle 2 settimane)
            day_order = list(range(7, 14)) + list(range(0, 7))  # prima giorni 7-13, poi 0-6
            
            for day in day_order:
                time_slots = self._generate_time_slots(day)
                
                # Ottimizzazione: prova prima gli slot che non hanno conflitti con altri lab
                time_slots_with_conflicts = []
                for time_slot in time_slots:
                    if time_slot.duration_minutes() != lab.duration_minutes:
                        continue
                        
                    conflicts = 0
                    for existing_lab in self.data.scheduled_labs:
                        if time_slot.overlaps(existing_lab.time_slot):
                            conflicts += 1
                    
                    time_slots_with_conflicts.append((time_slot, conflicts))
                
                # Ordina per numero di conflitti (prima quelli con meno conflitti)
                sorted_time_slots = [ts for ts, _ in sorted(time_slots_with_conflicts, key=lambda x: x[1])]
                
                for time_slot in sorted_time_slots:
                    available_rooms = self._get_available_rooms(lab, time_slot)
                    
                    for room in available_rooms:
                        available_students = [s for s in priority_students if s in 
                                            self._get_available_students(lab, time_slot)]
                        
                        if len(available_students) < current_min_students:
                            continue
                            
                        # Limita il numero di studenti alla capacità massima del laboratorio
                        students_to_assign = available_students[:min(len(available_students), lab.max_students)]
                        
                        # Crea il laboratorio programmato
                        scheduled_lab = ScheduledLab(
                            lab=lab,
                            room=room,
                            time_slot=time_slot,
                            students=students_to_assign
                        )
                        
                        # Aggiorna i dati di scheduling
                        self.data.scheduled_labs.append(scheduled_lab)
                        for student in students_to_assign:
                            self.student_lab_assignments[student].add(lab.id)
                        self.room_schedule[room.name].append((lab.id, time_slot))
                        
                        # Rimuovi gli studenti assegnati dal pool
                        students_to_schedule = [s for s in students_to_schedule if s not in students_to_assign]
                        
                        # Aggiorna la lista di priorità
                        priority_students = [s for s in priority_students if s in students_to_schedule]
                        
                        lab_sessions_scheduled += 1
                        success = True
                        break
                    
                    if success or not students_to_schedule:
                        break
                
                if success or not students_to_schedule:
                    break
            
            # Se non ci sono abbastanza sessioni, ma abbiamo programmato qualcosa, 
            # possiamo considerarlo un successo parziale
            if not success and students_to_schedule and lab_sessions_scheduled >= min_sessions_needed // 2:
                # Assegna i rimanenti studenti alle sessioni esistenti (anche se superano il massimo)
                existing_sessions = [sl for sl in self.data.scheduled_labs if sl.lab.id == lab.id]
                
                if existing_sessions:
                    # Distribuisci gli studenti rimanenti tra le sessioni esistenti
                    while students_to_schedule and existing_sessions:
                        # Prendi la sessione con meno studenti
                        session = min(existing_sessions, key=lambda s: len(s.students))
                        
                        # Prendi uno studente
                        student = students_to_schedule[0]
                        
                        # Aggiungilo alla sessione
                        session.students.append(student)
                        
                        # Aggiorna i dati di scheduling
                        self.student_lab_assignments[student].add(lab.id)
                        
                        # Rimuovilo dalla lista
                        students_to_schedule.pop(0)
                
                # Consideriamo un successo se almeno il 90% degli studenti sono stati assegnati
                total_students = self.data.total_students
                students_assigned = total_students - len(students_to_schedule)
                if students_assigned >= total_students * 0.9:
                    return True
        
        # Se non ci sono più studenti da programmare o abbiamo raggiunto un buon compromesso
        if not students_to_schedule or lab_sessions_scheduled > 0:
            return True
            
        return False
        
    def optimize_schedule(self) -> bool:
        """Attempt to optimize the schedule by balancing student workload"""
        # This is a simple implementation that tries to balance lab assignments
        # A more sophisticated algorithm could be implemented if needed
        
        # Count labs per student
        lab_counts = {student_id: len(labs) for student_id, labs in self.student_lab_assignments.items()}
        
        # Check if everyone has all labs
        if all(count == len(self.data.laboratories) for count in lab_counts.values()):
            return True
            
        return False
