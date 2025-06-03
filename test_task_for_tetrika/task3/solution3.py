def appearance(intervals: dict[str, list[int]]) -> int:
    lesson_start, lesson_end = intervals["lesson"]
    events = []

    # события для ученика
    for i in range(0, len(intervals["pupil"]), 2):
        start = max(intervals["pupil"][i], lesson_start)
        end = min(intervals["pupil"][i + 1], lesson_end)
        if start < end:
            events.append((start, 1, "pupil"))  # 1 - вход
            events.append((end, -1, "pupil"))  # -1 - выход

    # события для учителя
    for i in range(0, len(intervals["tutor"]), 2):
        start = max(intervals["tutor"][i], lesson_start)
        end = min(intervals["tutor"][i + 1], lesson_end)
        if start < end:
            events.append((start, 1, "tutor"))
            events.append((end, -1, "tutor"))

    # сортируем события по времени
    events.sort()

    total_time = 0
    pupil_present = 0
    tutor_present = 0
    last_time = None

    for time, event_type, person in events:
        # Если и ученик, и учитель были одновременно на уроке
        if pupil_present > 0 and tutor_present > 0 and last_time is not None:
            total_time += time - last_time

        # счетчики присутствия
        if person == "pupil":
            pupil_present += event_type
        else:
            tutor_present += event_type

        last_time = time

    return total_time
