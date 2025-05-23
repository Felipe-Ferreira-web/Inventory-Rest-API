from datetime import datetime


class Time(datetime):
    
    @staticmethod
    def register_time():

        time = datetime.now()
        time_format = time.strftime("%d/%m/%Y %H:%M:%S")
        time_format = str(time_format)
        return time_format