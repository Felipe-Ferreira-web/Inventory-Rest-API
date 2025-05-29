from datetime import datetime

# Clase com a função de registrar a data da operação realizada
class Time(datetime):
    
    @staticmethod
    def register_time():

        time = datetime.now()
        time_format = time.strftime("%d/%m/%Y %H:%M:%S")
        time_format = str(time_format) # Cria a data já formatada
        return time_format