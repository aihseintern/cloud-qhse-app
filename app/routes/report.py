from collections import Counter
from datetime import datetime, timedelta
import random
from flask import Blueprint, Response, abort, render_template, redirect, request, url_for, flash, session, jsonify
from flask_login import login_required
from app.models import CCTV, CCTVLocation, DetectedObject, Detector, DetectorType, Weight
from app import db
import logging
from utils.auth import get_allowed_permission_ids
from sqlalchemy.orm import joinedload
from dateutil.relativedelta import relativedelta

logging.basicConfig(level=logging.DEBUG)

report_bp = Blueprint('report', __name__, url_prefix='/report')

# REPORT
# @report_bp.route("/dashboard")
# @login_required
# def dashboard():
#     detected_objects = DetectedObject.query \
#                             .join(Detector, DetectedObject.detector_id == Detector.id) \
#                             .join(CCTV, Detector.cctv_id == CCTV.id) \
#                             .join(DetectorType, Detector.detector_type_id == DetectorType.id) \
#                             .join(CCTVLocation, CCTV.cctv_location_id == CCTVLocation.id) \
#                             .join(Weight, Detector.weight_id == Weight.id) \
#                             .filter(DetectedObject.permission_id == session.get('permission_id')) \
#                             .order_by(DetectedObject.timestamp.desc()) \
#                             .all()
    
#     cctv_locations = CCTVLocation.query.all()
    
#     # Data struktur untuk pie chart berdasarkan tipe CCTV
#     # Ambil semua CCTV berdasarkan lokasi
#     cctv_by_location = {location.id: CCTV.query.filter_by(cctv_location_id=location.id).all() for location in cctv_locations}

#     # Data struktur untuk pie chart berdasarkan tipe CCTV dan jumlah objek yang terdeteksi per tipe
#     detected_objects_by_cctv_type = {}

#     for location in cctv_locations:
#         # Hitung jumlah objek yang terdeteksi per tipe CCTV di lokasi tersebut
#         types_counter = Counter()
        
#         # Looping untuk setiap CCTV di lokasi
#         for cctv in cctv_by_location[location.id]:
#             # Hitung jumlah objek yang terdeteksi untuk setiap tipe CCTV
#             detected_object_count = DetectedObject.query \
#                 .join(Detector, DetectedObject.detector_id == Detector.id) \
#                 .filter(Detector.cctv_id == cctv.id) \
#                 .count()
            
#             # Tambahkan hasil ke counter
#             types_counter[cctv.type] += detected_object_count
        
#         detected_objects_by_cctv_type[location.name] = types_counter
        
#     print(detected_objects_by_cctv_type)
#     for location, types_counter in detected_objects_by_cctv_type.items():
#         sorted_types_counter = dict(sorted(types_counter.items(), key=lambda item: item[1], reverse=True))
#         top_3_types = dict(list(sorted_types_counter.items())[:3])
#         other_types = dict(list(sorted_types_counter.items())[3:])
#         detected_objects_by_cctv_type[location] = top_3_types
#         detected_objects_by_cctv_type[location]['Other'] = sum(other_types.values())

#     # Data struktur untuk bar chart berdasarkan hari dalam 7 hari terakhir
#     # After defining daily_counts
#     daily_counts = Counter([detected_object.timestamp.date() for detected_object in detected_objects])


#     # Check if daily_counts is empty
#     if daily_counts:
#         # If not empty, proceed to get the last 7 days
#         last_day = max(daily_counts)
#         last_7_days = [(last_day - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(7)]
#     else:
#         # If empty, set last_7_days to an empty list or some default values
#         last_7_days = []

#     # Ensure daily_detected_object_counts has values for each day in last_7_days
#     daily_detected_object_counts = [daily_counts.get(datetime.strptime(day, '%Y-%m-%d').date(), 0) for day in last_7_days]

    
#     # Data Struktur untuk scatter plot berdasarkan lokasi CCTV
#     detected_objects_by_location = Counter([detected_object.detector.cctv.cctv_location_id for detected_object in detected_objects])
#     scatter_data = []
#     for location in cctv_locations:
#         location_id = location.id
#         count = detected_objects_by_location.get(location_id, 0)  # Jumlah detected objects
#         scatter_data.append({
#             'name': location.name,  # Nama lokasi
#             'x': random.uniform(0, 100),  # Koordinat x
#             'y': random.uniform(0, 100),  # Koordinat y
#             'count': count  # Jumlah objek yang terdeteksi
#         })

#     # Jumlah data
#     cctv_count = CCTV.query.count()
#     weight_count = Weight.query.count()
#     detector_count = Detector.query.count()
#     detected_object_count = DetectedObject.query.count()

#     return render_template('new_dashboard.html', 
#                            detected_objects_by_cctv_type=detected_objects_by_cctv_type, 
#                             last_7_days=last_7_days,
#                             daily_detected_object_counts=daily_detected_object_counts,   
#                             scatter_data=scatter_data,    
#                             cctv_count=cctv_count,
#                             weight_count=weight_count,
#                             detector_count=detector_count,
#                             detected_object_count=detected_object_count,                       
#                             cctv_locations=cctv_locations)


@report_bp.route("/dashboard")
@login_required
def dashboard():
    ###############################
    ##### Base Configuration ######
    ###############################
    session_permission = session.get('permission_id')
    selected_location = request.args.get('location')
    subquery = (
        db.session.query(CCTVLocation.name, CCTVLocation.id)
        .distinct(CCTVLocation.name)
        .subquery()
    )

    cctv_locations = (
        db.session.query(subquery.c.name)
        .order_by(subquery.c.id)
    ).all()

    cctv_locations = [loc.name for loc in cctv_locations]
    detected_objects_query = (
        db.session.query(DetectedObject)
        .join(Detector, DetectedObject.detector_id == Detector.id)
        .join(CCTV, Detector.cctv_id == CCTV.id)
        .filter(DetectedObject.permission_id == session_permission)
    )
    
    if selected_location:
        detected_objects_query = detected_objects_query.filter(
            CCTV.cctv_location.has(name=selected_location)
        )
        
    current_date = datetime.utcnow() + timedelta(hours=7)


    ###########################
    ##### Dashboard Card ######
    ###########################
    all_cctv = db.session.query(CCTV).filter_by(permission_id=session_permission).count()
    all_detectors = db.session.query(Detector).filter_by(permission_id=session_permission).count()
    all_weight = db.session.query(Detector).filter(
        Detector.permission_id == session_permission,
        Detector.weight_id.isnot(None)
    ).count()
    all_detection = db.session.query(DetectedObject).filter_by(permission_id=session_permission).count()

    
    #################################
    ##### Daily Data Detected ######
    ################################
    start_time = current_date - timedelta(hours=24)
    
    daily_detected_results = (
        detected_objects_query
        .filter(DetectedObject.timestamp >= start_time)
        .with_entities(
            db.func.date_trunc('hour', DetectedObject.timestamp).label('detection_hour'),
            CCTV.type.label('type'),
            DetectedObject.name.label('object_name'),
            db.func.count(DetectedObject.id).label('count')
        )
        .group_by(db.func.date_trunc('hour', DetectedObject.timestamp), CCTV.type, DetectedObject.name)
        .order_by(db.func.date_trunc('hour', DetectedObject.timestamp))
        .all()
    )

    daily_counts_dict = {}
    daily_object_types_dict = {}
    daily_pie_chart_types_dict = {}

    for row in daily_detected_results:
        detection_hour = row.detection_hour
        cctv_type = row.type
        object_name = row.object_name
        count = row.count
        
        daily_counts_dict[detection_hour] = daily_counts_dict.get(detection_hour, 0) + count

        daily_object_types_dict[object_name] = daily_object_types_dict.get(object_name, 0) + count

        daily_pie_chart_types_dict[cctv_type] = daily_pie_chart_types_dict.get(cctv_type, 0) + count

    daily_labels = [
        (current_date - timedelta(hours=i)).replace(minute=0, second=0, microsecond=0) for i in range(24)
    ]
    daily_labels.reverse()

    daily_detected_object_counts = [
        daily_counts_dict.get(label, 0) for label in daily_labels
    ]

    daily_object_counts = {object_name: 0 for object_name in daily_object_types_dict.keys()}

    for label in daily_labels:
        for row in daily_detected_results:
            detection_hour = row.detection_hour
            object_name = row.object_name
            count = row.count
            if detection_hour == label:
                daily_object_counts[object_name] += count

    daily_object_counts = list(daily_object_counts.values())

    daily_object_types = list(daily_object_types_dict.keys())
    
    daily_pie_chart_counts_dict = {cctv_type: 0 for cctv_type in daily_pie_chart_types_dict.keys()}

    for label in daily_labels:
        for row in daily_detected_results:
            detection_hour = row.detection_hour
            cctv_type = row.type
            count = row.count
            if detection_hour == label:
                daily_pie_chart_counts_dict[cctv_type] += count

    daily_pie_chart_types_list = list(daily_pie_chart_counts_dict.keys())
    daily_pie_chart_counts_list = list(daily_pie_chart_counts_dict.values())

    if len(daily_pie_chart_types_list) > 4:
        other_count = sum(daily_pie_chart_counts_list[4:])
        daily_pie_chart_types_list = daily_pie_chart_types_list[:4] + ['Other']
        daily_pie_chart_counts_list = daily_pie_chart_counts_list[:4] + [other_count]
    
    # Debug Output 
    # total_pie_chart_counts = sum(daily_pie_chart_counts_list)
    # total_daily_detections = sum(daily_detected_object_counts)
    # formatted_daily_labels = [label.strftime('%Y-%m-%d %H:%M') for label in daily_labels]

    # # Combine formatted labels and daily_detected_object_counts
    # hourly_detected_counts = list(zip(formatted_daily_labels, daily_detected_object_counts))
    
    # print('Start Time', start_time)
    # print(f'Selected Location: {selected_location}')
    # print('Hourly Detected Counts', hourly_detected_counts)
    # print(f"Total detections in the last 24 hours: {total_daily_detections}")
    # print("Daily Object Types:", daily_object_types)
    # print("Daily Object Counts:", daily_object_counts) 
    # print("Total Daily Object Counts (Top 10):", sum(daily_object_counts))
    # print("Pie Chart Types List:", daily_pie_chart_types_list)
    # print("Pie Chart Counts List:", daily_pie_chart_counts_list)
    # print("Total Pie Chart Counts:", total_pie_chart_counts)

    # if total_daily_detections == sum(daily_object_counts) == total_pie_chart_counts:
    #     print("All totals are consistent.")
    # else:
    #     print("Totals are inconsistent.")
    
    ################################
    ##### Weekly Data Detected #####
    ###############################
    seven_days_ago = current_date - timedelta(days=7)
    
    weekly_detected_results = (
        detected_objects_query
        .filter(DetectedObject.timestamp >= seven_days_ago)
        .with_entities(
            db.func.date_trunc('day', DetectedObject.timestamp).label('detection_day'),
            CCTV.type.label('type'),
            DetectedObject.name.label('object_name'),
            db.func.count(DetectedObject.id).label('count')
        )
        .group_by(db.func.date_trunc('day', DetectedObject.timestamp), CCTV.type, DetectedObject.name)
        .order_by(db.func.date_trunc('day', DetectedObject.timestamp))
        .all()
    )

    weekly_counts_dict = {}
    weekly_object_types_dict = {}
    weekly_pie_chart_types_dict = {}

    for row in weekly_detected_results:
        detection_day = row.detection_day.strftime('%Y-%m-%d')  # Convert to string format YYYY-MM-DD
        cctv_type = row.type
        object_name = row.object_name
        count = row.count

        weekly_counts_dict[detection_day] = weekly_counts_dict.get(detection_day, 0) + count

        weekly_object_types_dict[object_name] = weekly_object_types_dict.get(object_name, 0) + count

        weekly_pie_chart_types_dict[cctv_type] = weekly_pie_chart_types_dict.get(cctv_type, 0) + count

    weekly_labels = [(current_date - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(7)]
    weekly_labels.reverse()

    weekly_detected_object_counts = [
        weekly_counts_dict.get(label, 0) for label in weekly_labels
    ]

    weekly_object_counts_dict = {object_name: 0 for object_name in weekly_object_types_dict.keys()}

    for row in weekly_detected_results:
        detection_day = row.detection_day.strftime('%Y-%m-%d')
        object_name = row.object_name
        count = row.count
        if detection_day in weekly_labels:
            weekly_object_counts_dict[object_name] += count

    weekly_object_types = list(weekly_object_types_dict.keys())
    weekly_object_counts = list(weekly_object_counts_dict.values())

    weekly_pie_chart_counts_dict = {cctv_type: 0 for cctv_type in weekly_pie_chart_types_dict.keys()}

    for row in weekly_detected_results:
        detection_day = row.detection_day.strftime('%Y-%m-%d')
        cctv_type = row.type
        count = row.count
        if detection_day in weekly_labels:
            weekly_pie_chart_counts_dict[cctv_type] += count

    weekly_pie_chart_types_list = list(weekly_pie_chart_counts_dict.keys())
    weekly_pie_chart_counts_list = list(weekly_pie_chart_counts_dict.values())

    if len(weekly_pie_chart_types_list) > 4:
        other_count = sum(weekly_pie_chart_counts_list[4:])
        weekly_pie_chart_types_list = weekly_pie_chart_types_list[:4] + ['Other']
        weekly_pie_chart_counts_list = weekly_pie_chart_counts_list[:4] + [other_count]

    # Debug Output 
    # total_weekly_detections = sum(weekly_detected_object_counts)
    # total_weekly_pie_chart_counts = sum(weekly_pie_chart_counts_list)
    # print(f'Weekly Object Count : {weekly_detected_object_counts}')
    # print(f'Total Weekly Detection : {total_weekly_detections}')
    # print(f'Weekly Object Types : {weekly_object_types}')
    # print(f'Weekly Object Counts : {weekly_object_counts}')
    # print(f'Total Weekly Object Counts : {sum(weekly_object_counts)}')
    # print(f'Pie Chart Types : {weekly_pie_chart_types_list}')
    # print(f'Pie Chart Counts : {weekly_pie_chart_counts_list}')
    # print(f'Total Pie Chart Counts : {total_weekly_pie_chart_counts}')

    # if total_weekly_detections == sum(weekly_object_counts) == total_weekly_pie_chart_counts:
    #     print("All totals are consistent.")
    # else:
    #     print("Totals are inconsistent.")

    
    return render_template(
        'dashboard.html',
        session_permission=session_permission,
        selected_location=selected_location,
        cctv_locations=cctv_locations,
        all_cctv=all_cctv,
        all_weight=all_weight,
        all_detectors=all_detectors,
        all_detection=all_detection,
        daily_labels=daily_labels,
        daily_counts=daily_detected_object_counts,
        daily_object_types=daily_object_types,
        daily_object_counts=daily_object_counts,
        daily_pie_chart_counts=daily_pie_chart_counts_list,
        daily_pie_chart_types=daily_pie_chart_types_list,
        weekly_labels=weekly_labels,
        weekly_counts=weekly_detected_object_counts,
        weekly_object_types=weekly_object_types,
        weekly_object_counts=weekly_object_counts,
        weekly_pie_chart_types=weekly_pie_chart_types_list,
        weekly_pie_chart_counts=weekly_pie_chart_counts_list
    )


@report_bp.route('/detected-object', methods=['GET'])
@login_required
def detected_object():
    page = request.args.get('page', 1, type=int)
    per_page = 10  # Jumlah objek per halaman
    search_query = request.args.get('search_query')

    if search_query:
        detected_objects = DetectedObject.query.join(Detector).join(CCTV).join(CCTVLocation).join(Weight).join(DetectorType, Weight.detector_type_id == DetectorType.id) \
            .filter(
                db.or_(
                    DetectedObject.name.ilike(f'%{search_query}%'),
                    CCTVLocation.name.ilike(f'%{search_query}%'),
                    CCTV.type.ilike(f'%{search_query}%'),  
                    DetectorType.name.ilike(f'%{search_query}%'),
                ),
                DetectedObject.permission_id == session.get('permission_id')
            ) \
            .order_by(DetectedObject.timestamp.desc()) \
            .paginate(page=page, per_page=per_page)
    else:
        detected_objects = DetectedObject.query.join(Detector).join(CCTV) \
            .filter(DetectedObject.permission_id == session.get('permission_id')) \
            .order_by(DetectedObject.timestamp.desc()) \
            .paginate(page=page, per_page=per_page)

    return render_template('detected_object.html', detected_objects=detected_objects, search_query=search_query)

@report_bp.route('/detected-object/view-object/<int:object_id>', methods=['GET'])
@login_required
def view_object(object_id):
    detected_object = DetectedObject.query.get_or_404(object_id)    
    return render_template('view_object.html', detected_object=detected_object)   