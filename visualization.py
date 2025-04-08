"""
Visualization utilities for the lab scheduling application.
"""
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import streamlit as st
from models import ScheduleData

# Aggiunta per visualizzazione tabellare in stile Word
import plotly.figure_factory as ff

def create_schedule_heatmap(schedule_data: ScheduleData, view_type: str = "room"):
    """
    Create a heatmap visualization of the schedule.
    
    Args:
        schedule_data: The schedule data
        view_type: The type of view (room, lab, day, or table)
    
    Returns:
        A Plotly figure or, for table view, a list of tables
    """
    df = schedule_data.get_data_frame()
    
    if df.empty:
        return None
    
    # Create a more detailed timescale
    time_range = pd.date_range("08:30", "16:30", freq="30min").strftime("%H:%M")
    
    # Prepare data for heatmap
    if view_type == "room":
        return _create_room_view(df, time_range)
    elif view_type == "lab":
        return _create_lab_view(df, time_range)
    elif view_type == "day":
        return _create_day_view(df, time_range)
    elif view_type == "table":
        return create_table_view(schedule_data)
    else:
        raise ValueError(f"Unknown view type: {view_type}")


def create_table_view(schedule_data: ScheduleData):
    """
    Create a table view of the schedule similar to the Word document format.
    
    Args:
        schedule_data: The schedule data
    
    Returns:
        A list of tables, one for each day with scheduled labs
    """
    if not schedule_data.scheduled_labs:
        return None
        
    # Get data frame with schedule info
    df = schedule_data.get_data_frame()
    
    if df.empty:
        return None
    
    # Prepare day-by-day tables
    days = sorted(df['Day'].unique())
    tables = []
    
    # Create a table for each day
    for day in days:
        day_df = df[df['Day'] == day]
        
        # Get all rooms used on this day
        rooms = sorted(day_df['Room'].unique())
        
        # Define fixed time slots
        time_slots = [
            {'start': '08:30', 'end': '11:00'},
            {'start': '11:10', 'end': '13:40'},
            {'start': '14:10', 'end': '17:10'}
        ]
        
        # Create header row
        header = ['DATA', 'ORARIO']
        for room in rooms:
            header.append(room.upper())
        
        # Prepare table data
        table_data = [header]
        
        # Prima riga con la data
        # Data di inizio (1 maggio 2025)
        start_date = datetime(2025, 5, 1)
        # Calcola la data effettiva aggiungendo il numero di giorni
        actual_date = start_date.replace(day=start_date.day + day)
        # Formatta la data in italiano: "GG Mese AAAA"
        date_text = actual_date.strftime("%d %B %Y").capitalize()
        first_row = [date_text, time_slots[0]['start'] + "–" + time_slots[0]['end']]
        
        has_content_first_slot = False
        # Prima fascia oraria (8:30-11:00)
        for room in rooms:
            # Filter labs for this room and first time slot
            slot_labs = day_df[
                (day_df['Room'] == room) & 
                (day_df['Start'] == time_slots[0]['start'])
            ]
            
            if not slot_labs.empty:
                has_content_first_slot = True
                lab = slot_labs.iloc[0]
                lab_name = lab['Lab']
                
                # Genera informazioni sugli studenti
                student_groups = []
                for scheduled_lab in schedule_data.scheduled_labs:
                    if (scheduled_lab.lab.name == lab_name and 
                        scheduled_lab.room.name == room and
                        scheduled_lab.time_slot.day == day and
                        scheduled_lab.time_slot.start_time.strftime("%H:%M") == time_slots[0]['start']):
                        
                        # Convert student IDs to group names
                        student_groups = [f"Gruppo {s+1}" for s in scheduled_lab.students[:6]]
                        if len(scheduled_lab.students) > 6:
                            student_groups.append(f"...+{len(scheduled_lab.students)-6}")
                        break
                        
                # Create cell content with lab name and student groups
                cell = f"{lab_name} ({lab['Duration']/60:.1f} ore)"
                if student_groups:
                    cell += "<br>" + "<br>".join(student_groups)
                
                first_row.append(cell)
            else:
                first_row.append("")
        
        # Aggiungiamo la prima riga solo se contiene almeno un laboratorio
        if has_content_first_slot:
            table_data.append(first_row)
            
            # Aggiungiamo la riga per i tutor
            tutor_row = ["", ""]
            for _ in range(len(rooms)):
                tutor_row.append("TUTOR")
            table_data.append(tutor_row)
        
        # Seconda fascia oraria (11:10-13:40)
        second_row = ["", time_slots[1]['start'] + "–" + time_slots[1]['end']]
        has_content_second_slot = False
        
        for room in rooms:
            # Filter labs for this room and second time slot
            slot_labs = day_df[
                (day_df['Room'] == room) & 
                (day_df['Start'] == time_slots[1]['start'])
            ]
            
            if not slot_labs.empty:
                has_content_second_slot = True
                lab = slot_labs.iloc[0]
                lab_name = lab['Lab']
                
                # Genera informazioni sugli studenti
                student_groups = []
                for scheduled_lab in schedule_data.scheduled_labs:
                    if (scheduled_lab.lab.name == lab_name and 
                        scheduled_lab.room.name == room and
                        scheduled_lab.time_slot.day == day and
                        scheduled_lab.time_slot.start_time.strftime("%H:%M") == time_slots[1]['start']):
                        
                        # Convert student IDs to group names
                        student_groups = [f"Gruppo {s+1}" for s in scheduled_lab.students[:6]]
                        if len(scheduled_lab.students) > 6:
                            student_groups.append(f"...+{len(scheduled_lab.students)-6}")
                        break
                        
                # Create cell content with lab name and student groups
                cell = f"{lab_name} ({lab['Duration']/60:.1f} ore)"
                if student_groups:
                    cell += "<br>" + "<br>".join(student_groups)
                
                second_row.append(cell)
            else:
                second_row.append("")
                
        # Aggiungiamo la seconda riga solo se contiene almeno un laboratorio
        if has_content_second_slot:
            table_data.append(second_row)
            
            # Aggiungiamo la riga per i tutor
            tutor_row = ["", ""]
            for _ in range(len(rooms)):
                tutor_row.append("TUTOR")
            table_data.append(tutor_row)
            
            # Aggiungiamo la pausa pranzo dopo la seconda fascia oraria
            lunch_row = ["", "13:40–14:10"]
            for _ in range(len(rooms)):
                lunch_row.append("PAUSA PRANZO")
            table_data.append(lunch_row)
        
        # Terza fascia oraria (14:10-17:10)
        third_row = ["", time_slots[2]['start'] + "–" + time_slots[2]['end']]
        has_content_third_slot = False
        
        for room in rooms:
            # Filter labs for this room and third time slot
            slot_labs = day_df[
                (day_df['Room'] == room) & 
                (day_df['Start'] == time_slots[2]['start'])
            ]
            
            if not slot_labs.empty:
                has_content_third_slot = True
                lab = slot_labs.iloc[0]
                lab_name = lab['Lab']
                
                # Genera informazioni sugli studenti
                student_groups = []
                for scheduled_lab in schedule_data.scheduled_labs:
                    if (scheduled_lab.lab.name == lab_name and 
                        scheduled_lab.room.name == room and
                        scheduled_lab.time_slot.day == day and
                        scheduled_lab.time_slot.start_time.strftime("%H:%M") == time_slots[2]['start']):
                        
                        # Convert student IDs to group names
                        student_groups = [f"Gruppo {s+1}" for s in scheduled_lab.students[:6]]
                        if len(scheduled_lab.students) > 6:
                            student_groups.append(f"...+{len(scheduled_lab.students)-6}")
                        break
                        
                # Create cell content with lab name and student groups
                cell = f"{lab_name} ({lab['Duration']/60:.1f} ore)"
                if student_groups:
                    cell += "<br>" + "<br>".join(student_groups)
                
                third_row.append(cell)
            else:
                third_row.append("")
        
        # Aggiungiamo la terza riga solo se contiene almeno un laboratorio
        if has_content_third_slot:
            table_data.append(third_row)
            
            # Aggiungiamo la riga per i tutor
            tutor_row = ["", ""]
            for _ in range(len(rooms)):
                tutor_row.append("TUTOR")
            table_data.append(tutor_row)
                
        # Create table for this day
        fig = ff.create_table(
            table_data,
            height_constant=45,  # Aumentato per dare più spazio
            colorscale=[[0, '#E5ECF6'], [1, 'white']],
        )
        
        # Update layout
        fig.update_layout(
            title=f"Programmazione {date_text}",
            margin=dict(l=20, r=20, t=50, b=20),
            height=len(table_data) * 65 + 50,  # Aumentato per dare più spazio verticale
            width=250 + 250 * len(rooms),      # Aumentato per dare più spazio orizzontale
        )
        
        tables.append(fig)
    
    return tables

def _create_room_view(df: pd.DataFrame, time_range: list) -> go.Figure:
    """Create a room-based view of the schedule"""
    
    fig = go.Figure()
    
    # Get unique rooms and dates
    rooms = sorted(df["Room"].unique())
    dates = sorted(df["Date"].unique())
    
    # Create a color scale based on labs
    labs = sorted(df["Lab"].unique())
    colors = px.colors.qualitative.Plotly
    lab_colors = {lab: colors[i % len(colors)] for i, lab in enumerate(labs)}
    
    # Add shapes and annotations for each scheduled lab
    for _, row in df.iterrows():
        room = row["Room"]
        date = row["Date"]
        lab = row["Lab"]
        start = row["Start"]
        end = row["End"]
        
        room_idx = rooms.index(room)
        date_idx = dates.index(date)
        
        # Calculate y position
        y0 = room_idx - 0.4
        y1 = room_idx + 0.4
        
        # Initialize x positions with default values
        x0 = date_idx
        x1 = date_idx + 0.5
        
        try:
            # Calculate x position based on time
            # Convert time to fraction of day
            start_dt = datetime.strptime(start, "%H:%M")
            end_dt = datetime.strptime(end, "%H:%M")
            
            day_start = datetime.strptime("08:30", "%H:%M")
            day_end = datetime.strptime("16:30", "%H:%M")
            
            # Handle lunch break
            lunch_start = datetime.strptime("12:30", "%H:%M")
            lunch_end = datetime.strptime("13:30", "%H:%M")
            
            # Calculate x position
            if end_dt <= lunch_start:
                # Before lunch
                day_length = (lunch_start - day_start).total_seconds()
                x0 = date_idx + (start_dt - day_start).total_seconds() / day_length * 0.4
                x1 = date_idx + (end_dt - day_start).total_seconds() / day_length * 0.4
            elif start_dt >= lunch_end:
                # After lunch
                day_length = (day_end - lunch_end).total_seconds()
                x0 = date_idx + 0.6 + (start_dt - lunch_end).total_seconds() / day_length * 0.4
                x1 = date_idx + 0.6 + (end_dt - lunch_end).total_seconds() / day_length * 0.4
            else:
                # Spans lunch break - visualize as full morning + full afternoon
                if start_dt < lunch_start:
                    # Starts before lunch
                    morning_length = (lunch_start - day_start).total_seconds()
                    x0 = date_idx + (start_dt - day_start).total_seconds() / morning_length * 0.4
                else:
                    # Starts during lunch
                    x0 = date_idx + 0.4  # End of morning
                
                if end_dt > lunch_end:
                    # Ends after lunch
                    afternoon_length = (day_end - lunch_end).total_seconds()
                    x1 = date_idx + 0.6 + (end_dt - lunch_end).total_seconds() / afternoon_length * 0.4
                else:
                    # Ends during lunch
                    x1 = date_idx + 0.6  # Start of afternoon
        except Exception as e:
            # In case of calculation error, use safe default values
            x0 = date_idx
            x1 = date_idx + 0.5
        
        # Add rectangle for this lab
        fig.add_shape(
            type="rect",
            x0=x0,
            y0=y0,
            x1=x1,
            y1=y1,
            fillcolor=lab_colors[lab],
            opacity=0.7,
            line=dict(color="black", width=1)
        )
        
        # Add text annotation
        fig.add_annotation(
            x=(x0 + x1) / 2,
            y=(y0 + y1) / 2,
            text=f"{lab}<br>{start}-{end}",
            showarrow=False,
            font=dict(color="black", size=10),
        )
    
    # Create the base heatmap (just for axes)
    heatmap_data = np.zeros((len(rooms), len(dates)))
    
    fig.add_trace(
        go.Heatmap(
            z=heatmap_data,
            x=dates,
            y=rooms,
            showscale=False,
            colorscale=[[0, 'rgba(0,0,0,0)'], [1, 'rgba(0,0,0,0)']],
        )
    )
    
    # Update layout
    fig.update_layout(
        title="Schedule by Room",
        height=100 + 100 * len(rooms),
        margin=dict(l=100, r=50, t=100, b=50),
        xaxis=dict(
            title="Date",
            tickangle=45,
            side="top",
        ),
        yaxis=dict(
            title="Room",
            tickangle=0,
        ),
    )
    
    # Add legend for labs
    for i, lab in enumerate(labs):
        fig.add_trace(go.Scatter(
            x=[None],
            y=[None],
            mode='markers',
            marker=dict(size=10, color=lab_colors[lab]),
            name=lab,
            showlegend=True
        ))
    
    return fig

def _create_lab_view(df: pd.DataFrame, time_range: list) -> go.Figure:
    """Create a lab-based view of the schedule"""
    
    fig = go.Figure()
    
    # Get unique labs and dates
    labs = sorted(df["Lab"].unique())
    dates = sorted(df["Date"].unique())
    
    # Create a color scale based on rooms
    rooms = sorted(df["Room"].unique())
    colors = px.colors.qualitative.Plotly
    room_colors = {room: colors[i % len(colors)] for i, room in enumerate(rooms)}
    
    # Add shapes and annotations for each scheduled lab
    for _, row in df.iterrows():
        room = row["Room"]
        date = row["Date"]
        lab = row["Lab"]
        start = row["Start"]
        end = row["End"]
        
        lab_idx = labs.index(lab)
        date_idx = dates.index(date)
        
        # Calculate y position
        y0 = lab_idx - 0.4
        y1 = lab_idx + 0.4
        
        # Initialize x positions with default values
        x0 = date_idx
        x1 = date_idx + 0.5
        
        try:
            # Calculate x position based on time
            # Convert time to fraction of day
            start_dt = datetime.strptime(start, "%H:%M")
            end_dt = datetime.strptime(end, "%H:%M")
            
            day_start = datetime.strptime("08:30", "%H:%M")
            day_end = datetime.strptime("16:30", "%H:%M")
            
            # Handle lunch break
            lunch_start = datetime.strptime("12:30", "%H:%M")
            lunch_end = datetime.strptime("13:30", "%H:%M")
            
            # Calculate x position
            if end_dt <= lunch_start:
                # Before lunch
                day_length = (lunch_start - day_start).total_seconds()
                x0 = date_idx + (start_dt - day_start).total_seconds() / day_length * 0.4
                x1 = date_idx + (end_dt - day_start).total_seconds() / day_length * 0.4
            elif start_dt >= lunch_end:
                # After lunch
                day_length = (day_end - lunch_end).total_seconds()
                x0 = date_idx + 0.6 + (start_dt - lunch_end).total_seconds() / day_length * 0.4
                x1 = date_idx + 0.6 + (end_dt - lunch_end).total_seconds() / day_length * 0.4
            else:
                # Spans lunch break - visualize as full morning + full afternoon
                if start_dt < lunch_start:
                    # Starts before lunch
                    morning_length = (lunch_start - day_start).total_seconds()
                    x0 = date_idx + (start_dt - day_start).total_seconds() / morning_length * 0.4
                else:
                    # Starts during lunch
                    x0 = date_idx + 0.4  # End of morning
                
                if end_dt > lunch_end:
                    # Ends after lunch
                    afternoon_length = (day_end - lunch_end).total_seconds()
                    x1 = date_idx + 0.6 + (end_dt - lunch_end).total_seconds() / afternoon_length * 0.4
                else:
                    # Ends during lunch
                    x1 = date_idx + 0.6  # Start of afternoon
        except Exception as e:
            # In case of calculation error, use safe default values
            x0 = date_idx
            x1 = date_idx + 0.5
        
        # Add rectangle for this lab
        fig.add_shape(
            type="rect",
            x0=x0,
            y0=y0,
            x1=x1,
            y1=y1,
            fillcolor=room_colors[room],
            opacity=0.7,
            line=dict(color="black", width=1)
        )
        
        # Add text annotation
        fig.add_annotation(
            x=(x0 + x1) / 2,
            y=(y0 + y1) / 2,
            text=f"{room}<br>{start}-{end}",
            showarrow=False,
            font=dict(color="black", size=10),
        )
    
    # Create the base heatmap (just for axes)
    heatmap_data = np.zeros((len(labs), len(dates)))
    
    fig.add_trace(
        go.Heatmap(
            z=heatmap_data,
            x=dates,
            y=labs,
            showscale=False,
            colorscale=[[0, 'rgba(0,0,0,0)'], [1, 'rgba(0,0,0,0)']],
        )
    )
    
    # Update layout
    fig.update_layout(
        title="Schedule by Lab",
        height=100 + 100 * len(labs),
        margin=dict(l=100, r=50, t=100, b=50),
        xaxis=dict(
            title="Date",
            tickangle=45,
            side="top",
        ),
        yaxis=dict(
            title="Lab",
            tickangle=0,
        ),
    )
    
    # Add legend for rooms
    for i, room in enumerate(rooms):
        fig.add_trace(go.Scatter(
            x=[None],
            y=[None],
            mode='markers',
            marker=dict(size=10, color=room_colors[room]),
            name=room,
            showlegend=True
        ))
    
    return fig

def _create_day_view(df: pd.DataFrame, time_range: list) -> go.Figure:
    """Create a day-based view of the schedule"""
    
    # Find the earliest and latest time slots
    min_time = min(df["Start"].apply(lambda x: datetime.strptime(x, "%H:%M")))
    max_time = max(df["End"].apply(lambda x: datetime.strptime(x, "%H:%M")))
    
    # Create a continuous time axis
    time_axis = pd.date_range(
        min_time.strftime("%H:%M"), 
        max_time.strftime("%H:%M"), 
        freq="30min"
    ).strftime("%H:%M")
    
    fig = go.Figure()
    
    # Get unique dates
    dates = sorted(df["Date"].unique())
    
    # For each date, create a subplot
    for date_idx, date in enumerate(dates):
        date_df = df[df["Date"] == date]
        
        # Get all rooms and labs for this date
        rooms = sorted(date_df["Room"].unique())
        labs = sorted(date_df["Lab"].unique())
        
        # Create a color scale based on labs
        colors = px.colors.qualitative.Plotly
        lab_colors = {lab: colors[i % len(colors)] for i, lab in enumerate(labs)}
        
        # For each lab scheduled on this date
        for _, row in date_df.iterrows():
            room = row["Room"]
            lab = row["Lab"]
            start = row["Start"]
            end = row["End"]
            
            room_idx = rooms.index(room)
            
            # Initialize x positions with default values
            x0 = 0
            x1 = 0.5
            
            try:
                # Calculate x position based on time (8:30 - 16:30)
                start_dt = datetime.strptime(start, "%H:%M")
                end_dt = datetime.strptime(end, "%H:%M")
                
                day_start = datetime.strptime("08:30", "%H:%M")
                day_end = datetime.strptime("16:30", "%H:%M")
                
                # Handle lunch break
                lunch_start = datetime.strptime("12:30", "%H:%M")
                lunch_end = datetime.strptime("13:30", "%H:%M")
                
                # Initialize x positions with default values
                x0 = 0
                x1 = 0.5
                
                try:
                    # Calculate x position
                    if end_dt <= lunch_start:
                        # Before lunch
                        day_length = (lunch_start - day_start).total_seconds()
                        x0 = (start_dt - day_start).total_seconds() / day_length * 0.4
                        x1 = (end_dt - day_start).total_seconds() / day_length * 0.4
                    elif start_dt >= lunch_end:
                        # After lunch
                        day_length = (day_end - lunch_end).total_seconds()
                        x0 = 0.6 + (start_dt - lunch_end).total_seconds() / day_length * 0.4
                        x1 = 0.6 + (end_dt - lunch_end).total_seconds() / day_length * 0.4
                    else:
                        # Spans lunch break - visualize as full morning + full afternoon
                        if start_dt < lunch_start:
                            # Starts before lunch
                            morning_length = (lunch_start - day_start).total_seconds()
                            x0 = (start_dt - day_start).total_seconds() / morning_length * 0.4
                        else:
                            # Starts during lunch
                            x0 = 0.4  # End of morning
                        
                        if end_dt > lunch_end:
                            # Ends after lunch
                            afternoon_length = (day_end - lunch_end).total_seconds()
                            x1 = 0.6 + (end_dt - lunch_end).total_seconds() / afternoon_length * 0.4
                        else:
                            # Ends during lunch
                            x1 = 0.6  # Start of afternoon
                except Exception as e:
                    # In case of calculation error, use safe default values
                    x0 = 0
                    x1 = 0.5
                
                # Scale to match the date position
                x0 += date_idx
                x1 += date_idx
            except Exception as e:
                # In case of calculation error, use safe default values
                x0 = date_idx
                x1 = date_idx + 0.5
                
            # Calculate y position
            y0 = room_idx - 0.4
            y1 = room_idx + 0.4
            
            # Add rectangle for this lab
            fig.add_shape(
                type="rect",
                x0=x0,
                y0=y0,
                x1=x1,
                y1=y1,
                fillcolor=lab_colors[lab],
                opacity=0.7,
                line=dict(color="black", width=1)
            )
            
            # Add text annotation
            fig.add_annotation(
                x=(x0 + x1) / 2,
                y=(y0 + y1) / 2,
                text=f"{lab}<br>{start}-{end}",
                showarrow=False,
                font=dict(color="black", size=10),
            )
    
    # Create the base heatmap data (just for axes)
    heatmap_data = np.zeros((len(rooms), len(dates)))
    
    # Add heatmap for the base grid
    fig.add_trace(
        go.Heatmap(
            z=heatmap_data,
            x=dates,
            y=rooms,
            showscale=False,
            colorscale=[[0, 'rgba(0,0,0,0)'], [1, 'rgba(0,0,0,0)']],
        )
    )
    
    # Update layout
    fig.update_layout(
        title="Schedule by Day",
        height=100 + 100 * len(rooms),
        margin=dict(l=100, r=50, t=100, b=50),
        xaxis=dict(
            title="Date",
            tickangle=45,
        ),
        yaxis=dict(
            title="Room",
            tickangle=0,
        ),
    )
    
    # Add legend for labs
    for i, lab in enumerate(labs):
        fig.add_trace(go.Scatter(
            x=[None],
            y=[None],
            mode='markers',
            marker=dict(size=10, color=lab_colors[lab]),
            name=lab,
            showlegend=True
        ))
    
    return fig

def create_student_assignment_chart(schedule_data: ScheduleData) -> go.Figure:
    """Create a chart showing how many students are assigned to each lab"""
    if not schedule_data.scheduled_labs:
        return None
        
    # Count students per lab
    lab_counts = {}
    for lab in schedule_data.get_selected_labs():
        lab_counts[lab.name] = 0
    
    for scheduled_lab in schedule_data.scheduled_labs:
        lab_counts[scheduled_lab.lab.name] += len(scheduled_lab.students)
    
    # Convert to DataFrame
    df = pd.DataFrame({
        'Lab': list(lab_counts.keys()),
        'Students': list(lab_counts.values())
    })
    
    # Sort by lab name
    df = df.sort_values('Lab')
    
    # Create bar chart
    fig = px.bar(
        df, 
        x='Lab', 
        y='Students',
        title='Number of Students Assigned to Each Lab',
        labels={'Students': 'Number of Students', 'Lab': 'Laboratory'},
        color='Students',
        color_continuous_scale=px.colors.sequential.Viridis
    )
    
    fig.update_layout(
        xaxis_tickangle=-45,
        height=500,
        margin=dict(l=50, r=50, t=100, b=150),
    )
    
    return fig