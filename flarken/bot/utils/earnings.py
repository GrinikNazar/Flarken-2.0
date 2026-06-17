
def calculate_earnings(total_points, best_days, place, threshold_met):
    earnings = 0

    if threshold_met:
        if place == 1:
            earnings += 1000
        elif place == 2:
            earnings += 700
        elif place == 3:
            earnings += 500
    else:
        if place == 1:
            earnings += 700
        elif place == 2:
            earnings += 500

    if threshold_met:
        if total_points >= 200:
            earnings += 3000
        elif total_points >= 180:
            earnings += 2500
        elif total_points >= 160:
            earnings += 2000
        elif total_points >= 140:
            earnings += 1500
        elif total_points >= 120:
            earnings += 1000
        elif total_points >= 100:
            earnings += 700
    else:
        if total_points >= 200:
            earnings += 2000
        elif total_points >= 180:
            earnings += 1500
        elif total_points >= 160:
            earnings += 1000
        elif total_points >= 140:
            earnings += 700
        elif total_points >= 120:
            earnings += 500
        elif total_points >= 100:
            earnings += 300

    best_day_bonus = 50 if threshold_met else 30
    earnings += best_days * best_day_bonus

    return earnings