def date_time_format(date_time):
    year = date_time[:4]
    month = date_time[4:6]
    day = date_time[6:8]
    hour = date_time[8:10]
    minutes = date_time[10:12]
    seconds = date_time[12:14]
    return '{0}/{1}/{2} {3}:{4}:{5}'.format(
        day, month, year, hour, minutes, seconds
    )
