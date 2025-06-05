from werkzeug.exceptions import BadRequest

# Converte uma string para booleano para ser usado nos filtros de pesquisa no get
def str_to_bool(value):


    # Se o valor for booleano, retorna diretamente
    if isinstance(value, bool):
        return value
    
    # Se for uma string 
    if isinstance(value, str):

        # Converte string minusculas para e verfica se é True
        if value.lower() in ['true', '1']:
            return True
        
        # Verifica se é False
        elif value.lower() in ['false', '0']:
            return False
        
    raise BadRequest("The value must be 'true', 'false', '1' or '0'.")